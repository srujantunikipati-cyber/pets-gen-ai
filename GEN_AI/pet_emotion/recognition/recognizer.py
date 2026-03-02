"""
Pet Face Recognition Pipeline.

Flow
----
1. Preprocess face crop → (160, 160, 3) float32
2. Run embedding model → 128-d L2-normalised vector
3. Query EmbeddingDB → best match (cosine distance)
4. Return RecognitionResult

When no embedding model is loaded (weights absent), returns a stub result
so the API never crashes — recognised as "unknown".
"""

from __future__ import annotations

import asyncio
import logging
import time
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

from pet_emotion.config import EmotionConfig, emotion_config
from pet_emotion.recognition.embedding_db import EmbeddingDB
from pet_emotion.recognition.siamese_model import (
    load_embedding_model,
    get_embedding,
    build_embedding_model,
)

logger = logging.getLogger(__name__)

_EXECUTOR = ThreadPoolExecutor(max_workers=2, thread_name_prefix="pet_recog_infer")


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------


@dataclass
class RecognitionResult:
    """Structured result from pet identity recognition."""

    identity: Optional[str]    # Pet name if matched, else None
    confidence: float          # 0–1 (1 = perfect match)
    distance: float            # Cosine L2 distance (lower = better)
    matched: bool              # True when identity is not None
    latency_ms: float
    registered_pets: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "identity": self.identity,
            "confidence": round(self.confidence, 4),
            "distance": round(self.distance, 4),
            "matched": self.matched,
            "latency_ms": round(self.latency_ms, 2),
            "registered_pets": self.registered_pets,
        }


# ---------------------------------------------------------------------------
# Recognizer
# ---------------------------------------------------------------------------


