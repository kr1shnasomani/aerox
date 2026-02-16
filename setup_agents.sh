#!/bin/bash

# AEROX Multi-Agent System - Quick Setup Script

echo "╔════════════════════════════════════════════════════════════╗"
echo "║       AEROX Multi-Agent System Setup                       ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check Python version
echo "1. Checking Python version..."
python_version=$(python --version 2>&1 | awk '{print $2}')
echo "   Python version: $python_version"

# Create virtual environment if doesn't exist
if [ ! -d "venv" ]; then
    echo ""
    echo "2. Creating virtual environment..."
    python -m venv venv
    echo "   ✓ Virtual environment created"
else
    echo ""
    echo "2. Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "3. Activating virtual environment..."
source venv/bin/activate
echo "   ✓ Activated"

# Install dependencies
echo ""
echo "4. Installing dependencies..."
pip install -r requirements.txt -q
echo "   ✓ Dependencies installed"

# Check if .env exists
echo ""
echo "5. Checking environment configuration..."
if [ ! -f "agents/.env" ]; then
    cp agents/.env.example agents/.env
    echo "   ⚠ Created agents/.env - Please add your GOOGLE_API_KEY"
    echo "   Get key from: https://ai.google.dev/"
else
    echo "   ✓ agents/.env exists"
fi

# Check if models exist
echo ""
echo "6. Checking ML models..."
if [ -f "models/intent_ensemble.pkl" ] && [ -f "models/capacity_cox.pkl" ]; then
    echo "   ✓ Intent and Capacity models found"
else
    echo "   ⚠ Models not found - will use mock data"
    echo "   To train models: python train_intent.py && python train_capacity.py"
fi

# Run syntax check
echo ""
echo "7. Validating agent files..."
python -m py_compile agents/*.py 2>&1
if [ $? -eq 0 ]; then
    echo "   ✓ All agent files valid"
else
    echo "   ✗ Syntax errors found"
    exit 1
fi

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║                  Setup Complete! 🚀                        ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
echo "Next steps:"
echo "  1. Add your Google API key to agents/.env"
echo "  2. Run demo: python -m agents.demo"
echo ""
echo "For help, see: agents/README.md"
echo ""
