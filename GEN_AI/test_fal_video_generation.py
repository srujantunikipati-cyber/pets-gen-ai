#!/usr/bin/env python3
"""Test fal.ai video generation locally."""

import asyncio
import httpx
import base64
import os
from pathlib import Path

# Test image (small base64 encoded test image)
TEST_IMAGE_BASE64 = """iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="""

async def test_fal_video_generation():
    """Test video generation with fal.ai."""
    base_url = "http://localhost:8000"
    
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  🧪 Testing fal.ai Video Generation")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("")
    
    # Test 1: Health check
    print("1️⃣ Checking server health...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(f"{base_url}/healthz")
            if response.status_code == 200:
                print("✅ Server is running")
            else:
                print(f"❌ Server health check failed: {response.status_code}")
                return
        except Exception as e:
            print(f"❌ Cannot connect to server: {e}")
            print("   Make sure uvicorn is running on port 8000")
            return
    
    # Test 2: Generate video with base64 image
    print("")
    print("2️⃣ Testing video generation with base64 image...")
    
    payload = {
        "text": "Test video generation",
        "image_data": f"data:image/png;base64,{TEST_IMAGE_BASE64}"
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            response = await client.post(
                f"{base_url}/api/generate-video",
                json=payload
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            
            if response.status_code == 200:
                data = response.json()
                job_id = data.get("job_id")
                status = data.get("status")
                print(f"✅ Video generation job created!")
                print(f"   Job ID: {job_id}")
                print(f"   Status: {status}")
                
                # Test 3: Check job status
                print("")
                print("3️⃣ Checking job status...")
                await asyncio.sleep(2)  # Wait a bit
                
                status_response = await client.get(
                    f"{base_url}/api/video-status/{job_id}"
                )
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    print(f"✅ Job status retrieved")
                    print(f"   Status: {status_data.get('status')}")
                    print(f"   Detail: {status_data.get('detail', 'N/A')}")
                else:
                    print(f"⚠️ Status check returned: {status_response.status_code}")
                    print(f"   Response: {status_response.text[:200]}")
                
            elif response.status_code == 422:
                print("❌ Validation error - check request format")
                print(f"   Details: {response.text}")
            else:
                print(f"❌ Request failed: {response.status_code}")
                print(f"   Response: {response.text[:200]}")
                
        except httpx.TimeoutException:
            print("❌ Request timed out")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  ✅ Testing Complete!")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("")

if __name__ == "__main__":
    asyncio.run(test_fal_video_generation())
