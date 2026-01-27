# Multi-stage build to reduce final image size
FROM python:3.10-slim as builder

# Install build dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Final stage - minimal runtime image
FROM python:3.10-slim

# Install only runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgl1 \
    libglib2.0-0 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Set working directory
WORKDIR /app

# Copy only essential application code
COPY app/ ./app/

# Copy IndicTrans2 (exclude large files via .dockerignore)
COPY IndicTrans2/ ./IndicTrans2/

# Create necessary directories
RUN mkdir -p logs storage/videos && \
    chmod -R 755 storage logs

# Don't download YOLO model at build time - download at runtime
# This saves ~200MB in the image
# The model will be downloaded automatically on first use

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD ["sh", "-c", "curl -f http://localhost:${PORT:-8000}/healthz || exit 1"]

# Run the application
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
