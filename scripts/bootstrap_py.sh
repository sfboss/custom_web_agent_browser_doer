#!/bin/bash
# Bootstrap Python environment and install Playwright

set -e

echo "🔧 Bootstrapping Python environment..."

# Check Python version
python3 --version

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source .venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install -U pip

# Install web-agent-py package
echo "Installing web-agent-py..."
pip install -e packages/web-agent-py

# Install UI requirements
echo "Installing UI requirements..."
pip install -r packages/web-agent-ui/requirements.txt

# Install Playwright browsers
echo "Installing Playwright browsers..."
python -m playwright install chromium

echo "✅ Bootstrap complete!"
echo ""
echo "To activate the environment, run:"
echo "  source .venv/bin/activate"
