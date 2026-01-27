#!/bin/bash
# Script to run Streamlit app for Pet Roast AI

echo "🚀 Starting Pet Roast AI Streamlit App..."
echo ""

# Check if port 8503 is available
if lsof -Pi :8503 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  Port 8503 is already in use. Killing existing process..."
    pkill -f "streamlit.*8503"
    sleep 2
fi

# Start Streamlit
cd "$(dirname "$0")"
python3 -m streamlit run streamlit_app.py --server.port 8503 --server.address localhost --server.headless true

echo ""
echo "✅ Streamlit app should be running at: http://localhost:8503"
