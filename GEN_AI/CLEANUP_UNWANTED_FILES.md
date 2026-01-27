# 🧹 Cleanup Unwanted Files

## Files to Keep (Essential)

### Core Application
- `app/` - Main application code
- `IndicTrans2/` - Translation service
- `Dockerfile` - Container configuration
- `railway.json` - Railway config
- `requirements.txt` - Python dependencies
- `streamlit_app.py` - Local testing UI

### Configuration
- `.env` - Local environment (gitignored)
- `.streamlit/config.toml` - Streamlit config

### Documentation (Essential)
- `README.md` - Main documentation
- `DEPLOYMENT_GUIDE.md` - Deployment instructions
- `PERFECT_RAILWAY_CREDENTIALS.md` - Credentials guide

---

## Files to Remove (Temporary/Fix Files)

### Temporary Fix Files
- `COMPLETE_FIX.md`
- `QUICK_FIX.txt`
- `FIX_BLANK_PAGE.md`
- `FIX_WEBSOCKET_ERROR.md`
- `STREAMLIT_FIX.md`

### Multiple Railway Guides (Keep Best Ones)
- Keep: `DEPLOYMENT_GUIDE.md`, `PERFECT_RAILWAY_CREDENTIALS.md`
- Remove duplicates: `RAILWAY_*.md` (keep only essential)

### Multiple Connection Scripts (Keep Best One)
- Keep: `connect_fix_all.sh` or `perfect_connect_fix.sh`
- Remove: `connect_*.sh`, `railway_*.sh` (keep only one)

---

**Let me create a cleanup script...**
