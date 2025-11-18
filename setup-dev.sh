#!/bin/bash
# Development setup script

set -e

echo "Setting up Popup AI development environment..."

# Check for Python 3.11+
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install pygobject pycairo httpx pydantic pydantic-settings

# Install dev dependencies
pip install black ruff

echo ""
echo "Development environment setup complete!"
echo ""
echo "To activate the virtual environment, run:"
echo "  source .venv/bin/activate"
echo ""
echo "To run the application in development mode:"
echo "  python -m popup_ai.main"
echo ""
