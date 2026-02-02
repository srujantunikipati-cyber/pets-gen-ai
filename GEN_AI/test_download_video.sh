#!/bin/bash

# Test Video Download Functionality
# Tests all endpoints including the new download feature

BASE_URL="https://pets-gen-ai-production-7245.up.railway.app"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎬 Complete Video Generation & Download Test"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 1. Generate Video
echo "1️⃣ Generating video..."
RESPONSE=$(curl -s -X POST "$BASE_URL/generate-video" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This adorable golden retriever loves playing fetch and running in the park",
    "imageUrl": "https://images.dog.ceo/breeds/retriever-golden/n02099601_1003.jpg"
  }')

echo "$RESPONSE" | jq '.'
JOB_ID=$(echo "$RESPONSE" | jq -r '.job_id')

if [ "$JOB_ID" = "null" ] || [ -z "$JOB_ID" ]; then
    echo "❌ Failed to generate video"
    exit 1
fi

echo ""
echo "✅ Job ID: $JOB_ID"
echo ""

# 2. Wait for video to complete
echo "2️⃣ Waiting for video generation (checking every 10 seconds)..."
echo ""

MAX_CHECKS=15
CHECK_COUNT=0
STATUS="processing"

while [ "$STATUS" = "processing" ] && [ $CHECK_COUNT -lt $MAX_CHECKS ]; do
    CHECK_COUNT=$((CHECK_COUNT + 1))
    SECONDS=$((CHECK_COUNT * 10))
    
    echo "Check #$CHECK_COUNT ($SECONDS seconds)..."
    
    STATUS_RESPONSE=$(curl -s "$BASE_URL/video-status/$JOB_ID")
    echo "$STATUS_RESPONSE" | jq '.'
    
    STATUS=$(echo "$STATUS_RESPONSE" | jq -r '.status')
    
    if [ "$STATUS" = "completed" ]; then
        echo "✅ Video completed!"
        break
    elif [ "$STATUS" = "failed" ]; then
        echo "❌ Video generation failed"
        exit 1
    else
        echo "   → Still processing, waiting 10 seconds..."
        sleep 10
    fi
done

if [ "$STATUS" != "completed" ]; then
    echo "⏱️  Timeout: Video still processing after $((MAX_CHECKS * 10)) seconds"
    echo "   Check later: curl $BASE_URL/video-result/$JOB_ID"
    exit 1
fi

echo ""

# 3. Get Video Result
echo "3️⃣ Getting video result..."
RESULT=$(curl -s "$BASE_URL/video-result/$JOB_ID")
echo "$RESULT" | jq '.'

VIDEO_URL=$(echo "$RESULT" | jq -r '.video_url')

if [ "$VIDEO_URL" = "null" ] || [ -z "$VIDEO_URL" ]; then
    echo "❌ No video URL available"
    exit 1
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Video Generation Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📹 Video URL:"
echo "   $VIDEO_URL"
echo ""

# 4. Test Download Endpoint
echo "4️⃣ Testing download endpoint..."
DOWNLOAD_URL="$BASE_URL/download-video/$JOB_ID"
OUTPUT_FILE="pet_video_${JOB_ID}.mp4"

echo "   Downloading to: $OUTPUT_FILE"
curl -L -o "$OUTPUT_FILE" "$DOWNLOAD_URL"

if [ -f "$OUTPUT_FILE" ]; then
    FILE_SIZE=$(ls -lh "$OUTPUT_FILE" | awk '{print $5}')
    echo ""
    echo "✅ Video downloaded successfully!"
    echo "   File: $OUTPUT_FILE"
    echo "   Size: $FILE_SIZE"
    echo ""
else
    echo "❌ Download failed"
    exit 1
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🎉 All Tests Passed!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📋 Summary:"
echo "   ✅ Video generated: $JOB_ID"
echo "   ✅ Video URL obtained: $VIDEO_URL"
echo "   ✅ Video downloaded: $OUTPUT_FILE ($FILE_SIZE)"
echo ""
echo "🎥 Play your video:"
echo "   mpv $OUTPUT_FILE"
echo "   # OR"
echo "   vlc $OUTPUT_FILE"
echo ""
echo "🔗 All Download Options:"
echo "   1. Direct URL:     $VIDEO_URL"
echo "   2. Download API:   $DOWNLOAD_URL"
echo "   3. wget:           wget '$VIDEO_URL' -O video.mp4"
echo "   4. curl:           curl -L '$DOWNLOAD_URL' -o video.mp4"
echo ""
