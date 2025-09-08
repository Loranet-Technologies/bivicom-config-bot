#!/bin/bash

# Create Multi-Platform Distribution Packages for Bivicom Radar Bot
echo "🚀 Creating multi-platform distribution packages..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Create releases directory
RELEASES_DIR="releases"
rm -rf "$RELEASES_DIR"
mkdir -p "$RELEASES_DIR"

echo "📦 Creating distribution packages in: $RELEASES_DIR"

# Function to create platform-specific package
create_platform_package() {
    local platform=$1
    local platform_dir="$RELEASES_DIR/bivicom-radar-bot-$platform"
    
    echo "🔨 Creating $platform package..."
    mkdir -p "$platform_dir"
    
    # Copy common files
    cp master_bot.py "$platform_dir/"
    cp script_no1.py "$platform_dir/"
    cp script_no2.py "$platform_dir/"
    cp script_no3.py "$platform_dir/"
    cp radar_bot_gui.py "$platform_dir/"
    cp bot_config.json "$platform_dir/"
    cp requirements.txt "$platform_dir/"
    cp requirements_gui.txt "$platform_dir/"
    cp COMPLETE_DOCUMENTATION.md "$platform_dir/"
    cp LICENSE "$platform_dir/"
    
    # Create platform-specific installation script
    case $platform in
        "windows")
            create_windows_installer "$platform_dir"
            ;;
        "linux")
            create_linux_installer "$platform_dir"
            ;;
        "macos")
            create_macos_installer "$platform_dir"
            ;;
    esac
    
    # Create ZIP file
    echo "📦 Creating $platform ZIP file..."
    cd "$platform_dir"
    zip -r "../bivicom-radar-bot-$platform-v1.0.zip" . -x "*.pyc" "__pycache__/*"
    cd "$SCRIPT_DIR"
    
    echo "✅ $platform package created: bivicom-radar-bot-$platform-v1.0.zip"
}

# Windows installer
create_windows_installer() {
    local dir=$1
    cat > "$dir/INSTALL.bat" << 'EOF'
@echo off
echo 🎉 Installing Bivicom Radar Bot for Windows...

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed. Please install Python 3.7 or higher.
    echo Download from: https://www.python.org/downloads/
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
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\Bivicom Radar Bot.lnk'); $Shortcut.TargetPath = 'python'; $Shortcut.Arguments = 'radar_bot_gui.py'; $Shortcut.WorkingDirectory = '%CD%'; $Shortcut.IconLocation = 'python.exe,0'; $Shortcut.Save()"

echo.
echo 🎉 Installation completed successfully!
echo.
echo 🖥️  Desktop shortcut created: Bivicom Radar Bot
echo.
echo 🚀 How to launch:
echo 1. Double-click the desktop shortcut
echo 2. Or run: python radar_bot_gui.py
echo.
echo 📖 Read COMPLETE_DOCUMENTATION.md for detailed instructions
echo.
echo ✅ Ready to use!
pause
EOF

    cat > "$dir/README_WINDOWS.txt" << 'EOF'
🎉 Bivicom Radar Bot - Windows Installation
==========================================

🚀 QUICK START:
1. Run: INSTALL.bat
2. Follow the installation prompts
3. Launch from desktop shortcut
4. Click "Start Bot" to begin device setup

📋 REQUIREMENTS:
- Windows 10 or higher
- Python 3.7 or higher
- Network access to 192.168.1.1
- SSH access with admin/admin credentials

🎯 WHAT IT DOES:
- Automatically configures network settings
- Verifies connectivity
- Deploys infrastructure
- Sends notifications when complete

📖 DETAILED INSTRUCTIONS:
- Read COMPLETE_DOCUMENTATION.md for full documentation
- All technical details and GUI instructions included

🆘 SUPPORT:
- Check the log files if something goes wrong
- All activity is logged with timestamps
- Contact the developer if you need help

Version: 1.0
Created: 2025-01-09
EOF
}

