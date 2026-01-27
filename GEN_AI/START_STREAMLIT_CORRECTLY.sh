#!/bin/bash
# Script to start Streamlit correctly with localhost

echo "🛑 Stopping any existing Streamlit processes..."
pkill -f streamlit 2>/dev/null
sleep 2

echo "🚀 Starting Streamlit on localhost:8503..."
cd "$(dirname "$0")"

python3 -m streamlit run streamlit_app.py \
    --server.port 8503 \
    --server.address localhost \
    --server.headless true \
    --browser.serverAddress localhost \
    --browser.serverPort 8503

echo ""
echo "✅ Streamlit started!"
echo "🌐 Open in browser: http://localhost:8503"
echo "   (NOT http://0.0.0.0:8503)"
