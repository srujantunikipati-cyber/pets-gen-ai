# GitHub Authentication Guide

## Current Situation
- **Repository**: `srujantunikipati-cyber/pets-gen-ai`
- **Your GitHub Account**: `Chetupatil24`
- **Issue**: Permission denied - need authentication to push

---

## Method 1: Personal Access Token (HTTPS) - ⭐ RECOMMENDED

### Step 1: Create Personal Access Token

1. **Go to GitHub Settings**:
   - Visit: https://github.com/settings/tokens
   - Or: GitHub → Your Profile → Settings → Developer settings → Personal access tokens → Tokens (classic)

2. **Generate New Token**:
   - Click **"Generate new token"** → **"Generate new token (classic)"**
   - **Note**: Give it a name like "pets-gen-ai-push"
   - **Expiration**: Choose your preference (90 days, 1 year, or no expiration)
   - **Scopes**: Check ✅ **`repo`** (Full control of private repositories)
     - This includes: `repo:status`, `repo_deployment`, `public_repo`, `repo:invite`, `security_events`
   - Click **"Generate token"**

3. **Copy the Token**:
   - ⚠️ **IMPORTANT**: Copy the token immediately - you won't see it again!
   - Example token format: `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx`

### Step 2: Use Token to Push

**Option A: Embed token in remote URL** (one-time setup)
```bash
cd /home/chetan-patil/myprojects/1
git remote set-url origin https://YOUR_TOKEN@github.com/srujantunikipati-cyber/pets-gen-ai.git
git push -u origin main
```

**Option B: Use token when prompted** (more secure)
```bash
cd /home/chetan-patil/myprojects/1
git remote set-url origin https://github.com/srujantunikipati-cyber/pets-gen-ai.git
git push -u origin main
# When prompted:
# Username: srujantunikipati-cyber
# Password: YOUR_PERSONAL_ACCESS_TOKEN
```

**Option C: Use Git Credential Helper** (most secure)
```bash
cd /home/chetan-patil/myprojects/1
git remote set-url origin https://github.com/srujantunikipati-cyber/pets-gen-ai.git

# Store credentials (will prompt for username and token)
git config --global credential.helper store
git push -u origin main
# Enter: srujantunikipati-cyber
# Enter: YOUR_PERSONAL_ACCESS_TOKEN
```

---

## Method 2: SSH Key Setup (For srujantunikipati-cyber Account)

### Step 1: Generate SSH Key (if you have access to that account)

```bash
# Generate new SSH key for srujantunikipati-cyber account
ssh-keygen -t ed25519 -C "srujantunikipati-cyber@github" -f ~/.ssh/id_ed25519_srujantunikipati

# Start SSH agent
eval "$(ssh-agent -s)"

# Add key to SSH agent
ssh-add ~/.ssh/id_ed25519_srujantunikipati
```

### Step 2: Add SSH Key to GitHub

1. **Copy public key**:
   ```bash
   cat ~/.ssh/id_ed25519_srujantunikipati.pub
   # Copy the entire output
   ```

2. **Add to GitHub**:
   - Login to GitHub as `srujantunikipati-cyber`
   - Go to: https://github.com/settings/keys
   - Click **"New SSH key"**
   - **Title**: "My Development Machine" (or any name)
   - **Key**: Paste the public key
   - Click **"Add SSH key"**

### Step 3: Configure SSH for Multiple Accounts

Create/edit `~/.ssh/config`:
```bash
# Default account (Chetupatil24)
Host github.com
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519

# srujantunikipati-cyber account
Host github-srujantunikipati
    HostName github.com
    User git
    IdentityFile ~/.ssh/id_ed25519_srujantunikipati
```

Then update remote:
```bash
cd /home/chetan-patil/myprojects/1
git remote set-url origin git@github-srujantunikipati:srujantunikipati-cyber/pets-gen-ai.git
git push -u origin main
```

---

## Method 3: Get Added as Collaborator (Easiest if you know the owner)

### Step 1: Ask Repository Owner

Contact `srujantunikipati-cyber` and ask them to:

1. Go to: https://github.com/srujantunikipati-cyber/pets-gen-ai/settings/access
2. Click **"Add people"** or **"Invite a collaborator"**
3. Enter: `Chetupatil24`
4. Select permission: **Write** (or **Admin**)
5. Click **"Add [username] to this repository"**

### Step 2: Accept Invitation

1. Check your email (`Chetupatil24` account)
2. Click the invitation link
3. Or go to: https://github.com/srujantunikipati-cyber/pets-gen-ai/invitations

### Step 3: Push

```bash
cd /home/chetan-patil/myprojects/1
git push -u origin main
```

---

## Method 4: Use GitHub CLI (gh)

### Step 1: Install GitHub CLI

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install gh

# Or download from: https://cli.github.com/
```

### Step 2: Authenticate

```bash
# Login with srujantunikipati-cyber account
gh auth login
# Follow prompts:
# - GitHub.com
# - HTTPS or SSH
# - Authenticate Git with your GitHub credentials? Yes
# - Login via web browser or token
```

### Step 3: Push

```bash
cd /home/chetan-patil/myprojects/1
git push -u origin main
```

---

## Quick Test: Verify Authentication

### For HTTPS (Personal Access Token):
```bash
cd /home/chetan-patil/myprojects/1
git ls-remote origin
# Should list branches without errors
```

### For SSH:
```bash
ssh -T git@github.com
# Should show: "Hi srujantunikipati-cyber! You've successfully authenticated..."
```

---

## Troubleshooting

### Error: "Permission denied (publickey)"
- **Solution**: SSH key not added to GitHub account
- **Fix**: Add your SSH public key to GitHub Settings → SSH and GPG keys

### Error: "Authentication failed"
- **Solution**: Token expired or incorrect
- **Fix**: Generate new Personal Access Token

### Error: "Repository not found"
- **Solution**: Repository doesn't exist or you don't have access
- **Fix**: Verify repository URL and access permissions

### Error: "403 Forbidden"
- **Solution**: Token doesn't have `repo` scope
- **Fix**: Regenerate token with `repo` scope checked

---

## Recommended Approach

**For quick setup**: Use **Method 1 (Personal Access Token)** with **Option C (Credential Helper)**

This is:
- ✅ Fastest to set up
- ✅ Most secure (token stored in credential helper)
- ✅ Works immediately
- ✅ No need to modify SSH config

---

## Next Steps After Authentication

Once authenticated, push your code:

```bash
cd /home/chetan-patil/myprojects/1
git push -u origin main
```

You should see:
```
Enumerating objects: XXX, done.
Counting objects: 100% (XXX/XXX), done.
Compressing objects: 100% (XXX/XXX), done.
Writing objects: 100% (XXX/XXX), done.
To github.com:srujantunikipati-cyber/pets-gen-ai.git
 * [new branch]      main -> main
Branch 'main' set up to track remote branch 'main' from 'origin'.
```

🎉 **Success!** All your code is now on GitHub!
