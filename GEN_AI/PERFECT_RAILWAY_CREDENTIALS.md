# ✅ Perfect Railway Credentials - Ready to Upload

## 🚀 Quick Setup Guide

1. **Open Railway Dashboard**: https://railway.app/project/d3e9f8f4-cdca-4825-9ec4-f7fa9844d266
2. **Go to**: Variables tab
3. **Click**: "New Variable" for each one below
4. **Save** after each variable

---

## 📋 Required Variables (Set These First)

### 1. fal.ai API Configuration

**Variable Name**: `FAL_API_KEY`  
**Value**: `0d44c9a0-5679-4338-9f14-055fa0907d5f:6e3f241a600df52476c1bb414dff5e4a`

**Variable Name**: `FAL_BASE_URL`  
**Value**: `https://queue.fal.run`

**Variable Name**: `FAL_MODEL_ID`  
**Value**: `fal-ai/minimax-video`

### 2. Storage Configuration

**Variable Name**: `VIDEO_STORAGE_PATH`  
**Value**: `storage/videos`

### 3. Redis Configuration

**Variable Name**: `USE_REDIS`  
**Value**: `true`

---

## 📋 Optional but Recommended Variables

**Variable Name**: `AI4BHARAT_BASE_URL`  
**Value**: `http://localhost:5000`

**Variable Name**: `AI4BHARAT_TRANSLATE_PATH`  
**Value**: `/translate`

**Variable Name**: `REQUEST_TIMEOUT_SECONDS`  
**Value**: `30.0`

**Variable Name**: `MAX_RETRIES`  
**Value**: `3`

**Variable Name**: `RETRY_BACKOFF_FACTOR`  
**Value**: `1.5`

---

## 📋 Redis URL (If Using Railway Redis Service)

**Variable Name**: `REDIS_URL`  
**Value**: `redis://default:password@redis.railway.internal:6379`

**Variable Name**: `REDIS_JOB_TTL_SECONDS`  
**Value**: `604800`

**Note**: Replace `password` with your actual Redis password from Railway Redis service.

---

## 📋 Update After Deployment (Important!)

After Railway deploys and you get your URL (e.g., `https://your-app.railway.app`):

### 1. Backend Webhook URL

**Variable Name**: `BACKEND_WEBHOOK_URL`  
**Value**: `https://your-app.railway.app/webhooks/video-complete`

**Replace** `your-app.railway.app` with your actual Railway domain.

### 2. CORS Origins

**Variable Name**: `CORS_ORIGINS`  
**Value**: `["https://your-app.railway.app"]`

**Replace** `your-app.railway.app` with your actual Railway domain.

---

## ❌ DO NOT SET These Variables

These will cause errors or are not needed:

- ❌ `HOST` - Railway sets this automatically
- ❌ `REVID_API_KEY` - We're using fal.ai, not Revid
- ❌ `REVID_WEBHOOK_SECRET` - Not needed for fal.ai

---

## ✅ Complete Variable List (Copy-Paste Format)

For Railway Dashboard, add these one by one:

```
FAL_API_KEY=0d44c9a0-5679-4338-9f14-055fa0907d5f:6e3f241a600df52476c1bb414dff5e4a
FAL_BASE_URL=https://queue.fal.run
FAL_MODEL_ID=fal-ai/minimax-video
VIDEO_STORAGE_PATH=storage/videos
USE_REDIS=true
AI4BHARAT_BASE_URL=http://localhost:5000
AI4BHARAT_TRANSLATE_PATH=/translate
REQUEST_TIMEOUT_SECONDS=30.0
MAX_RETRIES=3
RETRY_BACKOFF_FACTOR=1.5
```

---

## 🎯 After Setting Variables

1. ✅ Railway will **automatically redeploy**
2. ✅ Check **Deployments** tab for build progress
3. ✅ View **Logs** tab for runtime logs
4. ✅ Get your URL from **Settings** → **Networking**
5. ✅ Update `BACKEND_WEBHOOK_URL` and `CORS_ORIGINS` with your actual URL

---

**✅ All credentials are ready! Copy them to Railway Dashboard now!**
