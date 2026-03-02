"""
FastAPI routes for Pet Emotion Recognition.

Endpoints
---------
GET  /emotion/health        — Liveness + model status + monitoring summary
POST /emotion/predict       — Single image upload → emotion prediction
POST /emotion/predict-url   — Predict from a public image URL
POST /emotion/webcam-frame  — Single webcam frame (base64 JPEG) → emotion
POST /emotion/train         — Trigger async training job (admin)
POST /emotion/reload        — Hot-reload model weights (admin)

All endpoints return JSON.  Error responses follow RFC 7807 (application/problem+json).
"""

from __future__ import annotations

import asyncio
import base64
import logging
import time
from typing import Any, Dict, Optional

import httpx
import numpy as np
import cv2
from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, HttpUrl

from backend.services.pet_emotion_service import PetEmotionService, EmotionResult
from pet_emotion.utils.preprocessing import PreprocessingError
from pet_emotion.utils.monitoring import get_monitor
from pet_emotion.config import emotion_config

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/emotion", tags=["Pet Emotion Recognition"])

# Shared service instance (lazy-loaded on first call)
_service: Optional[PetEmotionService] = None


def _get_service() -> PetEmotionService:
    global _service
    if _service is None:
        _service = PetEmotionService.get_instance()
    return _service


# ---------------------------------------------------------------------------
# Response / request models
# ---------------------------------------------------------------------------


class EmotionResponse(BaseModel):
    label: str
    confidence: float
    all_scores: Dict[str, float]
    uncertain: bool
    latency_ms: float
    face_detected: bool


class PredictUrlRequest(BaseModel):
    image_url: HttpUrl = Field(..., description="Publicly accessible image URL")
    ground_truth: Optional[str] = Field(
        default=None, description="Optional true label for monitoring"
    )


class WebcamFrameRequest(BaseModel):
    frame_b64: str = Field(
        ...,
        description="Base64-encoded JPEG frame from webcam (e.g., data:image/jpeg;base64,...)",
    )


class TrainRequest(BaseModel):
    data_dir: str = Field(..., description="Absolute path to labelled dataset root")
    epochs: Optional[int] = Field(default=30, ge=1, le=200)
    batch_size: Optional[int] = Field(default=32, ge=4, le=256)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _emotion_response(result: EmotionResult) -> EmotionResponse:
    return EmotionResponse(**result.to_dict())


def _problem(status_code: int, title: str, detail: str) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={"status": status_code, "title": title, "detail": detail},
        media_type="application/problem+json",
    )


# ---------------------------------------------------------------------------
# GET /emotion/health
# ---------------------------------------------------------------------------


@router.get("/health", summary="Emotion service liveness & model status")
async def emotion_health() -> Dict[str, Any]:
    """Returns service status, model load state, and rolling performance metrics."""
    svc = _get_service()
    monitor = get_monitor()
    return {
        "status": "ok",
        "service": "PetEmotionRecognition",
        "model": emotion_config.model_name,
        "model_loaded": svc._model_loaded,
        "weights_path": emotion_config.weights_path,
        "num_classes": emotion_config.num_classes,
        "labels": emotion_config.labels,
        "monitoring": monitor.summary(),
    }


# ---------------------------------------------------------------------------
# POST /emotion/predict  (file upload)
# ---------------------------------------------------------------------------


@router.post(
    "/predict",
    response_model=EmotionResponse,
    summary="Predict pet emotion from an uploaded image",
    status_code=status.HTTP_200_OK,
)
async def predict(
    file: UploadFile = File(..., description="Pet face image (JPEG/PNG, ≤10 MB)"),
    ground_truth: Optional[str] = Form(
        default=None, description="Optional true emotion label for monitoring"
    ),
) -> EmotionResponse:
    """Upload a pet image and get an emotion prediction."""
    if file.size and file.size > emotion_config.max_image_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File too large. Maximum allowed: {emotion_config.max_image_size_bytes // 1_048_576} MB.",
        )

    data = await file.read()
    if not data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file uploaded.")

    try:
        svc = _get_service()
        result = await svc.predict_from_bytes(data, filename=file.filename or "", ground_truth=ground_truth)
        return _emotion_response(result)
    except PreprocessingError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        logger.exception("Unexpected error during /predict")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


# ---------------------------------------------------------------------------
# POST /emotion/predict-url
# ---------------------------------------------------------------------------


@router.post(
    "/predict-url",
    response_model=EmotionResponse,
    summary="Predict pet emotion from a public image URL",
)
async def predict_url(req: PredictUrlRequest) -> EmotionResponse:
    """Fetch an image from a URL and predict the pet's emotion."""
    try:
        async with httpx.AsyncClient(timeout=httpx.Timeout(30.0)) as client:
            resp = await client.get(str(req.image_url))
            resp.raise_for_status()
        data = resp.content
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to fetch image: HTTP {exc.response.status_code}",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY, detail=f"Image fetch error: {exc}"
        )

    try:
        svc = _get_service()
        result = await svc.predict_from_bytes(
            data, filename=str(req.image_url), ground_truth=req.ground_truth
        )
        return _emotion_response(result)
    except PreprocessingError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        logger.exception("Unexpected error during /predict-url")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


