#!/bin/bash

# Bivicom Radar Bot - Linux Installation Script
echo "🎉 Installing Bivicom Radar Bot for Linux..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if Python 3.7+ is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.7 or higher."
    echo "Ubuntu/Debian: sudo apt update && sudo apt install python3 python3-pip python3-venv python3-tk"
    echo "CentOS/RHEL: sudo yum install python3 python3-pip python3-tkinter"
    echo "Fedora: sudo dnf install python3 python3-pip python3-tkinter"
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
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
        sudo apt-get install python3-tk
    elif command -v yum &> /dev/null; then
        sudo yum install python3-tkinter
    elif command -v dnf &> /dev/null; then
        sudo dnf install python3-tkinter
    else
        echo "❌ Please install tkinter for your Linux distribution"
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

# Create desktop shortcut
echo "Creating desktop shortcut..."
cat > ~/Desktop/bivicom-radar-bot.desktop << 'DESKTOP_EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=Bivicom Radar Bot
Comment=Automated Bivicom Radar device setup
Exec=python3 radar_bot_gui.py
Icon=applications-internet
Path=SCRIPT_DIR_PLACEHOLDER
Terminal=false
Categories=Network;System;
DESKTOP_EOF

# Replace placeholder with actual path
sed -i "s|SCRIPT_DIR_PLACEHOLDER|$SCRIPT_DIR|g" ~/Desktop/bivicom-radar-bot.desktop
chmod +x ~/Desktop/bivicom-radar-bot.desktop

echo ""
echo "🎉 Installation completed successfully!"
echo ""
echo "🖥️  Desktop shortcut created: ~/Desktop/bivicom-radar-bot.desktop"
echo ""
echo "🚀 How to launch:"
echo "1. Double-click the desktop shortcut"
echo "2. Or run: python3 radar_bot_gui.py"
echo ""
echo "📖 Read README_GUI.md for detailed instructions"
echo ""
echo "✅ Ready to use!"
