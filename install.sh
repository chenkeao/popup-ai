#!/bin/bash
# Install script for Popup AI

set -e

PREFIX="$HOME/.local"

echo "Installing Popup AI..."

# Check for required tools
if ! command -v meson &> /dev/null; then
    echo "Error: meson is not installed"
    echo "Install it with: sudo dnf install meson"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Check Python dependencies
echo "Checking Python dependencies..."
MISSING_DEPS=()
for pkg in "gi" "httpx" "pydantic" "pydantic_settings" "markdown"; do
    if ! /usr/bin/python3 -c "import $pkg" 2>/dev/null; then
        MISSING_DEPS+=("$pkg")
    fi
done

if [ ${#MISSING_DEPS[@]} -gt 0 ]; then
    echo "Missing Python dependencies. Installing with pip..."
    /usr/bin/python3 -m pip install --user --break-system-packages pygobject httpx pydantic pydantic-settings markdown
fi

# Clean old build
if [ -d "build" ]; then
    echo "Removing old build..."
    rm -rf build
fi

# Build and install
echo "Configuring..."
meson setup build --prefix="$PREFIX"

echo "Building..."
meson compile -C build

echo "Installing..."
meson install -C build

# Compile GSchema
echo "Compiling GSchema..."
glib-compile-schemas ~/.local/share/glib-2.0/schemas/

echo ""
echo "✓ Installation complete!"
echo ""
echo "Usage:"
echo "  popup-ai [text]           - Open window with optional text"
echo "  popup-ai start            - Start background daemon"
echo "  popup-ai stop             - Stop background daemon"
echo "  popup-ai restart          - Restart background daemon"
echo "  popup-ai status           - Check daemon status"
echo ""
echo "The daemon will start automatically when you first run popup-ai."
echo ""
