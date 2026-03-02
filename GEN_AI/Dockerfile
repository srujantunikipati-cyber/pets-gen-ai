# =============================================================================
# Pet Roast AI — Production Dockerfile
# Base: python:3.11-slim (Ubuntu 22.04 compatible)
# Targets: Hostinger VPS / any x86_64 Linux host
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1: builder — install Python deps into a venv
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS builder

# System build deps (needed for OpenCV, TF, ffmpeg)
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libglib2.0-0 \
        libsm6 \
        libxrender1 \
        libxext6 \
        libgl1-mesa-glx \
        ffmpeg \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Create isolated Python virtualenv
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip + install deps
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


# ---------------------------------------------------------------------------
# Stage 2: runtime — lean final image
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

LABEL maintainer="Chetan Patil" \
      version="2.0.0" \
      description="Pet Roast AI — Fast API + Emotion Recognition"

# Runtime system libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
        libglib2.0-0 \
        libsm6 \
        libxrender1 \
        libxext6 \
        libgl1-mesa-glx \
        ffmpeg \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Copy venv from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Non-root user for security
RUN useradd --create-home --shell /bin/bash app
WORKDIR /home/app/api

# Copy application code
COPY --chown=app:app backend/           ./backend/
COPY --chown=app:app pet_emotion/       ./pet_emotion/
COPY --chown=app:app storage/           ./storage/

# Ensure model weights & monitoring dirs exist
RUN mkdir -p \
        pet_emotion/model/weights \
        pet_emotion/monitoring \
        storage/output \
        storage/temp && \
    chown -R app:app .

USER app

# Environment defaults (override in docker-compose / Hostinger panel)
ENV PORT=8000 \
    LOG_LEVEL=INFO \
    RELOAD=false \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE ${PORT}

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

CMD ["sh", "-c", "uvicorn backend.main:app --host 0.0.0.0 --port ${PORT} --workers 1 --log-level ${LOG_LEVEL,,}"]
