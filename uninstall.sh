#!/bin/bash
# Uninstall script for Popup AI

set -e

PREFIX="$HOME/.local"
APP_ID="io.github.chenkeao.popup-ai"

echo "Uninstalling Popup AI..."

# Stop daemon if running
if command -v popup-ai &> /dev/null; then
    echo "Stopping daemon..."
    popup-ai stop 2>/dev/null || true
fi

# Remove installed files
echo "Removing installed files..."
rm -f "$PREFIX/bin/popup-ai"
rm -rf "$PREFIX/lib/python3.14/site-packages/popup_ai"
rm -f "$PREFIX/share/glib-2.0/schemas/${APP_ID}.gschema.xml"
rm -f "$PREFIX/share/applications/${APP_ID}.desktop"
rm -f "$PREFIX/share/dbus-1/services/${APP_ID}.service"
rm -f "$PREFIX/share/icons/hicolor/scalable/apps/${APP_ID}.svg"

# Recompile schemas
if [ -d "$PREFIX/share/glib-2.0/schemas" ]; then
    glib-compile-schemas "$PREFIX/share/glib-2.0/schemas" 2>/dev/null || true
fi

# Remove runtime files
RUNTIME_DIR="${XDG_RUNTIME_DIR:-/tmp/runtime-$(id -u)}"
rm -f "$RUNTIME_DIR/popup-ai.pid"
rm -f "$RUNTIME_DIR/popup-ai.lock"
rm -f "$RUNTIME_DIR/popup-ai.log"

# Remove build directory
if [ -d "build" ]; then
    echo "Removing build directory..."
    rm -rf build
fi

echo ""
echo "✓ Uninstall complete!"
echo ""
