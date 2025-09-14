#!/bin/bash
# Build standalone executables for Linux, macOS, and Windows

echo "🔨 Building standalone executables..."

# Create build directory
mkdir -p dist/standalone

# Build for current platform (Linux/macOS)
echo "📦 Building for current platform..."
pyinstaller --onefile --windowed \
    --name="Bivicom-Configurator" \
    --add-data="network_config.sh:." \
    --add-data="requirements.txt:." \
    --add-data="LICENSE:." \
    --add-data="uploaded_files:uploaded_files" \
    --hidden-import="tkinter" \
    --hidden-import="paramiko" \
    --hidden-import="plyer" \
    gui_enhanced.py

# Move to dist directory
mv dist/Bivicom-Configurator* dist/standalone/ 2>/dev/null || true

echo "✅ Standalone executable created in dist/standalone/"
echo "📁 Files included:"
echo "   - Bivicom-Configurator (executable)"
echo "   - network_config.sh (configuration script)"
echo "   - requirements.txt (dependencies list)"
echo "   - LICENSE (license file)"
echo "   - uploaded_files/ (file upload directory)"
