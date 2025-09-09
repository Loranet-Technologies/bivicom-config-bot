#!/bin/bash

# Bivicom Bot Installer - Simple Build Script
# ===========================================

echo "🚀 Building Bivicom Bot Installer..."

# Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "❌ This build script is for macOS only"
    exit 1
fi

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install requirements
echo "📥 Installing requirements..."
pip install --upgrade pip
pip install -r requirements.txt

# Build executable
echo "🔨 Building executable..."
pyinstaller --onefile --windowed \
    --name="Bivicom Configurator V1" \
    --add-data="config.json:." \
    --add-data="LICENSE:." \
    gui.py

# Clean up
echo "🧹 Cleaning up..."
deactivate
rm -rf venv

echo "✅ Build complete!"
echo "📦 Executable: dist/Bivicom Configurator V1"
echo "📦 App bundle: dist/Bivicom Configurator V1.app"
