"""
Siamese Network for Pet Face Embeddings.

Architecture
-----------
  • Shared backbone: MobileNetV2 (pretrained ImageNet, stripped top)
  • Projection head: GAP → BN → Dense(256) → L2-normalised Dense(embedding_dim)
  • Training: Triplet loss (anchor, positive, negative) → margin 0.2
  • Inference: forward pass of ONE image → 128-d L2-normalised embedding

Usage
-----
    model = build_embedding_model(embedding_dim=128)
    # or
    model = load_embedding_model("/path/to/weights.h5")
    embedding = model.predict(batch)   # shape (N, 128), L2 normalised
"""

from __future__ import annotations

import logging
import os
from typing import Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

_tf = None
_keras = None


def _get_tf():
    global _tf, _keras
    if _tf is None:
        import tensorflow as tf  # noqa
        _tf = tf
        _keras = tf.keras
    return _tf, _keras


# ---------------------------------------------------------------------------
# Embedding network (shared encoder)
# ---------------------------------------------------------------------------


def build_embedding_model(
    embedding_dim: int = 128,
    input_shape: Tuple[int, int, int] = (160, 160, 3),
    l2_reg: float = 1e-4,
    dropout_rate: float = 0.35,
) -> "tf.keras.Model":  # type: ignore[name-defined]
    """Build a MobileNetV2-based face embedding encoder.

    The output is L2-normalised so embeddings lie on the unit hypersphere.
    Cosine similarity between two embeddings equals 1 - (||a - b||² / 2).

    Args:
        embedding_dim: Dimensionality of the output embedding vector.
        input_shape: (H, W, C) — default 160×160×3 (FaceNet-style).
        l2_reg: Weight decay on Dense layers.
        dropout_rate: Dropout before projection layers.

    Returns:
        Compiled Keras model: input (1, H, W, C) → embedding (1, embedding_dim).
    """
    tf, keras = _get_tf()
    reg = keras.regularizers.l2(l2_reg)

    base = keras.applications.MobileNetV2(
        input_shape=input_shape, include_top=False, weights="imagenet"
    )
    base.trainable = False
    logger.info(f"Embedding encoder: MobileNetV2 base loaded ({len(base.layers)} layers, frozen).")

    inputs = keras.Input(shape=input_shape, name="face_input")
    x = keras.applications.mobilenet_v2.preprocess_input(inputs)
    x = base(x, training=False)
    x = keras.layers.GlobalAveragePooling2D(name="emb_gap")(x)
    x = keras.layers.BatchNormalization(name="emb_bn1")(x)
    x = keras.layers.Dropout(dropout_rate, name="emb_drop1")(x)
    x = keras.layers.Dense(256, activation="relu", kernel_regularizer=reg, name="emb_dense1")(x)
    x = keras.layers.BatchNormalization(name="emb_bn2")(x)
    x = keras.layers.Dropout(dropout_rate * 0.5, name="emb_drop2")(x)
    x = keras.layers.Dense(embedding_dim, kernel_regularizer=reg, name="emb_dense2")(x)

    # L2 normalise — embeddings live on unit sphere
    outputs = keras.layers.Lambda(
        lambda v: tf.math.l2_normalize(v, axis=1), name="l2_norm"
    )(x)

    model = keras.Model(inputs, outputs, name="PetFaceEmbedding")
    model.compile(
        optimizer=keras.optimizers.Adam(1e-4),
        loss=_triplet_loss_fn(margin=0.2),
    )
    logger.info(f"Embedding model built — output: ({embedding_dim},) L2-normalised.")
    return model


# ---------------------------------------------------------------------------
# Triplet loss
# ---------------------------------------------------------------------------


def _triplet_loss_fn(margin: float = 0.2):
    """Online triplet loss (semi-hard mining not required for batch use)."""
    def triplet_loss(y_true, y_pred):
        import tensorflow as tf
        # y_pred shape: (3*N, embedding_dim) — [anchors; positives; negatives] stacked
        n = tf.shape(y_pred)[0] // 3
        anchors   = y_pred[:n]
        positives = y_pred[n: 2 * n]
        negatives = y_pred[2 * n:]

        pos_dist = tf.reduce_sum(tf.square(anchors - positives), axis=1)
        neg_dist = tf.reduce_sum(tf.square(anchors - negatives), axis=1)
        loss = tf.maximum(0.0, pos_dist - neg_dist + margin)
        return tf.reduce_mean(loss)

    return triplet_loss


# ---------------------------------------------------------------------------
# Fine-tune upper layers
# ---------------------------------------------------------------------------


def unfreeze_embedding_for_fine_tuning(
    model: "tf.keras.Model",  # type: ignore[name-defined]
    fine_tune_at: int = 120,
    lr: float = 5e-6,
) -> "tf.keras.Model":  # type: ignore[name-defined]
    """Unfreeze upper MobileNetV2 layers for stage-2 fine-tuning."""
    base = model.get_layer("mobilenetv2_1.00_160")
    base.trainable = True
    for layer in base.layers[:fine_tune_at]:
        layer.trainable = False
    tf, keras = _get_tf()
    model.compile(
        optimizer=keras.optimizers.Adam(lr),
        loss=_triplet_loss_fn(margin=0.2),
    )
    unfrozen = sum(1 for l in base.layers if l.trainable)
    logger.info(f"Embedding fine-tuning: {unfrozen} layers unfrozen from index {fine_tune_at}.")
    return model


# ---------------------------------------------------------------------------
# Load / save helpers
# ---------------------------------------------------------------------------


def load_embedding_model(
    weights_path: str,
    embedding_dim: int = 128,
    input_shape: Tuple[int, int, int] = (160, 160, 3),
) -> Optional["tf.keras.Model"]:  # type: ignore[name-defined]
    """Load pretrained embedding weights.  Returns None if file absent."""
    if not os.path.isfile(weights_path):
        logger.warning(
            f"Embedding weights not found at '{weights_path}'. "
            "Run training or place pretrained weights there."
        )
        return None
    try:
        model = build_embedding_model(embedding_dim=embedding_dim, input_shape=input_shape)
        model.load_weights(weights_path)
        logger.info(f"Embedding weights loaded from '{weights_path}'.")
        return model
    except Exception as exc:
        logger.error(f"Failed to load embedding weights: {exc}")
        raise


# ---------------------------------------------------------------------------
# Utility: compute embedding for a single processed numpy array
# ---------------------------------------------------------------------------


def get_embedding(
    model: "tf.keras.Model",  # type: ignore[name-defined]
    face_arr: np.ndarray,
) -> np.ndarray:
    """Run one face through the embedding model.

    Args:
        model: Loaded embedding model.
        face_arr: Float32 array of shape (H, W, 3) or (1, H, W, 3).

    Returns:
        1-D numpy array of shape (embedding_dim,), L2-normalised.
    """
    if face_arr.ndim == 3:
        face_arr = np.expand_dims(face_arr, axis=0)
    emb = model.predict(face_arr, verbose=0)[0]
    return emb.astype(np.float32)
