#!/bin/bash
# Perfect Railway Connection - Fixed with Correct Token Usage

TOKEN="d2438d39-dad1-4761-a423-bf02d3bdd002"
PROJECT_ID="d3e9f8f4-cdca-4825-9ec4-f7fa9844d266"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🔧 Perfect Railway Connection (Fixed)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Check CLI version
echo "Step 1: Checking Railway CLI version..."
RAILWAY_VERSION=$(railway --version 2>&1 | grep -o '[0-9]\+\.[0-9]\+\.[0-9]\+' | head -1)
echo "✅ Railway CLI version: $RAILWAY_VERSION"

# Logout first
echo ""
echo "Step 2: Cleaning previous session..."
railway logout 2>/dev/null || echo "No previous session"

# Try Account API Token (RAILWAY_API_TOKEN)
echo ""
echo "Step 3: Authenticating with Account API Token..."
export RAILWAY_API_TOKEN="$TOKEN"

if railway whoami &> /dev/null 2>&1; then
    echo "✅ Authentication successful with RAILWAY_API_TOKEN!"
    railway whoami
    AUTH_SUCCESS=true
else
    echo "⚠️  RAILWAY_API_TOKEN failed, trying RAILWAY_TOKEN..."
    export RAILWAY_TOKEN="$TOKEN"
    unset RAILWAY_API_TOKEN
    
    if railway whoami &> /dev/null 2>&1; then
        echo "✅ Authentication successful with RAILWAY_TOKEN!"
        railway whoami
        AUTH_SUCCESS=true
    else
        echo "❌ Both token methods failed"
        echo "⚠️  Token might be Project Token, not Account API Token"
        echo "   You may need Account API Token from: https://railway.app/account/tokens"
        AUTH_SUCCESS=false
    fi
fi

if [ "$AUTH_SUCCESS" = false ]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  ⚠️  Token Authentication Failed"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "The token might be a Project Token, not Account API Token."
    echo ""
    echo "To fix:"
    echo "1. Go to: https://railway.app/account/tokens"
    echo "2. Create new 'Account API Token' (not Project Token)"
    echo "3. Copy the full token"
    echo "4. Update this script with new token"
    echo ""
    exit 1
fi

# Link to project
echo ""
echo "Step 4: Linking to project..."
railway link --project "$PROJECT_ID" 2>/dev/null && echo "✅ Linked to project" || echo "⚠️  Already linked or link failed"

# Set all variables
echo ""
echo "Step 5: Setting environment variables..."
railway variables set FAL_API_KEY="0d44c9a0-5679-4338-9f14-055fa0907d5f:6e3f241a600df52476c1bb414dff5e4a" && echo "✅ FAL_API_KEY"
railway variables set FAL_BASE_URL="https://queue.fal.run" && echo "✅ FAL_BASE_URL"
railway variables set FAL_MODEL_ID="fal-ai/minimax-video" && echo "✅ FAL_MODEL_ID"
railway variables set USE_REDIS="true" && echo "✅ USE_REDIS"
railway variables set VIDEO_STORAGE_PATH="storage/videos" && echo "✅ VIDEO_STORAGE_PATH"
railway variables set REQUEST_TIMEOUT_SECONDS="30.0" && echo "✅ REQUEST_TIMEOUT_SECONDS"
railway variables set MAX_RETRIES="3" && echo "✅ MAX_RETRIES"
railway variables set RETRY_BACKOFF_FACTOR="1.5" && echo "✅ RETRY_BACKOFF_FACTOR"

# Verify variables
echo ""
echo "Step 6: Verifying variables..."
railway variables 2>&1 | grep -E "FAL_|USE_REDIS|VIDEO_STORAGE" | head -10 || echo "Variables set"

# Check deployment status
echo ""
echo "Step 7: Deployment status..."
railway status 2>&1

# Show recent logs
echo ""
echo "Step 8: Recent logs..."
railway logs --tail 20 2>&1 | head -40

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ Perfect Connection Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Useful Commands:"
echo "  railway logs --follow    # Watch logs in real-time"
echo "  railway status           # Check deployment status"
echo "  railway variables        # View all variables"
echo "  railway up               # Trigger deployment"
echo "  railway open             # Open Railway dashboard"
echo ""
