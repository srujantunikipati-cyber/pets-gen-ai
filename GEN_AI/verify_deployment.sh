#!/bin/bash
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🚀 Deployment Verification"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "1️⃣ Checking Python dependencies..."
python3 -c "import moviepy; print('   ✅ moviepy')" 2>/dev/null || echo "   ❌ moviepy"
python3 -c "import whisper; print('   ✅ whisper')" 2>/dev/null || echo "   ❌ whisper"
python3 -c "import ffmpeg; print('   ✅ ffmpeg-python')" 2>/dev/null || echo "   ❌ ffmpeg-python"

echo ""
echo "2️⃣ Checking system dependencies..."
which ffmpeg >/dev/null && echo "   ✅ ffmpeg installed" || echo "   ❌ ffmpeg not found"

echo ""
echo "3️⃣ Checking application imports..."
python3 -c "from app.main import app; print('   ✅ FastAPI app')" 2>/dev/null || echo "   ❌ FastAPI app import failed"

echo ""
echo "4️⃣ Checking services..."
python3 -c "from app.services.audio_extraction import get_audio_extraction_service; s = get_audio_extraction_service(); print('   ✅ Audio extraction service') if s else print('   ⚠️ Audio extraction service (optional)')" 2>/dev/null || echo "   ⚠️ Audio extraction service (optional)"
python3 -c "from app.services.speech_to_text import get_speech_to_text_service; s = get_speech_to_text_service(); print('   ✅ STT service') if s else print('   ⚠️ STT service (optional)')" 2>/dev/null || echo "   ⚠️ STT service (optional)"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ Verification Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "💡 If all checks pass, you're ready to:"
echo "   1. Start server: uvicorn app.main:app --host 0.0.0.0 --port 8000"
echo "   2. Test video input at: POST /api/generate-video"
echo "   3. Deploy to Railway (Dockerfile ready)"
echo ""
