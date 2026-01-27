# 🔧 Resolve All Railway Issues - Complete Guide

## ✅ Automated Fix (Recommended)

Run this single command to fix everything:

```bash
cd /home/chetan-patil/myprojects/1/GEN_AI
./fix_all_railway.sh
```

This script will:
1. ✅ Install Railway CLI (if needed)
2. ✅ Check authentication
3. ✅ Link to your project
4. ✅ Set all environment variables
5. ✅ Verify configuration
6. ✅ Show deployment status
7. ✅ Display recent logs

## 📋 Manual Fix Steps

If automated script doesn't work, follow these steps:

### Step 1: Install Railway CLI

```bash
npm i -g @railway/cli
```

### Step 2: Login

```bash
railway login
```
(Browser opens - authenticate there)

### Step 3: Connect to Project

```bash
cd /home/chetan-patil/myprojects/1/GEN_AI
railway link d3e9f8f4-cdca-4825-9ec4-f7fa9844d266
```

### Step 4: Set All Variables

```bash
railway variables set FAL_API_KEY="0d44c9a0-5679-4338-9f14-055fa0907d5f:6e3f241a600df52476c1bb414dff5e4a"
railway variables set FAL_BASE_URL="https://queue.fal.run"
railway variables set FAL_MODEL_ID="fal-ai/minimax-video"
railway variables set USE_REDIS="true"
railway variables set VIDEO_STORAGE_PATH="storage/videos"
railway variables set REQUEST_TIMEOUT_SECONDS="30.0"
railway variables set MAX_RETRIES="3"
railway variables set RETRY_BACKOFF_FACTOR="1.5"
```

### Step 5: Verify

```bash
railway status
railway variables
railway logs --tail 50
```

## 🚨 Common Issues & Auto-Fixes

### Issue 1: Build Fails
**Auto-Fix**: ✅ Dockerfile updated with error handling
**Manual**: Check Railway Dashboard → Deployments → Build Logs

### Issue 2: App Crashes
**Auto-Fix**: ✅ All required variables will be set
**Manual**: Check Railway Dashboard → Logs for errors

### Issue 3: Missing Variables
**Auto-Fix**: ✅ Script sets all required variables
**Manual**: Use `railway variables set KEY="value"`

### Issue 4: Port Issues
**Auto-Fix**: ✅ Dockerfile uses $PORT variable
**Manual**: Railway auto-sets PORT, no action needed

### Issue 5: Storage Permissions
**Auto-Fix**: ✅ Video storage has fallback to /tmp
**Manual**: Check logs for storage errors

## ✅ Verification Checklist

After running fixes:

- [ ] Railway CLI installed
- [ ] Logged in to Railway
- [ ] Project linked
- [ ] All variables set
- [ ] Deployment successful
- [ ] Health endpoint works
- [ ] Logs show no errors

## 🎯 Quick Commands

```bash
# Fix everything
./fix_all_railway.sh

# Check status
railway status

# View logs
railway logs --follow

# Deploy
railway up

# Open dashboard
railway open
```

## 📞 If Issues Persist

1. Check Railway Dashboard logs
2. Review build logs in Deployments tab
3. Verify all variables are set correctly
4. Check Railway status page for outages
5. Review RAILWAY_TROUBLESHOOTING.md

---

**Run `./fix_all_railway.sh` to resolve all issues automatically!**
