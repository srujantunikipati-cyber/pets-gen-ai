"""
JSON-backed embedding database for pet identity registration.

Schema (embedding_db.json)
--------------------------
{
  "pets": {
    "<pet_name>": {
      "embeddings": [[float, ...], ...],   // list of 128-d vectors
      "registered_at": "ISO-8601 timestamp",
      "num_samples": 3
    }
  },
  "metadata": {
    "embedding_dim": 128,
    "version": 1
  }
}

Thread-safety: all reads/writes are protected by a threading.Lock.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

_SENTINEL_DIM = 128  # Default embedding dim; validated on first write


class EmbeddingDBError(Exception):
    """Raised on DB integrity violations."""


class EmbeddingDB:
    """Thread-safe disk-backed pet face embedding database.

    Usage::

        db = EmbeddingDB("/path/to/embedding_db.json")
        db.register("Max", embedding_vector)
        name, conf, dist = db.find_nearest(query_embedding)
    """

    def __init__(self, db_path: str) -> None:
        self._path = Path(db_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._data: dict = self._load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def register(
        self,
        pet_name: str,
        embedding: np.ndarray,
        max_samples_per_pet: int = 10,
    ) -> int:
        """Register (or update) a pet's face embedding.

        Args:
            pet_name: Human-readable pet identifier.
            embedding: L2-normalised embedding vector.
            max_samples_per_pet: Keep at most this many samples per pet.

        Returns:
            Total number of samples stored for this pet after registration.
        """
        self._validate_embedding(embedding)
        name = pet_name.strip()
        if not name:
            raise EmbeddingDBError("pet_name must be non-empty.")

        vec = embedding.tolist()
        with self._lock:
            if "pets" not in self._data:
                self._data["pets"] = {}

            if name not in self._data["pets"]:
                self._data["pets"][name] = {
                    "embeddings": [],
                    "registered_at": _iso_now(),
                    "num_samples": 0,
                }

            entry = self._data["pets"][name]
            entry["embeddings"].append(vec)
            # Keep rolling window — drop oldest if over limit
            if len(entry["embeddings"]) > max_samples_per_pet:
                entry["embeddings"] = entry["embeddings"][-max_samples_per_pet:]
            entry["num_samples"] = len(entry["embeddings"])
            entry["last_updated"] = _iso_now()

            self._data["metadata"] = {
                "embedding_dim": len(vec),
                "version": 1,
                "total_pets": len(self._data["pets"]),
            }
            self._save()
            logger.info(f"Registered '{name}' — total samples: {entry['num_samples']}")
            return entry["num_samples"]

    def find_nearest(
        self,
        query: np.ndarray,
        top_k: int = 5,
        threshold: float = 0.55,
    ) -> Tuple[Optional[str], float, float]:
        """Find the closest registered pet by cosine distance.

        Args:
            query: L2-normalised query embedding.
            top_k: Compare query against up to *top_k* embeddings per pet.
            threshold: Distance ≤ threshold is considered a match.

        Returns:
            Tuple of (pet_name | None, confidence 0–1, cosine_distance).
            Returns (None, 0.0, 1.0) when database is empty.
        """
        self._validate_embedding(query)
        with self._lock:
            pets = self._data.get("pets", {})

        if not pets:
            return None, 0.0, 1.0

        best_name: Optional[str] = None
        best_dist = float("inf")

        for name, entry in pets.items():
            gallery = np.array(entry["embeddings"], dtype=np.float32)
            # Mean of top-k closest gallery embeddings
            dists = np.linalg.norm(gallery - query[np.newaxis, :], axis=1)
            top_dists = np.sort(dists)[:top_k]
            mean_dist = float(np.mean(top_dists))
            if mean_dist < best_dist:
                best_dist = mean_dist
                best_name = name

        if best_dist > threshold:
            return None, 0.0, round(best_dist, 4)

        # Convert L2 distance to confidence (1.0 = perfect match)
        confidence = round(max(0.0, 1.0 - best_dist / threshold), 4)
        return best_name, confidence, round(best_dist, 4)

    def list_pets(self) -> List[Dict]:
        """Return metadata for all registered pets."""
        with self._lock:
            pets = self._data.get("pets", {})
        return [
            {
                "name": name,
                "num_samples": entry["num_samples"],
                "registered_at": entry.get("registered_at", ""),
                "last_updated": entry.get("last_updated", ""),
            }
            for name, entry in pets.items()
        ]

    def delete_pet(self, pet_name: str) -> bool:
        """Remove a pet from the database.  Returns True if it existed."""
        with self._lock:
            deleted = self._data.get("pets", {}).pop(pet_name, None) is not None
            if deleted:
                logger.info(f"Deleted pet '{pet_name}' from embedding DB.")
                self._save()
        return deleted

    def pet_count(self) -> int:
        with self._lock:
            return len(self._data.get("pets", {}))

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _load(self) -> dict:
        if self._path.is_file():
            try:
                data = json.loads(self._path.read_text(encoding="utf-8"))
                logger.info(
                    f"EmbeddingDB loaded from '{self._path}' — "
                    f"{len(data.get('pets', {}))} pets."
                )
                return data
            except (json.JSONDecodeError, OSError) as exc:
                logger.warning(f"Could not load embedding DB: {exc}. Starting fresh.")
        return {"pets": {}, "metadata": {"embedding_dim": _SENTINEL_DIM, "version": 1}}

    def _save(self) -> None:
        try:
            self._path.write_text(
                json.dumps(self._data, indent=2), encoding="utf-8"
            )
        except OSError as exc:
            logger.error(f"Could not persist EmbeddingDB: {exc}")

    @staticmethod
    def _validate_embedding(emb: np.ndarray) -> None:
        if not isinstance(emb, np.ndarray):
            raise EmbeddingDBError(f"Embedding must be a numpy array, got {type(emb)}.")
        if emb.ndim != 1:
            raise EmbeddingDBError(f"Embedding must be 1-D, got shape {emb.shape}.")
        if len(emb) == 0:
            raise EmbeddingDBError("Embedding vector is empty.")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _iso_now() -> str:
    import datetime
    return datetime.datetime.utcnow().isoformat() + "Z"
