"""
Model monitoring and drift detection for Pet Emotion Recognition.

Features
--------
* Append each inference result (label, confidence, latency) to a JSONL log.
* Compute rolling accuracy against optional ground-truth labels.
* Alert (log WARNING) when rolling mean confidence drops by ``alert_threshold``.
* Expose a ``summary()`` method used by the /health endpoint.
"""

from __future__ import annotations

import json
import logging
import os
import threading
import time
from collections import deque
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

_WINDOW = 200  # Number of recent predictions to consider for rolling stats


class MetricsMonitor:
    """Thread-safe inference metrics recorder.

    There should be one shared instance per process (singleton pattern via
    ``get_monitor()`` factory below).
    """

    def __init__(self, metrics_file: str, alert_accuracy_drop: float = 0.05) -> None:
        self._file = Path(metrics_file)
        self._file.parent.mkdir(parents=True, exist_ok=True)
        self._alert_drop = alert_accuracy_drop
        self._lock = threading.Lock()

        # Rolling window — each entry: {"label": str, "confidence": float, "correct": bool | None}
        self._window: deque[Dict[str, Any]] = deque(maxlen=_WINDOW)
        self._total_predictions: int = 0
        self._total_correct: int = 0
        self._baseline_confidence: Optional[float] = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def record(
        self,
        label: str,
        confidence: float,
        latency_ms: float,
        ground_truth: Optional[str] = None,
        image_id: Optional[str] = None,
    ) -> None:
        """Record one prediction.

        Args:
            label: Predicted emotion label.
            confidence: Model confidence (0–1).
            latency_ms: End-to-end inference latency in milliseconds.
            ground_truth: Optional true label for accuracy calculation.
            image_id: Optional identifier for the input.
        """
        entry: Dict[str, Any] = {
            "ts": time.time(),
            "label": label,
            "confidence": round(confidence, 4),
            "latency_ms": round(latency_ms, 2),
        }
        if ground_truth is not None:
            entry["ground_truth"] = ground_truth
            entry["correct"] = label == ground_truth
        if image_id is not None:
            entry["image_id"] = image_id

        with self._lock:
            self._window.append(entry)
            self._total_predictions += 1
            if entry.get("correct") is True:
                self._total_correct += 1

        self._write(entry)
        self._check_drift(confidence)

    def summary(self) -> Dict[str, Any]:
        """Return a monitoring summary dict (used by /health endpoint)."""
        with self._lock:
            window_list = list(self._window)

        n = len(window_list)
        if n == 0:
            return {
                "total_predictions": self._total_predictions,
                "window_size": 0,
                "mean_confidence": None,
                "mean_latency_ms": None,
                "rolling_accuracy": None,
            }

        confidences = [e["confidence"] for e in window_list]
        latencies = [e["latency_ms"] for e in window_list]
        correct_entries = [e for e in window_list if "correct" in e]

        return {
            "total_predictions": self._total_predictions,
            "window_size": n,
            "mean_confidence": round(sum(confidences) / n, 4),
            "p50_confidence": round(sorted(confidences)[n // 2], 4),
            "mean_latency_ms": round(sum(latencies) / n, 2),
            "rolling_accuracy": (
                round(sum(1 for e in correct_entries if e["correct"]) / len(correct_entries), 4)
                if correct_entries else None
            ),
            "label_distribution": self._label_dist(window_list),
        }

    def reset_window(self) -> None:
        """Clear the rolling window (does NOT delete the log file)."""
        with self._lock:
            self._window.clear()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _write(self, entry: Dict[str, Any]) -> None:
        try:
            with open(self._file, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(entry) + "\n")
        except OSError as exc:
            logger.warning(f"Could not write metrics: {exc}")

    def _check_drift(self, confidence: float) -> None:
        with self._lock:
            window_list = list(self._window)

        n = len(window_list)
        if n < 20:
            return  # Not enough data yet

        rolling_mean = sum(e["confidence"] for e in window_list) / n

        if self._baseline_confidence is None:
            self._baseline_confidence = rolling_mean
            return

        drop = self._baseline_confidence - rolling_mean
        if drop > self._alert_drop:
            logger.warning(
                f"[DRIFT ALERT] Mean confidence dropped from "
                f"{self._baseline_confidence:.3f} to {rolling_mean:.3f} "
                f"(drop={drop:.3f} > threshold={self._alert_drop})."
            )

    @staticmethod
    def _label_dist(window: List[Dict[str, Any]]) -> Dict[str, int]:
        dist: Dict[str, int] = {}
        for e in window:
            dist[e["label"]] = dist.get(e["label"], 0) + 1
        return dist


# ---------------------------------------------------------------------------
# Singleton factory
# ---------------------------------------------------------------------------

_monitor_instance: Optional[MetricsMonitor] = None
_monitor_lock = threading.Lock()


def get_monitor(metrics_file: Optional[str] = None, alert_accuracy_drop: float = 0.05) -> MetricsMonitor:
    """Return (or create) the global ``MetricsMonitor`` singleton."""
    global _monitor_instance
    with _monitor_lock:
        if _monitor_instance is None:
            from pet_emotion.config import emotion_config

            _monitor_instance = MetricsMonitor(
                metrics_file=metrics_file or emotion_config.metrics_file,
                alert_accuracy_drop=alert_accuracy_drop,
            )
    return _monitor_instance
