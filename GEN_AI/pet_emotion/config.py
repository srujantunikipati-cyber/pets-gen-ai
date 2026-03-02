"""Centralised configuration for the Pet Emotion Recognition module."""

import os
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Tuple


# ---------------------------------------------------------------------------
# Base paths
# ---------------------------------------------------------------------------
ROOT_DIR = Path(__file__).resolve().parent  # pet_emotion/
WEIGHTS_DIR = ROOT_DIR / "model" / "weights"
WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)

# Recognition / landmarks dirs
RECOGNITION_DIR = ROOT_DIR / "recognition"
LANDMARKS_DIR = ROOT_DIR / "landmarks"


@dataclass
class EmotionConfig:
    """All knobs in one place — override via environment variables."""

    # Model
    model_name: str = "MobileNetV2_PetEmotion"
    num_classes: int = 6
    input_shape: Tuple[int, int, int] = (224, 224, 3)
    weights_path: str = str(WEIGHTS_DIR / "pet_emotion_mobilenetv2.h5")

    # Emotion labels (index → label) — MUST remain sorted for train/infer consistency
    labels: List[str] = field(
        default_factory=lambda: sorted(["angry", "fearful", "happy", "neutral", "sad", "surprised"])
    )

    # Training
    batch_size: int = 32
    epochs: int = 30
    learning_rate: float = 1e-4
    fine_tune_lr: float = 1e-5
    val_split: float = 0.2
    augmentation: bool = True
    fine_tune_at_layer: int = 100  # Unfreeze MobileNetV2 from this layer for fine-tuning

    # Data
    data_dir: str = str(ROOT_DIR / "data")
    processed_dir: str = str(ROOT_DIR / "data" / "processed")

    # Inference
    confidence_threshold: float = 0.40   # Below this → "uncertain"
    face_detection_scale: float = 1.1
    face_detection_min_neighbors: int = 4

    # API
    max_image_size_bytes: int = 10 * 1024 * 1024   # 10 MB
    allowed_extensions: List[str] = field(
        default_factory=lambda: [".jpg", ".jpeg", ".png", ".bmp", ".webp"]
    )

    # Monitoring
    metrics_file: str = str(ROOT_DIR / "monitoring" / "metrics.jsonl")
    alert_accuracy_drop: float = 0.05   # Alert if rolling accuracy drops by >5 %

    # -----------------------------------------------------------------------
    # Identity Recognition (Siamese Network)
    # -----------------------------------------------------------------------
    embedding_dim: int = 128          # Output dimension of face embedding
    embedding_input_shape: Tuple[int, int, int] = (160, 160, 3)  # Input to embedding net
    siamese_weights_path: str = str(WEIGHTS_DIR / "pet_face_embeddings.h5")
    embedding_db_path: str = str(ROOT_DIR / "recognition" / "embedding_db.json")
    recognition_threshold: float = 0.55   # Cosine distance ≤ this → matched
    recognition_top_k: int = 5            # Compare against top-k gallery entries

    # -----------------------------------------------------------------------
    # Landmark Detection
    # -----------------------------------------------------------------------
    # 46-point breakdown:
    #   eyes:  12 per eye × 2 = 24 (pupils, corners, lids)
    #   mouth: 10 (lip corners, midpoints, jawline)
    #   nose:  5  (bridge, nostrils, tip)
    #   ears:  8  per ear × 2 = included via ROI when visible (not in 46 count)
    total_landmarks: int = 46
    landmark_input_shape: Tuple[int, int, int] = (96, 96, 1)  # grayscale crop
    landmark_weights_path: str = str(WEIGHTS_DIR / "pet_landmark_cnn.h5")
    landmark_confidence_threshold: float = 0.30
    dlib_shape_predictor_path: str = str(ROOT_DIR / "landmarks" / "shape_predictor_68_face_landmarks.dat")
    use_mediapipe_fallback: bool = True   # Use MediaPipe when dlib model absent


# Singleton used across the application
emotion_config = EmotionConfig()
