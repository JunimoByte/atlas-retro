#!/usr/bin/env sh
# ==============================================================================
# Atlas Portable Installer (FreeBSD / GhostBSD)
# ==============================================================================

# 1. Ensure the script is run as root
if [ "$(id -u)" -ne 0 ]; then
    echo "Atlas requires root privileges to install to /usr/local/."
    echo "Elevating permissions via sudo..."
    exec sudo sh "$0" "$@"
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BINARY_NAME="Atlas-x86_64-Portable"
ICON_NAME="Icon.svg"

# Ensure the executable exists next to this script
if [ ! -f "$SCRIPT_DIR/$BINARY_NAME" ]; then
    if [ -f "$SCRIPT_DIR/Atlas-x86-Portable" ]; then
        BINARY_NAME="Atlas-x86-Portable"
    else
        echo "ERROR: Atlas portable binary not found in $SCRIPT_DIR."
        echo "Please extract the entire archive before running install_bsd.sh."
        exit 1
    fi
fi

# ==============================================================================
# OS COMPATIBILITY CHECK
# ==============================================================================
# Check if the system has older ABI libraries if required
if ! grep -q "libutil.so.9" /var/run/ld-elf.so.hints 2>/dev/null; then
    echo "Checking for FreeBSD 13 ABI compatibility libraries..."
    if command -v pkg >/dev/null 2>&1; then
        pkg install -y compat13x-amd64 2>/dev/null || true
    fi
fi

# ==============================================================================
# INSTALLATION
# ==============================================================================
echo "Installing Atlas binary..."
install -d -m 755 "/usr/local/bin"
install -m 755 "$SCRIPT_DIR/$BINARY_NAME" "/usr/local/bin/atlas"

echo "Installing Desktop Integration..."
ICON_DIR="/usr/local/share/icons/hicolor/scalable/apps"
install -d -m 755 "$ICON_DIR"

if [ -f "$SCRIPT_DIR/$ICON_NAME" ]; then
    install -m 644 "$SCRIPT_DIR/$ICON_NAME" "$ICON_DIR/atlas.svg"
elif [ -f "$SCRIPT_DIR/../assets/icons/Icon.svg" ]; then
    install -m 644 "$SCRIPT_DIR/../assets/icons/Icon.svg" "$ICON_DIR/atlas.svg"
else
    echo "Warning: $ICON_NAME not found. Skipping icon."
fi

DESKTOP_DIR="/usr/local/share/applications"
install -d -m 755 "$DESKTOP_DIR"

cat << 'EOF' > "$DESKTOP_DIR/atlas.desktop"
[Desktop Entry]
Name=Atlas
Comment=Browser profile backup application
Exec=/usr/local/bin/atlas
Icon=/usr/local/share/icons/hicolor/scalable/apps/atlas.svg
Terminal=false
Type=Application
Categories=Utility;Archiving;
EOF
chmod 644 "$DESKTOP_DIR/atlas.desktop"

echo ""
echo "=============================================================================="
echo "Installation Complete!"
echo "Atlas is now installed. You can launch it with 'atlas' or from your menu."
echo "=============================================================================="
