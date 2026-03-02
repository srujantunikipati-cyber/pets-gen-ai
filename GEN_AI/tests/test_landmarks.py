"""
Tests for pet facial landmark detection, alignment, and visualisation.

Covers:
  - LandmarkResult dataclass
  - LandmarkDetector with MediaPipe unavailable (OpenCV geometric fallback)
  - LandmarkDetector synthetic fallback
  - face_align utility functions
  - viz_landmarks draw_landmarks (no display, just shape checks)
"""

from __future__ import annotations

import io
from typing import List
from unittest.mock import MagicMock, patch

import cv2
import numpy as np
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_bgr(h: int = 200, w: int = 200, colour=(128, 128, 128)) -> np.ndarray:
    img = np.full((h, w, 3), colour, dtype=np.uint8)
    return img


def _make_jpeg_bytes(h: int = 200, w: int = 200) -> bytes:
    img = _make_bgr(h, w)
    ok, buf = cv2.imencode(".jpg", img)
    return buf.tobytes()


# ---------------------------------------------------------------------------
# LandmarkResult tests
# ---------------------------------------------------------------------------

class TestLandmarkResult:
    def test_empty_factory(self):
        from pet_emotion.landmarks.detector import LandmarkResult
        lr = LandmarkResult.empty("test")
        assert lr.confidence == 0.0
        assert lr.strategy == "test"
        assert lr.eyes == []

    def test_all_landmarks_property(self):
        from pet_emotion.landmarks.detector import LandmarkResult
        lr = LandmarkResult(
            eyes=[[0.1, 0.2]] * 24,
            mouth=[[0.5, 0.6]] * 10,
            nose=[[0.3, 0.4]] * 5,
        )
        assert lr.num_points == 39
        assert len(lr.all_landmarks) == 39

    def test_to_dict_structure(self):
        from pet_emotion.landmarks.detector import LandmarkResult
        lr = LandmarkResult(
            eyes=[[0.1, 0.1]] * 24,
            mouth=[[0.5, 0.5]] * 10,
            nose=[[0.3, 0.3]] * 5,
            ears=[[0.9, 0.9]] * 8,
            confidence=0.7,
            strategy="mediapipe",
            face_bbox=[10, 10, 80, 80],
        )
        d = lr.to_dict()
        assert "eyes" in d
        assert "mouth" in d
        assert "nose" in d
        assert "ears" in d
        assert "all" in d
        assert d["confidence"] == 0.7
        assert d["strategy"] == "mediapipe"
        assert len(d["all"]) == 39

    def test_to_dict_normalised_range(self):
        from pet_emotion.landmarks.detector import LandmarkResult
        lr = LandmarkResult(
            eyes=[[0.0, 1.0]] * 24,
            mouth=[[0.5, 0.5]] * 10,
            nose=[[0.2, 0.8]] * 5,
        )
        for pt in lr.all_landmarks:
            assert 0.0 <= pt[0] <= 1.0
            assert 0.0 <= pt[1] <= 1.0


# ---------------------------------------------------------------------------
# LandmarkDetector — OpenCV geometric fallback
# ---------------------------------------------------------------------------

class TestLandmarkDetectorOpenCV:
    """Tests that run without MediaPipe."""

    @pytest.fixture
    def detector(self):
        from pet_emotion.landmarks.detector import LandmarkDetector
        return LandmarkDetector(use_mediapipe=False)

    def test_detect_returns_landmark_result(self, detector):
        from pet_emotion.landmarks.detector import LandmarkResult
        img = _make_bgr()
        result = detector.detect(img)
        assert isinstance(result, LandmarkResult)

    def test_detect_from_bytes(self, detector):
        from pet_emotion.landmarks.detector import LandmarkResult
        result = detector.detect_from_bytes(_make_jpeg_bytes())
        assert isinstance(result, LandmarkResult)

    def test_detect_invalid_image(self, detector):
        result = detector.detect(np.array([]))
        assert result.strategy in ("invalid_input", "failed", "no_face_cv", "synthetic")

    def test_detect_bad_bytes(self, detector):
        result = detector.detect_from_bytes(b"not_image")
        assert result.strategy == "decode_error"

    def test_synthetic_fallback_structure(self, detector):
        """With a blank image, cascade finds nothing → synthetic."""
        img = _make_bgr(300, 300, colour=(200, 200, 200))
        result = detector.detect(img)
        # At least synthetic or opencv_geometric
        assert result.strategy in ("synthetic", "opencv_geometric", "no_face_cv")

    def test_landmark_counts_non_empty_result(self, detector):
        img = _make_bgr()
        result = detector._detect_synthetic(200, 200)
        assert len(result.eyes) == 24
        assert len(result.mouth) == 10
        assert len(result.nose) == 5

    def test_coordinates_in_unit_range(self, detector):
        result = detector._detect_synthetic(640, 480)
        for pt in result.all_landmarks:
            assert 0.0 <= pt[0] <= 1.0, f"x out of range: {pt[0]}"
            assert 0.0 <= pt[1] <= 1.0, f"y out of range: {pt[1]}"

    def test_detect_large_image(self, detector):
        img = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)
        result = detector.detect(img)
        assert result is not None


