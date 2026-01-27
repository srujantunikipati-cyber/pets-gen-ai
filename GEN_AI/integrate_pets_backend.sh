#!/bin/bash
# Integrate pets-backend with GEN_AI

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  🔗 Integrating pets-backend with GEN_AI"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Step 1: Clone pets-backend
echo "Step 1: Cloning pets-backend..."
cd /home/chetan-patil/myprojects/1
if [ -d "pets-backend" ]; then
    echo "✅ pets-backend already exists"
    cd pets-backend
    git pull
else
    git clone https://github.com/CJTechnology21/pets-backend.git
    cd pets-backend
fi

echo ""
echo "Step 2: Analyzing pets-backend structure..."
find . -type f -name "*.ts" -o -name "*.js" -o -name "*.json" | head -10

echo ""
echo "✅ pets-backend cloned and analyzed"
echo ""
echo "Next: Integrating with GEN_AI..."
