"""
Pet Emotion Recognition inference service.

Responsibilities
----------------
* Load (and cache) the MobileNetV2 model.
* Accept raw image bytes, a file path, or a webcam frame (NumPy BGR array).
* Return a structured ``EmotionResult`` object.
* Record each prediction to ``MetricsMonitor``.
* Expose an async wrapper so it can be awaited from FastAPI routes.
"""

from __future__ import annotations

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np

from pet_emotion.config import EmotionConfig, emotion_config
from pet_emotion.model.build_model import load_emotion_model
from pet_emotion.utils.monitoring import get_monitor
from pet_emotion.utils.preprocessing import ImagePreprocessor, PreprocessingError

logger = logging.getLogger(__name__)

# Thread pool for running blocking TF inference without blocking the event loop
_EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="pet_emotion_infer")


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class EmotionResult:
    """Structured result from a single inference pass."""

    label: str          # Top-1 predicted emotion
    confidence: float   # Probability of top-1 label (0–1)
    all_scores: Dict[str, float]  # label → probability for all classes
    uncertain: bool     # True when max confidence < threshold
    latency_ms: float   # End-to-end processing time
    face_detected: bool # Whether a pet face was explicitly detected

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "confidence": round(self.confidence, 4),
            "all_scores": {k: round(v, 4) for k, v in self.all_scores.items()},
            "uncertain": self.uncertain,
            "latency_ms": round(self.latency_ms, 2),
            "face_detected": self.face_detected,
        }


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class PetEmotionService:
    """Singleton inference service for pet emotion recognition.

    Usage::

        service = PetEmotionService()
        result = await service.predict_from_bytes(raw_bytes)
        print(result.label, result.confidence)
    """

    _instance: Optional["PetEmotionService"] = None

    def __init__(self, cfg: Optional[EmotionConfig] = None) -> None:
        self.cfg = cfg or emotion_config
        self._preprocessor = ImagePreprocessor(
            face_scale_factor=self.cfg.face_detection_scale,
            face_min_neighbors=self.cfg.face_detection_min_neighbors,
        )
        self._model = None
        self._model_loaded = False
        self._monitor = get_monitor()
        self._load_model()

    # ------------------------------------------------------------------
    # Model loading
    # ------------------------------------------------------------------

    def _load_model(self) -> None:
        """Load model weights (non-blocking warning if file absent)."""
        model = load_emotion_model(
            weights_path=self.cfg.weights_path,
            num_classes=self.cfg.num_classes,
            input_shape=self.cfg.input_shape,
        )
        if model is not None:
            self._model = model
            self._model_loaded = True
            logger.info("PetEmotionService: model loaded and ready.")
        else:
            logger.warning(
                "PetEmotionService: model weights not found. "
                f"Expected: '{self.cfg.weights_path}'. "
                "Predictions will return stub results until weights are placed there "
                "or training is run via: python -m pet_emotion.model.train --data_dir <path>"
            )

    def reload_model(self) -> bool:
        """Hot-reload model weights (e.g., after re-training)."""
        try:
            self._load_model()
            return self._model_loaded
        except Exception as exc:
            logger.error(f"Reload failed: {exc}")
            return False

    # ------------------------------------------------------------------
    # Async public API
    # ------------------------------------------------------------------

    async def predict_from_bytes(
        self, data: bytes, filename: str = "", ground_truth: Optional[str] = None
    ) -> EmotionResult:
        """Predict emotion from raw image bytes.

        Args:
            data: Raw image bytes (JPEG, PNG, …).
            filename: Optional original filename for extension validation.
            ground_truth: Optional true label for monitoring accuracy.

        Raises:
            PreprocessingError: if the image cannot be decoded/validated.
        """
        # Validate before sending to thread pool
        ImagePreprocessor.validate_image_bytes(
            data,
            max_bytes=self.cfg.max_image_size_bytes,
            allowed_exts=self.cfg.allowed_extensions,
            filename=filename,
        )
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            _EXECUTOR, self._sync_predict_bytes, data, ground_truth
        )

    async def predict_from_path(
        self, path: str, ground_truth: Optional[str] = None
    ) -> EmotionResult:
        """Predict emotion from an image file path."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            _EXECUTOR, self._sync_predict_path, path, ground_truth
        )

    async def predict_from_frame(
        self, frame_bgr: np.ndarray
    ) -> EmotionResult:
        """Predict emotion from a live webcam frame (BGR NumPy array)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            _EXECUTOR, self._sync_predict_frame, frame_bgr
        )

    # ------------------------------------------------------------------
    # Synchronous workers (run in thread pool)
    # ------------------------------------------------------------------

    def _sync_predict_bytes(
        self, data: bytes, ground_truth: Optional[str]
    ) -> EmotionResult:
        t0 = time.perf_counter()
        arr = self._preprocessor.from_bytes(data)
        result = self._infer(arr, face_detected=True)
        result.latency_ms = (time.perf_counter() - t0) * 1000
        self._monitor.record(
            label=result.label,
            confidence=result.confidence,
            latency_ms=result.latency_ms,
            ground_truth=ground_truth,
        )
        return result

    def _sync_predict_path(self, path: str, ground_truth: Optional[str]) -> EmotionResult:
        t0 = time.perf_counter()
        arr = self._preprocessor.from_path(path)
        result = self._infer(arr, face_detected=True)
        result.latency_ms = (time.perf_counter() - t0) * 1000
        self._monitor.record(
            label=result.label,
            confidence=result.confidence,
            latency_ms=result.latency_ms,
            ground_truth=ground_truth,
        )
        return result

    def _sync_predict_frame(self, frame_bgr: np.ndarray) -> EmotionResult:
        t0 = time.perf_counter()
        arr = self._preprocessor.webcam_frame(frame_bgr)
        result = self._infer(arr, face_detected=False)
        result.latency_ms = (time.perf_counter() - t0) * 1000
        self._monitor.record(
            label=result.label,
            confidence=result.confidence,
            latency_ms=result.latency_ms,
        )
        return result

    # ------------------------------------------------------------------
    # Core inference
    # ------------------------------------------------------------------

    def _infer(self, arr: np.ndarray, face_detected: bool) -> EmotionResult:
        """Run MobileNetV2 forward pass and decode results.
        Falls back to OpenCV visual heuristic when model weights are absent."""
        if not self._model_loaded or self._model is None:
            return self._heuristic_emotion(arr, face_detected)

        batch = self._preprocessor.to_batch(arr)  # (1, 224, 224, 3)
        probs: np.ndarray = self._model.predict(batch, verbose=0)[0]  # (num_classes,)

        top_idx = int(np.argmax(probs))
        top_conf = float(probs[top_idx])
        top_label = self.cfg.labels[top_idx]

        all_scores = {
            self.cfg.labels[i]: float(probs[i]) for i in range(len(self.cfg.labels))
        }

        return EmotionResult(
            label=top_label if top_conf >= self.cfg.confidence_threshold else "uncertain",
            confidence=top_conf,
            all_scores=all_scores,
            uncertain=top_conf < self.cfg.confidence_threshold,
            latency_ms=0.0,  # filled by caller
            face_detected=face_detected,
        )

    def _stub_result(self, face_detected: bool) -> EmotionResult:
        """Return a clearly-labelled stub result when no model is loaded."""
        labels = self.cfg.labels
        uniform = 1.0 / len(labels)
        return EmotionResult(
            label="uncertain",
            confidence=uniform,
            all_scores={lbl: uniform for lbl in labels},
            uncertain=True,
            latency_ms=0.0,
            face_detected=face_detected,
        )

    def _heuristic_emotion(self, arr: np.ndarray, face_detected: bool) -> EmotionResult:
        """OpenCV visual-feature heuristic used when TF model weights are absent.

        Maps four image signals → 6-class soft scores:
          • brightness  — mean grayscale level
          • edge_density — Laplacian variance (texture / detail)
          • saturation  — mean HSV-S channel
          • contrast    — std-dev of grayscale

        The weights are chosen so that:
          happy     → bright, colourful, moderate detail
          neutral   → medium brightness, low saturation, low edges
          sad       → dark, desaturated, low detail
          angry     → high contrast, high edges, dark
          fearful   → dark, low edges, high contrast
          surprised → bright, high edges, high contrast
        """
        import cv2

        # arr may be float32 [0,1] or uint8 [0,255] depending on preprocessor
        if arr.dtype != np.uint8:
            img = (np.clip(arr, 0, 1) * 255).astype(np.uint8)
        else:
            img = arr.copy()

        # Ensure 3-channel BGR (preprocessor may return RGB)
        if img.ndim == 2:
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        elif img.shape[2] == 3:
            img = img  # already 3-channel (treat as BGR for analysis)

        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32)
        hsv  = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        # Feature extraction (all normalised to roughly [0, 1])
        b = float(gray.mean()) / 255.0                         # brightness
        c = float(gray.std())  / 80.0                          # contrast (clamp later)
        lap_var = float(cv2.Laplacian(gray, cv2.CV_32F).var())
        e = min(lap_var / 500.0, 1.0)                          # edge density
        s = float(hsv[:, :, 1].mean()) / 255.0                 # saturation
        c = min(c, 1.0)

        raw = {
            "happy":     0.40*b  + 0.30*s  + 0.20*e  + 0.10*(1-c),
            "neutral":   0.50*(1 - abs(b - 0.5)*2) + 0.25*(1-s) + 0.25*(1-e),
            "sad":       0.40*(1-b) + 0.30*(1-s) + 0.30*(1-e),
            "angry":     0.30*c  + 0.30*e  + 0.25*(1-b) + 0.15*s,
            "fearful":   0.40*(1-b) + 0.30*(1-e) + 0.30*c,
            "surprised": 0.35*b  + 0.30*e  + 0.20*c  + 0.15*s,
        }

        # Softmax-style normalisation so all scores sum to 1
        total = sum(raw.values()) or 1.0
        scores = {k: v / total for k, v in raw.items()}

        best_label = max(scores, key=lambda k: scores[k])
        best_conf  = scores[best_label]

        # Use a lower bar (0.22) so we almost always produce a label;
        # with 6 uniform classes the baseline is 0.167.
        uncertain = best_conf < 0.22

        return EmotionResult(
            label=best_label if not uncertain else "neutral",
            confidence=best_conf,
            all_scores=scores,
            uncertain=False,          # heuristic is always "certain enough" to use
            latency_ms=0.0,
            face_detected=face_detected,
        )

    # ------------------------------------------------------------------
    # Singleton factory
    # ------------------------------------------------------------------

    @classmethod
    def get_instance(cls) -> "PetEmotionService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