# ---------------------------------------------------------------------------
# LandmarkDetector — MediaPipe mocked
# ---------------------------------------------------------------------------

class TestLandmarkDetectorMediaPipe:
    """Tests using a mocked MediaPipe FaceMesh."""

    def _build_mock_mp(self, n_landmarks: int = 478):
        """Build a minimal MediaPipe mock."""
        mock_lm = MagicMock()
        mock_lm.x = 0.5
        mock_lm.y = 0.5
        mock_face_lm = MagicMock()
        mock_face_lm.landmark = [mock_lm] * n_landmarks

        mock_result = MagicMock()
        mock_result.multi_face_landmarks = [mock_face_lm]

        face_mesh_instance = MagicMock()
        face_mesh_instance.process.return_value = mock_result

        face_mesh_cls = MagicMock(return_value=face_mesh_instance)

        mp_mock = MagicMock()
        mp_mock.solutions.face_mesh.FaceMesh = face_mesh_cls
        return mp_mock, face_mesh_instance

    def test_mediapipe_strategy_selected(self):
        from pet_emotion.landmarks.detector import LandmarkDetector
        mp_mock, fm = self._build_mock_mp()

        detector = LandmarkDetector(use_mediapipe=False)
        # Manually inject mock
        detector._mp_available = True
        detector._mp = mp_mock
        detector._mp_face_mesh = fm

        result = detector.detect(_make_bgr())
        assert result.strategy == "mediapipe"
        assert result.confidence == 0.90

    def test_mediapipe_returns_24_eye_pts(self):
        from pet_emotion.landmarks.detector import LandmarkDetector
        mp_mock, fm = self._build_mock_mp()

        detector = LandmarkDetector(use_mediapipe=False)
        detector._mp_available = True
        detector._mp = mp_mock
        detector._mp_face_mesh = fm

        result = detector.detect(_make_bgr())
        assert len(result.eyes) == 24

    def test_mediapipe_no_face_fallback(self):
        from pet_emotion.landmarks.detector import LandmarkDetector

        mock_result = MagicMock()
        mock_result.multi_face_landmarks = []  # no face detected
        fm = MagicMock()
        fm.process.return_value = mock_result

        mp_mock = MagicMock()
        detector = LandmarkDetector(use_mediapipe=False)
        detector._mp_available = True
        detector._mp = mp_mock
        detector._mp_face_mesh = fm

        result = detector.detect(_make_bgr())
        # Should fall back to opencv or synthetic
        assert result.strategy != "mediapipe"


# ---------------------------------------------------------------------------
# face_align tests
# ---------------------------------------------------------------------------

