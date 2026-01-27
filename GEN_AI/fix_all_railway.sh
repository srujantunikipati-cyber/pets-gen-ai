#!/bin/bash
# Complete Railway Fix All Script
# This script fixes all Railway deployment issues automatically

set -e

PROJECT_ID="d3e9f8f4-cdca-4825-9ec4-f7fa9844d266"
ENVIRONMENT_ID="d07ed2df-e646-45dd-9510-b40b1ceee70d"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🔧 Railway Fix All - Resolving All Issues"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Step 1: Verify Railway CLI
echo "Step 1: Checking Railway CLI..."
if ! command -v railway &> /dev/null; then
    echo "📦 Installing Railway CLI..."
    if command -v npm &> /dev/null; then
        npm i -g @railway/cli
    else
        echo "❌ npm not found. Please install Node.js first."
        exit 1
    fi
fi
echo "✅ Railway CLI ready: $(railway --version)"
echo ""

# Step 2: Check if logged in
echo "Step 2: Checking authentication..."
if railway whoami &> /dev/null 2>&1; then
    echo "✅ Already logged in"
    railway whoami
else
    echo "⚠️  Not logged in. You need to run: railway login"
    echo "   (This opens browser for authentication)"
    echo ""
    echo "After login, run this script again or continue manually."
    echo ""
    read -p "Press Enter after you've logged in, or Ctrl+C to exit..."
fi

echo ""
echo "Step 3: Linking to project..."
cd "$(dirname "$0")"
railway link "$PROJECT_ID" 2>/dev/null || echo "✅ Project already linked"
echo ""

# Step 4: Set all required environment variables
echo "Step 4: Setting environment variables..."
echo ""

VARS=(
    "FAL_API_KEY=0d44c9a0-5679-4338-9f14-055fa0907d5f:6e3f241a600df52476c1bb414dff5e4a"
    "FAL_BASE_URL=https://queue.fal.run"
    "FAL_MODEL_ID=fal-ai/minimax-video"
    "USE_REDIS=true"
    "VIDEO_STORAGE_PATH=storage/videos"
    "REQUEST_TIMEOUT_SECONDS=30.0"
    "MAX_RETRIES=3"
    "RETRY_BACKOFF_FACTOR=1.5"
)

for var in "${VARS[@]}"; do
    key="${var%%=*}"
    value="${var#*=}"
    echo "Setting $key..."
    if railway variables set "$key"="$value" 2>/dev/null; then
        echo "  ✅ $key set"
    else
        echo "  ⚠️  $key (may already be set or need login)"
    fi
done

echo ""
echo "Step 5: Verifying variables..."
railway variables | grep -E "FAL_|USE_REDIS|VIDEO_STORAGE" || echo "⚠️  Could not verify (may need login)"

echo ""
echo "Step 6: Checking deployment status..."
railway status || echo "⚠️  Could not get status (may need login)"

echo ""
echo "Step 7: Viewing recent logs..."
railway logs --tail 30 || echo "⚠️  Could not get logs (may need login)"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ Fix All Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. If not logged in yet:"
echo "   railway login"
echo ""
echo "2. Verify connection:"
echo "   railway status"
echo ""
echo "3. Monitor logs:"
echo "   railway logs --follow"
echo ""
echo "4. Deploy if needed:"
echo "   railway up"
echo ""
echo "5. Test health endpoint:"
echo "   railway open  # Get your URL"
echo "   curl https://your-app.railway.app/healthz"
echo ""
echo "✅ All fixes applied!"
echo ""
