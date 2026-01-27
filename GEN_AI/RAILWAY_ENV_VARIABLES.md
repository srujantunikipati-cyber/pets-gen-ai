# 🚀 Railway Environment Variables - Complete List

## ✅ Copy These Variables to Railway Dashboard

Go to: **https://railway.app/project/d3e9f8f4-cdca-4825-9ec4-f7fa9844d266** → **Variables** tab

### Required Variables (Copy One by One)

```
FAL_API_KEY=0d44c9a0-5679-4338-9f14-055fa0907d5f:6e3f241a600df52476c1bb414dff5e4a
```

```
FAL_BASE_URL=https://queue.fal.run
```

```
FAL_MODEL_ID=fal-ai/minimax-video
```

```
USE_REDIS=true
```

```
VIDEO_STORAGE_PATH=storage/videos
```

### Optional but Recommended Variables

```
AI4BHARAT_BASE_URL=http://localhost:5000
```

```
AI4BHARAT_TRANSLATE_PATH=/translate
```

```
REQUEST_TIMEOUT_SECONDS=30.0
```

```
MAX_RETRIES=3
```

```
RETRY_BACKOFF_FACTOR=1.5
```

### Redis Configuration (If Using Redis)

```
REDIS_URL=redis://default:password@redis.railway.internal:6379
```

```
REDIS_JOB_TTL_SECONDS=604800
```

### Webhook Configuration (Update After Deployment)

**⚠️ IMPORTANT**: Update these AFTER you get your Railway URL:

```
BACKEND_WEBHOOK_URL=https://your-app.railway.app/webhooks/video-complete
```

```
CORS_ORIGINS=["https://your-app.railway.app"]
```

**Note**: Replace `your-app.railway.app` with your actual Railway domain after deployment.

---

## 📋 Quick Copy-Paste Format

For easy copy-paste, here's the format Railway Dashboard expects:

**Variable Name** | **Value**
--- | ---
FAL_API_KEY | `0d44c9a0-5679-4338-9f14-055fa0907d5f:6e3f241a600df52476c1bb414dff5e4a`
FAL_BASE_URL | `https://queue.fal.run`
FAL_MODEL_ID | `fal-ai/minimax-video`
USE_REDIS | `true`
VIDEO_STORAGE_PATH | `storage/videos`
AI4BHARAT_BASE_URL | `http://localhost:5000`
AI4BHARAT_TRANSLATE_PATH | `/_translate`
REQUEST_TIMEOUT_SECONDS | `30.0`
MAX_RETRIES | `3`
RETRY_BACKOFF_FACTOR | `1.5`

---

## ⚠️ Variables to Remove

**DO NOT SET** these (they're not needed or will cause errors):

- ❌ `HOST` - Railway handles this automatically
- ❌ `REVID_API_KEY` - We're using fal.ai now, not Revid
- ❌ `REVID_WEBHOOK_SECRET` - Not needed for fal.ai

---

## ✅ After Setting Variables

1. **Save** each variable
2. Railway will **automatically redeploy**
3. Check **Deployments** tab for build progress
4. View **Logs** tab for runtime logs
5. Get your URL from **Settings** → **Networking**

---

## 🔄 Update After Deployment

Once you have your Railway URL (e.g., `https://your-app.railway.app`):

1. Update `BACKEND_WEBHOOK_URL`:
   ```
   BACKEND_WEBHOOK_URL=https://your-app.railway.app/webhooks/video-complete
   ```

2. Update `CORS_ORIGINS`:
   ```
   CORS_ORIGINS=["https://your-app.railway.app"]
   ```

---

**✅ Set these variables in Railway Dashboard and your app will deploy perfectly!**
