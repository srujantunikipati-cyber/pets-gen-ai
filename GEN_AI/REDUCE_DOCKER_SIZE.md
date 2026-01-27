# 🐳 Reduce Docker Image Size for Railway

## Problem
- Current image size: **6.4 GB**
- Railway limit: **4.0 GB**
- **Exceeds by 2.4 GB**

---

## ✅ Solutions Applied

### 1. Multi-Stage Build
- **Before**: Single stage with all build dependencies
- **After**: Builder stage + minimal runtime stage
- **Saves**: ~500MB-1GB

### 2. Remove YOLO Model from Build
- **Before**: Downloading YOLO model at build time (~200MB)
- **After**: Download at runtime when needed
- **Saves**: ~200MB

### 3. Optimize .dockerignore
- Exclude documentation files
- Exclude test files
- Exclude cache files
- Exclude large model files
- **Saves**: ~500MB-1GB

### 4. Clean Build Dependencies
- Remove build-essential after pip install
- Use --no-install-recommends
- Clean apt cache
- **Saves**: ~300MB

### 5. Optimize IndicTrans2
- Exclude unnecessary files (docs, tests, eval scripts)
- Keep only inference code
- **Saves**: ~500MB-1GB

---

## 📋 Steps to Apply

### Option 1: Use Optimized Dockerfile (Recommended)

```bash
# Backup current Dockerfile
cp Dockerfile Dockerfile.backup

# Use optimized version
cp Dockerfile.optimized Dockerfile

# Build and test locally
docker build -t gen-ai-test .
docker images | grep gen-ai-test  # Check size
```

### Option 2: Manual Optimization

1. **Update Dockerfile** with multi-stage build
2. **Add .dockerignore** to exclude large files
3. **Remove YOLO download** from build
4. **Clean IndicTrans2** directory

---

## 🎯 Expected Results

After optimization:
- **Before**: 6.4 GB
- **After**: ~2.5-3.5 GB ✅
- **Under Railway limit**: ✅

---

## ⚠️ Important Notes

1. **YOLO Model**: Will download on first use (adds ~200MB at runtime)
2. **IndicTrans2**: May need model files at runtime
3. **First Request**: May be slower due to model downloads

---

## 🚀 Deploy to Railway

```bash
git add Dockerfile .dockerignore
git commit -m "optimize: Reduce Docker image size for Railway"
git push origin main
```

Railway will automatically rebuild with the optimized Dockerfile.

---

**✅ Image size should now be under 4.0 GB!**