class TestFaceAlign:
    def test_align_face_no_landmarks(self):
        from pet_emotion.landmarks.detector import LandmarkResult
        from pet_emotion.landmarks.face_align import align_face
        img = _make_bgr(224, 224)
        lr = LandmarkResult.empty()
        aligned = align_face(img, lr)
        assert aligned is not None
        assert aligned.shape[:2] == (160, 160)

    def test_align_face_with_24_eye_pts(self):
        from pet_emotion.landmarks.detector import LandmarkResult
        from pet_emotion.landmarks.face_align import align_face
        img = _make_bgr(224, 224)
        # Provide synthetic eye points
        left_eyes = [[0.3 + i * 0.005, 0.4] for i in range(12)]
        right_eyes = [[0.6 + i * 0.005, 0.4] for i in range(12)]
        lr = LandmarkResult(eyes=left_eyes + right_eyes, confidence=0.8, strategy="test")
        aligned = align_face(img, lr)
        assert aligned.shape[:2] == (160, 160)
        assert aligned.dtype == np.uint8

    def test_crop_roi_basic(self):
        from pet_emotion.landmarks.face_align import crop_roi
        img = _make_bgr(400, 400)
        crop = crop_roi(img, [50, 50, 100, 100], padding=0.1)
        assert crop.shape[2] == 3
        assert crop.size > 0

    def test_crop_roi_with_resize(self):
        from pet_emotion.landmarks.face_align import crop_roi
        img = _make_bgr(400, 400)
        crop = crop_roi(img, [50, 50, 100, 100], output_size=(64, 64))
        assert crop.shape[:2] == (64, 64)

    def test_crop_roi_clamps_to_image(self):
        from pet_emotion.landmarks.face_align import crop_roi
        img = _make_bgr(100, 100)
        # Bbox that goes beyond image bounds
        crop = crop_roi(img, [80, 80, 100, 100], padding=0.5)
        assert crop.size > 0

    def test_normalise_landmarks(self):
        from pet_emotion.landmarks.detector import LandmarkResult
        from pet_emotion.landmarks.face_align import normalise_landmarks
        lr = LandmarkResult(
            eyes=[[0.5, 0.5]] * 24,
            mouth=[[0.5, 0.6]] * 10,
            nose=[[0.5, 0.45]] * 5,
            confidence=0.7, strategy="test",
        )
        normed = normalise_landmarks(lr, [100, 100, 200, 200], 400, 400)
        # All x,y should be in [0,1] after remapping
        for pt in normed.all_landmarks:
            assert 0.0 <= pt[0] <= 1.0
            assert 0.0 <= pt[1] <= 1.0

    def test_eye_centres(self):
        from pet_emotion.landmarks.detector import LandmarkResult
        from pet_emotion.landmarks.face_align import eye_centres
        left_eyes = [[0.3, 0.4]] * 12
        right_eyes = [[0.6, 0.4]] * 12
        lr = LandmarkResult(eyes=left_eyes + right_eyes)
        lc, rc = eye_centres(lr, 400, 400)
        assert lc is not None
        assert rc is not None
        assert abs(lc[0] - 0.3 * 400) < 1.0
        assert abs(rc[0] - 0.6 * 400) < 1.0


# ---------------------------------------------------------------------------
# viz_landmarks tests
# ---------------------------------------------------------------------------

class TestVizLandmarks:
    @pytest.fixture
    def sample_result(self):
        from pet_emotion.landmarks.detector import LandmarkResult
        return LandmarkResult(
            eyes=[[0.3, 0.4]] * 12 + [[0.6, 0.4]] * 12,
            mouth=[[0.5, 0.7]] * 10,
            nose=[[0.5, 0.55]] * 5,
            ears=[[0.2, 0.3]] * 4 + [[0.8, 0.3]] * 4,
            confidence=0.85,
            strategy="mediapipe",
            face_bbox=[40, 60, 120, 120],
        )

    def test_draw_landmarks_returns_same_shape(self, sample_result):
        from pet_emotion.landmarks.viz_landmarks import draw_landmarks
        img = _make_bgr(300, 300)
        out = draw_landmarks(img, sample_result)
        assert out.shape == img.shape

    def test_draw_landmarks_does_not_mutate_input(self, sample_result):
        from pet_emotion.landmarks.viz_landmarks import draw_landmarks
        img = _make_bgr(300, 300)
        orig = img.copy()
        draw_landmarks(img, sample_result)
        assert np.array_equal(img, orig)

    def test_draw_landmarks_with_labels(self, sample_result):
        from pet_emotion.landmarks.viz_landmarks import draw_landmarks
        img = _make_bgr(300, 300)
        out = draw_landmarks(img, sample_result, draw_labels=True)
        assert out is not None
        assert out.dtype == np.uint8

    def test_draw_connections(self, sample_result):
        from pet_emotion.landmarks.viz_landmarks import draw_connections
        img = _make_bgr(300, 300)
        out = draw_connections(img, sample_result)
        assert out.shape == img.shape

    def test_landmarks_to_svg_contains_circles(self, sample_result):
        from pet_emotion.landmarks.viz_landmarks import landmarks_to_svg
        svg = landmarks_to_svg(sample_result, width=400, height=400)
        assert "<svg" in svg
        assert "<circle" in svg
        assert "fill=" in svg

    def test_draw_empty_landmarks(self):
        from pet_emotion.landmarks.detector import LandmarkResult
        from pet_emotion.landmarks.viz_landmarks import draw_landmarks
        img = _make_bgr(200, 200)
        lr = LandmarkResult.empty()
        out = draw_landmarks(img, lr)
        assert out.shape == img.shape
