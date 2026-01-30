#!/bin/bash
# Startup script for Railway deployment

# Debug: Print environment variable
echo "PORT environment variable: $PORT"

# Use PORT environment variable from Railway, default to 8000
APP_PORT="${PORT:-8000}"

echo "Starting server on port $APP_PORT"

# Run uvicorn
exec uvicorn app.main:app --host 0.0.0.0 --port "$APP_PORT" --workers 1
