#!/bin/bash

# Bivicom Radar Bot - Installation Script for Friend
echo "🎉 Installing Bivicom Radar Bot..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if Python 3.7+ is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.7 or higher."
    echo "Download from: https://www.python.org/downloads/"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
REQUIRED_VERSION="3.7"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python $PYTHON_VERSION is too old. Please install Python 3.7 or higher."
    exit 1
fi

echo "✅ Python $PYTHON_VERSION found"

# Install tkinter (if needed)
echo "Checking tkinter..."
python3 -c "import tkinter" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing tkinter..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        brew install python-tk
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        sudo apt-get update
        sudo apt-get install python3-tk
    else
        echo "❌ Please install tkinter for your system"
        exit 1
    fi
fi

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements_gui.txt

# Create app bundle
echo "Creating app bundle..."
mkdir -p /Applications/BivicomRadarBot.app/Contents/MacOS
mkdir -p /Applications/BivicomRadarBot.app/Contents/Resources

# Create launcher script
cat > /Applications/BivicomRadarBot.app/Contents/MacOS/BivicomRadarBot << 'LAUNCHER_EOF'
#!/bin/bash
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$(dirname "$(dirname "$PROJECT_DIR")")")"
cd "$PROJECT_DIR"
source venv/bin/activate
python3 radar_bot_gui.py
LAUNCHER_EOF

chmod +x /Applications/BivicomRadarBot.app/Contents/MacOS/BivicomRadarBot

# Create Info.plist
cat > /Applications/BivicomRadarBot.app/Contents/Info.plist << 'PLIST_EOF'
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
PLIST_EOF

# Create desktop shortcut
ln -sf /Applications/BivicomRadarBot.app ~/Desktop/Bivicom\ Radar\ Bot

echo ""
echo "🎉 Installation completed successfully!"
echo ""
echo "📁 App installed to: /Applications/BivicomRadarBot.app"
echo "🖥️  Desktop shortcut: ~/Desktop/Bivicom Radar Bot"
echo ""
echo "🚀 How to launch:"
echo "1. Double-click the desktop shortcut"
echo "2. Or open Applications folder and double-click 'Bivicom Radar Bot'"
echo "3. Or use Spotlight search: Cmd+Space, type 'Bivicom'"
echo ""
echo "📖 Read README_GUI.md for detailed instructions"
echo ""
echo "✅ Ready to use!"
