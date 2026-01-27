#!/bin/bash
# Test all GEN_AI APIs

BASE_URL="http://localhost:8000"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🧪 Testing All GEN_AI APIs"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Test 1: Health Check
echo "1️⃣ Testing Health Check..."
HEALTH=$(curl -s "$BASE_URL/healthz")
echo "Response: $HEALTH"
if echo "$HEALTH" | grep -q "ok"; then
    echo "✅ Health check: PASSED"
else
    echo "❌ Health check: FAILED"
fi
echo ""

# Test 2: API Docs
echo "2️⃣ Testing API Documentation..."
DOCS=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/docs")
if [ "$DOCS" = "200" ]; then
    echo "✅ API Docs: Accessible at http://localhost:8000/docs"
else
    echo "❌ API Docs: FAILED (HTTP $DOCS)"
fi
echo ""

# Test 3: OpenAPI Schema
echo "3️⃣ Testing OpenAPI Schema..."
SCHEMA=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/openapi.json")
if [ "$SCHEMA" = "200" ]; then
    echo "✅ OpenAPI Schema: Accessible"
else
    echo "❌ OpenAPI Schema: FAILED (HTTP $SCHEMA)"
fi
echo ""

# Test 4: Translate Text (without auth)
echo "4️⃣ Testing Translate Text API..."
TRANSLATE_RESPONSE=$(curl -s -X POST "$BASE_URL/api/translate-text" \
    -H "Content-Type: application/json" \
    -d '{
        "text": "Hello, how are you?",
        "source_language": "eng_Latn",
        "target_language": "hin_Deva"
    }')
echo "Response: $TRANSLATE_RESPONSE"
if echo "$TRANSLATE_RESPONSE" | grep -q "translated_text\|error"; then
    echo "✅ Translate API: Responded"
else
    echo "⚠️ Translate API: May need AI4Bharat service running"
fi
echo ""

# Test 5: Generate Video (without auth - should fail or work)
echo "5️⃣ Testing Generate Video API..."
VIDEO_RESPONSE=$(curl -s -X POST "$BASE_URL/api/generate-video" \
    -H "Content-Type: application/json" \
    -d '{
        "text": "Test roast",
        "image_url": "https://example.com/test.jpg"
    }')
echo "Response: $VIDEO_RESPONSE"
if echo "$VIDEO_RESPONSE" | grep -q "job_id\|error"; then
    echo "✅ Generate Video API: Responded"
else
    echo "⚠️ Generate Video API: Check response"
fi
echo ""

# Test 6: Get Video Status (invalid job_id)
echo "6️⃣ Testing Get Video Status API..."
STATUS_RESPONSE=$(curl -s "$BASE_URL/api/video-status/invalid-job-id")
echo "Response: $STATUS_RESPONSE"
if echo "$STATUS_RESPONSE" | grep -q "error\|not found"; then
    echo "✅ Video Status API: Responded correctly"
else
    echo "⚠️ Video Status API: Check response"
fi
echo ""

# Test 7: Get Video Result (invalid job_id)
echo "7️⃣ Testing Get Video Result API..."
RESULT_RESPONSE=$(curl -s "$BASE_URL/api/video-result/invalid-job-id")
echo "Response: $RESULT_RESPONSE"
if echo "$RESULT_RESPONSE" | grep -q "error\|not found"; then
    echo "✅ Video Result API: Responded correctly"
else
    echo "⚠️ Video Result API: Check response"
fi
echo ""

# Test 8: Railway Info (if endpoint exists)
echo "8️⃣ Testing Railway Info API..."
RAILWAY_RESPONSE=$(curl -s "$BASE_URL/api/railway-info" 2>&1)
if echo "$RAILWAY_RESPONSE" | grep -q "project_id\|404"; then
    echo "✅ Railway Info API: Responded"
else
    echo "⚠️ Railway Info API: May not exist"
fi
echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  ✅ API Testing Complete!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📖 View full API docs at: http://localhost:8000/docs"
echo ""
