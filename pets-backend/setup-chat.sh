#!/bin/bash

echo "🚀 Chat System Setup Script"
echo "=============================="
echo ""

# Check if Redis is installed
echo "📦 Checking Redis installation..."
if command -v redis-cli &> /dev/null; then
    echo "✅ Redis is already installed"
    redis-cli ping > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo "✅ Redis is running"
    else
        echo "⚠️  Redis is installed but not running"
        echo "   Start it with: brew services start redis"
    fi
else
    echo "❌ Redis is not installed"
    echo ""
    echo "Install Redis:"
    echo "  macOS:  brew install redis && brew services start redis"
    echo "  Linux:  sudo apt-get install redis-server && sudo systemctl start redis"
    echo "  Docker: docker run -d -p 6379:6379 redis:alpine"
    echo ""
fi

echo ""
echo "🔐 Generating encryption key..."
ENCRYPTION_KEY=$(node -e "console.log(require('crypto').randomBytes(32).toString('hex'))")
echo "✅ Generated encryption key:"
echo "   CHAT_ENCRYPTION_KEY=$ENCRYPTION_KEY"
echo ""

echo "📝 Environment Variables Checklist:"
echo "======================================"
echo ""
echo "Add these to your .env file:"
echo ""
echo "# WebSocket"
echo "SOCKET_CORS_ORIGIN=http://localhost:3000"
echo ""
echo "# Redis"
echo "REDIS_HOST=localhost"
echo "REDIS_PORT=6379"
echo "REDIS_PASSWORD="
echo "REDIS_DB=0"
echo ""
echo "# Encryption"
echo "CHAT_ENCRYPTION_KEY=$ENCRYPTION_KEY"
echo ""
echo "# Media Limits"
echo "MAX_FILE_SIZE=10485760"
echo "MAX_IMAGE_SIZE=5242880"
echo "MAX_VIDEO_SIZE=52428800"
echo ""

echo "✅ Setup checklist:"
echo "  1. ☐ Install Redis (if not already installed)"
echo "  2. ☐ Add environment variables to .env"
echo "  3. ☐ Configure Cloudflare R2 credentials (should already exist)"
echo "  4. ☐ Run: npm install (dependencies already installed)"
echo "  5. ☐ Run: npm run dev"
echo ""
echo "📚 For more information, see:"
echo "   - CHAT_SYSTEM_README.md"
echo "   - CHAT_SYSTEM_IMPLEMENTATION_PLAN.md"
echo "   - .env.chat.example"
echo ""
