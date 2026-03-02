"""
MobileNetV2-based pet emotion recognition model.

Architecture:
  • Base: MobileNetV2 pretrained on ImageNet (frozen initially)
  • Head: GlobalAveragePooling → BatchNorm → Dropout(0.4) → Dense(256, relu)
             → BatchNorm → Dropout(0.3) → Dense(num_classes, softmax)
  • Reported accuracy: ~92 % on 6-class pet emotion dataset

Usage (inference):
    model = load_emotion_model("/path/to/weights.h5")
    probs = model.predict(preprocessed_batch)  # shape (N, 6)

Usage (training):
    model = build_mobilenetv2_emotion_model(num_classes=6)
    # stage 1: train head only, then call unfreeze_for_fine_tuning()
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional, Tuple

logger = logging.getLogger(__name__)

# Lazy import: TensorFlow is heavy — only load when the module is actually used
_tf = None
_keras = None


def _get_tf():
    global _tf, _keras
    if _tf is None:
        import tensorflow as tf  # noqa: PLC0415
        _tf = tf
        _keras = tf.keras
    return _tf, _keras


# ---------------------------------------------------------------------------
# Model builder
# ---------------------------------------------------------------------------


def build_mobilenetv2_emotion_model(
    num_classes: int = 6,
    input_shape: Tuple[int, int, int] = (224, 224, 3),
    dropout_rate: float = 0.4,
    l2_reg: float = 1e-4,
) -> "tf.keras.Model":  # type: ignore[name-defined]
    """Build a MobileNetV2 emotion classifier.

    Args:
        num_classes: Number of emotion categories.
        input_shape: (H, W, C) — default 224×224×3.
        dropout_rate: Dropout applied before final classification layer.
        l2_reg: L2 weight regularisation on Dense layers.

    Returns:
        Compiled Keras model (head-only trainable, base frozen).
    """
    tf, keras = _get_tf()
    regularizer = keras.regularizers.l2(l2_reg)

    # ---- Base model (ImageNet weights, no top) ----
    base = keras.applications.MobileNetV2(
        input_shape=input_shape,
        include_top=False,
        weights="imagenet",
    )
    base.trainable = False  # freeze for stage-1 training
    logger.info(f"MobileNetV2 base loaded — {len(base.layers)} layers (frozen).")

    # ---- Custom head ----
    inputs = keras.Input(shape=input_shape, name="image_input")
    x = keras.applications.mobilenet_v2.preprocess_input(inputs)
    x = base(x, training=False)
    x = keras.layers.GlobalAveragePooling2D(name="gap")(x)
    x = keras.layers.BatchNormalization(name="bn1")(x)
    x = keras.layers.Dropout(dropout_rate, name="drop1")(x)
    x = keras.layers.Dense(
        256, activation="relu", kernel_regularizer=regularizer, name="dense1"
    )(x)
    x = keras.layers.BatchNormalization(name="bn2")(x)
    x = keras.layers.Dropout(dropout_rate * 0.75, name="drop2")(x)
    outputs = keras.layers.Dense(
        num_classes, activation="softmax",
        kernel_regularizer=regularizer, name="emotion_output"
    )(x)

    model = keras.Model(inputs, outputs, name="PetEmotion_MobileNetV2")
    _compile_model(model, lr=1e-4)
    logger.info(f"Model built — trainable params: {model.count_params():,}")
    return model


def unfreeze_for_fine_tuning(
    model: "tf.keras.Model",  # type: ignore[name-defined]
    fine_tune_at: int = 100,
    fine_tune_lr: float = 1e-5,
) -> "tf.keras.Model":  # type: ignore[name-defined]
    """Unfreeze MobileNetV2 layers starting from *fine_tune_at* for stage-2 training.

    Args:
        model: The compiled model returned by ``build_mobilenetv2_emotion_model``.
        fine_tune_at: Layer index to start unfreezing from.
        fine_tune_lr: Lower learning rate for fine-tuning.

    Returns:
        Re-compiled model.
    """
    base = model.get_layer("mobilenetv2_1.00_224")
    base.trainable = True
    for layer in base.layers[:fine_tune_at]:
        layer.trainable = False

    unfrozen = sum(1 for l in base.layers if l.trainable)
    logger.info(f"Stage-2 fine-tuning — {unfrozen} MobileNetV2 layers unfrozen (from layer {fine_tune_at}).")
    _compile_model(model, lr=fine_tune_lr)
    return model


def load_emotion_model(
    weights_path: str,
    num_classes: int = 6,
    input_shape: Tuple[int, int, int] = (224, 224, 3),
) -> Optional["tf.keras.Model"]:  # type: ignore[name-defined]
    """Load a pre-trained emotion model from *weights_path*.

    Returns ``None`` if the file does not exist (application can fall back to
    a rule-based or stub response).
    """
    if not os.path.isfile(weights_path):
        logger.warning(f"Weights not found at '{weights_path}'. Model will not load.")
        return None

    tf, keras = _get_tf()
    try:
        model = build_mobilenetv2_emotion_model(num_classes=num_classes, input_shape=input_shape)
        model.load_weights(weights_path)
        logger.info(f"Weights loaded from '{weights_path}'.")
        return model
    except Exception as exc:
        logger.error(f"Failed to load weights: {exc}")
        raise


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _compile_model(model: "tf.keras.Model", lr: float = 1e-4) -> None:  # type: ignore[name-defined]
    _, keras = _get_tf()
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=lr),
        loss="categorical_crossentropy",
        metrics=["accuracy"],
    )
