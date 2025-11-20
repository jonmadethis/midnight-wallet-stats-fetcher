#!/bin/bash
# Midnight Wallet Statistics Fetcher - Setup Script
# This script installs all required dependencies

set -e  # Exit on error

echo "========================================="
echo "Midnight Wallet Stats - Setup"
echo "========================================="
echo ""

# Check Python version
echo "[1/5] Checking Python version..."
if ! command -v python3.11 &> /dev/null; then
    echo "❌ Error: Python 3.11 not found"
    echo "   Please install Python 3.11 or higher"
    exit 1
fi

PYTHON_VERSION=$(python3.11 --version | cut -d' ' -f2)
echo "   ✓ Found Python $PYTHON_VERSION"
echo ""

# Check pip
echo "[2/5] Checking pip..."
if ! command -v pip3.11 &> /dev/null; then
    echo "❌ Error: pip for Python 3.11 not found"
    echo "   Please install pip for Python 3.11"
    exit 1
fi
echo "   ✓ pip is available"
echo ""

# Install Python dependencies
echo "[3/5] Installing Python dependencies..."
pip3.11 install -r requirements.txt
echo "   ✓ Python dependencies installed"
echo ""

# Install Playwright browsers (for browser method)
echo "[4/5] Installing Playwright browsers..."
echo "   This may take a few minutes..."
python3.11 -m playwright install chromium
echo "   ✓ Playwright browsers installed"
echo ""

# Check for Xvfb (optional, for headless servers)
echo "[5/5] Checking for Xvfb (required on headless servers)..."
if command -v xvfb-run &> /dev/null; then
    echo "   ✓ Xvfb found - you can use the browser method on headless servers"
else
    echo "   ℹ Xvfb not found"
    echo "   This is optional, but needed for browser method on headless servers"
    echo "   To install on Ubuntu/Debian:"
    echo "   sudo apt-get install xvfb"
    echo ""
    echo "   Note: The direct method (fetch_wallet_stats_direct.py) doesn't need Xvfb"
fi
echo ""

echo "========================================="
echo "✓ Setup Complete!"
echo "========================================="
echo ""
echo "Quick Start:"
echo ""
echo "1. Create your wallet file (see example_wallets.json)"
echo ""
echo "2. Run the fast method:"
echo "   python3.11 fetch_wallet_stats_direct.py your_wallets.json"
echo ""
echo "3. Or use the browser method (more robust):"
echo "   xvfb-run -a python3.11 fetch_wallet_stats.py your_wallets.json"
echo ""
echo "For more information, see README.md"
echo ""
