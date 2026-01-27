# SSH Key Setup Guide for GitHub

## Current Situation
- ✅ You have SSH keys already
- ✅ Current key authenticates as `Chetupatil24`
- ⚠️ Need to authenticate as `srujantunikipati-cyber`

## Option 1: Add Existing Key to New Account (EASIEST)

If you have access to the `srujantunikipati-cyber` GitHub account:

### Step 1: Copy Your Public Key
```bash
cat ~/.ssh/id_ed25519.pub
```

### Step 2: Add to GitHub
1. **Login to GitHub** as `srujantunikipati-cyber`
2. Go to: https://github.com/settings/keys
3. Click **"New SSH key"**
4. **Title**: "My Development Machine" (or any name)
5. **Key type**: Authentication Key
6. **Key**: Paste the entire output from Step 1
7. Click **"Add SSH key"**

### Step 3: Test Connection
```bash
ssh -T git@github.com
```

Expected output:
```
Hi srujantunikipati-cyber! You've successfully authenticated...
```

### Step 4: Push Code
```bash
cd /home/chetan-patil/myprojects/1
git remote set-url origin git@github.com:srujantunikipati-cyber/pets-gen-ai.git
git push -u origin main
```

---

## Option 2: Create New SSH Key for srujantunikipati-cyber

If you want a separate key for this account:

### Step 1: Generate New SSH Key
```bash
ssh-keygen -t ed25519 -C "srujantunikipati-cyber@github" -f ~/.ssh/id_ed25519_srujantunikipati
```

When prompted:
- **Passphrase**: Press Enter (no passphrase) OR enter a secure passphrase
- **Confirm passphrase**: Press Enter again OR re-enter passphrase

### Step 2: Start SSH Agent
```bash
eval "$(ssh-agent -s)"
```

### Step 3: Add Key to SSH Agent
```bash
ssh-add ~/.ssh/id_ed25519_srujantunikipati
```

### Step 4: Copy Public Key
```bash
cat ~/.ssh/id_ed25519_srujantunikipati.pub
```

**Copy the entire output** (starts with `ssh-ed25519`)

### Step 5: Add to GitHub
1. **Login to GitHub** as `srujantunikipati-cyber`
2. Go to: https://github.com/settings/keys
3. Click **"New SSH key"**
4. **Title**: "Development Machine - pets-gen-ai"
5. **Key type**: Authentication Key
6. **Key**: Paste the public key from Step 4
7. Click **"Add SSH key"**

### Step 6: Configure SSH for Multiple Accounts

Create/edit `~/.ssh/config`:
```bash
nano ~/.ssh/config
```

Add this configuration:
```
# Default GitHub account (Chetupatil24)
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

Save and exit (Ctrl+X, then Y, then Enter)

### Step 7: Set Permissions
```bash
chmod 600 ~/.ssh/config
chmod 600 ~/.ssh/id_ed25519_srujantunikipati
chmod 644 ~/.ssh/id_ed25519_srujantunikipati.pub
```

### Step 8: Test Connection
```bash
ssh -T git@github-srujantunikipati
```

Expected output:
```
Hi srujantunikipati-cyber! You've successfully authenticated...
```

### Step 9: Update Git Remote and Push
```bash
cd /home/chetan-patil/myprojects/1
git remote set-url origin git@github-srujantunikipati:srujantunikipati-cyber/pets-gen-ai.git
git push -u origin main
```

---

## Quick Reference Commands

### Check Current SSH Keys
```bash
ls -la ~/.ssh/*.pub
```

### Test GitHub Connection
```bash
ssh -T git@github.com
```

### View Public Key
```bash
cat ~/.ssh/id_ed25519.pub
```

### Add Key to SSH Agent
```bash
eval "$(ssh-agent -s)"
ssh-add ~/.ssh/id_ed25519
```

---

## Troubleshooting

### Error: "Permission denied (publickey)"
- **Solution**: SSH key not added to GitHub account
- **Fix**: Add your public key to GitHub Settings → SSH and GPG keys

### Error: "Could not open a connection to your authentication agent"
- **Solution**: SSH agent not running
- **Fix**: Run `eval "$(ssh-agent -s)"` then `ssh-add ~/.ssh/your_key`

### Error: "Host key verification failed"
- **Solution**: Remove old GitHub host key
- **Fix**: `ssh-keygen -R github.com`

### Multiple Keys Not Working
- **Solution**: Use SSH config file (see Option 2, Step 6)
- **Fix**: Create `~/.ssh/config` with proper Host entries

---

## Security Notes

- ✅ **Never share your private key** (`~/.ssh/id_ed25519` or `~/.ssh/id_ed25519_srujantunikipati`)
- ✅ **Only share your public key** (`.pub` files)
- ✅ **Use passphrases** for extra security (optional but recommended)
- ✅ **Keep your private keys secure** (permissions should be 600)

---

## Next Steps After Setup

Once SSH is working:

1. **Verify connection**: `ssh -T git@github.com` (or `git@github-srujantunikipati`)
2. **Update remote**: `git remote set-url origin git@github.com:srujantunikipati-cyber/pets-gen-ai.git`
3. **Push code**: `git push -u origin main`

🎉 **You're all set!**
