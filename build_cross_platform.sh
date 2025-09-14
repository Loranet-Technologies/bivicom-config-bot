#!/bin/bash
# Cross-platform build script for Linux, macOS, and Windows

echo "🌍 Cross-Platform Standalone App Builder"
echo "========================================"

# Check if we're in a virtual environment
if [[ "$VIRTUAL_ENV" != "" ]]; then
    echo "✅ Virtual environment detected: $VIRTUAL_ENV"
else
    echo "⚠️  No virtual environment detected. Creating one..."
    python3 -m venv build_env
    source build_env/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    pip install pyinstaller
fi

# Install PyInstaller if not present
if ! command -v pyinstaller &> /dev/null; then
    echo "📦 Installing PyInstaller..."
    pip install pyinstaller
fi

# Create build directories
mkdir -p dist/{linux,macos,windows}
mkdir -p build_assets

# Copy required files
cp network_config.sh build_assets/
cp requirements.txt build_assets/
cp LICENSE build_assets/
cp -r uploaded_files build_assets/

echo "🔨 Building standalone executable..."

# Build the executable
pyinstaller --onefile --windowed \
    --name="Bivicom-Configurator" \
    --add-data="build_assets/network_config.sh:." \
    --add-data="build_assets/requirements.txt:." \
    --add-data="build_assets/LICENSE:." \
    --add-data="build_assets/uploaded_files:uploaded_files" \
    --hidden-import="tkinter" \
    --hidden-import="paramiko" \
    --hidden-import="plyer" \
    --hidden-import="threading" \
    --hidden-import="queue" \
    --hidden-import="subprocess" \
    --hidden-import="json" \
    --hidden-import="os" \
    --hidden-import="sys" \
    --hidden-import="time" \
    --hidden-import="datetime" \
    --hidden-import="platform" \
    --hidden-import="socket" \
    --hidden-import="ipaddress" \
    --distpath="dist/$(uname -s | tr '[:upper:]' '[:lower:]')" \
    gui_enhanced.py

# Create installation package
echo "📦 Creating installation package..."

PLATFORM=$(uname -s | tr '[:upper:]' '[:lower:]')
PACKAGE_DIR="dist/Bivicom-Configurator-${PLATFORM}"

mkdir -p "$PACKAGE_DIR"
cp "dist/${PLATFORM}/Bivicom-Configurator"* "$PACKAGE_DIR/"
cp build_assets/network_config.sh "$PACKAGE_DIR/"
cp build_assets/requirements.txt "$PACKAGE_DIR/"
cp build_assets/LICENSE "$PACKAGE_DIR/"
cp -r build_assets/uploaded_files "$PACKAGE_DIR/"

# Create README for the package
cat > "$PACKAGE_DIR/README.txt" << 'EOL'
Bivicom Configuration Manager - Standalone Application
====================================================

This is a standalone application that doesn't require Python installation.

Files included:
- Bivicom-Configurator: Main application executable
- network_config.sh: Configuration script
- requirements.txt: Dependencies list (for reference)
- LICENSE: License file
- uploaded_files/: Directory for file uploads

Usage:
1. Run the Bivicom-Configurator executable
2. Configure your network settings in the GUI
3. Use the network_config.sh script for advanced operations

Requirements:
- No Python installation required
- Works on Linux, macOS, and Windows
- Requires network access for device configuration

Support:
- GitHub: https://github.com/Loranet-Technologies/bivicom-config-bot
- Documentation: See README.md in the source repository
EOL

# Create archive
echo "🗜️  Creating archive..."
cd dist
tar -czf "Bivicom-Configurator-${PLATFORM}.tar.gz" "Bivicom-Configurator-${PLATFORM}"
cd ..

echo "✅ Build completed!"
echo "📁 Output files:"
echo "   - Executable: dist/${PLATFORM}/Bivicom-Configurator*"
echo "   - Package: dist/Bivicom-Configurator-${PLATFORM}.tar.gz"
echo "   - Package directory: dist/Bivicom-Configurator-${PLATFORM}/"

# Cleanup
rm -rf build_assets
rm -rf build

echo ""
echo "🚀 To distribute:"
echo "   1. Share the .tar.gz file for Linux/macOS"
echo "   2. For Windows, use the same process on a Windows machine"
echo "   3. Users can extract and run without Python installation"
