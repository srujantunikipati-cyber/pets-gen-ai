"""Tests for backend.routes.emotion_routes — FastAPI endpoints."""

from __future__ import annotations

import base64
import io
import json
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from backend.main import app
from backend.services.pet_emotion_service import EmotionResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_jpeg_bytes(w=200, h=200):
    img = Image.new("RGB", (w, h), (120, 60, 30))
    buf = io.BytesIO()
    img.save(buf, "JPEG")
    return buf.getvalue()


def _stub_result(label="happy", confidence=0.88):
    return EmotionResult(
        label=label,
        confidence=confidence,
        all_scores={"happy": confidence, "sad": 1 - confidence},
        uncertain=False,
        latency_ms=30.0,
        face_detected=True,
    )


# ---------------------------------------------------------------------------
# Test client fixture
# ---------------------------------------------------------------------------


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


# ---------------------------------------------------------------------------
# GET /emotion/health
# ---------------------------------------------------------------------------


class TestHealthEndpoint:
    def test_returns_200(self, client):
        with patch("backend.routes.emotion_routes._get_service") as mock_svc:
            mock_svc.return_value.cfg = MagicMock(
                model_name="Test", weights_path="/tmp/w.h5",
                num_classes=6, labels=["happy", "sad"],
            )
            mock_svc.return_value._model_loaded = False
            with patch("backend.routes.emotion_routes.get_monitor") as mock_mon:
                mock_mon.return_value.summary.return_value = {}
                resp = client.get("/emotion/health")
        assert resp.status_code == 200

    def test_response_has_required_keys(self, client):
        with patch("backend.routes.emotion_routes._get_service") as mock_svc:
            mock_svc.return_value.cfg = MagicMock(
                model_name="Test", weights_path="/tmp/w.h5",
                num_classes=6, labels=[],
            )
            mock_svc.return_value._model_loaded = True
            with patch("backend.routes.emotion_routes.get_monitor") as mock_mon:
                mock_mon.return_value.summary.return_value = {"total_predictions": 0}
                resp = client.get("/emotion/health")
        data = resp.json()
        assert "status" in data
        assert "model_loaded" in data
        assert "monitoring" in data


# ---------------------------------------------------------------------------
# POST /emotion/predict
# ---------------------------------------------------------------------------


class TestPredictEndpoint:
    def test_valid_jpeg_returns_200(self, client):
        with patch("backend.routes.emotion_routes._get_service") as mock_svc:
            svc_inst = AsyncMock()
            svc_inst.predict_from_bytes = AsyncMock(return_value=_stub_result())
            mock_svc.return_value = svc_inst

            resp = client.post(
                "/emotion/predict",
                files={"file": ("test.jpg", _make_jpeg_bytes(), "image/jpeg")},
            )
        assert resp.status_code == 200

    def test_response_shape(self, client):
        with patch("backend.routes.emotion_routes._get_service") as mock_svc:
            svc_inst = AsyncMock()
            svc_inst.predict_from_bytes = AsyncMock(return_value=_stub_result())
            mock_svc.return_value = svc_inst

            resp = client.post(
                "/emotion/predict",
                files={"file": ("test.jpg", _make_jpeg_bytes(), "image/jpeg")},
            )
        data = resp.json()
        assert data["label"] == "happy"
        assert "confidence" in data
        assert "all_scores" in data
        assert "uncertain" in data

    def test_empty_file_returns_400(self, client):
        with patch("backend.routes.emotion_routes._get_service"):
            resp = client.post(
                "/emotion/predict",
                files={"file": ("empty.jpg", b"", "image/jpeg")},
            )
        assert resp.status_code == 400

    def test_preprocessing_error_returns_422(self, client):
        from pet_emotion.utils.preprocessing import PreprocessingError

        with patch("backend.routes.emotion_routes._get_service") as mock_svc:
            svc_inst = AsyncMock()
            svc_inst.predict_from_bytes = AsyncMock(
                side_effect=PreprocessingError("bad image")
            )
            mock_svc.return_value = svc_inst

            resp = client.post(
                "/emotion/predict",
                files={"file": ("bad.jpg", _make_jpeg_bytes(), "image/jpeg")},
            )
        assert resp.status_code == 422

    def test_with_ground_truth_form_field(self, client):
        with patch("backend.routes.emotion_routes._get_service") as mock_svc:
            capture = []

            async def _capture(data, filename="", ground_truth=None):
                capture.append(ground_truth)
                return _stub_result()

            svc_inst = MagicMock()
            svc_inst.predict_from_bytes = _capture
            mock_svc.return_value = svc_inst

            resp = client.post(
                "/emotion/predict",
                files={"file": ("t.jpg", _make_jpeg_bytes(), "image/jpeg")},
                data={"ground_truth": "happy"},
            )
        assert resp.status_code == 200
        assert capture[0] == "happy"