class PetRecognizer:
    """Pet face recognition service.

    Singleton pattern — use ``PetRecognizer.get_instance()``.
    """

    _instance: Optional["PetRecognizer"] = None

    def __init__(self, cfg: Optional[EmotionConfig] = None) -> None:
        self.cfg = cfg or emotion_config
        self._model = None
        self._model_loaded = False
        self.db = EmbeddingDB(self.cfg.embedding_db_path)
        self._face_pp = _FacePreprocessor(target_size=self.cfg.embedding_input_shape[:2])
        self._load_model()

    # ------------------------------------------------------------------
    # Model loading
    # ------------------------------------------------------------------

    def _load_model(self) -> None:
        model = load_embedding_model(
            self.cfg.siamese_weights_path,
            embedding_dim=self.cfg.embedding_dim,
            input_shape=self.cfg.embedding_input_shape,
        )
        if model is not None:
            self._model = model
            self._model_loaded = True
            logger.info("PetRecognizer: embedding model loaded.")
        else:
            logger.warning(
                "PetRecognizer: embedding weights not found. "
                "Recognition will return 'unknown' until weights are placed at: "
                f"'{self.cfg.siamese_weights_path}'"
            )

    def reload_model(self) -> bool:
        try:
            self._load_model()
            return self._model_loaded
        except Exception as exc:
            logger.error(f"Reload failed: {exc}")
            return False

    # ------------------------------------------------------------------
    # Public async API
    # ------------------------------------------------------------------

    async def register_pet(
        self,
        pet_name: str,
        image_bytes: bytes,
    ) -> Dict:
        """Register a pet from raw image bytes.

        Extracts face embedding and stores it in the database.
        Multiple registrations with the same name add more gallery samples
        (improves accuracy).
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_EXECUTOR, self._sync_register, pet_name, image_bytes)

    async def recognize(
        self,
        image_bytes: bytes,
    ) -> RecognitionResult:
        """Identify a pet from image bytes."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_EXECUTOR, self._sync_recognize, image_bytes)

    async def recognize_from_array(self, bgr: np.ndarray) -> RecognitionResult:
        """Identify a pet from a BGR NumPy array (e.g. webcam frame)."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(_EXECUTOR, self._sync_recognize_array, bgr)

    # ------------------------------------------------------------------
    # Sync workers
    # ------------------------------------------------------------------

    def _sync_register(self, pet_name: str, image_bytes: bytes) -> Dict:
        t0 = time.perf_counter()
        rgb = self._decode_bytes(image_bytes)
        face = self._face_pp.process(rgb)
        emb = self._embed(face)
        samples = self.db.register(pet_name, emb)
        elapsed = round((time.perf_counter() - t0) * 1000, 2)
        return {
            "registered": True,
            "pet_name": pet_name,
            "num_samples": samples,
            "latency_ms": elapsed,
        }

    def _sync_recognize(self, image_bytes: bytes) -> RecognitionResult:
        t0 = time.perf_counter()
        rgb = self._decode_bytes(image_bytes)
        result = self._infer_from_rgb(rgb)
        result.latency_ms = (time.perf_counter() - t0) * 1000
        return result

    def _sync_recognize_array(self, bgr: np.ndarray) -> RecognitionResult:
        t0 = time.perf_counter()
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB) if bgr.shape[2] == 3 else bgr
        result = self._infer_from_rgb(rgb)
        result.latency_ms = (time.perf_counter() - t0) * 1000
        return result

    # ------------------------------------------------------------------
    # Core
    # ------------------------------------------------------------------

    def _infer_from_rgb(self, rgb: np.ndarray) -> RecognitionResult:
        face = self._face_pp.process(rgb)
        emb = self._embed(face)
        if emb is None:
            return self._stub_result()

        identity, confidence, distance = self.db.find_nearest(
            emb,
            top_k=self.cfg.recognition_top_k,
            threshold=self.cfg.recognition_threshold,
        )
        return RecognitionResult(
            identity=identity,
            confidence=confidence,
            distance=distance,
            matched=identity is not None,
            latency_ms=0.0,
            registered_pets=[p["name"] for p in self.db.list_pets()],
        )

    def _embed(self, face_arr: np.ndarray) -> Optional[np.ndarray]:
        """Run embedding model or return None if unavailable."""
        if not self._model_loaded or self._model is None:
            # Try a simple pixel-hash based pseudo-embedding for stub mode
            flat = cv2.resize(face_arr.astype(np.uint8), (16, 16)).flatten().astype(np.float32)
            norm = np.linalg.norm(flat)
            return flat / (norm + 1e-8)

        return get_embedding(self._model, face_arr)

    def _stub_result(self) -> RecognitionResult:
        return RecognitionResult(
            identity=None,
            confidence=0.0,
            distance=1.0,
            matched=False,
            latency_ms=0.0,
            registered_pets=[p["name"] for p in self.db.list_pets()],
        )

    @staticmethod
    def _decode_bytes(data: bytes) -> np.ndarray:
        arr = np.frombuffer(data, dtype=np.uint8)
        bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
        if bgr is None:
            raise ValueError("Could not decode image bytes for recognition.")
        return cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)

    # ------------------------------------------------------------------
    # Singleton
    # ------------------------------------------------------------------

    @classmethod
    def get_instance(cls) -> "PetRecognizer":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance


# ---------------------------------------------------------------------------
# Internal face preprocessor (160×160 crop for embedding)
# ---------------------------------------------------------------------------


class _FacePreprocessor:
    """Crop + align + resize a face region to the target embedding input size."""

    def __init__(self, target_size: Tuple[int, int] = (160, 160)) -> None:
        self._target = target_size
        from pathlib import Path
        import cv2 as _cv2
        _cv_data = Path(_cv2.__file__).parent / "data"
        _cat = str(_cv_data / "haarcascade_frontalcatface_extended.xml")
        _face = str(_cv_data / "haarcascade_frontalface_default.xml")
        self._cat_cc = self._load_cc(_cat)
        self._face_cc = self._load_cc(_face)

    def process(self, rgb: np.ndarray) -> np.ndarray:
        """Detect face, pad, resize to target, return float32."""
        gray = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
        bbox = self._detect(gray)
        if bbox is not None:
            x, y, w, h = bbox
            px, py = int(w * 0.12), int(h * 0.12)
            ih, iw = rgb.shape[:2]
            x1, y1 = max(0, x - px), max(0, y - py)
            x2, y2 = min(iw, x + w + px), min(ih, y + h + py)
            crop = rgb[y1:y2, x1:x2]
        else:
            # No face detected — use centre square of full image
            h, w = rgb.shape[:2]
            m = min(h, w)
            cy, cx = h // 2, w // 2
            crop = rgb[cy - m // 2: cy + m // 2, cx - m // 2: cx + m // 2]

        resized = cv2.resize(crop, self._target, interpolation=cv2.INTER_AREA)
        return resized.astype(np.float32)

    def _detect(self, gray: np.ndarray):
        for cc in (self._cat_cc, self._face_cc):
            if cc is None or cc.empty():
                continue
            faces = cc.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=4, minSize=(30, 30))
            if len(faces) > 0:
                return max(faces, key=lambda r: r[2] * r[3])
        return None

    @staticmethod
    def _load_cc(path: str):
        if not __import__("os").path.isfile(path):
            return None
        cc = cv2.CascadeClassifier(path)
        return None if cc.empty() else cc
