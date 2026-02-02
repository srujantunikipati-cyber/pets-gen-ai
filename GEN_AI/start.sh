#!/bin/bash
# Railway startup script - handles PORT variable properly

# Railway provides PORT env var, default to 8080 if not set
export PORT=${PORT:-8080}

echo "Starting server on port $PORT"

# Start uvicorn with the port
exec uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1
