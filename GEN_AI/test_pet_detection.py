#!/usr/bin/env python3
"""
Test pet detection validation - images/videos without pets should be rejected
"""

import requests
import json

RAILWAY_URL = "https://pets-gen-ai-production-7245.up.railway.app"

print("\n" + "=" * 70)
print("🔍 TESTING PET DETECTION VALIDATION")
print("=" * 70)

# Test 1: Valid pet image (should PASS)
print("\n1️⃣  Testing with valid pet image (Golden Retriever)")
try:
    payload = {
        "text": "Generate a fun roast video for this cute dog",
        "imageUrl": "https://images.dog.ceo/breeds/retriever-golden/n02099601_3004.jpg",
        "userId": "test-valid-pet"
    }
    response = requests.post(
        f"{RAILWAY_URL}/api/generate-video",
        json=payload,
        timeout=30
    )
    print(f"   Status: {response.status_code}")
    result = response.json()
    if response.status_code == 202:
        print(f"   ✅ PASS - Pet detected, job created: {result.get('job_id', 'N/A')}")
    else:
        print(f"   ❌ FAIL - Expected 202, got {response.status_code}")
        print(f"   Response: {json.dumps(result, indent=2)}")
except Exception as e:
    print(f"   ❌ ERROR: {e}")

# Test 2: Non-pet image - landscape (should FAIL)
print("\n2️⃣  Testing with non-pet image (landscape)")
try:
    payload = {
        "text": "Generate a video",
        "imageUrl": "https://images.unsplash.com/photo-1506905925346-21bda4d32df4?w=400",
        "userId": "test-no-pet-landscape"
    }
    response = requests.post(
        f"{RAILWAY_URL}/api/generate-video",
        json=payload,
        timeout=30
    )
    print(f"   Status: {response.status_code}")
    result = response.json()
    
    if response.status_code == 400:
        detail = result.get('detail', {})
        if isinstance(detail, dict) and detail.get('error') == 'no_pets_detected':
            print(f"   ✅ PASS - Correctly rejected (no pets detected)")
            print(f"   Message: {detail.get('message', 'N/A')}")
        else:
            print(f"   ⚠️  PARTIAL - Rejected but wrong error")
            print(f"   Response: {json.dumps(result, indent=2)}")
    else:
        print(f"   ❌ FAIL - Expected 400 rejection, got {response.status_code}")
        print(f"   Response: {json.dumps(result, indent=2)}")
except Exception as e:
    print(f"   ❌ ERROR: {e}")

# Test 3: Another valid pet image (should PASS)
print("\n3️⃣  Testing with another valid pet image (Cat)")
try:
    payload = {
        "text": "Roast this cat",
        "imageUrl": "https://cataas.com/cat",
        "userId": "test-valid-cat"
    }
    response = requests.post(
        f"{RAILWAY_URL}/api/generate-video",
        json=payload,
        timeout=30
    )
    print(f"   Status: {response.status_code}")
    result = response.json()
    if response.status_code == 202:
        print(f"   ✅ PASS - Pet detected, job created: {result.get('job_id', 'N/A')}")
    else:
        print(f"   Response: {json.dumps(result, indent=2)}")
except Exception as e:
    print(f"   ❌ ERROR: {e}")

print("\n" + "=" * 70)
print("✅ PET DETECTION TESTS COMPLETE")
print("=" * 70)
print("\nNote: Currently validation checks if image/video is valid.")
print("In production, use actual image classification API for pet detection.")
print("=" * 70)
