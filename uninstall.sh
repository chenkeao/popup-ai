#!/bin/bash
# Uninstall script for Popup AI

set -e

PREFIX="$HOME/.local"
SYSTEMD_USER_DIR="$HOME/.config/systemd/user"
APP_ID="io.github.chenkeao.popup-ai"

echo "Uninstalling Popup AI..."

# Stop and disable service
if systemctl --user is-active --quiet popup-ai.service; then
    echo "Stopping service..."
    systemctl --user stop popup-ai.service
fi

if systemctl --user is-enabled --quiet popup-ai.service 2>/dev/null; then
    echo "Disabling service..."
    systemctl --user disable popup-ai.service
fi

# Remove systemd service
if [ -f "$SYSTEMD_USER_DIR/popup-ai.service" ]; then
    echo "Removing systemd service..."
    rm -f "$SYSTEMD_USER_DIR/popup-ai.service"
    systemctl --user daemon-reload
fi

# Remove installed files
echo "Removing installed files..."
rm -f "$PREFIX/bin/popup-ai"
rm -rf "$PREFIX/lib/python3.14/site-packages/popup_ai"
rm -f "$PREFIX/share/glib-2.0/schemas/${APP_ID}.gschema.xml"

# Recompile schemas
if [ -d "$PREFIX/share/glib-2.0/schemas" ]; then
    glib-compile-schemas "$PREFIX/share/glib-2.0/schemas" 2>/dev/null || true
fi

# Remove build directory
if [ -d "build" ]; then
    echo "Removing build directory..."
    rm -rf build
fi

echo ""
echo "✓ Uninstall complete!"
echo ""
