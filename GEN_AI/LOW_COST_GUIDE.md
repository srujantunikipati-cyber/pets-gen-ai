# 🎯 LOW COST VIDEO GENERATION GUIDE

## 💰 COST COMPARISON (Per Video)

| Model | Cost | Speed | Quality | Audio | Best For |
|-------|------|-------|---------|-------|----------|
| **fast-svd** (RECOMMENDED) | $0.05 | 20-40s | Medium | ❌ | Budget + Quality |
| **fast-animatediff** | $0.02 | 10-20s | Low-Med | ❌ | Ultra Budget |
| **stable-video-diffusion** | $0.03 | 15-30s | Medium | ❌ | Balanced |
| **minimax-video** (Current) | $0.50 | 60-120s | High | ❌ | Premium |
| **luma-ai/dream-machine** | $1.00 | 90-180s | Very High | ❌ | Best Quality |

## 🚨 IF YOU'RE PAYING $5/VIDEO - PROBLEM!

**Expected costs:**
- Minimax: $0.50/video
- Fast-SVD: $0.05/video (90% cheaper!)
- AnimateDiff: $0.02/video (96% cheaper!)

**If paying $5/video, check:**
1. You might be using wrong endpoint
2. Multiple failed attempts being charged
3. Video duration settings too high
4. Wrong model configuration

---

## ✅ RECOMMENDED: Switch to Fast-SVD

**Benefits:**
- ✅ 90% cheaper ($0.05 vs $0.50)
- ✅ 50% faster (20-40s vs 60-120s)
- ✅ Good quality for pet videos
- ✅ Stable and reliable
- ✅ Your $9.46 = ~189 videos instead of 18!

**Model:** `fal-ai/fast-svd/image-to-video`

---

## 🎵 AUDIO GENERATION OPTIONS

### Option 1: ElevenLabs (Best Quality)
- **Cost:** $0.30 per 1000 characters
- **Quality:** Very High
- **Voices:** 100+ realistic voices
- **API:** elevenlabs.io

### Option 2: Google Cloud TTS (Budget)
- **Cost:** $4 per 1 million characters (~$0.004 per video)
- **Quality:** Good
- **Voices:** 100+ languages
- **API:** cloud.google.com/text-to-speech

### Option 3: OpenAI TTS (Balanced)
- **Cost:** $0.015 per 1000 characters
- **Quality:** High
- **Voices:** 6 realistic voices
- **API:** platform.openai.com

### Option 4: FREE - pyttsx3 (Offline)
- **Cost:** FREE
- **Quality:** Basic (robotic)
- **Voices:** System voices
- **Use:** Local generation only

---

## 🎯 BEST CONFIGURATION FOR YOU

### Low Cost + Audio Setup:
```python
VIDEO_MODEL = "fal-ai/fast-svd/image-to-video"  # $0.05/video
AUDIO_SERVICE = "google-cloud-tts"               # $0.004/video
TOTAL_COST = ~$0.054 per video                   # 90% savings!
```

### Your $9.46 will generate:
- **Current (Minimax only):** 18 videos
- **Fast-SVD + Audio:** 175 videos (9.7x more!)
- **AnimateDiff + Audio:** 396 videos (22x more!)

---

## 🔧 IMPLEMENTATION CHANGES

### 1. Update Model Configuration
```python
# In app/core/config.py
fal_model_id: str = "fal-ai/fast-svd/image-to-video"  # Change from minimax
```

### 2. Add Audio Configuration
```python
# Add to app/core/config.py
audio_provider: str = "google-cloud-tts"  # or "elevenlabs", "openai"
google_cloud_tts_api_key: str = ""
```

### 3. Strict Pet Detection
```python
# Already implemented in app/api/routes.py
# Ensures ONLY pet videos are generated
# Rejects non-pet images automatically
```

---

## 📊 COST BREAKDOWN EXAMPLES

### Example 1: 100 Videos with Current Setup
- Video (Minimax): 100 × $0.50 = $50.00
- **Total: $50.00**

### Example 2: 100 Videos with Fast-SVD + Audio
- Video (Fast-SVD): 100 × $0.05 = $5.00
- Audio (Google TTS): 100 × $0.004 = $0.40
- **Total: $5.40** (89% savings!)

### Example 3: 100 Videos with AnimateDiff + Audio
- Video (AnimateDiff): 100 × $0.02 = $2.00
- Audio (Google TTS): 100 × $0.004 = $0.40
- **Total: $2.40** (95% savings!)

---

## 🚀 QUICK SWITCH TO LOW COST

### Step 1: Update Config (Choose ONE)

**Option A: Fast-SVD (Recommended Balance)**
```bash
# Change in app/core/config.py line 36
fal_model_id: str = "fal-ai/fast-svd/image-to-video"
```

**Option B: AnimateDiff (Cheapest)**
```bash
fal_model_id: str = "fal-ai/fast-animatediff/image-to-video"
```

**Option C: Stable Video Diffusion**
```bash
fal_model_id: str = "fal-ai/stable-video-diffusion"
```

### Step 2: Deploy
```bash
git add -A
git commit -m "Switch to low-cost video model"
git push origin main
railway up
```

### Step 3: Test
```bash
# Same API, just cheaper!
curl -X POST https://your-railway.app/api/generate-video \
  -H "Content-Type: application/json" \
  -d '{"text": "...", "imageUrl": "..."}'
```

---

## 🎵 ADD AUDIO (Next Phase)

### Option 1: Google Cloud TTS (Recommended for You)

**Setup:**
1. Go to https://console.cloud.google.com
2. Enable "Text-to-Speech API"
3. Create API key
4. Add to Railway: `GOOGLE_TTS_API_KEY=your_key`

**Cost:** $0.004 per video (practically free!)

### Option 2: ElevenLabs (Best Quality)

**Setup:**
1. Go to https://elevenlabs.io
2. Get API key (free tier: 10k chars/month)
3. Add to Railway: `ELEVENLABS_API_KEY=your_key`

**Cost:** $0.30 per video (5x more expensive)

---

## ✅ IMMEDIATE ACTION PLAN

### To Save Money NOW:

1. **Switch to Fast-SVD** (saves 90%)
   ```bash
   # Change app/core/config.py line 36
   fal_model_id = "fal-ai/fast-svd/image-to-video"
   ```

2. **Add Google Cloud TTS** (adds audio for $0.004/video)
   - Enable API in Google Cloud
   - Add API key to Railway
   - Implement audio generation service

3. **Deploy Changes**
   ```bash
   git add -A && git commit -m "Switch to low-cost model + audio"
   railway up
   ```

### Result:
- **Before:** $0.50/video, no audio
- **After:** $0.054/video, with audio
- **Savings:** 89% + audio included!
- **Your $9.46:** 175 videos instead of 18

---

## 🔒 STRICT PET-ONLY GENERATION

Already implemented! Your API:
- ✅ Detects pets using YOLOv5
- ✅ Rejects non-pet images
- ✅ Only processes dog/cat/bird/rabbit images
- ✅ Returns error if no pet detected

No changes needed here!

---

## 📞 NEXT STEPS

1. **Tell me which model to switch to:**
   - Fast-SVD ($0.05) - Recommended
   - AnimateDiff ($0.02) - Ultra Budget
   - Keep Minimax ($0.50) - Premium

2. **Audio provider:**
   - Google TTS ($0.004) - Recommended
   - ElevenLabs ($0.30) - Premium
   - Skip audio for now

3. **I'll update the code and deploy!**

Want me to switch to Fast-SVD + Google TTS now?
