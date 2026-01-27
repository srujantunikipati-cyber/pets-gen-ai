# 🔧 Railway Token Authentication - Complete Fix Guide

## Understanding Token Types

Railway has **two types of tokens**:

### 1. Account API Token (Full Access)
- **Where**: https://railway.app/account/tokens
- **Use**: Full CLI functionality (whoami, link, deploy, logs)
- **Environment Variable**: `RAILWAY_API_TOKEN`
- **Command**: `railway login --token` or `export RAILWAY_API_TOKEN="token"`

### 2. Project Token (Scoped Access)
- **Where**: Project → Settings → Tokens
- **Use**: Limited to specific project (deploy, logs only)
- **Environment Variable**: `RAILWAY_TOKEN`
- **Limitation**: May NOT work for `whoami` or `link`

## ✅ Correct Token Usage

### For Full CLI Access (Recommended)

```bash
# Use Account API Token
export RAILWAY_API_TOKEN="your-account-api-token"
railway whoami  # Should work
railway link --project <project-id>
railway variables set KEY="value"
```

### For Project-Only Access

```bash
# Use Project Token
export RAILWAY_TOKEN="your-project-token"
railway up  # May work
railway logs  # May work
# But railway whoami may fail
```

## 🔧 Fixing Token Issues

### Step 1: Verify CLI Version

```bash
railway --version
```

Should be **4.26.0** or later. If not:

```bash
npm uninstall -g @railway/cli
npm install -g @railway/cli@latest
```

### Step 2: Get Correct Token Type

1. Go to: https://railway.app/account/tokens
2. Click **"New Token"**
3. Name it: "CLI Access" or "Cursor CLI"
4. **Copy the FULL token immediately** (shown only once)
5. This is your **Account API Token**

### Step 3: Use Correct Environment Variable

```bash
# For Account API Token (full access)
export RAILWAY_API_TOKEN="your-account-api-token"

# Verify it works
railway whoami
```

### Step 4: Alternative - Interactive Login

If token doesn't work:

```bash
railway login
# Opens browser - authenticate there
```

## 🎯 Complete Fix Script

Run `./fix_all_perfect.sh` which:
- ✅ Checks CLI version
- ✅ Tries RAILWAY_API_TOKEN first
- ✅ Falls back to RAILWAY_TOKEN
- ✅ Links to project
- ✅ Sets all variables
- ✅ Verifies deployment

## ⚠️ Common Issues

### Issue 1: "Unauthorized" Error

**Cause**: Using Project Token instead of Account API Token

**Fix**: 
1. Get Account API Token from https://railway.app/account/tokens
2. Use `RAILWAY_API_TOKEN` environment variable

### Issue 2: Token Not Working

**Cause**: Token might be expired or invalid

**Fix**:
1. Regenerate token at https://railway.app/account/tokens
2. Copy immediately (shown only once)
3. Update script with new token

### Issue 3: CLI Version Too Old

**Cause**: Old CLI version doesn't support new token format

**Fix**:
```bash
npm uninstall -g @railway/cli
npm install -g @railway/cli@latest
railway --version  # Verify
```

## ✅ Verification Checklist

- [ ] Railway CLI version 4.26.0 or later
- [ ] Using Account API Token (not Project Token)
- [ ] Using `RAILWAY_API_TOKEN` environment variable
- [ ] `railway whoami` works
- [ ] `railway link --project <id>` works
- [ ] Variables can be set

## 📋 Quick Reference

```bash
# Check version
railway --version

# Login with token
export RAILWAY_API_TOKEN="your-token"
railway whoami

# Link to project
railway link --project d3e9f8f4-cdca-4825-9ec4-f7fa9844d266

# Set variables
railway variables set KEY="value"

# Check status
railway status

# View logs
railway logs --follow
```

---

**✅ Use Account API Token with RAILWAY_API_TOKEN for full CLI access!**