# ---------------------------------------------------------------------------
# POST /emotion/webcam-frame   (real-time webcam)
# ---------------------------------------------------------------------------


@router.post(
    "/webcam-frame",
    response_model=EmotionResponse,
    summary="Real-time webcam frame emotion detection",
)
async def webcam_frame(req: WebcamFrameRequest) -> EmotionResponse:
    """Accept a single base64-encoded JPEG frame and return the emotion prediction.

    The client should send frames at ≤5 FPS to stay within CPU budget.
    """
    # Strip data URI prefix if present (data:image/jpeg;base64,<data>)
    b64_data = req.frame_b64
    if "," in b64_data:
        b64_data = b64_data.split(",", 1)[1]

    try:
        raw = base64.b64decode(b64_data)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid base64 encoding.",
        )

    # Decode to BGR NumPy array
    arr = np.frombuffer(raw, dtype=np.uint8)
    frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Could not decode frame — ensure it is a valid JPEG.",
        )

    try:
        svc = _get_service()
        result = await svc.predict_from_frame(frame)
        return _emotion_response(result)
    except Exception as exc:
        logger.exception("Unexpected error during /webcam-frame")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc))


# ---------------------------------------------------------------------------
# POST /emotion/reload   (admin — hot-reload weights)
# ---------------------------------------------------------------------------


@router.post("/reload", summary="Hot-reload model weights (admin)", include_in_schema=False)
async def reload_model() -> Dict[str, Any]:
    """Reload MobileNetV2 weights without restarting the server."""
    svc = _get_service()
    success = svc.reload_model()
    if not success:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "reloaded": False,
                "message": f"Weights not found at '{emotion_config.weights_path}'.",
            },
        )
    return {"reloaded": True, "message": "Model reloaded successfully."}


# ---------------------------------------------------------------------------
# POST /emotion/train   (admin — trigger training)
# ---------------------------------------------------------------------------


@router.post("/train", summary="Trigger model training (admin)", include_in_schema=False)
async def trigger_training(req: TrainRequest) -> Dict[str, Any]:
    """Launch a background training job.  Returns immediately with a job token."""
    import uuid
    import threading

    job_id = str(uuid.uuid4())

    def _run_training():
        try:
            from pet_emotion.config import EmotionConfig
            from pet_emotion.model.train import train

            cfg = EmotionConfig(
                data_dir=req.data_dir,
                epochs=req.epochs or 30,
                batch_size=req.batch_size or 32,
            )
            weights_out = train(cfg)
            logger.info(f"[train job {job_id}] Training complete → {weights_out}")
            # Auto-reload after training
            _get_service().reload_model()
        except Exception as exc:
            logger.error(f"[train job {job_id}] Training failed: {exc}")

    t = threading.Thread(target=_run_training, daemon=True, name=f"train-{job_id[:8]}")
    t.start()

    return {
        "job_id": job_id,
        "status": "started",
        "message": f"Training started in background. Monitor logs for progress.",
    }


# ---------------------------------------------------------------------------
# Identity recognition + landmark endpoints
# ---------------------------------------------------------------------------

# Lazy-loaded PetFaceService instance
_face_service: Optional[Any] = None


def _get_face_service():
    global _face_service
    if _face_service is None:
        from backend.services.pet_face_service import PetFaceService
        _face_service = PetFaceService.get_instance()
    return _face_service


class RegisterPetResponse(BaseModel):
    registered: bool
    pet_name: str
    num_samples: int
    message: str = ""


class RecognizeResponse(BaseModel):
    matched: bool
    name: Optional[str]
    confidence: float
    distance: float


class LandmarkResponse(BaseModel):
    eyes: list
    mouth: list
    nose: list
    ears: list
    all: list
    confidence: float
    strategy: str
    face_bbox: Optional[list]


class AnalyzeResponse(BaseModel):
    emotion: Dict[str, Any]
    identity: Dict[str, Any]
    landmarks: Dict[str, Any]


@router.post(
    "/register_pet",
    response_model=RegisterPetResponse,
    summary="Register a pet face for identity recognition",
    description=(
        "Upload a clear face photo of a pet. "
        "The system extracts an embedding and stores it under *pet_name*. "
        "Call multiple times to add more samples (max 10 per pet)."
    ),
)
async def register_pet(
    pet_name: str = Form(..., description="Unique name for the pet"),
    file: UploadFile = File(..., description="Pet face image (JPEG/PNG)"),
) -> RegisterPetResponse:
    t0 = time.perf_counter()
    image_bytes = await file.read()
    if len(image_bytes) > emotion_config.max_image_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image exceeds {emotion_config.max_image_size_bytes // (1024*1024)} MB limit",
        )

    pet_name = pet_name.strip()
    if not pet_name:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="pet_name must not be empty")

    svc = _get_face_service()
    try:
        out = await svc.register_pet(pet_name, image_bytes)
    except Exception as exc:
        logger.exception("register_pet error")
        raise HTTPException(status_code=500, detail=str(exc))

    latency = (time.perf_counter() - t0) * 1000
    logger.info("register_pet '%s' → registered=%s samples=%s  (%.1f ms)",
                pet_name, out.get("registered"), out.get("num_samples"), latency)

    return RegisterPetResponse(
        registered=out.get("registered", False),
        pet_name=pet_name,
        num_samples=out.get("num_samples", 0),
        message=(
            f"Added sample for '{pet_name}'. "
            f"Total samples: {out.get('num_samples', 0)}."
        ) if out.get("registered") else out.get("error", "Registration failed"),
    )


