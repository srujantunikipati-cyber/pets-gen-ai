# Railway Deployment Guide - Complete Setup

## 🚀 Quick Deploy Steps

### Step 1: Connect Repository to Railway

1. **Go to Railway Dashboard**:
   - Visit: https://railway.app/dashboard
   - Login with your Railway account

2. **Create New Project**:
   - Click **"New Project"**
   - Select **"Deploy from GitHub repo"**
   - Choose: `srujantunikipati-cyber/pets-gen-ai`
   - Railway will auto-detect the `Dockerfile` ✅

3. **Project Settings**:
   - Project Name: `pet_roasting` (or your preferred name)
   - Project ID: `d3e9f8f4-cdca-4825-9ec4-f7fa9844d266` (already exists)

### Step 2: Add Redis Service

1. In your Railway project, click **"New"**
2. Select **"Database"** → **"Redis"**
3. Railway will automatically:
   - Create Redis instance
   - Set `REDIS_URL` environment variable
   - Connect it to your service

### Step 3: Configure Environment Variables

Go to your service → **Variables** tab and add:

```bash
# fal.ai Configuration (REQUIRED)
FAL_API_KEY=0d44c9a0-5679-4338-9f14-055fa0907d5f:6e3f241a600df52476c1bb414dff5e4a
FAL_BASE_URL=https://queue.fal.run
FAL_MODEL_ID=fal-ai/minimax-video

# AI4Bharat Configuration
AI4BHARAT_BASE_URL=http://localhost:5000
AI4BHARAT_TRANSLATE_PATH=/translate
AI4BHARAT_API_KEY=your_ai4bharat_key_here

# Redis Configuration (Auto-set by Railway, but you can override)
USE_REDIS=true
REDIS_JOB_TTL_SECONDS=604800

# Server Configuration
HOST=0.0.0.0
PORT=8000
REQUEST_TIMEOUT_SECONDS=30.0

# Webhook & CORS
BACKEND_WEBHOOK_URL=https://your-backend.railway.app/webhooks/pet-roast-complete
CORS_ORIGINS=["https://your-backend.railway.app","https://your-frontend.railway.app"]

# Retry Configuration
MAX_RETRIES=3
RETRY_BACKOFF_FACTOR=1.5

# Video Storage
VIDEO_STORAGE_PATH=/app/storage/videos

# pets-backend Integration (Optional)
PETS_BACKEND_URL=https://your-pets-backend.railway.app
PETS_BACKEND_ENABLED=false
```

### Step 4: Deploy

Railway will automatically:
- ✅ Detect `Dockerfile` in `GEN_AI/` directory
- ✅ Build the Docker image
- ✅ Deploy the service
- ✅ Expose the service URL

**Note**: If Dockerfile is in `GEN_AI/` subdirectory, Railway might need configuration:

1. Go to **Settings** → **Service Settings**
2. Set **Root Directory** to: `GEN_AI`
3. Or create `railway.json` in root:

```json
{
  "$schema": "https://railway.app/railway.schema.json",
  "build": {
    "builder": "DOCKERFILE",
    "dockerfilePath": "GEN_AI/Dockerfile"
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### Step 5: Verify Deployment

1. **Check Build Logs**:
   - Go to **Deployments** tab
   - Click on latest deployment
   - Check for build errors

2. **Check Service Logs**:
   - Go to **Logs** tab
   - Look for: `Application startup complete`
   - Check for any errors

3. **Test Health Endpoint**:
   ```bash
   curl https://your-service.up.railway.app/healthz
   ```
   Expected: `{"status":"ok"}`

4. **Test API Docs**:
   - Visit: `https://your-service.up.railway.app/docs`
   - Should show Swagger UI

## 🔧 Troubleshooting Railway Issues

### Issue 1: Build Fails - "libgl1-mesa-glx not found"
**Status**: ✅ FIXED
- Dockerfile already uses `libgl1` (correct package)
- If you see this error, Railway might be using cached build
- **Solution**: Clear build cache or redeploy

### Issue 2: Image Size Exceeds 4GB
**Status**: ⚠️ Need to optimize
- Current image might be large due to dependencies
- **Solutions**:
  1. Use multi-stage build (already implemented)
  2. Remove unnecessary files via `.dockerignore`
  3. Consider Railway Pro plan (higher limits)

### Issue 3: Service Crashes on Startup
**Check**:
- Environment variables are set correctly
- `PORT` environment variable is used (Railway sets this automatically)
- Service listens on `0.0.0.0` (already configured)

### Issue 4: Redis Connection Fails
**Check**:
- Redis service is added to project
- `REDIS_URL` is set automatically by Railway
- `USE_REDIS=true` is set

### Issue 5: fal.ai API Errors
**Check**:
- `FAL_API_KEY` is correct
- `FAL_BASE_URL` is `https://queue.fal.run`
- `FAL_MODEL_ID` is correct

## 📋 Railway CLI Commands (Optional)

If you want to use Railway CLI:

```bash
# Login
railway login

# Link to project
railway link

# Set variables
railway variables set FAL_API_KEY=your_key

# Deploy
railway up

# View logs
railway logs

# Open service
railway open
```

## 🔍 Monitoring

### Check Logs
```bash
# Via Railway Dashboard
# Go to: Service → Logs tab

# Via CLI
railway logs
```

### Check Metrics
- Go to **Metrics** tab
- Monitor:
  - CPU usage
  - Memory usage
  - Request count
  - Error rate

## 🎯 Post-Deployment Checklist

- [ ] Health endpoint returns `{"status":"ok"}`
- [ ] API docs accessible at `/docs`
- [ ] Video generation endpoint works
- [ ] Redis connection successful
- [ ] fal.ai integration working
- [ ] Video download working
- [ ] Webhook endpoint accessible

## 📞 Support

If you encounter issues:
1. Check Railway logs
2. Check build logs
3. Verify environment variables
4. Check `FIXES_SUMMARY.md` for known issues

---

**Ready to deploy!** 🚀
