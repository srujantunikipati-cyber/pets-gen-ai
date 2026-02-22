# Highly optimized Root Dockerfile for Railway Deployment
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies (FFmpeg is critical)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY GEN_AI/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code from the GEN_AI subfolder
COPY GEN_AI/backend ./backend

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Default command for Railway Deployment
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
