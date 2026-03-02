"""Tests for pet_emotion.config — EmotionConfig."""

from __future__ import annotations

import os

import pytest

from pet_emotion.config import EmotionConfig, emotion_config


class TestEmotionConfig:
    def test_default_num_classes(self):
        cfg = EmotionConfig()
        assert cfg.num_classes == 6

    def test_default_labels_count(self):
        cfg = EmotionConfig()
        assert len(cfg.labels) == cfg.num_classes

    def test_default_input_shape(self):
        cfg = EmotionConfig()
        assert cfg.input_shape == (224, 224, 3)

    def test_confidence_threshold_range(self):
        cfg = EmotionConfig()
        assert 0 < cfg.confidence_threshold < 1

    def test_custom_override(self):
        cfg = EmotionConfig(num_classes=4, epochs=10)
        assert cfg.num_classes == 4
        assert cfg.epochs == 10

    def test_singleton_is_emotion_config_instance(self):
        assert isinstance(emotion_config, EmotionConfig)

    def test_allowed_extensions_non_empty(self):
        cfg = EmotionConfig()
        assert len(cfg.allowed_extensions) > 0

    def test_max_image_size_positive(self):
        cfg = EmotionConfig()
        assert cfg.max_image_size_bytes > 0

    def test_weights_path_inside_module(self):
        cfg = EmotionConfig()
        assert "pet_emotion" in cfg.weights_path or cfg.weights_path.endswith(".h5")

    def test_labels_sorted(self):
        """Labels must be sorted so training and inference use the same ordering."""
        cfg = EmotionConfig()
        assert cfg.labels == sorted(cfg.labels)
