# 🔗 Final Integration Guide - GEN_AI + pets-backend

## 🎯 Architecture

```
┌─────────────┐
│   Frontend  │
└──────┬──────┘
       │
       ├───→ pets-backend (GraphQL) ──→ Authentication & User Management
       │
       └───→ GEN_AI (FastAPI) ──→ Video Generation & Pet Detection
```

---

## 📋 Step 1: Deploy pets-backend

### Option A: Railway

1. Go to: https://railway.app
2. New Project → Deploy from GitHub
3. Select: `CJTechnology21/pets-backend`
4. Set environment variables (see pets-backend README)
5. Deploy

### Option B: Render

1. Go to: https://render.com
2. New Web Service → Connect GitHub
3. Select: `CJTechnology21/pets-backend`
4. Set environment variables
5. Deploy

**Get pets-backend URL**: `https://pets-backend.railway.app` (or your URL)

---

## 📋 Step 2: Configure GEN_AI

### Add to GEN_AI Environment Variables:

```
PETS_BACKEND_URL=https://pets-backend.railway.app
PETS_BACKEND_ENABLED=true
```

---

## 📋 Step 3: Update GEN_AI Code

The integration code has been added:
- ✅ `app/clients/pets_backend.py` - GraphQL client
- ✅ `app/core/config.py` - Configuration updated
- ✅ `app/core/exceptions.py` - PetsBackendError added

---

## 📋 Step 4: Add Authentication Middleware

GEN_AI will verify JWT tokens from pets-backend before processing requests.

---

## ✅ Integration Complete!

Your GEN_AI now connects to pets-backend for authentication!

---

**📖 See detailed integration code in the repository.**
