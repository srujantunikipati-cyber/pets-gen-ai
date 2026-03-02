"""
PetFaceService — unified service combining:
  • Pet emotion detection   (PetEmotionService / MobileNetV2)
  • Pet identity recognition (PetRecognizer / Siamese embedding)
  • Facial landmark detection (LandmarkDetector / MediaPipe + OpenCV)

Usage::

    svc = PetFaceService.get_instance()
    result = await svc.analyze(image_bytes)
    # result.emotion, result.identity, result.landmarks

    # Register a new pet
    await svc.register_pet("Buddy", image_bytes)

    # Identify
    result = await svc.recognize(image_bytes)
"""

from __future__ import annotations

import asyncio
import base64
import logging
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional

import cv2
import numpy as np

# Lazy imports to avoid circular imports and soft-dependency on optional modules
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Combined result dataclass
# ---------------------------------------------------------------------------

@dataclass
class AnalysisResult:
    """Full per-image analysis: emotion + identity + landmarks."""

    # Emotion
    emotion: str = "unknown"
    emotion_confidence: float = 0.0
    emotion_scores: Dict[str, float] = field(default_factory=dict)

    # Identity
    identity_name: Optional[str] = None
    identity_confidence: float = 0.0
    identity_distance: float = 1.0
    identity_matched: bool = False

    # Landmarks
    landmarks_eyes: List[List[float]] = field(default_factory=list)
    landmarks_mouth: List[List[float]] = field(default_factory=list)
    landmarks_nose: List[List[float]] = field(default_factory=list)
    landmarks_ears: List[List[float]] = field(default_factory=list)
    landmarks_confidence: float = 0.0
    landmarks_strategy: str = "none"
    face_bbox: Optional[List[int]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "emotion": {
                "label": self.emotion,
                "confidence": round(self.emotion_confidence, 4),
                "scores": {k: round(v, 4) for k, v in self.emotion_scores.items()},
            },
            "identity": {
                "name": self.identity_name,
                "confidence": round(self.identity_confidence, 4),
                "distance": round(self.identity_distance, 4),
                "matched": self.identity_matched,
            },
            "landmarks": {
                "eyes": self.landmarks_eyes,
                "mouth": self.landmarks_mouth,
                "nose": self.landmarks_nose,
                "ears": self.landmarks_ears,
                "all": self.landmarks_eyes + self.landmarks_mouth + self.landmarks_nose,
                "confidence": round(self.landmarks_confidence, 4),
                "strategy": self.landmarks_strategy,
                "face_bbox": self.face_bbox,
            },
        }


# ---------------------------------------------------------------------------
# PetFaceService
# ---------------------------------------------------------------------------

