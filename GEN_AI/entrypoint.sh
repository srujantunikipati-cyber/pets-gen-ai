#!/bin/bash
set -e

# Set default port if not provided
PORT=${PORT:-8080}

echo "🚀 Starting uvicorn on port $PORT..."

# Start uvicorn with the actual port number
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT" --workers 1