# ---------------------------------------------------------------------------
# POST /emotion/predict-url
# ---------------------------------------------------------------------------


class TestPredictUrlEndpoint:
    def test_valid_url(self, client):
        with patch("backend.routes.emotion_routes._get_service") as mock_svc, \
             patch("httpx.AsyncClient") as mock_http:

            # Mock HTTP response
            mock_response = MagicMock()
            mock_response.content = _make_jpeg_bytes()
            mock_response.raise_for_status = MagicMock()
            mock_http.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            svc_inst = AsyncMock()
            svc_inst.predict_from_bytes = AsyncMock(return_value=_stub_result())
            mock_svc.return_value = svc_inst

            resp = client.post(
                "/emotion/predict-url",
                json={"image_url": "https://example.com/cat.jpg"},
            )
        assert resp.status_code == 200

    def test_missing_image_url_returns_422(self, client):
        resp = client.post("/emotion/predict-url", json={})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /emotion/webcam-frame
# ---------------------------------------------------------------------------


class TestWebcamFrameEndpoint:
    def _make_b64_frame(self):
        frame_bytes = _make_jpeg_bytes(224, 224)
        return base64.b64encode(frame_bytes).decode()

    def test_valid_frame_returns_200(self, client):
        with patch("backend.routes.emotion_routes._get_service") as mock_svc:
            svc_inst = AsyncMock()
            svc_inst.predict_from_frame = AsyncMock(return_value=_stub_result())
            mock_svc.return_value = svc_inst

            resp = client.post(
                "/emotion/webcam-frame",
                json={"frame_b64": self._make_b64_frame()},
            )
        assert resp.status_code == 200

    def test_data_uri_prefix_stripped(self, client):
        """frame_b64 with 'data:image/jpeg;base64,...' prefix should work."""
        with patch("backend.routes.emotion_routes._get_service") as mock_svc:
            svc_inst = AsyncMock()
            svc_inst.predict_from_frame = AsyncMock(return_value=_stub_result())
            mock_svc.return_value = svc_inst

            b64 = "data:image/jpeg;base64," + self._make_b64_frame()
            resp = client.post("/emotion/webcam-frame", json={"frame_b64": b64})
        assert resp.status_code == 200

    def test_invalid_base64_returns_422(self, client):
        resp = client.post(
            "/emotion/webcam-frame",
            json={"frame_b64": "!!!not_base64!!!"},
        )
        assert resp.status_code == 422

    def test_missing_field_returns_422(self, client):
        resp = client.post("/emotion/webcam-frame", json={})
        assert resp.status_code == 422


# ---------------------------------------------------------------------------
# POST /emotion/reload
# ---------------------------------------------------------------------------


class TestReloadEndpoint:
    def test_successful_reload(self, client):
        with patch("backend.routes.emotion_routes._get_service") as mock_svc:
            mock_svc.return_value.reload_model.return_value = True
            resp = client.post("/emotion/reload")
        assert resp.status_code == 200
        assert resp.json()["reloaded"] is True

    def test_failed_reload_returns_500(self, client):
        with patch("backend.routes.emotion_routes._get_service") as mock_svc, \
             patch("backend.routes.emotion_routes.emotion_config") as mock_cfg:
            mock_svc.return_value.reload_model.return_value = False
            mock_cfg.weights_path = "/tmp/missing.h5"
            resp = client.post("/emotion/reload")
        assert resp.status_code == 500
