# Railway Deployment Guide - PostgreSQL Connection Fix

## Issue Summary
When deploying to Railway, you're experiencing **PostgreSQL connection timeouts** because:
1. Neon database (us-east-1) may not be reachable from Railway infrastructure
2. SSL configuration issues
3. Database credentials or connection pool exhaustion

---

## Solution: Use Railway's PostgreSQL Service (RECOMMENDED)

### Step 1: Create PostgreSQL Service in Railway
1. Go to your Railway project dashboard
2. Click **+ New Service** → Select **PostgreSQL**
3. Railway will automatically set `DATABASE_URL` environment variable
4. The database will be on the same network, ensuring fast, reliable connections

### Step 2: Update Your .env for Railway
Remove the Neon database URL and use Railway's auto-generated one:

```properties
# Railway will provide this automatically
# DATABASE_URL=postgresql://...@...railway.app/railway

# But you can also use local dev credentials:
NODE_ENV=production
PORT=4000
```

### Step 3: Deploy
Railway will automatically inject the `DATABASE_URL` from the PostgreSQL service. No manual configuration needed!

---

## Alternative: Keep Neon Database

If you prefer to use Neon, follow these steps:

### 1. Update Neon Settings
- Log in to Neon dashboard
- Go to your project's IP whitelist
- Add Railway's IP ranges (ask Railway support for your region's IPs)
- Or set to allow all IPs (less secure but works for testing)

### 2. Use Connection Pool (PgBouncer)
In Neon dashboard:
- Enable **Project pooling** for your database
- Update your `DATABASE_URL` to use the pooler endpoint:
  ```
  postgresql://...@...neon.tech/neondb?sslmode=require
  ```

### 3. Update .env in Railway
In Railway dashboard → Variables:
```
DATABASE_URL=postgresql://neondb_owner:YOUR_PASSWORD@YOUR_POOLER_HOST/neondb?sslmode=require
```

---

## Debugging Connection Issues

### Check Logs
```bash
# View Railway logs in real-time
railway logs
```

### Common Errors & Solutions

| Error | Solution |
|-------|----------|
| `ETIMEDOUT` on port 5432 | IP not whitelisted or wrong host |
| `SSL: CERTIFICATE_VERIFY_FAILED` | Set `sslmode=require` with `rejectUnauthorized: false` |
| `connect ENETUNREACH` | Database host is unreachable from Railway's network |
| `too many connections` | Enable connection pooling |

---

## Signup/Login Issue: User Not Found

### Root Cause
After Firebase user creation, the PostgreSQL save might be failing due to connection timeout.

### Fix
1. Wait for email verification via OTP before logging in
2. Check logs: `railway logs` to see if user is actually saved
3. Verify PostgreSQL is accessible before signup

### Verification Steps
```sql
-- Check if user exists in database
SELECT * FROM "user" WHERE email = 'abtiwari797@gmail.com';

-- Check OTP records
SELECT * FROM user_otp WHERE "userId" = 'abtiwari797@gmail.com';
```

---

## Recommended Setup for Production

```
┌─────────────────┐
│  Railway App    │  (Node.js + TypeScript)
└────────┬────────┘
         │
         │ Same network
         ↓
┌─────────────────┐
│ Railway         │  (PostgreSQL)
│ PostgreSQL      │
└─────────────────┘
```

**Benefits:**
- ✅ No IP whitelisting needed
- ✅ Automatic backups
- ✅ Same region = low latency
- ✅ Built-in monitoring
- ✅ Easy scaling

---

## Environment Variables for Railway

**In Railway Dashboard → Variables:**

```
NODE_ENV=production
PORT=4000
SMTP_USER=abtiwari797@gmail.com
SMTP_PASS=ylbg qgap soer eakv
GOOGLE_CLIENT_ID=700225592377-ti1no1t1g667jle5rhpmq3d109rdogmi.apps.googleusercontent.com

# DATABASE_URL will be auto-set by Railway PostgreSQL service
# Don't set it manually if using Railway's PostgreSQL
```

---

## Testing Locally Before Deploying

```bash
# Test with local PostgreSQL
npm run dev

# Check that signup creates user
# Check that login finds the user
# Check that OTP verification works
```

---

## Need Help?

Check Railway logs:
```bash
railway login
railway link  # Link to your project
railway logs --service your-app-service
```

Contact Railway support for:
- Network connectivity issues
- PostgreSQL service setup
- IP whitelisting for external databases
