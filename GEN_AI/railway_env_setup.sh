#!/bin/bash
# Railway Environment Variables Setup Script

echo "Setting Railway environment variables..."

railway variables set FAL_API_KEY="0d44c9a0-5679-4338-9f14-055fa0907d5f:6e3f241a600df52476c1bb414dff5e4a"
railway variables set FAL_BASE_URL="https://queue.fal.run"
railway variables set FAL_MODEL_ID="fal-ai/minimax-video"
railway variables set USE_REDIS="false"
railway variables set REQUEST_TIMEOUT_SECONDS="30.0"
railway variables set MAX_RETRIES="3"
railway variables set RETRY_BACKOFF_FACTOR="2.0"

echo "✅ All environment variables set successfully!"
echo ""
echo "Current Railway variables:"
railway variables
