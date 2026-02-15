#!/usr/bin/env bash
# Customer Support Agent Template - Setup Script
# Usage: bash setup.sh
set -euo pipefail

echo "=========================================="
echo "  Customer Support Agent - Setup"
echo "=========================================="

# Check Python version
PYTHON_CMD=""
for cmd in python3 python; do
    if command -v "$cmd" &> /dev/null; then
        version=$("$cmd" --version 2>&1 | grep -oP '\d+\.\d+')
        major=$(echo "$version" | cut -d. -f1)
        minor=$(echo "$version" | cut -d. -f2)
        if [ "$major" -ge 3 ] && [ "$minor" -ge 10 ]; then
            PYTHON_CMD="$cmd"
            break
        fi
    fi
done

if [ -z "$PYTHON_CMD" ]; then
    echo "Error: Python 3.10+ is required but not found."
    echo "Install from: https://www.python.org/downloads/"
    exit 1
fi

echo "[1/4] Python found: $($PYTHON_CMD --version)"

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "[2/4] Creating virtual environment..."
    $PYTHON_CMD -m venv .venv
else
    echo "[2/4] Virtual environment already exists"
fi

# Activate and install
echo "[3/4] Installing dependencies..."
source .venv/bin/activate
pip install -e ".[dev]" --quiet

# Configure environment
if [ ! -f ".env" ]; then
    echo "[4/4] Creating .env from template..."
    cp .env.example .env
    echo ""
    echo "  ⚠️  Edit .env and add your API key:"
    echo "     OPENAI_API_KEY=sk-your-key-here"
else
    echo "[4/4] .env already exists"
fi

echo ""
echo "=========================================="
echo "  Setup complete!"
echo "=========================================="
echo ""
echo "  Activate:  source .venv/bin/activate"
echo "  Run:       python -m customer_support"
echo "  Test:      pytest -v"
echo ""
