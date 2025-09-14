# 🧪 Testing the Build System

This guide shows how to test the standalone application build system.

## 📋 Pre-Test Checklist

### 1. Verify Prerequisites
```bash
# Check Python version (3.8+ required)
python3 --version

# Check if PyInstaller is installed
pip list | grep pyinstaller

# If not installed:
pip install pyinstaller

# Verify all dependencies
pip install -r requirements.txt
```

### 2. Test GUI Application First
```bash
# Test the GUI works before building
python3 gui_enhanced.py
```
**Expected:** GUI should open without errors

## 🔧 Build Testing Steps

### Step 1: Test Quick Build
```bash
# Make script executable
chmod +x build_standalone.sh

# Run quick build
./build_standalone.sh
```

**Expected Output:**
```
🔨 Building standalone executables...
📦 Building for current platform...
✅ Standalone executable created in dist/standalone/
📁 Files included:
   - Bivicom-Configurator (executable)
   - network_config.sh (configuration script)
   - requirements.txt (dependencies list)
   - LICENSE (license file)
   - uploaded_files/ (file upload directory)
```

### Step 2: Test Cross-Platform Build
```bash
# Make script executable
chmod +x build_cross_platform.sh

# Run comprehensive build
./build_cross_platform.sh
```

**Expected Output:**
```
🌍 Cross-Platform Standalone App Builder
========================================
✅ Virtual environment detected: /path/to/venv
📦 Installing PyInstaller...
🔨 Building standalone executable...
📦 Creating installation package...
🗜️  Creating archive...
✅ Build completed!
📁 Output files:
   - Executable: dist/linux/Bivicom-Configurator*
   - Package: dist/Bivicom-Configurator-linux.tar.gz
   - Package directory: dist/Bivicom-Configurator-linux/
```

### Step 3: Verify Build Output
```bash
# Check if files were created
ls -la dist/

# Check package contents
tar -tzf dist/Bivicom-Configurator-linux.tar.gz

# Check executable permissions
ls -la dist/linux/Bivicom-Configurator*
```

## 🧪 Functional Testing

### Test 1: Executable Runs
```bash
# Test the standalone executable
cd dist/linux/
./Bivicom-Configurator
```

**Expected:** GUI should open (same as Python version)

### Test 2: File Structure
```bash
# Verify all required files are present
ls -la dist/linux/
```

**Required Files:**
- ✅ `Bivicom-Configurator` (executable)
- ✅ `network_config.sh` (configuration script)
- ✅ `requirements.txt` (dependencies list)
- ✅ `LICENSE` (license file)
- ✅ `uploaded_files/` (directory)
- ✅ `README.txt` (usage instructions)

### Test 3: Network Script Works
```bash
# Test network script is executable
chmod +x network_config.sh

# Test help command
./network_config.sh --help
```

**Expected:** Help text should display

### Test 4: File Upload Feature
```bash
# Test uploaded_files directory
ls -la uploaded_files/
```

**Expected:** Should contain flows.json and package.json

## 🐛 Troubleshooting Tests

### Test 1: Missing Dependencies
```bash
# Check for missing imports
python3 -c "import tkinter, paramiko, plyer; print('All imports OK')"
```

### Test 2: PyInstaller Issues
```bash
# Test PyInstaller with debug
pyinstaller --onefile --debug=all \
    --name="Bivicom-Configurator-Test" \
    gui_enhanced.py
```

### Test 3: File Size Check
```bash
# Check executable size
ls -lh dist/linux/Bivicom-Configurator
```

**Expected:** Should be reasonable size (50-200MB typical)

## 🔍 Advanced Testing

### Test 1: Clean System Test
```bash
# Test on system without Python (if possible)
# Or test in Docker container without Python
docker run -it --rm -v $(pwd)/dist:/app ubuntu:20.04
cd /app/linux/
./Bivicom-Configurator
```

### Test 2: Different Python Versions
```bash
# Test with different Python versions
python3.8 gui_enhanced.py
python3.9 gui_enhanced.py
python3.10 gui_enhanced.py
python3.11 gui_enhanced.py
```

### Test 3: Memory Usage
```bash
# Monitor memory usage during build
/usr/bin/time -v ./build_standalone.sh
```

## 📊 Test Results Template

### Build Test Results
```
✅ Quick Build: PASS/FAIL
✅ Cross-Platform Build: PASS/FAIL
✅ Executable Creation: PASS/FAIL
✅ File Structure: PASS/FAIL
✅ GUI Launch: PASS/FAIL
✅ Network Script: PASS/FAIL
✅ File Upload: PASS/FAIL
```

### Performance Metrics
```
📊 Executable Size: ___ MB
📊 Build Time: ___ seconds
📊 Memory Usage: ___ MB
📊 Dependencies: ___ packages
```

## 🚀 Automated Testing Script

Create a test script to automate testing:

```bash
#!/bin/bash
# test_build.sh - Automated build testing

echo "🧪 Starting Build Tests..."

# Test 1: Prerequisites
echo "📋 Testing prerequisites..."
python3 --version || { echo "❌ Python not found"; exit 1; }
pip list | grep pyinstaller || { echo "❌ PyInstaller not found"; exit 1; }
echo "✅ Prerequisites OK"

# Test 2: GUI Test
echo "🖥️ Testing GUI..."
timeout 10s python3 gui_enhanced.py &
GUI_PID=$!
sleep 5
kill $GUI_PID 2>/dev/null
echo "✅ GUI Test OK"

# Test 3: Build Test
echo "🔨 Testing build..."
./build_standalone.sh || { echo "❌ Build failed"; exit 1; }
echo "✅ Build Test OK"

# Test 4: Executable Test
echo "🚀 Testing executable..."
cd dist/linux/
timeout 10s ./Bivicom-Configurator &
EXE_PID=$!
sleep 5
kill $EXE_PID 2>/dev/null
echo "✅ Executable Test OK"

echo "🎉 All tests passed!"
```

## 📝 Test Report Template

### Test Environment
- **OS:** Linux/macOS/Windows
- **Python Version:** 3.x.x
- **PyInstaller Version:** x.x.x
- **Build Date:** YYYY-MM-DD

### Test Results
- **Build Success:** ✅/❌
- **Executable Size:** ___ MB
- **Build Time:** ___ seconds
- **GUI Launch:** ✅/❌
- **Network Script:** ✅/❌
- **File Upload:** ✅/❌

### Issues Found
- [ ] Issue 1: Description
- [ ] Issue 2: Description

### Recommendations
- [ ] Recommendation 1
- [ ] Recommendation 2
