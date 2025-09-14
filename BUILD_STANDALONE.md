# 🚀 Building Standalone Applications

This guide shows how to create standalone executables that don't require Python installation.

## 📋 Prerequisites

### For All Platforms:
```bash
# Install PyInstaller
pip install pyinstaller

# Install all dependencies
pip install -r requirements.txt
```

### Platform-Specific Requirements:

**Linux:**
- Python 3.8+
- tkinter (usually included with Python)
- Build tools: `sudo apt-get install build-essential`

**macOS:**
- Python 3.8+
- Xcode Command Line Tools: `xcode-select --install`
- tkinter (usually included with Python)

**Windows:**
- Python 3.8+
- Visual Studio Build Tools or Visual Studio Community
- tkinter (usually included with Python)

## 🔧 Build Methods

### Method 1: Quick Build (Current Platform)
```bash
# Run the simple build script
./build_standalone.sh
```

### Method 2: Cross-Platform Build
```bash
# Run the comprehensive build script
./build_cross_platform.sh
```

### Method 3: Windows Build
```cmd
# On Windows, run the batch file
build_windows.bat
```

### Method 4: Manual PyInstaller Command
```bash
# Basic standalone build
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
```

## 📦 Output Structure

After building, you'll get:

```
dist/
├── Bivicom-Configurator-linux/
│   ├── Bivicom-Configurator          # Linux executable
│   ├── network_config.sh             # Configuration script
│   ├── requirements.txt              # Dependencies list
│   ├── LICENSE                       # License file
│   ├── uploaded_files/               # File upload directory
│   └── README.txt                    # Usage instructions
├── Bivicom-Configurator-macos/
│   ├── Bivicom-Configurator          # macOS executable
│   └── ... (same files as Linux)
└── Bivicom-Configurator-windows/
    ├── Bivicom-Configurator.exe      # Windows executable
    └── ... (same files as Linux)
```

## 🌍 Cross-Platform Distribution

### For Linux:
1. Build on Linux: `./build_cross_platform.sh`
2. Share: `Bivicom-Configurator-linux.tar.gz`

### For macOS:
1. Build on macOS: `./build_cross_platform.sh`
2. Share: `Bivicom-Configurator-macos.tar.gz`

### For Windows:
1. Build on Windows: `build_windows.bat`
2. Share: `Bivicom-Configurator-windows.zip`

## 🎯 Advanced Options

### Smaller Executable Size:
```bash
# Use UPX compression (install UPX first)
pyinstaller --onefile --windowed --upx-dir=/path/to/upx \
    --name="Bivicom-Configurator" \
    gui_enhanced.py
```

### Console Version (for debugging):
```bash
# Remove --windowed flag to show console
pyinstaller --onefile \
    --name="Bivicom-Configurator-Console" \
    gui_enhanced.py
```

### Custom Icon:
```bash
# Add custom icon
pyinstaller --onefile --windowed \
    --icon=icon.ico \
    --name="Bivicom-Configurator" \
    gui_enhanced.py
```

## 🔍 Troubleshooting

### Common Issues:

**1. "No module named 'tkinter'"**
```bash
# Ubuntu/Debian
sudo apt-get install python3-tk

# CentOS/RHEL
sudo yum install tkinter
```

**2. "Permission denied" on executable**
```bash
chmod +x Bivicom-Configurator
```

**3. Large file size**
- Use `--exclude-module` to exclude unused modules
- Use UPX compression
- Consider using `--onedir` instead of `--onefile`

**4. Windows antivirus false positive**
- Sign the executable with a code signing certificate
- Submit to antivirus vendors for whitelisting

### Debug Mode:
```bash
# Build with debug information
pyinstaller --onefile --debug=all \
    --name="Bivicom-Configurator-Debug" \
    gui_enhanced.py
```

## 📋 Distribution Checklist

- [ ] Test executable on target platform
- [ ] Verify all dependencies are included
- [ ] Test network_config.sh script functionality
- [ ] Verify file upload feature works
- [ ] Check GUI responsiveness
- [ ] Test on clean system (no Python installed)
- [ ] Create installation package
- [ ] Write user documentation
- [ ] Test installation process

## 🚀 Quick Start for Users

1. **Download** the appropriate package for your platform
2. **Extract** the archive
3. **Run** the executable:
   - Linux/macOS: `./Bivicom-Configurator`
   - Windows: Double-click `Bivicom-Configurator.exe`
4. **Configure** your network settings in the GUI
5. **Use** the network_config.sh script for advanced operations

## 📞 Support

- **GitHub**: https://github.com/Loranet-Technologies/bivicom-config-bot
- **Issues**: Report problems in the GitHub issues section
- **Documentation**: See README.md for detailed usage instructions
