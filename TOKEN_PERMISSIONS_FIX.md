# GitHub Fine-Grained Token Setup Guide

## Current Issue
The fine-grained personal access token is being denied (403 error) when trying to push.

## Required Token Permissions

For fine-grained tokens to work with git push, you need:

### ✅ Required Permissions:
1. **Repository access**: Must be scoped to `srujantunikipati-cyber/pets-gen-ai` repository
2. **Contents**: Must have **Write** permission (not just Read)
3. **Metadata**: Must have **Read** permission

## How to Fix Token Permissions

### Step 1: Go to Token Settings
1. Visit: https://github.com/settings/tokens
2. Find your token (the one ending in `...K4`)
3. Click **"Configure"** or **"Edit"**

### Step 2: Check Repository Access
- Ensure the token has access to: `srujantunikipati-cyber/pets-gen-ai`
- If it says "All repositories" or "Only select repositories", make sure `pets-gen-ai` is included

### Step 3: Check Permissions
Under **Repository permissions**, ensure:
- ✅ **Contents**: Set to **Write** (required for push)
- ✅ **Metadata**: Set to **Read** (required)

### Step 4: Save and Retry
1. Click **"Save"** or **"Update token"**
2. Wait 1-2 minutes for changes to propagate
3. Try pushing again

## Alternative: Use Classic Token (Easier)

If fine-grained tokens are causing issues, create a **Classic Personal Access Token**:

1. Go to: https://github.com/settings/tokens
2. Click **"Generate new token"** → **"Generate new token (classic)"**
3. **Note**: "pets-gen-ai-push"
4. **Expiration**: Choose your preference
5. **Scopes**: Check ✅ **`repo`** (Full control of private repositories)
6. Click **"Generate token"**
7. Copy the token (starts with `ghp_...`)

Then use it:
```bash
cd /home/chetan-patil/myprojects/1
git remote set-url origin https://YOUR_CLASSIC_TOKEN@github.com/srujantunikipati-cyber/pets-gen-ai.git
git push -u origin main
```

## Verify Token Works

Test the token with a simple API call:
```bash
curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user
```

If this returns your user info, the token is valid but might need repository permissions.

## Current Status

- ✅ All code committed locally
- ✅ Remote configured correctly
- ❌ Token permissions need to be updated
- ⏳ Waiting for token permission fix

## Next Steps

1. **Update token permissions** (see above)
2. **Or create a classic token** (easier option)
3. **Then push again**:
   ```bash
   cd /home/chetan-patil/myprojects/1
   git push -u origin main
   ```
