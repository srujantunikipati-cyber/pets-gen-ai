#!/usr/bin/env python3
"""Test script for video input features."""

import asyncio
import sys
from app.services.audio_extraction import get_audio_extraction_service
from app.services.speech_to_text import get_speech_to_text_service
from app.services.content_filter import get_content_filter_service
from app.clients.ai4bharat import AI4BharatClient
import httpx

async def test_services():
    """Test all new services."""
    print("🧪 Testing Video Input Features")
    print("=" * 50)
    
    # Test audio extraction service
    print("\n1️⃣ Testing Audio Extraction Service...")
    audio_service = get_audio_extraction_service()
    if audio_service:
        print("   ✅ Audio extraction service available")
    else:
        print("   ⚠️ Audio extraction service not available")
        print("   💡 Install moviepy: pip install moviepy")
    
    # Test STT service
    print("\n2️⃣ Testing Speech-to-Text Service...")
    stt_service = get_speech_to_text_service()
    if stt_service:
        print("   ✅ Speech-to-text service available")
        print(f"   📊 Model size: {stt_service.model_size}")
    else:
        print("   ⚠️ Speech-to-text service not available")
        print("   💡 Install whisper: pip install openai-whisper")
    
    # Test content filter service
    print("\n3️⃣ Testing Content Filter Service...")
    try:
        settings = __import__('app.core.config', fromlist=['get_settings']).get_settings()
        async with httpx.AsyncClient(timeout=30.0) as client:
            ai4bharat_client = AI4BharatClient(
                http_client=client,
                base_url=settings.ai4bharat_base_url,
                translate_path=settings.ai4bharat_translate_path,
                api_key=settings.ai4bharat_api_key,
            )
            content_filter = get_content_filter_service(ai4bharat_client)
            print("   ✅ Content filter service available")
    except Exception as e:
        print(f"   ⚠️ Content filter service: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Service availability check complete!")
    print("\n💡 To test with actual video:")
    print("   1. Start server: uvicorn app.main:app --host 0.0.0.0 --port 8000")
    print("   2. POST to /api/generate-video with video_data")
    print("   3. Check job status at /api/video-status/{job_id}")

if __name__ == "__main__":
    asyncio.run(test_services())
