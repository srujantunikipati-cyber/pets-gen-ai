#!/bin/bash

echo "═══════════════════════════════════════════════════════════════"
echo "🧪 BACKEND API TESTING - CURL COMMANDS"
echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "🔗 Railway URL: https://pets-gen-ai-production-7245.up.railway.app"
echo ""

# Test 1: Generate video with base64 image
echo "════════════════════════════════════════════════════════════════"
echo "1️⃣ TEST: Image to Video (Base64 encoding)"
echo "════════════════════════════════════════════════════════════════"
echo ""

IMAGE_B64=$(base64 -w 0 ~/myprojects/1/GEN_AI/images.jpeg)

echo "📤 Sending request with base64 image..."
curl -X POST "https://pets-gen-ai-production-7245.up.railway.app/api/generate-video" \
  -H "Content-Type: application/json" \
  -d "{
    \"text\": \"A beautiful animated pet scene\",
    \"image_data\": \"$IMAGE_B64\"
  }" | jq '.'

echo ""
echo ""

# Test 2: Simple text-based video generation
echo "════════════════════════════════════════════════════════════════"
echo "2️⃣ TEST: Text to Video (No image)"
echo "════════════════════════════════════════════════════════════════"
echo ""

echo "📤 Sending request with text only..."
curl -X POST "https://pets-gen-ai-production-7245.up.railway.app/api/generate-video" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "A playful cat playing with a toy"
  }' | jq '.'

echo ""
echo ""

# Test 3: Check status endpoint
echo "════════════════════════════════════════════════════════════════"
echo "3️⃣ INFO: How to check video status"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "After getting a job_id from the above requests, check status with:"
echo ""
echo "curl 'https://pets-gen-ai-production-7245.up.railway.app/api/video-result/YOUR_JOB_ID' | jq '.'"
echo ""

echo "════════════════════════════════════════════════════════════════"
echo "✅ TESTING COMPLETE"
echo "════════════════════════════════════════════════════════════════"
