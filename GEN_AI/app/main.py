"""FastAPI application entry point for the pet roasting backend."""

import logging
import os
import traceback
from contextlib import asynccontextmanager

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Remove invalid CORS_ORIGINS from environment before importing settings
if "CORS_ORIGINS" in os.environ:
    cors_val = os.environ["CORS_ORIGINS"]
    if cors_val in ["[*]", "[*", "*]", "*"]:
        os.environ.pop("CORS_ORIGINS", None)

from app.api.routes import router as api_router
from app.clients.ai4bharat import AI4BharatClient
from app.clients.fal import FalClient
from app.core.config import Settings, get_settings, clear_settings_cache
from app.services.job_store import JobStore
from app.services.video_storage import VideoStorageService
from app.services.audio_extraction import get_audio_extraction_service
from app.services.speech_to_text import get_speech_to_text_service

_logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown resources."""
    
    # Clear settings cache on startup to ensure fresh config
    clear_settings_cache()
    settings: Settings = get_settings()
    timeout = httpx.Timeout(settings.request_timeout_seconds)

    # Use in-memory job store only (no Redis on Railway)
    job_store = JobStore()
    _logger.info("Using in-memory job storage")
    
    # Initialize video storage service
    video_storage = VideoStorageService(storage_path=settings.video_storage_path)

    async with httpx.AsyncClient(timeout=timeout) as async_client:
        ai4bharat_client = AI4BharatClient(
            http_client=async_client,
            base_url=settings.ai4bharat_base_url,
            translate_path=settings.ai4bharat_translate_path,
            api_key=settings.ai4bharat_api_key,
            max_retries=settings.max_retries,
            retry_backoff_factor=settings.retry_backoff_factor,
        )
        fal_client = None
        if settings.fal_api_key:
            fal_client = FalClient(
                http_client=async_client,
                api_key=settings.fal_api_key,
                base_url=str(settings.fal_base_url),
                model_id=settings.fal_model_id,
                max_retries=settings.max_retries,
                retry_backoff_factor=settings.retry_backoff_factor,
            )
            _logger.info("✅ fal.ai client initialized")
        else:
            _logger.warning("⚠️ FAL_API_KEY not set; /api/generate-video will return 503")

        app.state.settings = settings
        app.state.job_store = job_store
        app.state.ai4bharat_client = ai4bharat_client
        app.state.fal_client = fal_client
        app.state.video_storage = video_storage
        
        # Initialize audio extraction and STT services (optional)
        try:
            audio_service = get_audio_extraction_service()
            app.state.audio_extraction_service = audio_service
            if audio_service:
                _logger.info("✅ Audio extraction service initialized")
        except Exception as e:
            _logger.warning(f"⚠️  Audio extraction service not available: {e}")
            app.state.audio_extraction_service = None
        
        try:
            stt_service = get_speech_to_text_service(model_size="base")
            app.state.stt_service = stt_service
            if stt_service:
                _logger.info("✅ Speech-to-text service initialized")
        except Exception as e:
            _logger.warning(f"⚠️  Speech-to-text service not available: {e}")
            app.state.stt_service = None

        _logger.info("Application startup complete")
        yield

        # Cleanup
        _logger.info("Application shutdown complete")


app = FastAPI(
    title="Pet Roast AI Backend",
    version="0.1.0",
    description="AI-powered pet roasting backend orchestrating multilingual NLP, video generation, and AR filters.",
    lifespan=lifespan,
)

# Configure CORS for Railway backend
settings_for_cors = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings_for_cors.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router)

# Add simple redirect routes without /api prefix (just redirect to /api/* versions)
from fastapi.responses import RedirectResponse

@app.post("/generate-video")
async def generate_video_redirect(request: Request):
    """Redirect to /api/generate-video"""
    body = await request.body()
    return RedirectResponse(url="/api/generate-video", status_code=307)

@app.get("/video-status/{job_id}")
async def video_status_redirect(job_id: str):
    """Redirect to /api/video-status/{job_id}"""
    return RedirectResponse(url=f"/api/video-status/{job_id}")

@app.get("/video-result/{job_id}")
async def video_result_redirect(job_id: str):
    """Redirect to /api/video-result/{job_id}"""
    return RedirectResponse(url=f"/api/video-result/{job_id}")

@app.get("/download-video/{job_id}")
async def download_video_redirect(job_id: str):
    """Redirect to /api/download-video/{job_id}"""
    return RedirectResponse(url=f"/api/download-video/{job_id}")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch unhandled exceptions and return 500 with detail and log traceback."""
    _logger.exception("Unhandled exception: %s", exc)
    tb = traceback.format_exc()
    _logger.debug("Traceback: %s", tb)
    return JSONResponse(
        status_code=500,
        content={
            "detail": str(exc),
            "type": type(exc).__name__,
        },
    )


@app.get("/healthz")
async def healthcheck() -> dict:
    """Simple readiness probe for container orchestrators."""

    return {"status": "ok"}

