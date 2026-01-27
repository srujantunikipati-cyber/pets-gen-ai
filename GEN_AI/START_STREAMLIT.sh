#!/bin/bash
# Start Streamlit app for Pet Roast AI

echo "🚀 Starting Pet Roast AI Streamlit App..."
echo ""

# Kill any existing Streamlit processes on port 8503
pkill -f "streamlit.*8503" 2>/dev/null
sleep 2

# Change to project directory
cd "$(dirname "$0")"

# Start Streamlit (will use .streamlit/config.toml)
python3 -m streamlit run streamlit_app.py

echo ""
echo "✅ Streamlit app running at: http://localhost:8503"
echo "📝 Check streamlit.log for logs"
