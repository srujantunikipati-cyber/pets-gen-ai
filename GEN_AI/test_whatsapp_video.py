#!/usr/bin/env python3
"""Test video generation with WhatsApp video - Local and Railway"""

import base64
import requests
import json

VIDEO_PATH = "/home/chetan-patil/myprojects/1/GEN_AI/WhatsApp Video 2026-01-30 at 4.17.58 PM.mp4"

def encode_video_to_base64(video_path: str) -> str:
    """Encode video file to base64 data URI"""
    with open(video_path, 'rb') as f:
        video_bytes = f.read()
    
    b64 = base64.b64encode(video_bytes).decode('utf-8')
    return f"data:video/mp4;base64,{b64}"

def test_local():
    """Test video generation on local server"""
    print("\n🏠 TESTING LOCAL SERVER (localhost:8000)")
    print("=" * 60)
    
    try:
        video_data = encode_video_to_base64(VIDEO_PATH)
        print(f"✅ Video encoded: {len(video_data)} characters")
        
        payload = {
            "videoData": video_data,
            "userId": "test-user-local"
        }
        
        print("📤 Sending request to http://localhost:8000/api/generate-video...")
        response = requests.post(
            "http://localhost:8000/api/generate-video",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        print(f"📥 Status: {response.status_code}")
        print(f"📄 Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 202:
            print("✅ Local test SUCCESS!")
            return response.json()
        else:
            print(f"❌ Local test FAILED: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Local test ERROR: {e}")
        return None

def test_railway():
    """Test video generation on Railway"""
    print("\n☁️  TESTING RAILWAY DEPLOYMENT")
    print("=" * 60)
    
    try:
        video_data = encode_video_to_base64(VIDEO_PATH)
        print(f"✅ Video encoded: {len(video_data)} characters")
        
        payload = {
            "videoData": video_data,
            "userId": "test-user-railway"
        }
        
        url = "https://pets-gen-ai-production-7245.up.railway.app/api/generate-video"
        print(f"📤 Sending request to {url}...")
        
        response = requests.post(
            url,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60
        )
        
        print(f"📥 Status: {response.status_code}")
        print(f"📄 Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 202:
            print("✅ Railway test SUCCESS!")
            return response.json()
        else:
            print(f"❌ Railway test FAILED: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Railway test ERROR: {e}")
        return None

if __name__ == "__main__":
    print("\n🎬 TESTING WHATSAPP VIDEO GENERATION")
    print("=" * 60)
    print(f"📹 Video: {VIDEO_PATH}")
    print(f"👤 User ID: test-user-local / test-user-railway")
    
    # Test local first
    local_result = test_local()
    
    # Test Railway
    railway_result = test_railway()
    
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    print(f"Local:   {'✅ PASS' if local_result else '❌ FAIL'}")
    print(f"Railway: {'✅ PASS' if railway_result else '❌ FAIL'}")
    
    if local_result:
        print(f"\n📝 Local Job ID: {local_result.get('job_id')}")
    if railway_result:
        print(f"📝 Railway Job ID: {railway_result.get('job_id')}")