@router.post(
    "/recognize",
    response_model=RecognizeResponse,
    summary="Identify a pet by face",
    description=(
        "Upload a pet face image. Returns the closest registered pet and "
        "a similarity confidence score."
    ),
)
async def recognize_pet(
    file: UploadFile = File(..., description="Pet face image (JPEG/PNG)"),
) -> RecognizeResponse:
    t0 = time.perf_counter()
    image_bytes = await file.read()
    if len(image_bytes) > emotion_config.max_image_size_bytes:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail="Image too large")

    svc = _get_face_service()
    try:
        out = await svc.recognize(image_bytes)
    except Exception as exc:
        logger.exception("recognize error")
        raise HTTPException(status_code=500, detail=str(exc))

    latency = (time.perf_counter() - t0) * 1000
    logger.info("recognize → matched=%s name=%s conf=%.3f  (%.1f ms)",
                out.get("matched"), out.get("name"), out.get("confidence", 0), latency)

    return RecognizeResponse(**{k: out[k] for k in ("matched", "name", "confidence", "distance")})


@router.post(
    "/landmarks",
    response_model=LandmarkResponse,
    summary="Detect 46-point facial landmarks",
    description=(
        "Returns 46 facial landmark coordinates (normalised [0,1]) split into: "
        "eyes (24 pts), mouth (10 pts), nose (5 pts), and optional ear points. "
        "Primary strategy: MediaPipe FaceMesh. Fallback: OpenCV geometric estimation."
    ),
)
async def detect_landmarks(
    file: UploadFile = File(..., description="Pet face image (JPEG/PNG)"),
) -> LandmarkResponse:
    t0 = time.perf_counter()
    image_bytes = await file.read()
    if len(image_bytes) > emotion_config.max_image_size_bytes:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail="Image too large")

    svc = _get_face_service()
    try:
        lm = await svc.detect_landmarks(image_bytes)
    except Exception as exc:
        logger.exception("detect_landmarks error")
        raise HTTPException(status_code=500, detail=str(exc))

    latency = (time.perf_counter() - t0) * 1000
    logger.info("landmarks strategy=%s conf=%.2f  (%.1f ms)",
                lm.get("strategy"), lm.get("confidence", 0), latency)

    return LandmarkResponse(
        eyes=lm.get("eyes", []),
        mouth=lm.get("mouth", []),
        nose=lm.get("nose", []),
        ears=lm.get("ears", []),
        all=lm.get("all", []),
        confidence=lm.get("confidence", 0.0),
        strategy=lm.get("strategy", "none"),
        face_bbox=lm.get("face_bbox"),
    )


@router.post(
    "/analyze",
    summary="Complete pet face analysis",
    description=(
        "Runs all three pipelines on a single image upload: "
        "(1) emotion classification, "
        "(2) identity recognition (if pets are registered), "
        "(3) 46-point landmark detection. "
        "Pass *annotated=true* to include a base64-encoded JPEG with drawn landmarks."
    ),
)
async def analyze_pet(
    file: UploadFile = File(..., description="Pet image (JPEG/PNG)"),
    annotated: bool = Form(default=False, description="Return annotated image as base64 JPEG"),
) -> Dict[str, Any]:
    t0 = time.perf_counter()
    image_bytes = await file.read()
    if len(image_bytes) > emotion_config.max_image_size_bytes:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail="Image too large")

    svc = _get_face_service()
    try:
        result = await svc.analyze(image_bytes)
    except Exception as exc:
        logger.exception("analyze error")
        raise HTTPException(status_code=500, detail=str(exc))

    response: Dict[str, Any] = result.to_dict()
    response["latency_ms"] = round((time.perf_counter() - t0) * 1000, 2)

    if annotated:
        try:
            b64 = await svc.annotated_image_b64(image_bytes)
            response["annotated_image_b64"] = b64
        except Exception:
            response["annotated_image_b64"] = None

    logger.info(
        "analyze → emotion=%s identity=%s landmarks=%s  (%.1f ms)",
        response["emotion"]["label"],
        response["identity"]["name"],
        response["landmarks"]["strategy"],
        response["latency_ms"],
    )
    return response


@router.get(
    "/pets",
    summary="List registered pet names",
    description="Returns the list of pet names that have registered face embeddings.",
)
async def list_pets() -> Dict[str, Any]:
    svc = _get_face_service()
    return {"pets": await svc.list_pets()}