class PetFaceService:
    """
    Singleton service providing emotion + identity + landmark inference.

    Thread-safe; async-first using a dedicated thread-pool executor.
    """

    _instance: Optional["PetFaceService"] = None
    _lock = asyncio.Lock()

    def __init__(self) -> None:
        self._emotion_service = None
        self._recognizer = None
        self._landmark_detector = None
        self._ready = False
        self._init()

    def _init(self) -> None:
        # ---- Emotion service ----
        try:
            from backend.services.pet_emotion_service import PetEmotionService
            self._emotion_service = PetEmotionService.get_instance()
            logger.info("PetFaceService: emotion service ready.")
        except Exception as exc:
            logger.warning("PetFaceService: emotion service unavailable (%s).", exc)

        # ---- Identity recognizer ----
        try:
            from pet_emotion.recognition.recognizer import PetRecognizer
            self._recognizer = PetRecognizer.get_instance()
            logger.info("PetFaceService: identity recognizer ready.")
        except Exception as exc:
            logger.warning("PetFaceService: recognizer unavailable (%s).", exc)

        # ---- Landmark detector ----
        try:
            from pet_emotion.landmarks.detector import LandmarkDetector
            self._landmark_detector = LandmarkDetector(use_mediapipe=True)
            logger.info("PetFaceService: landmark detector ready (strategy=%s).",
                        "mediapipe" if self._landmark_detector._mp_available else "opencv")
        except Exception as exc:
            logger.warning("PetFaceService: landmark detector unavailable (%s).", exc)

        self._ready = True
        logger.info("PetFaceService initialised.")

    # -----------------------------------------------------------------
    # Singleton factory
    # -----------------------------------------------------------------

    @classmethod
    def get_instance(cls) -> "PetFaceService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # -----------------------------------------------------------------
    # Public async API
    # -----------------------------------------------------------------

    async def analyze(self, image_bytes: bytes) -> AnalysisResult:
        """
        Run all three pipelines on *image_bytes*.

        Returns :class:`AnalysisResult`.
        """
        loop = asyncio.get_event_loop()

        # Run in thread pool to avoid blocking the event loop
        result = await loop.run_in_executor(None, self._analyze_sync, image_bytes)
        return result

    async def register_pet(self, pet_name: str, image_bytes: bytes) -> Dict[str, Any]:
        """
        Register a new pet face embedding.

        Returns::

            {"registered": True, "pet_name": str, "num_samples": int}
        """
        if self._recognizer is None:
            return {"registered": False, "error": "Recognizer not initialised"}

        result = await self._recognizer.register_pet(pet_name, image_bytes)
        # register_pet returns a dict: {registered, pet_name, num_samples, latency_ms}
        return {
            "registered": result.get("registered", False),
            "pet_name": pet_name,
            "num_samples": result.get("num_samples", 0),
        }

    async def recognize(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Identify a pet from *image_bytes*.

        Returns::

            {"matched": bool, "name": str|None, "confidence": float, "distance": float}
        """
        if self._recognizer is None:
            return {"matched": False, "name": None, "confidence": 0.0, "distance": 1.0,
                    "error": "Recognizer not initialised"}

        rec_result = await self._recognizer.recognize(image_bytes)
        return {
            "matched": rec_result.matched,
            "name": rec_result.pet_name,
            "confidence": round(rec_result.confidence, 4),
            "distance": round(rec_result.distance, 4),
        }

    async def detect_landmarks(self, image_bytes: bytes) -> Dict[str, Any]:
        """
        Run 46-point landmark detection on *image_bytes*.

        Returns the landmark dict from :meth:`LandmarkResult.to_dict`.
        """
        if self._landmark_detector is None:
            return {"error": "Landmark detector not initialised", "eyes": [], "mouth": [], "nose": []}

        loop = asyncio.get_event_loop()
        lm_result = await loop.run_in_executor(
            None, self._landmark_detector.detect_from_bytes, image_bytes
        )
        return lm_result.to_dict()

    async def list_pets(self) -> List[str]:
        """Return list of registered pet names."""
        if self._recognizer is None:
            return []
        try:
            return self._recognizer.db.list_pets()
        except Exception:
            return []

    # -----------------------------------------------------------------
    # Internal synchronous worker
    # -----------------------------------------------------------------

    def _analyze_sync(self, image_bytes: bytes) -> AnalysisResult:
        result = AnalysisResult()

        # Decode once
        arr = np.frombuffer(image_bytes, dtype=np.uint8)
        bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if bgr is None:
            logger.warning("PetFaceService.analyze: failed to decode image bytes.")
            return result

        # ---- Emotion ----
        if self._emotion_service is not None:
            try:
                em = self._emotion_service._sync_predict_frame(bgr)
                result.emotion = em.label
                result.emotion_confidence = em.confidence
                result.emotion_scores = em.scores
            except Exception as exc:
                logger.debug("Emotion inference error: %s", exc)

        # ---- Identity ----
        if self._recognizer is not None:
            try:
                rec = self._recognizer._sync_recognize_array(bgr)
                result.identity_name = rec.identity
                result.identity_confidence = rec.confidence
                result.identity_distance = rec.distance
                result.identity_matched = rec.matched
            except Exception as exc:
                logger.debug("Recognition error: %s", exc)

        # ---- Landmarks ----
        if self._landmark_detector is not None:
            try:
                lm = self._landmark_detector.detect(bgr)
                result.landmarks_eyes = lm.eyes
                result.landmarks_mouth = lm.mouth
                result.landmarks_nose = lm.nose
                result.landmarks_ears = lm.ears
                result.landmarks_confidence = lm.confidence
                result.landmarks_strategy = lm.strategy
                result.face_bbox = lm.face_bbox
            except Exception as exc:
                logger.debug("Landmark detection error: %s", exc)

        return result

    # -----------------------------------------------------------------
    # Annotated image helper
    # -----------------------------------------------------------------

    async def annotated_image_b64(self, image_bytes: bytes) -> Optional[str]:
        """
        Run analysis and return a base-64 encoded JPEG with landmarks overlaid.
        Returns *None* if landmarks couldn't be detected.
        """
        arr = np.frombuffer(image_bytes, dtype=np.uint8)
        bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if bgr is None:
            return None

        loop = asyncio.get_event_loop()

        def _draw():
            from pet_emotion.landmarks.detector import LandmarkDetector
            from pet_emotion.landmarks.viz_landmarks import draw_landmarks
            if self._landmark_detector is None:
                return None
            lm_result = self._landmark_detector.detect(bgr)
            annotated = draw_landmarks(bgr, lm_result, draw_bbox=True, draw_labels=True)
            ok, buf = cv2.imencode(".jpg", annotated, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if not ok:
                return None
            return base64.b64encode(buf.tobytes()).decode("utf-8")

        return await loop.run_in_executor(None, _draw)
