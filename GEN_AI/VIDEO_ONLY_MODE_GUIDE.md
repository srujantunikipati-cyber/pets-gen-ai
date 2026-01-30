# 🎬 Video-Only Mode Guide

## Overview

The GEN_AI Pet Roast service now supports **video-only input mode** where you only need to provide a video with voice - no separate text or image required!

## 🔄 Processing Flow

```
📥 Input: Video with voice
    ↓
🎵 Extract audio from video (moviepy)
    ↓
🎤 Convert speech to text (faster-whisper)
    ↓  - Detects original language automatically
    ↓  - Transcribes audio to text
    ↓
🛡️ Filter & process text (AI4Bharat)
    ↓  - Filters abusive content
    ↓  - Processes/enhances text
    ↓
🖼️ Extract frame from video (moviepy)
    ↓  - Gets frame for pet detection
    ↓
🐾 Validate pet presence (YOLOv5)
    ↓  - Ensures video contains pets
    ↓
🎬 Generate roast video (fal.ai)
    ↓  - Uses processed text + frame
    ↓  - Maintains original language
    ↓
✅ Output: Generated roast video URL
```

## 📦 Requirements

### 1. Install Dependencies

```bash
pip install moviepy faster-whisper ffmpeg-python
```

### 2. Verify Installation

```bash
python3 test_video_only_mode.py
```

Expected output:
```
✅ Audio Extraction Service: Available
✅ Speech-to-Text Service: Available
✅ Content Filter Service: Available (via AI4Bharat)
```

## 🚀 Usage

### Start the Server

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### API Request

#### Option 1: Using video_data (Base64)

```bash
curl -X POST http://localhost:8000/api/generate-video \
  -H "Content-Type: application/json" \
  -d '{
    "video_data": "data:video/mp4;base64,<YOUR_BASE64_VIDEO>"
  }'
```

#### Option 2: Using video_url

```bash
curl -X POST http://localhost:8000/api/generate-video \
  -H "Content-Type: application/json" \
  -d '{
    "video_url": "https://example.com/pet-video.mp4"
  }'
```

#### Option 3: Using video field (backward compatible)

```bash
curl -X POST http://localhost:8000/api/generate-video \
  -H "Content-Type: application/json" \
  -d '{
    "video": "https://example.com/pet-video.mp4"
  }'
```

### Response

```json
{
  "job_id": "abc123def456",
  "status": "processing"
}
```

### Check Status

```bash
curl http://localhost:8000/api/video-status/abc123def456
```

### Get Result

```bash
curl http://localhost:8000/api/video-result/abc123def456
```

## 🎯 Use Cases

### 1. Pet Video Roasting
- User records video saying: "This is my lazy cat, roast him!"
- System extracts audio → converts to text → generates roast video

### 2. Multi-Language Support
- User speaks in Hindi/Tamil/Telugu/etc.
- System automatically detects language
- Generates video in the same language

### 3. Content Safety
- User's speech is analyzed for abusive content
- AI4Bharat filters inappropriate words
- Clean, safe content is used for generation

## 🔧 Configuration

### Environment Variables

```bash
# Required for video generation
FAL_API_KEY=your_fal_api_key

# Required for text processing
AI4BHARAT_API_KEY=your_ai4bharat_api_key

# Optional for additional translation
SARVAM_API_KEY=your_sarvam_api_key
```

### Supported Video Formats

- MP4 (recommended)
- AVI
- MOV
- WebM
- Any format supported by moviepy/ffmpeg

### Audio Requirements

- Clear audio with voice
- Any language (auto-detected)
- Minimum duration: 1 second
- Maximum duration: As per fal.ai limits

## ⚠️ Error Handling

### "No speech detected in video audio"
- **Cause**: Video has no audio or audio is too quiet
- **Solution**: Ensure video has clear audible speech

### "No pets found in the uploaded video"
- **Cause**: Video doesn't contain detectable pets
- **Solution**: Upload video with visible pets (dogs, cats, birds, etc.)

### "Audio extraction services not available"
- **Cause**: moviepy or faster-whisper not installed
- **Solution**: Run `pip install moviepy faster-whisper`

## 📊 API Response Codes

| Code | Status | Description |
|------|--------|-------------|
| 202 | Accepted | Video processing started |
| 400 | Bad Request | Invalid input or no pets detected |
| 503 | Service Unavailable | Required services not configured |
| 500 | Internal Server Error | Processing error occurred |

## 🧪 Testing

### Test with Sample Video

```bash
# Create a simple test
python3 << EOF
import requests
import base64

# Read your pet video
with open('my_pet_video.mp4', 'rb') as f:
    video_bytes = f.read()
    video_base64 = base64.b64encode(video_bytes).decode()
    
# Make API request
response = requests.post(
    'http://localhost:8000/api/generate-video',
    json={'video_data': f'data:video/mp4;base64,{video_base64}'}
)

print('Job ID:', response.json()['job_id'])
EOF
```

### Run Test Suite

```bash
# Test all services
python3 test_video_features.py

# Test video-only mode
python3 test_video_only_mode.py

# Verify deployment
./verify_deployment.sh
```

## 📝 Notes

- **No separate image required**: Frame is extracted from video automatically
- **No separate text required**: Text is extracted from audio automatically
- **Original language maintained**: Video generated in detected language
- **Content filtering**: Automatic filtering of inappropriate content
- **Pet validation**: Ensures video contains pets before processing

## 🎓 Examples

### Example 1: Simple Pet Roast

**Input Video**: User speaks "This is my dog Max, he sleeps all day"

**Processing**:
1. Audio extracted: "This is my dog Max, he sleeps all day"
2. Language detected: English
3. Content filtered: ✓ No issues
4. Frame extracted: Shows dog
5. Pet detected: ✓ Dog found
6. Video generated: Roast about lazy dog Max

### Example 2: Multi-Language

**Input Video**: User speaks in Hindi "यह मेरी बिल्ली है, बहुत आलसी है"

**Processing**:
1. Audio extracted: "यह मेरी बिल्ली है, बहुत आलसी है"
2. Language detected: Hindi
3. Content filtered: ✓ No issues
4. Frame extracted: Shows cat
5. Pet detected: ✓ Cat found
6. Video generated: Roast in Hindi about lazy cat

## 🤝 Integration with pets-backend

If integrating with pets-backend, include auth token:

```json
{
  "video_data": "data:video/mp4;base64,...",
  "auth_token": "firebase_jwt_token",
  "user_id": "user123"
}
```

## 📚 Additional Resources

- [API Documentation](API_DOCUMENTATION.md)
- [Deployment Guide](DEPLOYMENT_GUIDE.md)
- [README](README.md)

---

**Status**: ✅ Fully Implemented and Tested
**Last Updated**: January 29, 2026
