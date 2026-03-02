"""Tests for pet_emotion.utils.monitoring — MetricsMonitor."""

from __future__ import annotations

import json
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from pet_emotion.utils.monitoring import MetricsMonitor, get_monitor


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def monitor(tmp_path) -> MetricsMonitor:
    metrics_file = str(tmp_path / "metrics.jsonl")
    return MetricsMonitor(metrics_file=metrics_file, alert_accuracy_drop=0.05)


# ---------------------------------------------------------------------------
# record()
# ---------------------------------------------------------------------------


class TestRecord:
    def test_record_writes_to_file(self, monitor, tmp_path):
        monitor.record("happy", 0.92, 45.0)
        lines = Path(monitor._file).read_text().strip().splitlines()
        assert len(lines) == 1
        entry = json.loads(lines[0])
        assert entry["label"] == "happy"
        assert entry["confidence"] == 0.92

    def test_record_increments_total(self, monitor):
        for i in range(5):
            monitor.record("sad", 0.7, 30.0)
        assert monitor._total_predictions == 5

    def test_record_with_ground_truth_tracks_correct(self, monitor):
        monitor.record("happy", 0.9, 20.0, ground_truth="happy")
        monitor.record("sad", 0.8, 20.0, ground_truth="happy")
        assert monitor._total_correct == 1

    def test_record_with_image_id(self, monitor, tmp_path):
        monitor.record("neutral", 0.85, 25.0, image_id="img_001")
        lines = Path(monitor._file).read_text().strip().splitlines()
        entry = json.loads(lines[0])
        assert entry["image_id"] == "img_001"

    def test_multiple_records_appended(self, monitor):
        for label in ["happy", "sad", "angry"]:
            monitor.record(label, 0.8, 30.0)
        lines = Path(monitor._file).read_text().strip().splitlines()
        assert len(lines) == 3


# ---------------------------------------------------------------------------
# summary()
# ---------------------------------------------------------------------------


class TestSummary:
    def test_empty_window_returns_none_stats(self, monitor):
        s = monitor.summary()
        assert s["window_size"] == 0
        assert s["mean_confidence"] is None

    def test_summary_after_records(self, monitor):
        monitor.record("happy", 0.9, 30.0)
        monitor.record("sad", 0.7, 40.0)
        s = monitor.summary()
        assert s["window_size"] == 2
        assert abs(s["mean_confidence"] - 0.8) < 0.001

    def test_label_distribution(self, monitor):
        for _ in range(3):
            monitor.record("happy", 0.9, 20.0)
        monitor.record("sad", 0.6, 20.0)
        s = monitor.summary()
        assert s["label_distribution"]["happy"] == 3
        assert s["label_distribution"]["sad"] == 1

    def test_rolling_accuracy_with_labels(self, monitor):
        monitor.record("happy", 0.9, 20.0, ground_truth="happy")
        monitor.record("sad", 0.8, 20.0, ground_truth="happy")   # wrong
        monitor.record("neutral", 0.7, 20.0, ground_truth="neutral")
        s = monitor.summary()
        # 2 correct out of 3
        assert abs(s["rolling_accuracy"] - 2 / 3) < 0.001


# ---------------------------------------------------------------------------
# reset_window()
# ---------------------------------------------------------------------------


class TestResetWindow:
    def test_reset_clears_window(self, monitor):
        monitor.record("happy", 0.9, 20.0)
        monitor.reset_window()
        assert monitor.summary()["window_size"] == 0

    def test_total_predictions_preserved_after_reset(self, monitor):
        monitor.record("happy", 0.9, 20.0)
        monitor.reset_window()
        assert monitor._total_predictions == 1


# ---------------------------------------------------------------------------
# Drift detection (private)
# ---------------------------------------------------------------------------


class TestDriftDetection:
    def test_drift_alert_logged(self, monitor, caplog):
        import logging
        # Establish baseline with high confidence
        for _ in range(25):
            monitor.record("happy", 0.95, 10.0)

        # Simulate large drop
        for _ in range(25):
            monitor.record("sad", 0.50, 10.0)

        # Should have logged a WARNING
        warning_messages = [r.message for r in caplog.records if r.levelno == logging.WARNING]
        drift_alerts = [m for m in warning_messages if "DRIFT" in m]
        assert len(drift_alerts) > 0


# ---------------------------------------------------------------------------
# get_monitor() singleton
# ---------------------------------------------------------------------------


class TestGetMonitorSingleton:
    def test_returns_same_instance(self, tmp_path, monkeypatch):
        import pet_emotion.utils.monitoring as mod

        # Reset singleton
        mod._monitor_instance = None

        monkeypatch.setattr(
            "pet_emotion.config.emotion_config.metrics_file",
            str(tmp_path / "m.jsonl"),
        )
        m1 = get_monitor()
        m2 = get_monitor()
        assert m1 is m2

        # Cleanup
        mod._monitor_instance = None
