import logging
import logging.config
import logging.handlers
import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from backend.config import settings
from backend.routes.video_routes import router as video_router
from backend.routes.emotion_routes import router as emotion_router

# ---------------------------------------------------------------------------
# Logging configuration
# ---------------------------------------------------------------------------

_LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()


def _setup_logging() -> None:
    """Configure logging with a console handler always, file handler if writable."""
    log_dir = Path(settings.STORAGE_DIR)
    log_file = log_dir / "app.log"

    handlers_cfg: dict = {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "stream": "ext://sys.stdout",
        }
    }
    handler_names = ["console"]

    # Only add file handler if the directory is writable
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file.touch(exist_ok=True)
        handlers_cfg["file"] = {
            "class": "logging.handlers.RotatingFileHandler",
            "formatter": "standard",
            "filename": str(log_file),
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "encoding": "utf-8",
        }
        handler_names.append("file")
    except (PermissionError, OSError):
        pass  # File logging silently skipped — console only

    logging.config.dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s [%(levelname)s] %(name)s — %(message)s",
                    "datefmt": "%Y-%m-%dT%H:%M:%S",
                }
            },
            "handlers": handlers_cfg,
            "root": {"level": _LOG_LEVEL, "handlers": handler_names},
        }
    )


_setup_logging()
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Pet Roast AI",
    description=(
        "AI-powered pet roasting service — video generation, emotion recognition, "
        "multi-language translation."
    ),
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---- CORS ----
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---- Global exception handler ----
@app.exception_handler(Exception)
async def _unhandled_exception(request: Request, exc: Exception) -> JSONResponse:
    logger.exception(f"Unhandled error on {request.method} {request.url.path}: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "status": 500,
            "title": "Internal Server Error",
            "detail": "An unexpected error occurred. Please try again later.",
        },
        media_type="application/problem+json",
    )


# ---- Routers ----
app.include_router(video_router)
app.include_router(emotion_router)


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------


@app.get("/health", tags=["System"])
async def health_check():
    """Global liveness probe — suitable for Docker HEALTHCHECK and load balancers."""
    return {
        "status": "ok",
        "service": "Pet Roast AI Backend",
        "version": app.version,
    }


# ---------------------------------------------------------------------------
# Startup / shutdown events
# ---------------------------------------------------------------------------


@app.on_event("startup")
async def _startup() -> None:
    logger.info("=== Pet Roast AI Backend starting up ===")
    # Eagerly warm-up the emotion model so first request isn't slow
    try:
        from backend.services.pet_emotion_service import PetEmotionService
        PetEmotionService.get_instance()
        logger.info("PetEmotionService warm-up complete.")
    except Exception as exc:
        logger.warning(f"PetEmotionService warm-up skipped: {exc}")


@app.on_event("shutdown")
async def _shutdown() -> None:
    logger.info("=== Pet Roast AI Backend shutting down ===")


# ---------------------------------------------------------------------------
# Dev entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("RELOAD", "false").lower() == "true",
        log_level=_LOG_LEVEL.lower(),
    )
