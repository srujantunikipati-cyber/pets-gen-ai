"""
Tests for pet identity recognition components.

Covers:
  - EmbeddingDB CRUD operations
  - PetRecognizer stub / fallback behaviour (no model weights required)
  - RecognitionResult dataclass
  - Siamese model builder (topology only — no training)
"""

from __future__ import annotations

import json
import math
import os
import tempfile
import threading
from unittest.mock import MagicMock, patch

import numpy as np
import pytest

# ---------------------------------------------------------------------------
# EmbeddingDB tests
# ---------------------------------------------------------------------------

class TestEmbeddingDB:
    """Test the JSON-backed pet face gallery."""

    @pytest.fixture
    def tmp_db_path(self, tmp_path):
        return str(tmp_path / "test_embeddings.json")

    @pytest.fixture
    def db(self, tmp_db_path):
        from pet_emotion.recognition.embedding_db import EmbeddingDB
        return EmbeddingDB(db_path=tmp_db_path)

    # --- registration ---

    def test_register_new_pet(self, db):
        emb = np.ones(128, dtype=np.float32)
        n = db.register("Buddy", emb)
        assert n == 1

    def test_register_adds_to_existing(self, db):
        emb = np.random.rand(128).astype(np.float32)
        db.register("Max", emb)
        db.register("Max", emb * 0.9)
        n = db.register("Max", emb * 0.8)
        assert n == 3

    def test_register_caps_at_max_samples(self, db):
        for i in range(15):
            db.register("Rex", np.random.rand(128).astype(np.float32))
        # Load raw DB to check
        with open(db._path) as f:
            raw = json.load(f)
        assert len(raw["pets"]["Rex"]["embeddings"]) <= 10

    def test_register_persists_to_disk(self, tmp_db_path):
        from pet_emotion.recognition.embedding_db import EmbeddingDB
        db1 = EmbeddingDB(db_path=tmp_db_path)
        db1.register("Whiskers", np.ones(128, dtype=np.float32))
        # New instance reads from disk
        db2 = EmbeddingDB(db_path=tmp_db_path)
        names = [p["name"] for p in db2.list_pets()]
        assert "Whiskers" in names

    # --- find_nearest ---

    def test_find_nearest_returns_correct_pet(self, db):
        emb_a = np.zeros(128, dtype=np.float32); emb_a[0] = 1.0
        emb_b = np.zeros(128, dtype=np.float32); emb_b[1] = 1.0
        db.register("Alpha", emb_a)
        db.register("Beta", emb_b)

        name, conf, dist = db.find_nearest(emb_a, threshold=2.0)
        assert name == "Alpha"

    def test_find_nearest_returns_none_below_threshold(self, db):
        db.register("Solo", np.ones(128, dtype=np.float32) / np.sqrt(128))
        query = np.zeros(128, dtype=np.float32); query[0] = 1.0
        name, conf, dist = db.find_nearest(query, threshold=0.001)
        assert name is None

    def test_find_nearest_on_empty_db(self, db):
        query = np.ones(128, dtype=np.float32) / np.sqrt(128)
        name, conf, dist = db.find_nearest(query)
        assert name is None
        assert conf == 0.0

    # --- list / delete ---

    def test_list_pets(self, db):
        for pet in ["Fido", "Kitty", "Bird"]:
            db.register(pet, np.random.rand(128).astype(np.float32))
        pets = db.list_pets()
        assert len(pets) == 3
        # Each entry is a dict with 'name' key
        assert all("name" in p for p in pets)

    def test_delete_pet(self, db):
        db.register("Gone", np.ones(128, dtype=np.float32))
        ok = db.delete_pet("Gone")
        assert ok is True
        assert db.pet_count() == 0

    def test_delete_nonexistent_pet(self, db):
        ok = db.delete_pet("ghost")
        assert ok is False

    # --- thread safety ---

    def test_concurrent_registration(self, db):
        """Multiple threads registering simultaneously should not corrupt the DB."""
        errors = []

        def _worker(name: str):
            try:
                for _ in range(5):
                    db.register(name, np.random.rand(128).astype(np.float32))
            except Exception as exc:
                errors.append(exc)

        threads = [threading.Thread(target=_worker, args=(f"Pet{i}",)) for i in range(6)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert errors == [], f"Thread errors: {errors}"


# ---------------------------------------------------------------------------
# PetRecognizer tests
# ---------------------------------------------------------------------------

class TestPetRecognizer:
    """Test PetRecognizer with stub fallback (no model weights required)."""

    @pytest.fixture(autouse=True)
    def reset_singleton(self):
        """Ensure a fresh singleton per test."""
        from pet_emotion.recognition import recognizer as rec_mod
        rec_mod.PetRecognizer._instance = None
        yield
        rec_mod.PetRecognizer._instance = None

    @pytest.fixture
    def recognizer(self, tmp_path, monkeypatch):
        from pet_emotion.config import EmotionConfig
        from pet_emotion.recognition.recognizer import PetRecognizer
        cfg = EmotionConfig()
        cfg.embedding_db_path = str(tmp_path / "emb.json")
        cfg.siamese_weights_path = str(tmp_path / "nonexistent.h5")  # force stub mode
        r = PetRecognizer(cfg=cfg)
        return r

    @pytest.fixture
    def white_image_bytes(self):
        import cv2, io
        img = np.full((160, 160, 3), 200, dtype=np.uint8)
        ok, buf = cv2.imencode(".jpg", img)
        return buf.tobytes()

    # --- RecognitionResult ---

    def test_recognition_result_dataclass(self):
        from pet_emotion.recognition.recognizer import RecognitionResult
        r = RecognitionResult(
            identity="Buddy",
            confidence=0.9,
            distance=0.1,
            matched=True,
            latency_ms=5.0,
        )
        assert r.to_dict()["identity"] == "Buddy"
        assert r.to_dict()["matched"] is True

    def test_recognition_result_no_match(self):
        from pet_emotion.recognition.recognizer import RecognitionResult
        r = RecognitionResult(identity=None, confidence=0.0, distance=0.99, matched=False, latency_ms=1.0)
        d = r.to_dict()
        assert d["matched"] is False
        assert d["identity"] is None

    # --- register_pet async ---

    @pytest.mark.asyncio
    async def test_register_pet_returns_tuple(self, recognizer, white_image_bytes):
        result = await recognizer.register_pet("Buddy", white_image_bytes)
        assert isinstance(result, dict)
        assert "registered" in result
        assert "num_samples" in result

    @pytest.mark.asyncio
    async def test_register_then_recognize(self, recognizer, white_image_bytes):
        await recognizer.register_pet("Buddy", white_image_bytes)
        result = await recognizer.recognize(white_image_bytes)
        # With stub embedding, result should not crash
        assert hasattr(result, "matched")
        assert hasattr(result, "confidence")
        assert hasattr(result, "pet_name")

    # --- empty DB ---

    @pytest.mark.asyncio
    async def test_recognize_empty_db(self, recognizer, white_image_bytes):
        result = await recognizer.recognize(white_image_bytes)
        assert result.matched is False
        assert result.pet_name is None

    # --- bad input ---

    @pytest.mark.asyncio
    async def test_register_bad_image_bytes(self, recognizer):
        result = await recognizer.register_pet("Test", b"not_an_image")
        # Should not raise — stub handles gracefully
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_recognize_bad_image_bytes(self, recognizer):
        result = await recognizer.recognize(b"garbage")
        assert result.matched is False

    # --- recognize_from_array ---

    @pytest.mark.asyncio
    async def test_recognize_from_array(self, recognizer):
        bgr = np.full((160, 160, 3), 128, dtype=np.uint8)
        result = await recognizer.recognize_from_array(bgr)
        assert hasattr(result, "matched")

    # --- singleton ---

    def test_singleton_same_instance(self):
        from pet_emotion.recognition.recognizer import PetRecognizer
        a = PetRecognizer.get_instance()
        b = PetRecognizer.get_instance()
        assert a is b
