#!/bin/bash

# Script to test SSH connection and push code to GitHub

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔐 Testing SSH Connection to GitHub"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Test SSH connection
echo "Testing connection..."
ssh_output=$(ssh -T git@github.com 2>&1)

if echo "$ssh_output" | grep -q "srujantunikipati-cyber"; then
    echo "✅ SSH authenticated as srujantunikipati-cyber!"
    echo ""
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📤 Pushing code to GitHub..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    cd /home/chetan-patil/myprojects/1
    
    # Set remote to SSH
    git remote set-url origin git@github.com:srujantunikipati-cyber/pets-gen-ai.git
    
    # Push code
    git push -u origin main
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "✅ SUCCESS! Code pushed to GitHub!"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        echo "Repository: https://github.com/srujantunikipati-cyber/pets-gen-ai"
    else
        echo ""
        echo "❌ Push failed. Check the error above."
    fi
elif echo "$ssh_output" | grep -q "Chetupatil24"; then
    echo "⚠️  SSH authenticated as Chetupatil24 (not srujantunikipati-cyber)"
    echo ""
    echo "You need to add your SSH key to the srujantunikipati-cyber account."
    echo "See SSH_SETUP_GUIDE.md for instructions."
else
    echo "❌ SSH authentication failed"
    echo "Error: $ssh_output"
    echo ""
    echo "Make sure you've added your SSH key to GitHub:"
    echo "https://github.com/settings/keys"
fi
