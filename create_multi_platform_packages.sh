#!/bin/bash

# Create Multi-Platform Distribution Packages
echo "Creating distribution packages for Windows 11 and Ubuntu 20+..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Create distribution directories
rm -rf distribution_windows distribution_ubuntu distribution_macos
mkdir -p distribution_windows distribution_ubuntu distribution_macos

echo "📦 Creating platform-specific packages..."

# =============================================================================
# WINDOWS 11 PACKAGE
# =============================================================================
echo "🪟 Creating Windows 11 package..."

# Copy files to Windows directory
cp -r dist/ distribution_windows/
cp radar_bot_gui.py distribution_windows/
cp master_bot.py distribution_windows/
cp script_no1.py distribution_windows/
cp script_no2.py distribution_windows/
cp script_no3.py distribution_windows/
cp bot_config.json distribution_windows/
cp requirements_gui.txt distribution_windows/
cp README_GUI.md distribution_windows/
cp DEPLOYMENT_GUIDE.md distribution_windows/

# Create Windows installation script
cat > distribution_windows/INSTALL_WINDOWS.bat << 'EOF'
@echo off
echo 🎉 Installing Bivicom Radar Bot for Windows 11...

REM Check if Python is installed
python --version >nul 2>&1
if %errorLevel% neq 0 (
    echo ❌ Python is not installed. Please install Python 3.7 or higher.
    echo Download from: https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo ✅ Python found

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements_gui.txt

REM Create desktop shortcut
echo Creating desktop shortcut...
set "DESKTOP=%USERPROFILE%\Desktop"
echo [InternetShortcut] > "%DESKTOP%\Bivicom Radar Bot.url"
echo URL=file:///%CD%\radar_bot_gui.py >> "%DESKTOP%\Bivicom Radar Bot.url"
echo IconFile=%CD%\radar_bot_gui.py >> "%DESKTOP%\Bivicom Radar Bot.url"
echo IconIndex=0 >> "%DESKTOP%\Bivicom Radar Bot.url"

REM Create launcher script
echo Creating launcher script...
echo @echo off > LAUNCH_BIVICOM_RADAR_BOT.bat
echo call venv\Scripts\activate.bat >> LAUNCH_BIVICOM_RADAR_BOT.bat
echo python radar_bot_gui.py >> LAUNCH_BIVICOM_RADAR_BOT.bat
echo pause >> LAUNCH_BIVICOM_RADAR_BOT.bat

echo.
echo 🎉 Installation completed successfully!
echo.
echo 🚀 How to launch:
echo 1. Double-click "LAUNCH_BIVICOM_RADAR_BOT.bat"
echo 2. Or double-click the desktop shortcut
echo 3. Or run: python radar_bot_gui.py
echo.
echo 📖 Read README_GUI.md for detailed instructions
echo.
echo ✅ Ready to use!
pause
EOF

# Create Windows README
cat > distribution_windows/README_WINDOWS.txt << 'EOF'
🎉 Bivicom Radar Bot - Windows 11 Installation
==============================================

This is a standalone GUI application for setting up Bivicom Radar devices on Windows 11.

🚀 QUICK START:
1. Run: INSTALL_WINDOWS.bat (as Administrator)
2. Follow the installation prompts
3. Launch using: LAUNCH_BIVICOM_RADAR_BOT.bat
4. Click "Start Bot" to begin device setup

📋 REQUIREMENTS:
- Windows 11 (or Windows 10)
- Python 3.7 or higher
- Network access to 192.168.1.1
- SSH access with admin/admin credentials

🎯 WHAT IT DOES:
- Automatically configures network settings
- Verifies connectivity
- Deploys infrastructure
- Sends notifications when complete

📖 DETAILED INSTRUCTIONS:
- Read README_GUI.md for full documentation
- Read DEPLOYMENT_GUIDE.md for technical details

🆘 SUPPORT:
- Check the log files if something goes wrong
- All activity is logged with timestamps
- Contact the developer if you need help

Version: 1.0
Created: 2025-01-09
EOF

# =============================================================================
# UBUNTU 20+ PACKAGE
# =============================================================================
echo "🐧 Creating Ubuntu 20+ package..."

# Copy files to Ubuntu directory
cp -r dist/ distribution_ubuntu/
cp radar_bot_gui.py distribution_ubuntu/
cp master_bot.py distribution_ubuntu/
cp script_no1.py distribution_ubuntu/
cp script_no2.py distribution_ubuntu/
cp script_no3.py distribution_ubuntu/
cp bot_config.json distribution_ubuntu/
cp requirements_gui.txt distribution_ubuntu/
cp README_GUI.md distribution_ubuntu/
cp DEPLOYMENT_GUIDE.md distribution_ubuntu/

# Create Ubuntu installation script
cat > distribution_ubuntu/INSTALL_UBUNTU.sh << 'EOF'
#!/bin/bash

# Bivicom Radar Bot - Ubuntu 20+ Installation Script
echo "🎉 Installing Bivicom Radar Bot for Ubuntu 20+..."

# Check if Python 3.7+ is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Installing..."
    sudo apt update
    sudo apt install -y python3 python3-pip python3-venv
fi

# Check Python version
PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
REQUIRED_VERSION="3.7"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python $PYTHON_VERSION is too old. Installing Python 3.8..."
    sudo apt update
    sudo apt install -y python3.8 python3.8-pip python3.8-venv
    python3.8 -m pip install --upgrade pip
    PYTHON_CMD="python3.8"
else
    PYTHON_CMD="python3"
fi

echo "✅ Python found: $PYTHON_VERSION"

# Install tkinter
echo "Installing tkinter..."
sudo apt update
sudo apt install -y python3-tk

# Create virtual environment
echo "Creating virtual environment..."
$PYTHON_CMD -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements_gui.txt

# Create desktop shortcut
echo "Creating desktop shortcut..."
cat > ~/Desktop/Bivicom\ Radar\ Bot.desktop << 'DESKTOP_EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=Bivicom Radar Bot
Comment=Device Setup Application
Exec=$PWD/LAUNCH_BIVICOM_RADAR_BOT.sh
Icon=applications-system
Terminal=false
Categories=Network;System;
DESKTOP_EOF

chmod +x ~/Desktop/Bivicom\ Radar\ Bot.desktop

# Create launcher script
echo "Creating launcher script..."
cat > LAUNCH_BIVICOM_RADAR_BOT.sh << 'LAUNCHER_EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python3 radar_bot_gui.py
LAUNCHER_EOF

chmod +x LAUNCH_BIVICOM_RADAR_BOT.sh

echo ""
echo "🎉 Installation completed successfully!"
echo ""
echo "🚀 How to launch:"
echo "1. Double-click the desktop shortcut"
echo "2. Or run: ./LAUNCH_BIVICOM_RADAR_BOT.sh"
echo "3. Or run: python3 radar_bot_gui.py"
echo ""
echo "📖 Read README_GUI.md for detailed instructions"
echo ""
echo "✅ Ready to use!"
EOF

chmod +x distribution_ubuntu/INSTALL_UBUNTU.sh

# Create Ubuntu README
cat > distribution_ubuntu/README_UBUNTU.txt << 'EOF'
🎉 Bivicom Radar Bot - Ubuntu 20+ Installation
==============================================

This is a standalone GUI application for setting up Bivicom Radar devices on Ubuntu 20+.

🚀 QUICK START:
1. Run: ./INSTALL_UBUNTU.sh
2. Follow the installation prompts
3. Launch using desktop shortcut or: ./LAUNCH_BIVICOM_RADAR_BOT.sh
4. Click "Start Bot" to begin device setup

📋 REQUIREMENTS:
- Ubuntu 20.04 or higher
- Python 3.7 or higher
- Network access to 192.168.1.1
- SSH access with admin/admin credentials

🎯 WHAT IT DOES:
- Automatically configures network settings
- Verifies connectivity
- Deploys infrastructure
- Sends notifications when complete

📖 DETAILED INSTRUCTIONS:
- Read README_GUI.md for full documentation
- Read DEPLOYMENT_GUIDE.md for technical details

🆘 SUPPORT:
- Check the log files if something goes wrong
- All activity is logged with timestamps
- Contact the developer if you need help

Version: 1.0
Created: 2025-01-09
EOF

# =============================================================================
# MACOS PACKAGE (Updated)
# =============================================================================
echo "🍎 Creating macOS package..."

# Copy files to macOS directory
cp -r dist/ distribution_macos/
cp radar_bot_gui.py distribution_macos/
cp master_bot.py distribution_macos/
cp script_no1.py distribution_macos/
cp script_no2.py distribution_macos/
cp script_no3.py distribution_macos/
cp bot_config.json distribution_macos/
cp requirements_gui.txt distribution_macos/
cp README_GUI.md distribution_macos/
cp DEPLOYMENT_GUIDE.md distribution_macos/

# Create macOS installation script
cat > distribution_macos/INSTALL_MACOS.sh << 'EOF'
#!/bin/bash

# Bivicom Radar Bot - macOS Installation Script
echo "🎉 Installing Bivicom Radar Bot for macOS..."

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
    brew install python-tk
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
EOF

chmod +x distribution_macos/INSTALL_MACOS.sh

# Create macOS README
cat > distribution_macos/README_MACOS.txt << 'EOF'
🎉 Bivicom Radar Bot - macOS Installation
=========================================

This is a standalone GUI application for setting up Bivicom Radar devices on macOS.

🚀 QUICK START:
1. Run: ./INSTALL_MACOS.sh
2. Follow the installation prompts
3. Launch from desktop shortcut or Applications folder
4. Click "Start Bot" to begin device setup

📋 REQUIREMENTS:
- macOS 10.13 or higher
- Python 3.7 or higher
- Network access to 192.168.1.1
- SSH access with admin/admin credentials

🎯 WHAT IT DOES:
- Automatically configures network settings
- Verifies connectivity
- Deploys infrastructure
- Sends notifications when complete

📖 DETAILED INSTRUCTIONS:
- Read README_GUI.md for full documentation
- Read DEPLOYMENT_GUIDE.md for technical details

🆘 SUPPORT:
- Check the log files if something goes wrong
- All activity is logged with timestamps
- Contact the developer if you need help

Version: 1.0
Created: 2025-01-09
EOF

# Create ZIP files for each platform
echo "📦 Creating ZIP files..."

# Windows ZIP
cd distribution_windows
zip -r "../BivicomRadarBot_Windows11.zip" . -x "*.pyc" "__pycache__/*"
cd ..

# Ubuntu ZIP
cd distribution_ubuntu
zip -r "../BivicomRadarBot_Ubuntu20+.zip" . -x "*.pyc" "__pycache__/*"
cd ..

# macOS ZIP
cd distribution_macos
zip -r "../BivicomRadarBot_macOS.zip" . -x "*.pyc" "__pycache__/*"
cd ..

echo ""
echo "✅ Multi-platform distribution packages created successfully!"
echo ""
echo "📦 Package contents:"
echo "   🪟 Windows 11: BivicomRadarBot_Windows11.zip"
echo "   🐧 Ubuntu 20+: BivicomRadarBot_Ubuntu20+.zip"
echo "   🍎 macOS: BivicomRadarBot_macOS.zip"
echo ""
echo "📤 How to send to your friend:"
echo "1. Send the appropriate ZIP file for their operating system"
echo "2. Tell them to extract it and run the installation script"
echo "3. Each package includes platform-specific instructions"
echo ""
echo "🎁 Your friend will have everything they need for their platform!"
