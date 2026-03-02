"""
Training script for Pet Emotion Recognition model.

Usage (from project root):
    python -m pet_emotion.model.train --data_dir ./pet_emotion/data/raw --epochs 30

Expected data directory layout:
    data/raw/
        angry/        *.jpg / *.png
        fearful/      ...
        happy/        ...
        neutral/      ...
        sad/          ...
        surprised/    ...
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from pathlib import Path

# Allow running as a script from project root
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from pet_emotion.config import emotion_config, EmotionConfig  # noqa: E402
from pet_emotion.model.build_model import (  # noqa: E402
    build_mobilenetv2_emotion_model,
    unfreeze_for_fine_tuning,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------


def _build_datasets(cfg: EmotionConfig):
    """Build train / validation tf.data datasets from directory layout."""
    import tensorflow as tf

    img_size = cfg.input_shape[:2]

    train_ds = tf.keras.utils.image_dataset_from_directory(
        cfg.data_dir,
        validation_split=cfg.val_split,
        subset="training",
        seed=42,
        image_size=img_size,
        batch_size=cfg.batch_size,
        label_mode="categorical",
        class_names=cfg.labels,
    )

    val_ds = tf.keras.utils.image_dataset_from_directory(
        cfg.data_dir,
        validation_split=cfg.val_split,
        subset="validation",
        seed=42,
        image_size=img_size,
        batch_size=cfg.batch_size,
        label_mode="categorical",
        class_names=cfg.labels,
    )

    # Performance tuning
    AUTOTUNE = tf.data.AUTOTUNE
    train_ds = train_ds.cache().shuffle(1000).prefetch(AUTOTUNE)
    val_ds = val_ds.cache().prefetch(AUTOTUNE)

    logger.info(f"Labels → index map: {cfg.labels}")
    return train_ds, val_ds


def _build_augmentation_layer():
    """Return a Keras Sequential augmentation pipeline."""
    import tensorflow as tf

    return tf.keras.Sequential(
        [
            tf.keras.layers.RandomFlip("horizontal"),
            tf.keras.layers.RandomRotation(0.15),
            tf.keras.layers.RandomZoom(0.10),
            tf.keras.layers.RandomContrast(0.10),
            tf.keras.layers.RandomBrightness(0.08),
        ],
        name="augmentation",
    )


# ---------------------------------------------------------------------------
# Main training routine
# ---------------------------------------------------------------------------


def train(cfg: EmotionConfig | None = None) -> str:
    """Train (or fine-tune) the MobileNetV2 emotion model.

    Args:
        cfg: ``EmotionConfig`` to use; defaults to global ``emotion_config``.

    Returns:
        Path to saved weights file.
    """
    import tensorflow as tf

    if cfg is None:
        cfg = emotion_config

    if not os.path.isdir(cfg.data_dir):
        raise FileNotFoundError(
            f"Data directory '{cfg.data_dir}' not found. "
            "Create sub-folders per emotion class and populate with images."
        )

    Path(cfg.weights_path).parent.mkdir(parents=True, exist_ok=True)
    train_ds, val_ds = _build_datasets(cfg)

    # Optionally prepend augmentation to training data
    if cfg.augmentation:
        aug = _build_augmentation_layer()
        train_ds = train_ds.map(
            lambda x, y: (aug(x, training=True), y),
            num_parallel_calls=tf.data.AUTOTUNE,
        )

    # ---- Stage 1: Train head only ----
    logger.info("=== Stage 1: Training HEAD only ===")
    model = build_mobilenetv2_emotion_model(
        num_classes=cfg.num_classes,
        input_shape=cfg.input_shape,
    )

    callbacks_s1 = _make_callbacks(cfg, stage=1)
    model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=max(5, cfg.epochs // 3),
        callbacks=callbacks_s1,
    )

    # ---- Stage 2: Fine-tune upper MobileNetV2 layers ----
    logger.info("=== Stage 2: Fine-tuning ===")
    model = unfreeze_for_fine_tuning(
        model,
        fine_tune_at=cfg.fine_tune_at_layer,
        fine_tune_lr=cfg.fine_tune_lr,
    )
    callbacks_s2 = _make_callbacks(cfg, stage=2)
    model.fit(
        train_ds,
        validation_data=val_ds,
        epochs=cfg.epochs,
        initial_epoch=max(5, cfg.epochs // 3),
        callbacks=callbacks_s2,
    )

    # Save final weights
    model.save_weights(cfg.weights_path)
    logger.info(f"Training complete — weights saved to '{cfg.weights_path}'.")
    return cfg.weights_path


def _make_callbacks(cfg: EmotionConfig, stage: int):
    import tensorflow as tf

    ckpt_path = str(
        Path(cfg.weights_path).parent / f"stage{stage}_best.h5"
    )
    return [
        tf.keras.callbacks.ModelCheckpoint(
            ckpt_path,
            save_best_only=True,
            save_weights_only=True,
            monitor="val_accuracy",
            verbose=1,
        ),
        tf.keras.callbacks.EarlyStopping(
            monitor="val_accuracy",
            patience=7,
            restore_best_weights=True,
            verbose=1,
        ),
        tf.keras.callbacks.ReduceLROnPlateau(
            monitor="val_loss",
            factor=0.5,
            patience=3,
            min_lr=1e-7,
            verbose=1,
        ),
        tf.keras.callbacks.TensorBoard(
            log_dir=str(Path(cfg.weights_path).parent / f"logs/stage{stage}"),
            histogram_freq=1,
        ),
    ]


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train Pet Emotion Recognition model")
    parser.add_argument("--data_dir", required=True, help="Root data directory (emotion sub-folders)")
    parser.add_argument("--epochs", type=int, default=30)
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--weights_out", default=emotion_config.weights_path)
    args = parser.parse_args()

    cfg = EmotionConfig(
        data_dir=args.data_dir,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        weights_path=args.weights_out,
    )
    train(cfg)
