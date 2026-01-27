#!/bin/bash
# Final Fix All - Using Multiple Methods

TOKEN="d2438d39-dad1-4761-a423-bf02d3bdd002"
PROJECT_ID="d3e9f8f4-cdca-4825-9ec4-f7fa9844d266"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🔧 Final Fix All - Railway Connection"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Method 1: Try Railway CLI with token
echo "Method 1: Trying Railway CLI..."
export RAILWAY_TOKEN="$TOKEN"
if railway whoami &> /dev/null 2>&1; then
    echo "✅ CLI authentication successful!"
    railway whoami
    railway link --project "$PROJECT_ID" 2>/dev/null
    railway variables set FAL_API_KEY="0d44c9a0-5679-4338-9f14-055fa0907d5f:6e3f241a600df52476c1bb414dff5e4a" && echo "✅ FAL_API_KEY"
    railway variables set FAL_BASE_URL="https://queue.fal.run" && echo "✅ FAL_BASE_URL"
    railway variables set FAL_MODEL_ID="fal-ai/minimax-video" && echo "✅ FAL_MODEL_ID"
    railway variables set USE_REDIS="true" && echo "✅ USE_REDIS"
    railway variables set VIDEO_STORAGE_PATH="storage/videos" && echo "✅ VIDEO_STORAGE_PATH"
    echo ""
    echo "✅ All variables set via CLI!"
    railway status
    exit 0
else
    echo "⚠️  CLI authentication failed"
fi

# Method 2: Use Railway API directly
echo ""
echo "Method 2: Using Railway API directly..."
API_BASE="https://api.railway.app/v1"

# Test auth
AUTH_TEST=$(curl -s -H "Authorization: Bearer $TOKEN" "$API_BASE/user" 2>&1)
if echo "$AUTH_TEST" | grep -q "email\|id"; then
    echo "✅ API authentication successful!"
    
    # Get project variables endpoint
    echo "Setting variables via API..."
    # Note: Railway API endpoints may vary, this is a template
    echo "⚠️  API method needs Railway API documentation"
    echo "✅ Use Railway Dashboard instead (most reliable)"
else
    echo "❌ API authentication also failed"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  📋 RECOMMENDED: Use Railway Dashboard"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "1. Open: https://railway.app/project/$PROJECT_ID"
echo "2. Go to 'Variables' tab"
echo "3. Add variables (see DEPLOYMENT_READY.md)"
echo "4. Save - Railway auto-deploys!"
echo ""
