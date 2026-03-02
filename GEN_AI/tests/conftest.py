"""Shared test fixtures and helpers for the Pet Roast AI test suite."""

from __future__ import annotations

import io
import os
import sys
from pathlib import Path
from typing import Generator
from unittest.mock import MagicMock, patch, AsyncMock

import numpy as np
import pytest
from PIL import Image

# Ensure project root is on path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_jpeg_bytes(width: int = 200, height: int = 200, color=(128, 64, 32)) -> bytes:
    """Create an in-memory JPEG image and return its bytes."""
    img = Image.new("RGB", (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def make_png_bytes(width: int = 100, height: int = 100) -> bytes:
    img = Image.new("RGB", (width, height), (200, 100, 50))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def make_bgr_frame(width: int = 224, height: int = 224) -> np.ndarray:
    """Return a random BGR NumPy array (simulates a webcam frame)."""
    rng = np.random.default_rng(42)
    return rng.integers(0, 255, (height, width, 3), dtype=np.uint8)


# ---------------------------------------------------------------------------
# Pytest fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def jpeg_bytes() -> bytes:
    return make_jpeg_bytes()


@pytest.fixture
def png_bytes() -> bytes:
    return make_png_bytes()


@pytest.fixture
def bgr_frame() -> np.ndarray:
    return make_bgr_frame()


@pytest.fixture
def tiny_jpeg_bytes() -> bytes:
    """10×10 image — below the minimum accepted size."""
    return make_jpeg_bytes(10, 10)


@pytest.fixture
def oversized_jpeg_bytes() -> bytes:
    """Single-pixel white image with inflated content (simulated large file)."""
    # We'll simulate >10 MB by passing a large dummy bytes object
    return b"\xff\xd8\xff" + b"\x00" * (11 * 1024 * 1024)


@pytest.fixture(autouse=True)
def set_env_vars(monkeypatch):
    """Inject dummy API keys so services don't error on import."""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    monkeypatch.setenv("FAL_KEY", "fal-test-key")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379")
    monkeypatch.setenv("STORAGE_DIR", "/tmp/pet_roast_test_storage")
