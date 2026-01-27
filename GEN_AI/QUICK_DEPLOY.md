# ⚡ Quick Deployment Guide - 5 Minutes

## 🚀 Fastest Way to Deploy

### Step 1: Connect to Railway (2 minutes)

1. Go to: https://railway.app
2. Click: "New Project"
3. Select: "Deploy from GitHub repo"
4. Choose: `Chetupatil24/GEN_AI`
5. Railway auto-detects Dockerfile ✅

### Step 2: Set Variables (2 minutes)

Go to: **Variables** tab → Add these:

```
FAL_API_KEY = 0d44c9a0-5679-4338-9f14-055fa0907d5f:6e3f241a600df52476c1bb414dff5e4a
FAL_BASE_URL = https://queue.fal.run
FAL_MODEL_ID = fal-ai/minimax-video
VIDEO_STORAGE_PATH = storage/videos
USE_REDIS = true
```

**Click "Save" after each one**

### Step 3: Wait for Deploy (1 minute)

- Check **Deployments** tab
- Wait for "Deployed" ✅
- Get URL from **Settings** → **Networking**

### Step 4: Test (30 seconds)

```bash
curl https://your-app.railway.app/healthz
```

Should return: `{"status":"ok"}`

---

## ✅ Done!

Your app is now live! 🎉

---

**📖 For detailed guide, see: DEPLOYMENT_GUIDE.md**
