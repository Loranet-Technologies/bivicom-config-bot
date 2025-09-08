#!/bin/bash

# Create proper macOS app bundle for Bivicom Radar Bot
echo "Creating macOS app bundle..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Create app bundle structure
APP_NAME="BivicomRadarBot"
APP_DIR="/Applications/${APP_NAME}.app"

echo "Creating app bundle at: $APP_DIR"

# Remove existing app if it exists
if [ -d "$APP_DIR" ]; then
    echo "Removing existing app bundle..."
    sudo rm -rf "$APP_DIR"
fi

# Create app bundle structure
sudo mkdir -p "$APP_DIR/Contents/MacOS"
sudo mkdir -p "$APP_DIR/Contents/Resources"

# Copy the executable
echo "Copying executable..."
sudo cp "dist/BivicomRadarBot" "$APP_DIR/Contents/MacOS/"

# Make executable
sudo chmod +x "$APP_DIR/Contents/MacOS/BivicomRadarBot"

# Create Info.plist
echo "Creating Info.plist..."
sudo tee "$APP_DIR/Contents/Info.plist" > /dev/null << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>BivicomRadarBot</string>
    <key>CFBundleIdentifier</key>
    <string>com.bivicom.radarbot</string>
    <key>CFBundleName</key>
    <string>Bivicom Radar Bot</string>
    <key>CFBundleDisplayName</key>
    <string>Bivicom Radar Bot</string>
    <key>CFBundleVersion</key>
    <string>1.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundleInfoDictionaryVersion</key>
    <string>6.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
    <key>CFBundleGetInfoString</key>
    <string>Bivicom Radar Bot - Device Setup Application</string>
    <key>CFBundleSignature</key>
    <string>????</string>
    <key>NSHighResolutionCapable</key>
    <true/>
    <key>LSUIElement</key>
    <false/>
</dict>
</plist>
EOF

# Create desktop shortcut
echo "Creating desktop shortcut..."
ln -sf "$APP_DIR" ~/Desktop/Bivicom\ Radar\ Bot

echo "✅ App bundle created successfully!"
echo "📁 Location: $APP_DIR"
echo "🖥️  Desktop shortcut: ~/Desktop/Bivicom Radar Bot"
echo ""
echo "You can now launch the app by:"
echo "1. Double-clicking the desktop shortcut"
echo "2. Opening Applications folder and double-clicking 'Bivicom Radar Bot'"
echo "3. Using Spotlight search: Cmd+Space, type 'Bivicom'"
