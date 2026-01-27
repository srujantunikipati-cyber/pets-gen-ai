#!/bin/bash
# Cleanup Unwanted Files - Keep Only Essential

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🧹 Cleaning Up Unwanted Files"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Files to remove (temporary fix files)
FILES_TO_REMOVE=(
    "COMPLETE_FIX.md"
    "QUICK_FIX.txt"
    "FIX_BLANK_PAGE.md"
    "FIX_WEBSOCKET_ERROR.md"
    "STREAMLIT_FIX.md"
    "fix_streamlit_websocket.py"
    "redirect_to_localhost.html"
    "test_simple.py"
)

# Railway duplicate guides (keep only essential)
RAILWAY_DUPLICATES=(
    "RAILWAY_FIX_GUIDE.md"
    "RAILWAY_TROUBLESHOOTING.md"
    "RAILWAY_PROJECT_INFO.md"
    "RAILWAY_REMOTE_CONNECT.md"
    "RAILWAY_FIX_GUIDE.md"
    "RAILWAY_TOKEN_GUIDE.md"
    "GET_FULL_TOKEN.md"
    "SET_VARIABLES_RAILWAY.md"
    "FINAL_RAILWAY_CONNECTION.md"
    "QUICK_RAILWAY_CONNECT.md"
    "NEXT_STEPS.md"
    "FINAL_SOLUTION.md"
    "CLI_LIMITATION_FIX.md"
    "PERFECT_CONNECTION_FINAL.md"
    "DEPLOYMENT_READY.md"
    "RAILWAY_BUILD_FIX.md"
    "DOCKERFILE_FIX.md"
)

# Connection scripts (keep only best one)
SCRIPTS_TO_REMOVE=(
    "connect_railway.sh"
    "railway_connect.sh"
    "railway_fix.sh"
    "railway_fix_all.sh"
    "connect_with_token.sh"
    "connect_with_api.sh"
    "connect_and_fix_all.sh"
    "connect_perfect.sh"
    "connect_now.sh"
    "setup_railway_remote.sh"
    "final_connect_fix.sh"
    "perfect_connect_api.sh"
)

echo "Removing temporary fix files..."
for file in "${FILES_TO_REMOVE[@]}"; do
    if [ -f "$file" ]; then
        rm "$file"
        echo "  ✅ Removed: $file"
    fi
done

echo ""
echo "Removing duplicate Railway guides (keeping essential ones)..."
for file in "${RAILWAY_DUPLICATES[@]}"; do
    if [ -f "$file" ]; then
        rm "$file"
        echo "  ✅ Removed: $file"
    fi
done

echo ""
echo "Removing duplicate connection scripts (keeping best one)..."
for file in "${SCRIPTS_TO_REMOVE[@]}"; do
    if [ -f "$file" ]; then
        rm "$file"
        echo "  ✅ Removed: $file"
    fi
done

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ Cleanup Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "✅ Kept Essential Files:"
echo "  • DEPLOYMENT_GUIDE.md"
echo "  • PERFECT_RAILWAY_CREDENTIALS.md"
echo "  • RENDER_DEPLOYMENT.md"
echo "  • perfect_connect_fix.sh"
echo ""
