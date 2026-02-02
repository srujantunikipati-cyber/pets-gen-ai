#!/bin/bash

# Quick test script to generate a video and check result

BASE_URL="https://pets-gen-ai-production-7245.up.railway.app"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎬 Testing Video Generation"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Step 1: Generate video
echo "1️⃣ Generating video with dog image..."
RESPONSE=$(curl -s -X POST "$BASE_URL/api/generate-video" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This dog thinks they are the main character in every story",
    "imageUrl": "https://images.dog.ceo/breeds/retriever-golden/n02099601_3004.jpg",
    "userId": "test-user"
  }')

echo "$RESPONSE" | jq '.'
JOB_ID=$(echo "$RESPONSE" | jq -r '.job_id')

if [ "$JOB_ID" = "null" ] || [ -z "$JOB_ID" ]; then
  echo "❌ Failed to get job_id. Response:"
  echo "$RESPONSE"
  exit 1
fi

echo ""
echo "✅ Job ID: $JOB_ID"
echo ""

# Step 2: Wait and check status
echo "2️⃣ Checking status (will check every 10 seconds)..."
echo ""

for i in {1..12}; do
  echo "Check #$i (${i}0 seconds)..."
  STATUS_RESPONSE=$(curl -s "$BASE_URL/api/video-status/$JOB_ID")
  echo "$STATUS_RESPONSE" | jq '.'
  
  STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.status')
  
  if [ "$STATUS" = "completed" ] || [ "$STATUS" = "failed" ]; then
    break
  fi
  
  if [ $i -lt 12 ]; then
    echo "   → Still $STATUS, waiting 10 seconds..."
    sleep 10
  fi
  echo ""
done

echo ""
echo "3️⃣ Getting video result..."
RESULT=$(curl -s "$BASE_URL/api/video-result/$JOB_ID")
echo "$RESULT" | jq '.'

VIDEO_URL=$(echo "$RESULT" | jq -r '.video_url')
if [ "$VIDEO_URL" != "null" ] && [ -n "$VIDEO_URL" ]; then
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "✅ SUCCESS! Video URL:"
  echo "$VIDEO_URL"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""
  echo "🎥 Download your video:"
  echo "   wget '$VIDEO_URL' -O my_pet_roast_video.mp4"
  echo ""
  echo "   Or open in browser:"
  echo "   $VIDEO_URL"
else
  echo ""
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo "⚠️  Video URL not available yet"
  echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
  echo ""
  echo "Detail: $(echo "$RESULT" | jq -r '.detail')"
  echo ""
  echo "💡 This could mean:"
  echo "   1. Video is still processing (check again later)"
  echo "   2. FAL.ai credits exhausted"
  echo "   3. Job failed during generation"
  echo ""
  echo "🔑 Make sure you have FAL.ai credits:"
  echo "   https://fal.ai/dashboard/billing"
fi
