"""
Landmark visualisation utilities.

Provides:
  - draw_landmarks()     — draw 46-pt schema on a BGR image
  - draw_connections()   — draw anatomical connections between landmark groups
  - landmarks_to_svg()   — generate an SVG string for web overlays
"""

from __future__ import annotations

from typing import List, Optional, Tuple

import cv2
import numpy as np

from .detector import LandmarkResult


# ---------------------------------------------------------------------------
# Colour constants (BGR)
# ---------------------------------------------------------------------------

_COLOUR_EYES   = (255, 100,   0)   # blue-orange
_COLOUR_NOSE   = ( 50, 200,  50)   # green
_COLOUR_MOUTH  = (  0,  60, 220)   # red
_COLOUR_EARS   = (  0, 220, 220)   # yellow
_COLOUR_TEXT   = (255, 255, 255)   # white
_COLOUR_BBOX   = (200, 200, 200)   # light grey


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def draw_landmarks(
    image_bgr: np.ndarray,
    landmarks: LandmarkResult,
    radius: int = 3,
    thickness: int = -1,
    draw_bbox: bool = True,
    draw_labels: bool = False,
    alpha: float = 0.85,
) -> np.ndarray:
    """
    Draw 46-point landmarks on a copy of *image_bgr*.

    Args:
        image_bgr:    Source BGR image (will not be mutated).
        landmarks:    :class:`LandmarkResult` to render.
        radius:       Dot radius in pixels.
        thickness:    -1 = filled circle, otherwise stroke width.
        draw_bbox:    If True, draw the face bounding rectangle.
        draw_labels:  If True, annotate group labels (eyes, nose, mouth).
        alpha:        Blend weight for overlay compositing (0.0–1.0).

    Returns:
        A new BGR image with landmarks drawn.
    """
    canvas = image_bgr.copy()
    overlay = canvas.copy()

    h, w = canvas.shape[:2]

    def _px(pt: List[float]) -> Tuple[int, int]:
        return int(pt[0] * w), int(pt[1] * h)

    # ---- Bounding box ----
    if draw_bbox and landmarks.face_bbox:
        x, y, bw, bh = landmarks.face_bbox
        cv2.rectangle(overlay, (x, y), (x + bw, y + bh), _COLOUR_BBOX, 1)

    # ---- Anatomical regions ----
    _draw_group(overlay, landmarks.eyes[:12],   _COLOUR_EYES,  _px, radius, thickness)
    _draw_group(overlay, landmarks.eyes[12:],   _COLOUR_EYES,  _px, radius, thickness)
    _draw_group(overlay, landmarks.nose,        _COLOUR_NOSE,  _px, radius, thickness)
    _draw_group(overlay, landmarks.mouth,       _COLOUR_MOUTH, _px, radius, thickness)
    _draw_group(overlay, landmarks.ears,        _COLOUR_EARS,  _px, radius, thickness)

    # ---- Anatomical connections ----
    _draw_eye_outline(overlay, landmarks.eyes[:12],  _COLOUR_EYES,  _px)
    _draw_eye_outline(overlay, landmarks.eyes[12:],  _COLOUR_EYES,  _px)
    _draw_mouth_outline(overlay, landmarks.mouth,    _COLOUR_MOUTH, _px)

    # ---- Group labels ----
    if draw_labels:
        _label_group(overlay, landmarks.eyes[:12],  "L-eye", _COLOUR_EYES, _px)
        _label_group(overlay, landmarks.eyes[12:],  "R-eye", _COLOUR_EYES, _px)
        _label_group(overlay, landmarks.nose,        "nose",  _COLOUR_NOSE, _px)
        _label_group(overlay, landmarks.mouth,       "mouth", _COLOUR_MOUTH, _px)

    # ---- Confidence badge ----
    badge = f"{landmarks.strategy}  conf:{landmarks.confidence:.2f}"
    cv2.putText(
        overlay, badge, (8, 22),
        cv2.FONT_HERSHEY_SIMPLEX, 0.55, _COLOUR_TEXT, 1, cv2.LINE_AA
    )

    # Composite
    cv2.addWeighted(overlay, alpha, canvas, 1 - alpha, 0, canvas)
    return canvas


