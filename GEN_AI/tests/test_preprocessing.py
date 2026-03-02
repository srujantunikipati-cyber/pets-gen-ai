"""Tests for pet_emotion.utils.preprocessing — ImagePreprocessor."""

from __future__ import annotations

import io
import os

import numpy as np
import pytest
from PIL import Image

from pet_emotion.utils.preprocessing import ImagePreprocessor, PreprocessingError
from tests.conftest import make_jpeg_bytes, make_png_bytes, make_bgr_frame


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def preprocessor() -> ImagePreprocessor:
    return ImagePreprocessor()


@pytest.fixture
def sample_jpeg(tmp_path) -> str:
    path = tmp_path / "test.jpg"
    path.write_bytes(make_jpeg_bytes(300, 300))
    return str(path)


# ---------------------------------------------------------------------------
# from_bytes
# ---------------------------------------------------------------------------


class TestFromBytes:
    def test_jpeg_returns_correct_shape(self, preprocessor):
        arr = preprocessor.from_bytes(make_jpeg_bytes())
        assert arr.shape == (224, 224, 3)

    def test_png_returns_correct_shape(self, preprocessor):
        arr = preprocessor.from_bytes(make_png_bytes())
        assert arr.shape == (224, 224, 3)

    def test_returns_float32(self, preprocessor):
        arr = preprocessor.from_bytes(make_jpeg_bytes())
        assert arr.dtype == np.float32

    def test_invalid_bytes_raises(self, preprocessor):
        with pytest.raises(PreprocessingError, match="decode"):
            preprocessor.from_bytes(b"not an image")

    def test_empty_bytes_raises(self, preprocessor):
        with pytest.raises(PreprocessingError):
            preprocessor.from_bytes(b"")


# ---------------------------------------------------------------------------
# from_path
# ---------------------------------------------------------------------------


class TestFromPath:
    def test_valid_path(self, preprocessor, sample_jpeg):
        arr = preprocessor.from_path(sample_jpeg)
        assert arr.shape == (224, 224, 3)

    def test_missing_file_raises(self, preprocessor):
        with pytest.raises(PreprocessingError, match="Could not read"):
            preprocessor.from_path("/nonexistent/file.jpg")


# ---------------------------------------------------------------------------
# from_array
# ---------------------------------------------------------------------------


class TestFromArray:
    def test_bgr_array(self, preprocessor, bgr_frame):
        arr = preprocessor.from_array(bgr_frame)
        assert arr.shape == (224, 224, 3)

    def test_grayscale_array(self, preprocessor):
        gray = np.zeros((200, 200), dtype=np.uint8)
        arr = preprocessor.from_array(gray)
        assert arr.shape == (224, 224, 3)

    def test_rgba_array(self, preprocessor):
        rgba = np.zeros((200, 200, 4), dtype=np.uint8)
        arr = preprocessor.from_array(rgba)
        assert arr.shape == (224, 224, 3)

    def test_empty_array_raises(self, preprocessor):
        with pytest.raises(PreprocessingError):
            preprocessor.from_array(np.array([]))


# ---------------------------------------------------------------------------
# webcam_frame
# ---------------------------------------------------------------------------


class TestWebcamFrame:
    def test_valid_frame(self, preprocessor, bgr_frame):
        arr = preprocessor.webcam_frame(bgr_frame)
        assert arr.shape == (224, 224, 3)
        assert arr.dtype == np.float32

    def test_none_frame_raises(self, preprocessor):
        with pytest.raises(PreprocessingError):
            preprocessor.webcam_frame(None)

    def test_empty_frame_raises(self, preprocessor):
        with pytest.raises(PreprocessingError):
            preprocessor.webcam_frame(np.array([]))


# ---------------------------------------------------------------------------
# to_batch
# ---------------------------------------------------------------------------


class TestToBatch:
    def test_adds_batch_dimension(self, preprocessor):
        arr = preprocessor.from_bytes(make_jpeg_bytes())
        batch = ImagePreprocessor.to_batch(arr)
        assert batch.shape == (1, 224, 224, 3)


# ---------------------------------------------------------------------------
# validate_image_bytes
# ---------------------------------------------------------------------------


class TestValidateImageBytes:
    def test_valid(self):
        ImagePreprocessor.validate_image_bytes(make_jpeg_bytes(), max_bytes=10_485_760)

    def test_too_large_raises(self):
        with pytest.raises(PreprocessingError, match="too large"):
            ImagePreprocessor.validate_image_bytes(b"x" * 1000, max_bytes=500)

    def test_empty_raises(self):
        with pytest.raises(PreprocessingError, match="empty"):
            ImagePreprocessor.validate_image_bytes(b"")

    def test_bad_extension_raises(self):
        with pytest.raises(PreprocessingError, match="extension"):
            ImagePreprocessor.validate_image_bytes(
                make_jpeg_bytes(),
                allowed_exts=[".jpg", ".png"],
                filename="photo.bmp",
            )

    def test_allowed_extension_passes(self):
        ImagePreprocessor.validate_image_bytes(
            make_jpeg_bytes(),
            allowed_exts=[".jpg", ".jpeg"],
            filename="photo.jpeg",
        )

    def test_no_filename_skips_ext_check(self):
        # Should not raise even if allowed_exts is given but filename is empty
        ImagePreprocessor.validate_image_bytes(
            make_jpeg_bytes(),
            allowed_exts=[".png"],
            filename="",
        )
