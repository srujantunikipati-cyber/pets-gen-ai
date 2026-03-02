"""
OpenCV-based image preprocessing for Pet Emotion Recognition.

Responsibilities
----------------
1. Decode / load image from bytes, file path, or NumPy array.
2. Validate format, size, and content (must contain a pet face).
3. Detect & crop the dominant animal face using Haarcascade.
4. Resize + normalise to (224, 224, 3) for MobileNetV2.
5. Support webcam frame preprocessing (BGR → RGB pipeline).
"""

from __future__ import annotations

import io
import logging
import os
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Haarcascade paths
# ---------------------------------------------------------------------------
_CV2_DATA = Path(cv2.__file__).parent / "data"
_FRONTAL_CAT = _CV2_DATA / "haarcascade_frontalcatface_extended.xml"
_FRONTAL_FACE = _CV2_DATA / "haarcascade_frontalface_default.xml"  # fallback for dogs

# Model input size
_TARGET_SIZE: Tuple[int, int] = (224, 224)
_MAX_PIXEL_DIM = 4096


class PreprocessingError(ValueError):
    """Raised when an image cannot be pre-processed for inference."""


class ImagePreprocessor:
    """Stateless image pre-processor for pet emotion recognition.

    Example::

        preprocessor = ImagePreprocessor()
        array = preprocessor.from_bytes(raw_bytes)   # shape (224, 224, 3) float32
        batch  = preprocessor.to_batch(array)         # shape (1, 224, 224, 3)
    """

    def __init__(
        self,
        face_scale_factor: float = 1.1,
        face_min_neighbors: int = 4,
        target_size: Tuple[int, int] = _TARGET_SIZE,
    ) -> None:
        self._scale = face_scale_factor
        self._min_neighbors = face_min_neighbors
        self._target = target_size

        self._cat_cascade: Optional[cv2.CascadeClassifier] = self._load_cascade(str(_FRONTAL_CAT))
        self._face_cascade: Optional[cv2.CascadeClassifier] = self._load_cascade(str(_FRONTAL_FACE))

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def from_bytes(self, data: bytes) -> np.ndarray:
        """Decode raw image bytes → normalised float32 array (H, W, 3).

        Raises:
            PreprocessingError: if the bytes cannot be decoded.
        """
        arr = np.frombuffer(data, dtype=np.uint8)
        img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if img is None:
            raise PreprocessingError("Could not decode image bytes — unsupported format or corrupt file.")
        return self._process(img)

    def from_path(self, path: str) -> np.ndarray:
        """Load an image from *path* → normalised float32 array."""
        img = cv2.imread(path, cv2.IMREAD_COLOR)
        if img is None:
            raise PreprocessingError(f"Could not read image at '{path}'.")
        return self._process(img)

    def from_array(self, img: np.ndarray) -> np.ndarray:
        """Accept an existing BGR NumPy array → normalised float32 array."""
        if img is None or img.size == 0:
            raise PreprocessingError("Received empty image array.")
        return self._process(img.copy())

    def webcam_frame(self, frame_bgr: np.ndarray) -> np.ndarray:
        """Pre-process a live webcam frame (BGR) for real-time inference.

        Does NOT raise on face-detection failure — returns the full resized
        frame instead so the stream never breaks.
        """
        if frame_bgr is None or frame_bgr.size == 0:
            raise PreprocessingError("Empty webcam frame received.")
        try:
            return self._process(frame_bgr.copy(), strict_face=False)
        except PreprocessingError:
            # Graceful degradation: use whole frame
            rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
            return self._resize_and_normalise(rgb)

    @staticmethod
    def to_batch(arr: np.ndarray) -> np.ndarray:
        """Expand a (H, W, 3) array to a (1, H, W, 3) batch."""
        return np.expand_dims(arr, axis=0)

    # ------------------------------------------------------------------
    # Static helpers
    # ------------------------------------------------------------------

    @staticmethod
    def validate_image_bytes(
        data: bytes,
        max_bytes: int = 10 * 1024 * 1024,
        allowed_exts: Optional[list] = None,
        filename: str = "",
    ) -> None:
        """Pre-flight checks before attempting to decode.

        Raises:
            PreprocessingError: with a human-readable message.
        """
        if not data:
            raise PreprocessingError("Image data is empty.")
        if len(data) > max_bytes:
            raise PreprocessingError(
                f"Image too large: {len(data) / 1_048_576:.1f} MB > {max_bytes / 1_048_576:.0f} MB limit."
            )
        if allowed_exts and filename:
            ext = Path(filename).suffix.lower()
            if ext not in allowed_exts:
                raise PreprocessingError(
                    f"File extension '{ext}' not allowed. Accepted: {allowed_exts}."
                )

    # ------------------------------------------------------------------
    # Internal processing pipeline
    # ------------------------------------------------------------------

    def _process(self, bgr: np.ndarray, strict_face: bool = True) -> np.ndarray:
        """Full processing pipeline: validate → detect face → resize → normalise."""
        bgr = self._validate_dimensions(bgr)
        bgr = self._auto_orient(bgr)
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

        crop = self._detect_and_crop_face(rgb, strict=strict_face)
        return self._resize_and_normalise(crop)

    def _validate_dimensions(self, img: np.ndarray) -> np.ndarray:
        h, w = img.shape[:2]
        if h < 32 or w < 32:
            raise PreprocessingError(f"Image too small: {w}×{h}. Minimum 32×32 px.")
        if h > _MAX_PIXEL_DIM or w > _MAX_PIXEL_DIM:
            # Downsample very large images to avoid memory issues
            scale = _MAX_PIXEL_DIM / max(h, w)
            new_w, new_h = int(w * scale), int(h * scale)
            img = cv2.resize(img, (new_w, new_h), interpolation=cv2.INTER_AREA)
            logger.debug(f"Downsampled oversized image to {new_w}×{new_h}.")
        return img

    @staticmethod
    def _auto_orient(img: np.ndarray) -> np.ndarray:
        """Handle images with unexpected channel counts."""
        if img.ndim == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        elif img.shape[2] == 4:
            img = cv2.cvtColor(img, cv2.COLOR_BGRA2BGR)
        return img

    def _detect_and_crop_face(self, rgb: np.ndarray, strict: bool = True) -> np.ndarray:
        """Attempt cat → dog (frontal) face detection; return cropped region."""
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        faces = self._run_cascade(self._cat_cascade, gray)

        if faces is None or len(faces) == 0:
            faces = self._run_cascade(self._face_cascade, gray)

        if faces is None or len(faces) == 0:
            if strict:
                logger.warning("No pet face detected — using full image for inference.")
            return rgb  # Fall back to full image

        # Use the largest bounding box (most prominent face)
        x, y, w, h = max(faces, key=lambda r: r[2] * r[3])

        # Add 15 % padding around the face
        pad_x = int(w * 0.15)
        pad_y = int(h * 0.15)
        img_h, img_w = rgb.shape[:2]
        x1 = max(0, x - pad_x)
        y1 = max(0, y - pad_y)
        x2 = min(img_w, x + w + pad_x)
        y2 = min(img_h, y + h + pad_y)

        cropped = rgb[y1:y2, x1:x2]
        logger.debug(f"Face cropped: ({x1},{y1}) → ({x2},{y2})")
        return cropped

    def _run_cascade(
        self, cascade: Optional[cv2.CascadeClassifier], gray: np.ndarray
    ) -> Optional[np.ndarray]:
        if cascade is None or cascade.empty():
            return None
        return cascade.detectMultiScale(
            gray,
            scaleFactor=self._scale,
            minNeighbors=self._min_neighbors,
            minSize=(30, 30),
            flags=cv2.CASCADE_SCALE_IMAGE,
        )

    def _resize_and_normalise(self, rgb: np.ndarray) -> np.ndarray:
        resized = cv2.resize(rgb, self._target, interpolation=cv2.INTER_AREA)
        # MobileNetV2 expects pixel values in [0, 255] uint8 or will use its own
        # preprocess_input inside the model.  We return float32 [0, 255] here so
        # the model-internal preprocess_input layer scales correctly.
        return resized.astype(np.float32)

    # ------------------------------------------------------------------
    # Cascade loader
    # ------------------------------------------------------------------

    @staticmethod
    def _load_cascade(path: str) -> Optional[cv2.CascadeClassifier]:
        if not os.path.isfile(path):
            logger.warning(f"Haarcascade not found: {path}")
            return None
        cc = cv2.CascadeClassifier(path)
        if cc.empty():
            logger.warning(f"Failed to load cascade: {path}")
            return None
        logger.debug(f"Loaded cascade: {path}")
        return cc