def draw_connections(
    image_bgr: np.ndarray,
    landmarks: LandmarkResult,
    colour: Tuple[int, int, int] = (180, 180, 180),
    thickness: int = 1,
) -> np.ndarray:
    """
    Draw straight-line connections between consecutive landmarks in each group.

    Returns a new BGR image.
    """
    canvas = image_bgr.copy()
    h, w = canvas.shape[:2]

    def _px(pt: List[float]) -> Tuple[int, int]:
        return int(pt[0] * w), int(pt[1] * h)

    for group in (landmarks.eyes[:12], landmarks.eyes[12:], landmarks.mouth, landmarks.nose):
        pts = [_px(p) for p in group]
        for i in range(len(pts) - 1):
            cv2.line(canvas, pts[i], pts[i + 1], colour, thickness, cv2.LINE_AA)

    return canvas


def landmarks_to_svg(
    landmarks: LandmarkResult,
    width: int = 400,
    height: int = 400,
) -> str:
    """
    Generate an SVG string representing the landmarks at the given canvas size.

    Useful for browser-based overlays via a ``<img>`` + ``<svg>`` stack.
    """
    circles: List[str] = []

    def _colour_to_hex(bgr: Tuple[int, int, int]) -> str:
        return "#{:02x}{:02x}{:02x}".format(bgr[2], bgr[1], bgr[0])

    def _add(pts: List[List[float]], fill: Tuple[int, int, int], r: int = 4) -> None:
        hex_col = _colour_to_hex(fill)
        for pt in pts:
            cx = pt[0] * width
            cy = pt[1] * height
            circles.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r}" fill="{hex_col}"/>')

    _add(landmarks.eyes[:12], _COLOUR_EYES)
    _add(landmarks.eyes[12:], _COLOUR_EYES)
    _add(landmarks.nose, _COLOUR_NOSE)
    _add(landmarks.mouth, _COLOUR_MOUTH)
    _add(landmarks.ears, _COLOUR_EARS, r=3)

    circles_str = "\n  ".join(circles)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" viewBox="0 0 {width} {height}">\n'
        f'  {circles_str}\n'
        f"</svg>"
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _draw_group(
    img: np.ndarray,
    pts: List[List[float]],
    colour: Tuple[int, int, int],
    to_px,
    radius: int,
    thickness: int,
) -> None:
    for pt in pts:
        cv2.circle(img, to_px(pt), radius, colour, thickness, cv2.LINE_AA)


def _draw_eye_outline(
    img: np.ndarray,
    eye_pts: List[List[float]],
    colour: Tuple[int, int, int],
    to_px,
) -> None:
    """Connect upper-lid and lower-lid in a rough ellipse."""
    if len(eye_pts) < 9:
        return
    # upper lid: points 1-4 (indices 1,2,3,4)
    upper = [to_px(eye_pts[i]) for i in (1, 2, 4, 3, 1)]
    for i in range(len(upper) - 1):
        cv2.line(img, upper[i], upper[i + 1], colour, 1, cv2.LINE_AA)
    # lower lid: points 5-8 (indices 5,6,8,7,5)
    lower = [to_px(eye_pts[i]) for i in (5, 6, 8, 7, 5)]
    for i in range(len(lower) - 1):
        cv2.line(img, lower[i], lower[i + 1], colour, 1, cv2.LINE_AA)


def _draw_mouth_outline(
    img: np.ndarray,
    mouth_pts: List[List[float]],
    colour: Tuple[int, int, int],
    to_px,
) -> None:
    if len(mouth_pts) < 8:
        return
    # outer loop: corners → upper-lip top → corners → lower-lip bottom
    outer = [0, 4, 8, 2, 9, 5, 1, 7, 3, 6, 0]
    for i in range(len(outer) - 1):
        if outer[i] < len(mouth_pts) and outer[i + 1] < len(mouth_pts):
            cv2.line(img, to_px(mouth_pts[outer[i]]), to_px(mouth_pts[outer[i + 1]]),
                     colour, 1, cv2.LINE_AA)


def _label_group(
    img: np.ndarray,
    pts: List[List[float]],
    label: str,
    colour: Tuple[int, int, int],
    to_px,
) -> None:
    if not pts:
        return
    # Place label above the centroid of the group
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    cx_px, cy_px = to_px([sum(xs) / len(xs), sum(ys) / len(ys)])
    cv2.putText(
        img, label, (cx_px - 10, cy_px - 10),
        cv2.FONT_HERSHEY_SIMPLEX, 0.40, colour, 1, cv2.LINE_AA
    )
