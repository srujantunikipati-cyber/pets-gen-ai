#!/bin/bash
# Script to start all required services

echo "🚀 Starting all services..."

# Kill existing processes
pkill -f "uvicorn.*app.main" 2>/dev/null
pkill -f "uvicorn.*inference_server" 2>/dev/null
pkill -f "streamlit.*streamlit_app" 2>/dev/null
sleep 2

cd "$(dirname "$0")"

# Start AI4Bharat service
echo "1. Starting AI4Bharat service on port 5000..."
cd IndicTrans2
python3 -m uvicorn inference_server_simple:app --host 0.0.0.0 --port 5000 2>&1 &
AI4BHARAT_PID=$!
cd ..
sleep 5

# Start FastAPI backend
echo "2. Starting FastAPI backend on port 8000..."
export FAL_API_KEY='0d44c9a0-5679-4338-9f14-055fa0907d5f:6e3f241a600df52476c1bb414dff5e4a'
export FAL_BASE_URL='https://queue.fal.run'
export FAL_MODEL_ID='fal-ai/minimax-video'
export USE_REDIS=false
unset CORS_ORIGINS
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload 2>&1 &
FASTAPI_PID=$!
sleep 10

# Start Streamlit app
echo "3. Starting Streamlit app on port 8503..."
python3 -m streamlit run streamlit_app.py --server.port 8503 --server.address localhost 2>&1 &
STREAMLIT_PID=$!
sleep 8

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ ALL SERVICES STARTED"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "   AI4Bharat:  http://localhost:5000 (PID: $AI4BHARAT_PID)"
echo "   FastAPI:    http://localhost:8000 (PID: $FASTAPI_PID)"
echo "   Streamlit:  http://localhost:8503 (PID: $STREAMLIT_PID)"
echo ""
echo "📝 Access the app at: http://localhost:8503"
echo ""
