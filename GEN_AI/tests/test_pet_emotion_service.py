"""Tests for backend.services.pet_emotion_service — PetEmotionService."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

from backend.services.pet_emotion_service import PetEmotionService, EmotionResult
from tests.conftest import make_jpeg_bytes, make_bgr_frame


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def reset_singleton():
    """Ensure each test gets a fresh service instance."""
    PetEmotionService._instance = None
    yield
    PetEmotionService._instance = None


@pytest.fixture
def no_weights_service(tmp_path) -> PetEmotionService:
    """Service with no weights file — model NOT loaded."""
    from pet_emotion.config import EmotionConfig

    cfg = EmotionConfig(weights_path=str(tmp_path / "nonexistent.h5"))
    return PetEmotionService(cfg=cfg)


@pytest.fixture
def mocked_model_service(tmp_path) -> PetEmotionService:
    """Service with a mocked Keras model (no actual TF dependency in tests)."""
    from pet_emotion.config import EmotionConfig

    cfg = EmotionConfig(weights_path=str(tmp_path / "weights.h5"), num_classes=6)

    svc = PetEmotionService.__new__(PetEmotionService)
    svc.cfg = cfg

    # Mock preprocessor
    mock_pp = MagicMock()
    mock_pp.from_bytes.return_value = np.zeros((224, 224, 3), dtype=np.float32)
    mock_pp.from_path.return_value = np.zeros((224, 224, 3), dtype=np.float32)
    mock_pp.webcam_frame.return_value = np.zeros((224, 224, 3), dtype=np.float32)
    mock_pp.to_batch = lambda x: np.expand_dims(x, axis=0)
    svc._preprocessor = mock_pp

    # Mock Keras model
    mock_model = MagicMock()
    probs = np.array([0.05, 0.05, 0.75, 0.05, 0.05, 0.05], dtype=np.float32)  # happy wins
    mock_model.predict.return_value = np.array([probs])
    svc._model = mock_model
    svc._model_loaded = True

    # Mock monitor
    svc._monitor = MagicMock()
    svc._monitor.record = MagicMock()

    return svc


# ---------------------------------------------------------------------------
# No-model stub behaviour
# ---------------------------------------------------------------------------


class TestNoModelStub:
    def test_stub_returns_uncertain(self, no_weights_service):
        result = no_weights_service._stub_result(face_detected=False)
        assert result.uncertain is True
        assert result.label == "uncertain"

    def test_stub_has_all_labels(self, no_weights_service):
        result = no_weights_service._stub_result(face_detected=False)
        assert set(result.all_scores.keys()) == set(no_weights_service.cfg.labels)

    def test_stub_uniform_scores(self, no_weights_service):
        result = no_weights_service._stub_result(face_detected=False)
        scores = list(result.all_scores.values())
        assert abs(max(scores) - min(scores)) < 0.001  # all equal


# ---------------------------------------------------------------------------
# Inference with mocked model
# ---------------------------------------------------------------------------


class TestMockedInference:
    def test_infer_returns_happy(self, mocked_model_service):
        arr = np.zeros((224, 224, 3), dtype=np.float32)
        result = mocked_model_service._infer(arr, face_detected=True)
        assert result.label == "happy"
        assert result.confidence == pytest.approx(0.75, abs=0.001)

    def test_infer_face_detected_propagated(self, mocked_model_service):
        arr = np.zeros((224, 224, 3), dtype=np.float32)
        result = mocked_model_service._infer(arr, face_detected=True)
        assert result.face_detected is True

    def test_infer_low_confidence_uncertain(self, mocked_model_service):
        probs = np.array([0.18, 0.17, 0.17, 0.16, 0.16, 0.16], dtype=np.float32)
        mocked_model_service._model.predict.return_value = np.array([probs])
        # All scores < 0.40 threshold
        mocked_model_service.cfg.confidence_threshold = 0.40
        arr = np.zeros((224, 224, 3), dtype=np.float32)
        result = mocked_model_service._infer(arr, face_detected=False)
        assert result.uncertain is True

    @pytest.mark.asyncio
    async def test_predict_from_bytes(self, mocked_model_service):
        result = await mocked_model_service.predict_from_bytes(make_jpeg_bytes())
        assert result.label == "happy"

    @pytest.mark.asyncio
    async def test_predict_from_path(self, mocked_model_service, tmp_path):
        img_path = tmp_path / "test.jpg"
        img_path.write_bytes(make_jpeg_bytes())
        result = await mocked_model_service.predict_from_path(str(img_path))
        assert result.label == "happy"

    @pytest.mark.asyncio
    async def test_predict_from_frame(self, mocked_model_service):
        frame = make_bgr_frame()
        result = await mocked_model_service.predict_from_frame(frame)
        assert result.label == "happy"

    @pytest.mark.asyncio
    async def test_monitor_record_called(self, mocked_model_service):
        await mocked_model_service.predict_from_bytes(make_jpeg_bytes())
        mocked_model_service._monitor.record.assert_called_once()


# ---------------------------------------------------------------------------
# EmotionResult.to_dict()
# ---------------------------------------------------------------------------


class TestEmotionResultToDict:
    def test_keys_present(self):
        result = EmotionResult(
            label="happy",
            confidence=0.9,
            all_scores={"happy": 0.9, "sad": 0.1},
            uncertain=False,
            latency_ms=25.0,
            face_detected=True,
        )
        d = result.to_dict()
        assert set(d.keys()) == {
            "label", "confidence", "all_scores", "uncertain", "latency_ms", "face_detected"
        }

    def test_confidence_rounded(self):
        result = EmotionResult(
            label="sad", confidence=0.123456789,
            all_scores={}, uncertain=False, latency_ms=10.0, face_detected=False,
        )
        d = result.to_dict()
        assert len(str(d["confidence"]).split(".")[-1]) <= 4


# ---------------------------------------------------------------------------
# Singleton factory
# ---------------------------------------------------------------------------


class TestSingleton:
    def test_get_instance_returns_same(self, no_weights_service):
        PetEmotionService._instance = no_weights_service
        assert PetEmotionService.get_instance() is no_weights_service
