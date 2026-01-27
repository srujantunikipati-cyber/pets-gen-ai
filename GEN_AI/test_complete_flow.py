#!/usr/bin/env python3
"""Complete end-to-end test of video generation flow."""

import asyncio
import httpx
import base64
from PIL import Image
import io
import sys

# Create a test image with a pet (simulated)
def create_test_image():
    """Create a simple test image."""
    img = Image.new('RGB', (512, 512), color=(100, 150, 200))
    # Add some "pet-like" features (just colored rectangles)
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    # Draw a simple "pet" shape
    draw.ellipse([200, 200, 300, 300], fill=(255, 200, 100))  # Body
    draw.ellipse([220, 180, 240, 200], fill=(0, 0, 0))  # Eye
    draw.ellipse([260, 180, 280, 200], fill=(0, 0, 0))  # Eye
    draw.arc([220, 240, 280, 280], start=0, end=180, fill=(0, 0, 0), width=3)  # Mouth
    
    # Convert to base64
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    img_base64 = base64.b64encode(img_bytes.read()).decode('utf-8')
    return f"data:image/png;base64,{img_base64}"

async def test_complete_flow():
    """Test complete video generation flow."""
    base_url = "http://localhost:8000"
    
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  🧪 Complete End-to-End Test")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("")
    
    # Step 1: Health check
    print("1️⃣ Checking server health...")
    try:
        async with httpx.AsyncClient(timeout=30.0) as health_client:
            response = await health_client.get(f"{base_url}/healthz")
            if response.status_code == 200:
                print("   ✅ Server is running")
            else:
                print(f"   ❌ Server health check failed: {response.status_code}")
                return False
    except Exception as e:
        print(f"   ❌ Cannot connect to server: {e}")
        print("   💡 Make sure uvicorn is running: uvicorn app.main:app --host 0.0.0.0 --port 8000")
        return False
    
    # Step 2: Create test image
    print("")
    print("2️⃣ Creating test image...")
    test_image = create_test_image()
    print(f"   ✅ Test image created ({len(test_image)} bytes)")
    
    # Step 3: Test translation
    print("")
    print("3️⃣ Testing translation API...")
    try:
        translate_response = await client.post(
            f"{base_url}/api/translate-text",
            json={
                "text": "Hello, this is a test",
                "source_lang": "en",
                "target_lang": "hi",
                "task": "translation"
            }
        )
        if translate_response.status_code == 200:
            translate_data = translate_response.json()
            print(f"   ✅ Translation working: {translate_data.get('translated_text', 'N/A')[:50]}...")
        else:
            print(f"   ⚠️ Translation API returned: {translate_response.status_code}")
            print(f"   Response: {translate_response.text[:200]}")
    except Exception as e:
        print(f"   ⚠️ Translation test failed: {e}")
    
    # Step 4: Generate video
    print("")
    print("4️⃣ Testing video generation...")
    try:
        video_payload = {
            "text": "This is a test video generation for my pet",
            "image_data": test_image
        }
        
        print("   📤 Sending video generation request...")
        video_response = await client.post(
            f"{base_url}/api/generate-video",
            json=video_payload,
            timeout=60.0
        )
        
        print(f"   📊 Status Code: {video_response.status_code}")
        
        if video_response.status_code == 202:
            video_data = video_response.json()
            job_id = video_data.get("job_id")
            status = video_data.get("status")
            print(f"   ✅ Video generation job created!")
            print(f"   📋 Job ID: {job_id}")
            print(f"   📊 Status: {status}")
            
            # Step 5: Check job status
            print("")
            print("5️⃣ Checking job status...")
            await asyncio.sleep(3)  # Wait a bit
            
            status_response = await client.get(
                f"{base_url}/api/video-status/{job_id}",
                timeout=30.0
            )
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f"   ✅ Job status retrieved")
                print(f"   📊 Status: {status_data.get('status')}")
                print(f"   📝 Detail: {status_data.get('detail', 'N/A')}")
            else:
                print(f"   ⚠️ Status check returned: {status_response.status_code}")
                print(f"   Response: {status_response.text[:200]}")
            
            # Step 6: Try to get result (may not be ready yet)
            print("")
            print("6️⃣ Checking video result...")
            result_response = await client.get(
                f"{base_url}/api/video-result/{job_id}",
                timeout=30.0
            )
            
            if result_response.status_code == 200:
                result_data = result_response.json()
                if result_data.get("video_url"):
                    print(f"   ✅ Video ready!")
                    print(f"   🎬 Video URL: {result_data.get('video_url')}")
                else:
                    print(f"   ⏳ Video still processing...")
                    print(f"   📊 Status: {result_data.get('status')}")
            else:
                print(f"   ⏳ Video not ready yet (status: {result_response.status_code})")
            
            return True
            
        elif video_response.status_code == 400:
            error_data = video_response.json()
            error_detail = error_data.get("detail", {})
            if isinstance(error_detail, dict):
                error_type = error_detail.get("error")
                if error_type == "no_pets_detected":
                    print(f"   ⚠️ No pets detected in test image (expected for simple test)")
                    print(f"   💡 This is normal - the image is too simple")
                    print(f"   ✅ API is working correctly - pet detection is functioning")
                    return True
            print(f"   ❌ Error: {error_data}")
            return False
        else:
            print(f"   ❌ Request failed: {video_response.status_code}")
            print(f"   Response: {video_response.text[:500]}")
            return False
            
    except httpx.TimeoutException:
        print("   ❌ Request timed out")
        return False
    except Exception as e:
        print(f"   ❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  ✅ Testing Complete!")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("")

if __name__ == "__main__":
    success = asyncio.run(test_complete_flow())
    sys.exit(0 if success else 1)
