"""
Face alignment utilities for pet facial landmarks.

Provides:
  - align_face()    — affine warp using left/right eye centres
  - crop_roi()      — padded crop for a given bbox
  - normalise_landmarks() — re-express landmarks relative to aligned crop
"""

from __future__ import annotations

import math
from typing import List, Optional, Tuple

import cv2
import numpy as np

from .detector import LandmarkResult


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_ALIGN_TARGET_SIZE = (160, 160)
_EYE_CENTRE_RATIO_X = 0.35   # desired eye_x / width
_EYE_CENTRE_RATIO_Y = 0.40   # desired eye_y / height


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def align_face(
    image_bgr: np.ndarray,
    landmarks: LandmarkResult,
    output_size: Tuple[int, int] = _ALIGN_TARGET_SIZE,
) -> Optional[np.ndarray]:
    """
    Warp ``image_bgr`` so that the eyes are at canonical positions.

    Returns the aligned :class:`numpy.ndarray` (BGR) or *None* if alignment
    was not possible (e.g. no landmark data).

    Args:
        image_bgr:   Source image in BGR colour order.
        landmarks:   :class:`LandmarkResult` from :class:`LandmarkDetector`.
        output_size: (width, height) of the returned image.

    Returns:
        Aligned BGR image or ``None``.
    """
    if not landmarks.eyes or len(landmarks.eyes) < 12:
        # Not enough landmark data — return a plain centre-crop
        return _centre_crop(image_bgr, output_size)

    h, w = image_bgr.shape[:2]
    ow, oh = output_size

    # Left eye centroid  (first 12 normalised points → pixel coords)
    left_eye_pts = np.array(
        [[p[0] * w, p[1] * h] for p in landmarks.eyes[:12]], dtype=np.float32
    )
    right_eye_pts = np.array(
        [[p[0] * w, p[1] * h] for p in landmarks.eyes[12:]], dtype=np.float32
    )

    left_eye_centre = left_eye_pts.mean(axis=0)
    right_eye_centre = right_eye_pts.mean(axis=0)

    # Angle between eyes → rotate so eyes are horizontal
    dx = right_eye_centre[0] - left_eye_centre[0]
    dy = right_eye_centre[1] - left_eye_centre[1]
    angle_deg = math.degrees(math.atan2(dy, dx))

    # Inter-ocular distance and desired distance
    eye_dist = float(np.linalg.norm(right_eye_centre - left_eye_centre))
    desired_dist = (1.0 - 2.0 * _EYE_CENTRE_RATIO_X) * ow
    if desired_dist <= 0 or eye_dist < 1e-6:
        return _centre_crop(image_bgr, output_size)

    scale = desired_dist / eye_dist

    # Eye midpoint
    eye_mid = (left_eye_centre + right_eye_centre) / 2.0

    # Rotation matrix around midpoint
    M = cv2.getRotationMatrix2D(tuple(eye_mid), angle_deg, scale)

    # Shift so the midpoint lands at the canonical position
    M[0, 2] += ow * 0.5 - eye_mid[0]
    M[1, 2] += oh * _EYE_CENTRE_RATIO_Y - eye_mid[1]

    aligned = cv2.warpAffine(image_bgr, M, (ow, oh), flags=cv2.INTER_LINEAR)
    return aligned


def crop_roi(
    image_bgr: np.ndarray,
    bbox: List[int],
    padding: float = 0.20,
    output_size: Optional[Tuple[int, int]] = None,
) -> np.ndarray:
    """
    Return a padded crop of *image_bgr* described by *bbox*.

    Args:
        image_bgr:   Source BGR image.
        bbox:        [x, y, w, h] in pixels (as returned by LandmarkResult.face_bbox).
        padding:     Fractional padding added on each side (default 20 %).
        output_size: If given, resize the crop to this (width, height).

    Returns:
        Cropped (and optionally resized) BGR image.
    """
    h, w = image_bgr.shape[:2]
    x, y, bw, bh = bbox

    pad_x = int(bw * padding)
    pad_y = int(bh * padding)

    x0 = max(0, x - pad_x)
    y0 = max(0, y - pad_y)
    x1 = min(w, x + bw + pad_x)
    y1 = min(h, y + bh + pad_y)

    crop = image_bgr[y0:y1, x0:x1]

    if output_size is not None and crop.size > 0:
        crop = cv2.resize(crop, output_size, interpolation=cv2.INTER_LINEAR)

    return crop


def normalise_landmarks(
    landmarks: LandmarkResult,
    bbox: List[int],
    img_w: int,
    img_h: int,
) -> LandmarkResult:
    """
    Re-express normalised-image landmark coordinates relative to *bbox*.

    Useful when you want landmarks relative to the face crop rather than
    the full image frame.

    Args:
        landmarks: Original :class:`LandmarkResult` (coords in [0,1] image space).
        bbox:      [x, y, w, h] of the crop in pixels.
        img_w:     Full image width.
        img_h:     Full image height.

    Returns:
        New :class:`LandmarkResult` with coords in [0,1] crop space.
    """
    from .detector import LandmarkResult as _LR

    x, y, bw, bh = bbox

    def _remap(pts: List[List[float]]) -> List[List[float]]:
        out = []
        for px, py in pts:
            # Convert to absolute pixel
            abs_x = px * img_w
            abs_y = py * img_h
            # Re-normalise within crop
            rel_x = (abs_x - x) / bw if bw > 0 else 0.5
            rel_y = (abs_y - y) / bh if bh > 0 else 0.5
            out.append([
                max(0.0, min(1.0, rel_x)),
                max(0.0, min(1.0, rel_y)),
            ])
        return out

    return _LR(
        eyes=_remap(landmarks.eyes),
        mouth=_remap(landmarks.mouth),
        nose=_remap(landmarks.nose),
        ears=_remap(landmarks.ears),
        confidence=landmarks.confidence,
        strategy=landmarks.strategy + "_normalised",
        face_bbox=bbox,
    )


def eye_centres(
    landmarks: LandmarkResult,
    img_w: int,
    img_h: int,
) -> Tuple[Optional[Tuple[float, float]], Optional[Tuple[float, float]]]:
    """
    Return pixel-space (x, y) centres for left and right eyes, or *None*.
    """
    if not landmarks.eyes or len(landmarks.eyes) < 24:
        return None, None

    def _centre(pts: List[List[float]]) -> Tuple[float, float]:
        xs = [p[0] * img_w for p in pts]
        ys = [p[1] * img_h for p in pts]
        return float(sum(xs) / len(xs)), float(sum(ys) / len(ys))

    return _centre(landmarks.eyes[:12]), _centre(landmarks.eyes[12:])


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _centre_crop(
    image_bgr: np.ndarray, output_size: Tuple[int, int]
) -> np.ndarray:
    """Fallback: square centre crop + resize."""
    h, w = image_bgr.shape[:2]
    side = min(h, w)
    y0 = (h - side) // 2
    x0 = (w - side) // 2
    crop = image_bgr[y0: y0 + side, x0: x0 + side]
    return cv2.resize(crop, output_size, interpolation=cv2.INTER_LINEAR)