# Linux installer
create_linux_installer() {
    local dir=$1
    cat > "$dir/INSTALL.sh" << 'EOF'
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
echo "📖 Read COMPLETE_DOCUMENTATION.md for detailed instructions"
echo ""
echo "✅ Ready to use!"
EOF

    chmod +x "$dir/INSTALL.sh"

    cat > "$dir/README_LINUX.txt" << 'EOF'
🎉 Bivicom Radar Bot - Linux Installation
=========================================

🚀 QUICK START:
1. Run: ./INSTALL.sh
2. Follow the installation prompts
3. Launch from desktop shortcut
4. Click "Start Bot" to begin device setup

📋 REQUIREMENTS:
- Linux (Ubuntu, CentOS, Fedora, etc.)
- Python 3.7 or higher
- Network access to 192.168.1.1
- SSH access with admin/admin credentials

🎯 WHAT IT DOES:
- Automatically configures network settings
- Verifies connectivity
- Deploys infrastructure
- Sends notifications when complete

📖 DETAILED INSTRUCTIONS:
- Read COMPLETE_DOCUMENTATION.md for full documentation
- All technical details and GUI instructions included

🆘 SUPPORT:
- Check the log files if something goes wrong
- All activity is logged with timestamps
- Contact the developer if you need help

Version: 1.0
Created: 2025-01-09
EOF
}

# macOS installer
create_macos_installer() {
    local dir=$1
    cat > "$dir/INSTALL.sh" << 'EOF'
#!/bin/bash

# Bivicom Radar Bot - macOS Installation Script
echo "🎉 Installing Bivicom Radar Bot for macOS..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if Python 3.7+ is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.7 or higher."
    echo "Download from: https://www.python.org/downloads/"
    echo "Or install via Homebrew: brew install python3"
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
    if command -v brew &> /dev/null; then
        brew install python-tk
    else
        echo "❌ Please install tkinter. Consider installing Homebrew first:"
        echo "/bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)\""
        echo "Then run: brew install python-tk"
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
echo "📖 Read COMPLETE_DOCUMENTATION.md for detailed instructions"
echo ""
echo "✅ Ready to use!"
EOF

    chmod +x "$dir/INSTALL.sh"

    cat > "$dir/README_MACOS.txt" << 'EOF'
🎉 Bivicom Radar Bot - macOS Installation
=========================================

🚀 QUICK START:
1. Run: ./INSTALL.sh
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
- Read COMPLETE_DOCUMENTATION.md for full documentation
- All technical details and GUI instructions included

🆘 SUPPORT:
- Check the log files if something goes wrong
- All activity is logged with timestamps
- Contact the developer if you need help

Version: 1.0
Created: 2025-01-09
EOF
}

# Create packages for all platforms
create_platform_package "windows"
create_platform_package "linux"
create_platform_package "macos"

# Create a universal README
cat > "$RELEASES_DIR/README.txt" << 'EOF'
🎉 Bivicom Radar Bot v1.0 - Multi-Platform Release
==================================================

This release includes packages for all major operating systems:

📦 AVAILABLE PACKAGES:
- bivicom-radar-bot-windows-v1.0.zip (Windows 10+)
- bivicom-radar-bot-linux-v1.0.zip (Linux - Ubuntu, CentOS, Fedora, etc.)
- bivicom-radar-bot-macos-v1.0.zip (macOS 10.13+)

🚀 QUICK START:
1. Download the package for your operating system
2. Extract the ZIP file
3. Run the installation script:
   - Windows: Double-click INSTALL.bat
   - Linux: Run ./INSTALL.sh
   - macOS: Run ./INSTALL.sh
4. Launch the application and click "Start Bot"

📋 REQUIREMENTS:
- Python 3.7 or higher
- Network access to 192.168.1.1
- SSH access with admin/admin credentials
- Target devices must be Bivicom-compatible

🎯 WHAT IT DOES:
- Automatically configures network settings
- Verifies connectivity
- Deploys infrastructure
- Sends notifications when complete

📖 DOCUMENTATION:
- COMPLETE_DOCUMENTATION.md: Comprehensive guide with all information
- Platform-specific README files for installation help

🆘 SUPPORT:
- Check the log files if something goes wrong
- All activity is logged with timestamps
- Contact the developer if you need help

Version: 1.0
Release Date: 2025-01-09
Author: Aqmar - Loranet Technologies
License: MIT
EOF

echo ""
echo "✅ Multi-platform distribution packages created successfully!"
echo ""
echo "📦 Package contents:"
echo "   - bivicom-radar-bot-windows-v1.0.zip"
echo "   - bivicom-radar-bot-linux-v1.0.zip"
echo "   - bivicom-radar-bot-macos-v1.0.zip"
echo "   - README.txt (universal instructions)"
echo ""
echo "📤 Ready for distribution to all platforms!"
