#!/bin/bash

# Fix the app icon to work properly
echo "Fixing app icon..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Create app bundle structure
APP_NAME="BivicomRadarBot"
APP_DIR="/Applications/${APP_NAME}.app"

echo "Creating working app bundle at: $APP_DIR"

# Remove existing app if it exists
if [ -d "$APP_DIR" ]; then
    echo "Removing existing app bundle..."
    sudo rm -rf "$APP_DIR"
fi

# Create app bundle structure
sudo mkdir -p "$APP_DIR/Contents/MacOS"
sudo mkdir -p "$APP_DIR/Contents/Resources"

# Create launcher script that uses the correct path
echo "Creating launcher script..."
sudo tee "$APP_DIR/Contents/MacOS/BivicomRadarBot" > /dev/null << EOF
#!/bin/bash

# Bivicom Radar Bot Launcher Script
# This script launches the GUI from the correct directory

# The project directory is fixed to the correct location
PROJECT_DIR="/Users/shamry/Projects/bivicom-radar-bot"

# Change to project directory
cd "\$PROJECT_DIR"

# Activate virtual environment and run GUI
source venv/bin/activate
python3 radar_bot_gui.py
EOF

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
rm -f ~/Desktop/Bivicom\ Radar\ Bot
ln -sf "$APP_DIR" ~/Desktop/Bivicom\ Radar\ Bot

echo "✅ App icon fixed successfully!"
echo "📁 Location: $APP_DIR"
echo "🖥️  Desktop shortcut: ~/Desktop/Bivicom Radar Bot"
echo ""
echo "The app icon should now work properly!"
echo "Try double-clicking the desktop shortcut or the app in Applications folder."
