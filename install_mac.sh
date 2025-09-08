#!/bin/bash

echo "Installing Bivicom Radar Bot..."
echo

# Create Applications directory if it doesn't exist
APP_DIR="/Applications/BivicomRadarBot.app"
if [ ! -d "$APP_DIR" ]; then
    mkdir -p "$APP_DIR/Contents/MacOS"
    mkdir -p "$APP_DIR/Contents/Resources"
fi

# Copy executable
cp "BivicomRadarBot" "$APP_DIR/Contents/MacOS/"

# Create Info.plist
cat > "$APP_DIR/Contents/Info.plist" << EOF
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
</dict>
</plist>
EOF

# Make executable
chmod +x "$APP_DIR/Contents/MacOS/BivicomRadarBot"

echo
echo "Installation completed successfully!"
echo "Application installed to: $APP_DIR"
echo "You can find it in your Applications folder."
echo
