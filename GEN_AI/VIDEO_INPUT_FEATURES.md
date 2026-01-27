# 🎬 Video Input Features - Complete Implementation

## Overview

The application now supports **two modes** for video generation:

1. **Text + Image Mode** (Original): User provides text and image
2. **Video Input Mode** (New): User provides video, system extracts audio, converts to text, filters abusive content, and generates video

---

## 🆕 New Features

### 1. **Video Input Support**
- Accept video files via `video_data` (base64) or `video_url`
- Automatically extracts audio from video
- Extracts frame from video for pet detection

### 2. **Speech-to-Text (STT)**
- Uses OpenAI Whisper for high-quality transcription
- Automatically detects language
- Supports multiple languages (Hindi, English, Telugu, Tamil, etc.)

### 3. **Content Filtering**
- LLM-based filtering of abusive words
- Preserves original meaning and tone
- Keeps text in original language (if audio was scanned)

### 4. **Smart Language Handling**
- If video input is used, keeps text in original detected language
- If text input is used, translates to English (existing behavior)

---

## 📋 API Changes

### Updated Request Schema

```json
{
  // Mode 1: Text + Image (existing)
  "text": "Your roast text",
  "image_url": "https://...",
  // OR
  "image_data": "data:image/png;base64,...",
  
  // Mode 2: Video Input (new)
  "video_url": "https://...",
  // OR
  "video_data": "data:video/mp4;base64,..."
}
```

### Response (unchanged)

```json
{
  "job_id": "abc123",
  "status": "queued"
}
```

---

## 🔄 Processing Flow

### Video Input Mode Flow:

```
1. User uploads video
   ↓
2. Extract audio from video (moviepy)
   ↓
3. Convert audio to text (Whisper STT)
   ↓
4. Filter abusive words (LLM/AI4Bharat)
   ↓
5. Extract frame from video for pet detection
   ↓
6. Validate pets in frame
   ↓
7. Generate video with filtered text (fal.ai)
   ↓
8. Return job_id
```

### Text + Image Mode Flow (unchanged):

```
1. User provides text + image
   ↓
2. Validate pets in image
   ↓
3. Process text via AI4Bharat
   ↓
4. Generate video (fal.ai)
   ↓
5. Return job_id
```

---

## 🛠️ New Services

### 1. Audio Extraction Service
- **File**: `app/services/audio_extraction.py`
- **Dependencies**: `moviepy`
- **Features**:
  - Extract audio from video files
  - Support for base64 video data
  - Support for video URLs
  - Multiple output formats (WAV, MP3)

### 2. Speech-to-Text Service
- **File**: `app/services/speech_to_text.py`
- **Dependencies**: `openai-whisper`
- **Features**:
  - High-quality transcription
  - Automatic language detection
  - Support for multiple languages
  - Configurable model size (tiny, base, small, medium, large)

### 3. Content Filter Service
- **File**: `app/services/content_filter.py`
- **Dependencies**: `ai4bharat` (existing)
- **Features**:
  - LLM-based content filtering
  - Removes/replaces abusive words
  - Preserves meaning and tone
  - Language-aware filtering

---

## 📦 New Dependencies

Added to `requirements.txt`:

```txt
# Audio & Speech Processing
moviepy==1.0.3
openai-whisper==20231117
ffmpeg-python==0.2.0
```

**Note**: `ffmpeg` system package is also required (handled in Dockerfile)

---

## 🐳 Docker Updates

The Dockerfile needs to include `ffmpeg` for audio processing:

```dockerfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgl1 \
    libglib2.0-0 \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*
```

---

## 🧪 Testing

### Test Video Input Mode:

```bash
curl -X POST http://localhost:8000/api/generate-video \
  -H "Content-Type: application/json" \
  -d '{
    "video_data": "data:video/mp4;base64,..."
  }'
```

### Test Text + Image Mode (existing):

```bash
curl -X POST http://localhost:8000/api/generate-video \
  -H "Content-Type: application/json" \
  -d '{
    "text": "Your roast text",
    "image_data": "data:image/png;base64,..."
  }'
```

---

## ⚙️ Configuration

### Optional Environment Variables:

```bash
# Whisper model size (default: "base")
WHISPER_MODEL_SIZE=base  # Options: tiny, base, small, medium, large

# Larger models = better accuracy but slower
# Smaller models = faster but less accurate
```

---

## 🎯 Key Benefits

1. **No Manual Text Input**: Users can just upload a video
2. **Automatic Language Detection**: Works with any language
3. **Content Safety**: Automatic filtering of abusive content
4. **Preserves Original Language**: If audio is scanned, keeps same language
5. **Backward Compatible**: Existing text+image mode still works

---

## 🔍 Error Handling

### Service Unavailable:
- If `moviepy` not installed → Returns 503 with clear message
- If `whisper` not installed → Returns 503 with clear message

### Processing Errors:
- Audio extraction fails → Returns 500 with error details
- STT fails → Returns 500 with error details
- No speech detected → Returns 400 with helpful message
- No pets detected → Returns 400 (same as before)

---

## 📝 Implementation Details

### Language Preservation Logic:

```python
# If video input is used:
target_language = detected_language  # Keep original language

# If text input is used:
target_language = "en"  # Translate to English
```

### Content Filtering:

- Uses AI4Bharat LLM for intelligent filtering
- Removes/replaces abusive words while preserving meaning
- Falls back to original text if filtering fails

### Frame Extraction:

- Extracts frame at middle of video (or 1 second if shorter)
- Converts to PNG base64 for pet detection
- Uses same pet detection pipeline as image mode

---

## ✅ Status

- ✅ Video input support added
- ✅ Audio extraction service created
- ✅ Speech-to-text service created
- ✅ Content filter service created
- ✅ API endpoint updated
- ✅ Dependencies added
- ✅ Error handling implemented
- ✅ Backward compatibility maintained

---

## 🚀 Next Steps

1. **Install dependencies**: `pip install -r requirements.txt`
2. **Install system dependencies**: `ffmpeg` (for audio processing)
3. **Test locally**: Upload a video with audio
4. **Deploy**: Update Dockerfile with `ffmpeg` if needed

---

## 📚 Files Modified/Created

### New Files:
- `app/services/audio_extraction.py`
- `app/services/speech_to_text.py`
- `app/services/content_filter.py`
- `VIDEO_INPUT_FEATURES.md` (this file)

### Modified Files:
- `app/schemas.py` - Added video input fields
- `app/api/routes.py` - Updated generate-video endpoint
- `app/dependencies.py` - Added new service dependencies
- `app/main.py` - Initialize new services
- `requirements.txt` - Added new dependencies

---

**All features implemented and ready for testing!** 🎉
