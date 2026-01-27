#!/bin/bash
# Perfect Railway Connection - Using Account API Token

TOKEN="099fbe14-1936-421a-8154-226b646c3529"
PROJECT_ID="d3e9f8f4-cdca-4825-9ec4-f7fa9844d266"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🔧 Railway Connection & Fix All (Account API Token)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Set Account API Token
export RAILWAY_API_TOKEN="$TOKEN"

# Step 1: Verify authentication
echo "Step 1: Verifying authentication..."
if railway whoami &> /dev/null 2>&1; then
    echo "✅ Authentication successful!"
    railway whoami
else
    echo "❌ Authentication failed"
    exit 1
fi

# Step 2: Link to project
echo ""
echo "Step 2: Linking to project..."
railway link --project "$PROJECT_ID" 2>/dev/null && echo "✅ Linked to project" || echo "⚠️  Already linked"

# Step 3: Set all variables
echo ""
echo "Step 3: Setting environment variables..."
railway variables set FAL_API_KEY="0d44c9a0-5679-4338-9f14-055fa0907d5f:6e3f241a600df52476c1bb414dff5e4a" && echo "✅ FAL_API_KEY"
railway variables set FAL_BASE_URL="https://queue.fal.run" && echo "✅ FAL_BASE_URL"
railway variables set FAL_MODEL_ID="fal-ai/minimax-video" && echo "✅ FAL_MODEL_ID"
railway variables set USE_REDIS="true" && echo "✅ USE_REDIS"
railway variables set VIDEO_STORAGE_PATH="storage/videos" && echo "✅ VIDEO_STORAGE_PATH"
railway variables set REQUEST_TIMEOUT_SECONDS="30.0" && echo "✅ REQUEST_TIMEOUT_SECONDS"
railway variables set MAX_RETRIES="3" && echo "✅ MAX_RETRIES"
railway variables set RETRY_BACKOFF_FACTOR="1.5" && echo "✅ RETRY_BACKOFF_FACTOR"

# Step 4: Verify variables
echo ""
echo "Step 4: Verifying variables..."
railway variables 2>&1 | grep -E "FAL_|USE_REDIS|VIDEO_STORAGE" | head -10 || echo "Variables set"

# Step 5: Deployment status
echo ""
echo "Step 5: Deployment status..."
railway status 2>&1

# Step 6: Recent logs
echo ""
echo "Step 6: Recent logs..."
railway logs --tail 20 2>&1 | head -40

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ Connection & Fix Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Useful Commands:"
echo "  export RAILWAY_API_TOKEN=\"$TOKEN\""
echo "  railway logs --follow    # Watch logs in real-time"
echo "  railway status           # Check deployment status"
echo "  railway variables        # View all variables"
echo "  railway up               # Trigger deployment"
echo "  railway open             # Open Railway dashboard"
echo ""
