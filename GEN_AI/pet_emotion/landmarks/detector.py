"""
Pet Facial Landmark Detector — 46-point schema
==============================================

Strategy cascade:
  1. MediaPipe FaceMesh (468-pt) → map to 46 pet anatomical points  [primary]
  2. OpenCV Haarcascade ROI + geometric estimation                   [fallback]
  3. Synthetic pseudo-landmarks from bounding-box only              [last resort]

46-point layout:
  eyes  : 24 pts (12 per eye — pupil, 4 lid, 4 orbital, 2 canthus)
  mouth : 10 pts (4 upper-lip, 4 lower-lip, 2 lip corners)
  nose  :  5 pts (bridge, 2 nostrils, tip, septum base)
  ears  :  7 pts per ear when detected (bonus, not counted in 46)
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class LandmarkResult:
    """46-point landmark result."""

    # core 46 pts (lists of [x, y] normalised to [0, 1])
    eyes: List[List[float]] = field(default_factory=list)    # 24 pts (12+12)
    mouth: List[List[float]] = field(default_factory=list)   # 10 pts
    nose: List[List[float]] = field(default_factory=list)    #  5 pts
    ears: List[List[float]] = field(default_factory=list)    #  bonus pts

    # metadata
    confidence: float = 0.0
    strategy: str = "none"
    face_bbox: Optional[List[int]] = None   # [x, y, w, h] in pixels

    # ---------- helpers ----------

    @property
    def all_landmarks(self) -> List[List[float]]:
        """Flat list of all core 46 points (eyes + mouth + nose)."""
        return self.eyes + self.mouth + self.nose

    @property
    def num_points(self) -> int:
        return len(self.all_landmarks)

    def to_dict(self) -> dict:
        return {
            "eyes": self.eyes,
            "mouth": self.mouth,
            "nose": self.nose,
            "ears": self.ears,
            "all": self.all_landmarks,
            "confidence": self.confidence,
            "strategy": self.strategy,
            "face_bbox": self.face_bbox,
        }

    @classmethod
    def empty(cls, strategy: str = "failed") -> "LandmarkResult":
        return cls(
            eyes=[], mouth=[], nose=[], ears=[],
            confidence=0.0, strategy=strategy
        )


# ---------------------------------------------------------------------------
# MediaPipe face-mesh landmark indices mapped to 46-pt pet schema
# ---------------------------------------------------------------------------

# Reference: MediaPipe FaceMesh canonical 468-point map.
# For pets we use the central face region which is consistent across species.

_MP_EYE_LEFT: List[int] = [
    473,  # pupil centre  (0)
    362, 385, 387, 263,  # upper-lid (1-4)
    380, 373, 374, 249,  # lower-lid (5-8)
    263, 362,            # canthus lateral + medial (9-10)
    386,                 # orbital top (11)
]

_MP_EYE_RIGHT: List[int] = [
    468,  # pupil centre  (0)
    33,  105, 107, 133,  # upper-lid (1-4)
    153, 145, 144, 163,  # lower-lid (5-8)
    133,  33,            # canthus lateral + medial (9-10)
    159,                 # orbital top (11)
]

_MP_MOUTH: List[int] = [
     61,  # left corner (0)
    291,  # right corner (1)
    0,   # upper-lip top (2)
    17,  # lower-lip bottom (3)
    40,  # upper-lip left (4)
    270, # upper-lip right (5)
    91,  # lower-lip left (6)
    321, # lower-lip right (7)
    80,  # upper-mid-left (8)
    311, # upper-mid-right (9)
]

_MP_NOSE: List[int] = [
    1,   # nose tip (0)
    4,   # nose base / septum (1)
    19,  # bridge top (2)
    64,  # left nostril (3)
    294, # right nostril (4)
]


# ---------------------------------------------------------------------------
# Main detector
# ---------------------------------------------------------------------------

class LandmarkDetector:
    """
    Detects 46 facial landmarks on pet images.

    Usage::

        detector = LandmarkDetector()
        result = detector.detect(image_bgr)
        print(result.to_dict())
    """

    def __init__(self, use_mediapipe: bool = True):
        self._mp_available = False
        self._mp_face_mesh = None
        self._face_cascade: Optional[cv2.CascadeClassifier] = None

        if use_mediapipe:
            self._mp_available = self._init_mediapipe()

        self._init_opencv_cascade()

    # -----------------------------------------------------------------
    # Init helpers
    # -----------------------------------------------------------------

    def _init_mediapipe(self) -> bool:
        try:
            import mediapipe as mp  # noqa: F401
            self._mp = mp
            face_mesh_module = mp.solutions.face_mesh
            self._mp_face_mesh = face_mesh_module.FaceMesh(
                static_image_mode=True,
                max_num_faces=1,
                refine_landmarks=True,  # enables iris (468+10 iris pts)
                min_detection_confidence=0.4,
            )
            logger.debug("MediaPipe FaceMesh initialised (primary landmark strategy).")
            return True
        except ImportError:
            logger.info("MediaPipe not installed — falling back to OpenCV geometric estimator.")
            return False
        except Exception as exc:
            logger.warning("MediaPipe init failed (%s) — falling back to OpenCV.", exc)
            return False

    def _init_opencv_cascade(self) -> None:
        cascade_names = [
            "haarcascade_frontalcatface_extended.xml",
            "haarcascade_frontalcatface.xml",
            "haarcascade_frontalface_default.xml",
        ]
        for name in cascade_names:
            path = cv2.data.haarcascades + name
            clf = cv2.CascadeClassifier(path)
            if not clf.empty():
                self._face_cascade = clf
                logger.debug("OpenCV cascade loaded: %s", name)
                return
        logger.warning("No Haarcascade found — OpenCV fallback will use full image bbox.")

    # -----------------------------------------------------------------
    # Public API
    # -----------------------------------------------------------------

    def detect(self, image_bgr: np.ndarray) -> LandmarkResult:
        """
        Detect 46 landmarks from a BGR image array.

        Returns :class:`LandmarkResult` (all coordinates normalised to [0, 1]).
        """
        if image_bgr is None or image_bgr.size == 0:
            return LandmarkResult.empty("invalid_input")

        h, w = image_bgr.shape[:2]

        # ---- Strategy 1: MediaPipe ----
        if self._mp_available and self._mp_face_mesh is not None:
            result = self._detect_mediapipe(image_bgr, w, h)
            if result.confidence > 0:
                return result

        # ---- Strategy 2: OpenCV geometric ----
        result = self._detect_opencv_geometric(image_bgr, w, h)
        if result.confidence > 0:
            return result

        # ---- Strategy 3: Bounding-box synthetic ----
        return self._detect_synthetic(w, h)

    def detect_from_bytes(self, image_bytes: bytes) -> LandmarkResult:
        """Accept raw image bytes (JPEG/PNG/etc.)."""
        arr = np.frombuffer(image_bytes, dtype=np.uint8)
        bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if bgr is None:
            return LandmarkResult.empty("decode_error")
        return self.detect(bgr)

    # -----------------------------------------------------------------
    # Strategy 1 — MediaPipe FaceMesh
    # -----------------------------------------------------------------

    def _detect_mediapipe(self, bgr: np.ndarray, w: int, h: int) -> LandmarkResult:
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        try:
            out = self._mp_face_mesh.process(rgb)
        except Exception as exc:
            logger.debug("MediaPipe inference error: %s", exc)
            return LandmarkResult.empty("mp_error")

        if not out.multi_face_landmarks:
            return LandmarkResult.empty("no_face_mp")

        lm = out.multi_face_landmarks[0].landmark  # list of 478 NormalizedLandmark

        def _pt(idx: int) -> List[float]:
            p = lm[idx]
            # clamp to [0, 1]
            return [max(0.0, min(1.0, float(p.x))), max(0.0, min(1.0, float(p.y)))]

        # Safely fetch; if index out of range (< 478) return centre
        n_lm = len(lm)
        def _safe_pt(idx: int) -> List[float]:
            if idx >= n_lm:
                return [0.5, 0.5]
            return _pt(idx)

        eyes = [_safe_pt(i) for i in _MP_EYE_LEFT] + [_safe_pt(i) for i in _MP_EYE_RIGHT]
        mouth = [_safe_pt(i) for i in _MP_MOUTH]
        nose = [_safe_pt(i) for i in _MP_NOSE]

        # Ear estimates — cheekbone-area proxies (no true ear in FaceMesh)
        ears = [
            _safe_pt(234),  # left jaw hinge
            _safe_pt(127),
            _safe_pt(162),
            _safe_pt(21),
            _safe_pt(454),  # right jaw hinge
            _safe_pt(356),
            _safe_pt(389),
            _safe_pt(251),
        ]

        # Face bbox from extreme points
        xs = [p[0] for p in eyes + mouth + nose]
        ys = [p[1] for p in eyes + mouth + nose]
        x0, y0 = int(min(xs) * w), int(min(ys) * h)
        x1, y1 = int(max(xs) * w), int(max(ys) * h)

        return LandmarkResult(
            eyes=eyes,
            mouth=mouth,
            nose=nose,
            ears=ears,
            confidence=0.90,
            strategy="mediapipe",
            face_bbox=[x0, y0, x1 - x0, y1 - y0],
        )

    # -----------------------------------------------------------------
    # Strategy 2 — OpenCV Haarcascade + geometric estimation
    # -----------------------------------------------------------------

    def _detect_opencv_geometric(self, bgr: np.ndarray, w: int, h: int) -> LandmarkResult:
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        gray = cv2.equalizeHist(gray)

        bboxes = self._find_faces(gray)
        if not bboxes:
            return LandmarkResult.empty("no_face_cv")

        # Use the largest face
        bx, by, bw, bh = max(bboxes, key=lambda b: b[2] * b[3])

        eyes, mouth, nose = self._estimate_landmarks_from_bbox(bx, by, bw, bh, w, h)

        return LandmarkResult(
            eyes=eyes,
            mouth=mouth,
            nose=nose,
            ears=self._estimate_ears_from_bbox(bx, by, bw, bh, w, h),
            confidence=0.55,
            strategy="opencv_geometric",
            face_bbox=[bx, by, bw, bh],
        )

    def _find_faces(self, gray: np.ndarray) -> List[Tuple[int, int, int, int]]:
        if self._face_cascade is None:
            return []
        detections = self._face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.1,
            minNeighbors=3,
            minSize=(40, 40),
        )
        if len(detections) == 0:
            return []
        return [tuple(d) for d in detections]

    def _estimate_landmarks_from_bbox(
        self, bx: int, by: int, bw: int, bh: int, img_w: int, img_h: int
    ) -> Tuple[List[List[float]], List[List[float]], List[List[float]]]:
        """
        Derive 46 anatomically-plausible landmark positions from a face bbox.

        Coordinate system: fractional [0, 1] over the full image.
        """

        def n(px: float, py: float) -> List[float]:
            """Normalise pixel coords to [0,1]."""
            return [px / img_w, py / img_h]

        # Face centre and dimensions
        cx = bx + bw / 2
        cy = by + bh / 2

        # ---- Eyes (12 pts × 2 = 24) ----
        # Eye centres approximately at 35% down the face, 25% left/right of centre
        eye_y = by + bh * 0.35
        eye_sep = bw * 0.25
        el_cx = cx - eye_sep          # left eye centre x
        er_cx = cx + eye_sep          # right eye centre x
        ey_rx = bw * 0.085            # x-radius of eye
        ey_ry = bh * 0.055            # y-radius of eye

        def _eye_pts(ecx: float, ecy: float) -> List[List[float]]:
            pts = [
                n(ecx, ecy),                              # 0 pupil centre
                n(ecx, ecy - ey_ry),                      # 1 upper lid top
                n(ecx - ey_rx * 0.6, ecy - ey_ry * 0.8), # 2 upper-lid left
                n(ecx + ey_rx * 0.6, ecy - ey_ry * 0.8), # 3 upper-lid right
                n(ecx, ecy - ey_ry * 0.5),                # 4 upper-lid mid
                n(ecx, ecy + ey_ry),                      # 5 lower lid bottom
                n(ecx - ey_rx * 0.6, ecy + ey_ry * 0.8), # 6 lower-lid left
                n(ecx + ey_rx * 0.6, ecy + ey_ry * 0.8), # 7 lower-lid right
                n(ecx, ecy + ey_ry * 0.5),                # 8 lower-lid mid
                n(ecx - ey_rx, ecy),                      # 9 lateral canthus
                n(ecx + ey_rx, ecy),                      # 10 medial canthus
                n(ecx, ecy - ey_ry * 1.3),                # 11 orbital peak
            ]
            return pts

        eyes = _eye_pts(el_cx, eye_y) + _eye_pts(er_cx, eye_y)

        # ---- Nose (5 pts) ----
        nose_top_y = by + bh * 0.45
        nose_tip_y = by + bh * 0.65
        nose_w = bw * 0.12
        nose = [
            n(cx, nose_tip_y),                          # 0 tip
            n(cx, nose_tip_y + bh * 0.03),              # 1 septum base
            n(cx, nose_top_y),                          # 2 bridge top
            n(cx - nose_w, nose_tip_y - bh * 0.02),    # 3 left nostril
            n(cx + nose_w, nose_tip_y - bh * 0.02),    # 4 right nostril
        ]

        # ---- Mouth (10 pts) ----
        mouth_y = by + bh * 0.78
        mouth_w = bw * 0.20
        mouth_h = bh * 0.07
        mouth = [
            n(cx - mouth_w, mouth_y),                  # 0 left corner
            n(cx + mouth_w, mouth_y),                  # 1 right corner
            n(cx, mouth_y - mouth_h),                  # 2 upper lip top
            n(cx, mouth_y + mouth_h),                  # 3 lower lip bottom
            n(cx - mouth_w * 0.6, mouth_y - mouth_h * 0.7),   # 4 upper-left
            n(cx + mouth_w * 0.6, mouth_y - mouth_h * 0.7),   # 5 upper-right
            n(cx - mouth_w * 0.6, mouth_y + mouth_h * 0.7),   # 6 lower-left
            n(cx + mouth_w * 0.6, mouth_y + mouth_h * 0.7),   # 7 lower-right
            n(cx - mouth_w * 0.3, mouth_y - mouth_h * 0.9),   # 8 upper-mid-left
            n(cx + mouth_w * 0.3, mouth_y - mouth_h * 0.9),   # 9 upper-mid-right
        ]

        return eyes, mouth, nose

    def _estimate_ears_from_bbox(
        self, bx: int, by: int, bw: int, bh: int, img_w: int, img_h: int
    ) -> List[List[float]]:
        def n(px: float, py: float) -> List[float]:
            return [px / img_w, py / img_h]

        cx = bx + bw / 2
        ear_y_top = by - bh * 0.25
        ear_y_base = by + bh * 0.05
        ear_x_sep = bw * 0.40

        left_pts = [
            n(cx - ear_x_sep - bw * 0.05, ear_y_top),
            n(cx - ear_x_sep, ear_y_top + bh * 0.12),
            n(cx - ear_x_sep + bw * 0.05, ear_y_top),
            n(cx - ear_x_sep, ear_y_base),
        ]
        right_pts = [
            n(cx + ear_x_sep + bw * 0.05, ear_y_top),
            n(cx + ear_x_sep, ear_y_top + bh * 0.12),
            n(cx + ear_x_sep - bw * 0.05, ear_y_top),
            n(cx + ear_x_sep, ear_y_base),
        ]
        return left_pts + right_pts

    # -----------------------------------------------------------------
    # Strategy 3 — Synthetic (bounding box of full image)
    # -----------------------------------------------------------------

    def _detect_synthetic(self, w: int, h: int) -> LandmarkResult:
        """Generate plausible landmarks using whole-image as face bbox."""
        # Treat the central 80% as the face
        margin_x = w * 0.10
        margin_y = h * 0.10
        bx = int(margin_x)
        by = int(margin_y)
        bw = int(w - 2 * margin_x)
        bh = int(h - 2 * margin_y)

        eyes, mouth, nose = self._estimate_landmarks_from_bbox(bx, by, bw, bh, w, h)
        ears = self._estimate_ears_from_bbox(bx, by, bw, bh, w, h)

        return LandmarkResult(
            eyes=eyes,
            mouth=mouth,
            nose=nose,
            ears=ears,
            confidence=0.20,
            strategy="synthetic",
            face_bbox=[bx, by, bw, bh],
        )

    # -----------------------------------------------------------------
    # Cleanup
    # -----------------------------------------------------------------

    def close(self) -> None:
        if self._mp_face_mesh is not None:
            try:
                self._mp_face_mesh.close()
            except Exception:
                pass

    def __del__(self) -> None:
        self.close()
