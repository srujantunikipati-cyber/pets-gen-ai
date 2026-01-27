# 🚀 Complete Railway Deployment Guide

## Step-by-Step Deployment Instructions

### Prerequisites

✅ GitHub repository: https://github.com/Chetupatil24/GEN_AI  
✅ Railway account: https://railway.app  
✅ All code pushed to GitHub  

---

## Step 1: Connect GitHub to Railway

1. **Go to Railway Dashboard**: https://railway.app
2. **Click**: "New Project"
3. **Select**: "Deploy from GitHub repo"
4. **Authorize**: Railway to access your GitHub account
5. **Select Repository**: `Chetupatil24/GEN_AI`
6. **Railway will automatically**:
   - Detect your `Dockerfile`
   - Start building your app
   - Create a deployment

---

## Step 2: Set Environment Variables

1. **In your Railway project**, go to **"Variables"** tab
2. **Click**: "New Variable" for each variable below

### Required Variables (Set These First)

**Variable 1:**
- **Name**: `FAL_API_KEY`
- **Value**: `0d44c9a0-5679-4338-9f14-055fa0907d5f:6e3f241a600df52476c1bb414dff5e4a`
- **Click**: "Save"

**Variable 2:**
- **Name**: `FAL_BASE_URL`
- **Value**: `https://queue.fal.run`
- **Click**: "Save"

**Variable 3:**
- **Name**: `FAL_MODEL_ID`
- **Value**: `fal-ai/minimax-video`
- **Click**: "Save"

**Variable 4:**
- **Name**: `VIDEO_STORAGE_PATH`
- **Value**: `storage/videos`
- **Click**: "Save"

**Variable 5:**
- **Name**: `USE_REDIS`
- **Value**: `true`
- **Click**: "Save"

### Optional Variables (Recommended)

**Variable 6:**
- **Name**: `AI4BHARAT_BASE_URL`
- **Value**: `http://localhost:5000`
- **Click**: "Save"

**Variable 7:**
- **Name**: `AI4BHARAT_TRANSLATE_PATH`
- **Value**: `/translate`
- **Click**: "Save"

**Variable 8:**
- **Name**: `REQUEST_TIMEOUT_SECONDS`
- **Value**: `30.0`
- **Click**: "Save"

**Variable 9:**
- **Name**: `MAX_RETRIES`
- **Value**: `3`
- **Click**: "Save"

**Variable 10:**
- **Name**: `RETRY_BACKOFF_FACTOR`
- **Value**: `1.5`
- **Click**: "Save"

---

## Step 3: Add Redis Service (Optional but Recommended)

1. **In Railway project**, click **"+ New"**
2. **Select**: "Database" → "Add Redis"
3. **Railway will automatically**:
   - Create Redis instance
   - Set `REDIS_URL` environment variable
   - Connect it to your app

**Note**: If you add Redis, you can also set:
- **Name**: `REDIS_JOB_TTL_SECONDS`
- **Value**: `604800` (7 days)

---

## Step 4: Monitor Deployment

1. **Go to**: "Deployments" tab
2. **Watch**: Build progress
   - ✅ Building Docker image
   - ✅ Installing dependencies
   - ✅ Starting application
3. **Wait for**: "Deployed" status (usually 3-5 minutes)

---

## Step 5: Check Logs

1. **Go to**: "Logs" tab
2. **Look for**:
   - ✅ "Application startup complete"
   - ✅ "Uvicorn running on http://0.0.0.0:PORT"
   - ❌ Any error messages

**If you see errors**, check:
- All required variables are set
- Build completed successfully
- No import errors

---

## Step 6: Get Your Public URL

1. **Go to**: "Settings" tab
2. **Click**: "Networking"
3. **Click**: "Generate Domain"
4. **Copy**: Your Railway URL (e.g., `https://your-app.railway.app`)

---

## Step 7: Update Webhook URLs (After Getting URL)

Once you have your Railway URL, update these variables:

1. **Go to**: "Variables" tab
2. **Update** `BACKEND_WEBHOOK_URL`:
   - **Name**: `BACKEND_WEBHOOK_URL`
   - **Value**: `https://your-app.railway.app/webhooks/video-complete`
   - **Replace** `your-app.railway.app` with your actual URL
   - **Click**: "Save"

3. **Update** `CORS_ORIGINS`:
   - **Name**: `CORS_ORIGINS`
   - **Value**: `["https://your-app.railway.app"]`
   - **Replace** `your-app.railway.app` with your actual URL
   - **Click**: "Save"

---

## Step 8: Test Your Deployment

### Test Health Endpoint

```bash
curl https://your-app.railway.app/healthz
```

**Expected Response**:
```json
{"status":"ok"}
```

### Test API Documentation

Open in browser:
```
https://your-app.railway.app/docs
```

You should see FastAPI Swagger documentation.

---

## Step 9: Verify Video Generation

1. **Send a test request** to generate video:
   ```bash
   curl -X POST https://your-app.railway.app/api/generate-video \
     -H "Content-Type: application/json" \
     -d '{
       "image_url": "https://example.com/pet.jpg",
       "source_language": "en",
       "target_language": "hi"
     }'
   ```

2. **Check logs** for:
   - ✅ Job created
   - ✅ Video generation started
   - ✅ Video completed

---

## ✅ Deployment Checklist

- [ ] GitHub repository connected to Railway
- [ ] All required variables set
- [ ] Redis service added (optional)
- [ ] Deployment successful (check Deployments tab)
- [ ] No errors in logs
- [ ] Health endpoint returns `{"status":"ok"}`
- [ ] Public URL generated
- [ ] Webhook URLs updated with actual URL
- [ ] CORS origins updated with actual URL

---

## 🔧 Troubleshooting

### Build Fails

**Check**:
- Dockerfile syntax is correct
- All dependencies in `requirements.txt`
- Build logs in "Deployments" tab

**Fix**: Check build logs for specific errors

### App Crashes

**Check**:
- All required variables are set
- Runtime logs in "Logs" tab
- No missing dependencies

**Fix**: Review logs for error messages

### Port Issues

**Already Fixed**: Dockerfile uses `$PORT` variable automatically

### Video Generation Fails

**Check**:
- `FAL_API_KEY` is correct
- `FAL_BASE_URL` is `https://queue.fal.run`
- `FAL_MODEL_ID` is `fal-ai/minimax-video`
- Logs show fal.ai API responses

---

## 📋 Quick Reference

### Railway Dashboard Links

- **Project**: https://railway.app/project/d3e9f8f4-cdca-4825-9ec4-f7fa9844d266
- **Variables**: https://railway.app/project/d3e9f8f4-cdca-4825-9ec4-f7fa9844d266/variables
- **Deployments**: https://railway.app/project/d3e9f8f4-cdca-4825-9ec4-f7fa9844d266/deployments
- **Logs**: https://railway.app/project/d3e9f8f4-cdca-4825-9ec4-f7fa9844d266/logs

### Important Endpoints

- **Health Check**: `https://your-app.railway.app/healthz`
- **API Docs**: `https://your-app.railway.app/docs`
- **Generate Video**: `POST https://your-app.railway.app/api/generate-video`
- **Video Status**: `GET https://your-app.railway.app/api/video-status/{job_id}`

---

## 🎯 After Successful Deployment

Your app will:
- ✅ Accept video generation requests
- ✅ Detect pets in images
- ✅ Generate videos via fal.ai
- ✅ Store videos in `storage/videos`
- ✅ Handle webhooks from fal.ai
- ✅ Translate text using AI4Bharat

---

**✅ Follow these steps and your app will deploy successfully!**
