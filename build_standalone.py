#!/usr/bin/env python3
"""
Build Script for Bivicom Radar Bot Standalone Executable
========================================================

This script creates standalone executables for Windows and macOS using PyInstaller.
The executable will include all dependencies and can run without Python installation.

Usage:
    python build_standalone.py [--platform windows|mac|all]

Author: AI Assistant
Date: 2025-01-09
"""

import os
import sys
import subprocess
import platform
import shutil
import argparse
from pathlib import Path

class StandaloneBuilder:
    def __init__(self):
        self.project_dir = Path(__file__).parent
        self.dist_dir = self.project_dir / "dist"
        self.build_dir = self.project_dir / "build"
        self.spec_file = self.project_dir / "radar_bot_gui.spec"
        
        # Required files for the executable
        self.required_files = [
            "radar_bot_gui.py",
            "master_bot.py", 
            "script_no1.py",
            "script_no2.py",
            "script_no3.py",
            "bot_config.json"
        ]
        
        # Additional data files
        self.data_files = [
            ("bot_config.json", "."),
        ]
        
    def check_requirements(self):
        """Check if all required files and tools are available"""
        print("Checking requirements...")
        
        # Check required files
        missing_files = []
        for file in self.required_files:
            if not (self.project_dir / file).exists():
                missing_files.append(file)
        
        if missing_files:
            print(f"❌ Missing required files: {', '.join(missing_files)}")
            return False
        
        # Check PyInstaller
        try:
            import PyInstaller
            print(f"✅ PyInstaller found: {PyInstaller.__version__}")
        except ImportError:
            print("❌ PyInstaller not found. Installing...")
            subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
            print("✅ PyInstaller installed")
        
        # Check other dependencies
        try:
            import paramiko
            print("✅ paramiko found")
        except ImportError:
            print("❌ paramiko not found. Installing...")
            subprocess.run([sys.executable, "-m", "pip", "install", "paramiko"], check=True)
            print("✅ paramiko installed")
        
        return True
    
    def create_spec_file(self, platform_name: str):
        """Create PyInstaller spec file"""
        print(f"Creating spec file for {platform_name}...")
        
        # Determine executable name and icon
        if platform_name == "windows":
            exe_name = "BivicomRadarBot.exe"
            icon_file = None  # You can add an icon file if available
        else:
            exe_name = "BivicomRadarBot"
            icon_file = None
        
        # Create spec file content
        spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['radar_bot_gui.py'],
    pathex=['{self.project_dir}'],
    binaries=[
        ('/System/Library/Frameworks/Tk.framework', 'Tk.framework'),
        ('/System/Library/Frameworks/Tcl.framework', 'Tcl.framework'),
    ],
    datas={self.data_files},
    hiddenimports=[
        'paramiko',
        'tkinter',
        'tkinter.ttk',
        'tkinter.scrolledtext',
        'tkinter.messagebox',
        'tkinter.filedialog',
        'tkinter.simpledialog',
        '_tkinter',
        'threading',
        'queue',
        'subprocess',
        'signal',
        'json',
        'time',
        'datetime',
        'ipaddress',
        'concurrent.futures',
        'socket',
        're'
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{exe_name}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon={f"'{icon_file}'" if icon_file else None},
)
'''
        
        # Write spec file
        with open(self.spec_file, 'w') as f:
            f.write(spec_content)
        
        print(f"✅ Spec file created: {self.spec_file}")
    
    def build_executable(self, platform_name: str):
        """Build the standalone executable"""
        print(f"Building executable for {platform_name}...")
        
        # Clean previous builds
        if self.dist_dir.exists():
            shutil.rmtree(self.dist_dir)
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
        
        # Create spec file
        self.create_spec_file(platform_name)
        
        # Build command
        build_cmd = [
            sys.executable, "-m", "PyInstaller",
            "--clean",
            "--noconfirm",
            str(self.spec_file)
        ]
        
        print(f"Running: {' '.join(build_cmd)}")
        
        try:
            result = subprocess.run(build_cmd, cwd=self.project_dir, check=True, 
                                  capture_output=True, text=True)
            print("✅ Build completed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Build failed: {e}")
            print(f"stdout: {e.stdout}")
            print(f"stderr: {e.stderr}")
            return False
    
    def create_installer_script(self, platform_name: str):
        """Create installer script for the executable"""
        if platform_name == "windows":
            self.create_windows_installer()
        elif platform_name == "mac":
            self.create_mac_installer()
    
    def create_windows_installer(self):
        """Create Windows installer script"""
        installer_script = self.project_dir / "install_windows.bat"
        
        script_content = '''@echo off
echo Installing Bivicom Radar Bot...
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Running with administrator privileges.
) else (
    echo This script requires administrator privileges.
    echo Please run as administrator.
    pause
    exit /b 1
)

REM Create installation directory
set "INSTALL_DIR=%ProgramFiles%\\BivicomRadarBot"
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

REM Copy executable
copy "BivicomRadarBot.exe" "%INSTALL_DIR%\\"

REM Create desktop shortcut
set "DESKTOP=%USERPROFILE%\\Desktop"
echo [InternetShortcut] > "%DESKTOP%\\Bivicom Radar Bot.url"
echo URL=file:///%INSTALL_DIR%\\BivicomRadarBot.exe >> "%DESKTOP%\\Bivicom Radar Bot.url"
echo IconFile=%INSTALL_DIR%\\BivicomRadarBot.exe >> "%DESKTOP%\\Bivicom Radar Bot.url"
echo IconIndex=0 >> "%DESKTOP%\\Bivicom Radar Bot.url"

echo.
echo Installation completed successfully!
echo Desktop shortcut created.
echo.
pause
'''
        
        with open(installer_script, 'w') as f:
            f.write(script_content)
        
        print(f"✅ Windows installer script created: {installer_script}")
    
    def create_mac_installer(self):
        """Create macOS installer script"""
        installer_script = self.project_dir / "install_mac.sh"
        
        script_content = '''#!/bin/bash

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
'''
        
        with open(installer_script, 'w') as f:
            f.write(script_content)
        
        # Make script executable
        os.chmod(installer_script, 0o755)
        
        print(f"✅ macOS installer script created: {installer_script}")
    
    def create_readme(self, platform_name: str):
        """Create README file for the standalone executable"""
        readme_file = self.dist_dir / "README.txt"
        
        readme_content = f'''Bivicom Radar Bot - Standalone Application
==========================================

This is a standalone version of the Bivicom Radar Bot that can run without 
Python installation.

Platform: {platform_name.title()}
Build Date: {subprocess.run(['date'], capture_output=True, text=True).stdout.strip()}

INSTALLATION:
1. Run the installer script (install_{platform_name}.bat/sh)
2. Or simply run the executable directly

USAGE:
1. Launch the application
2. Click "Start Bot" to begin device setup
3. Monitor the progress in the log window
4. You'll receive a notification when setup completes

FEATURES:
- Real-time log display with color-coded messages
- Progress indicators for device setup
- System notifications when setup completes
- Graceful exit handling
- Cross-platform compatibility

REQUIREMENTS:
- Network access to 192.168.1.1
- SSH access with admin/admin credentials
- Target device must be reachable

TROUBLESHOOTING:
- If the application doesn't start, try running as administrator
- Check that the target device is reachable at 192.168.1.1
- Ensure SSH credentials are correct (admin/admin)
- Check firewall settings

SUPPORT:
For technical support, contact the development team.

Version: 1.0
'''
        
        with open(readme_file, 'w') as f:
            f.write(readme_content)
        
        print(f"✅ README created: {readme_file}")
    
    def build_platform(self, platform_name: str):
        """Build executable for specific platform"""
        print(f"\n{'='*60}")
        print(f"Building for {platform_name.upper()}")
        print(f"{'='*60}")
        
        if not self.check_requirements():
            return False
        
        if not self.build_executable(platform_name):
            return False
        
        # Create installer script
        self.create_installer_script(platform_name)
        
        # Create README
        self.create_readme(platform_name)
        
        # Show results
        exe_name = "BivicomRadarBot.exe" if platform_name == "windows" else "BivicomRadarBot"
        exe_path = self.dist_dir / exe_name
        
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"\n✅ Build completed successfully!")
            print(f"📁 Executable: {exe_path}")
            print(f"📊 Size: {size_mb:.1f} MB")
            print(f"🚀 Ready to distribute!")
        else:
            print(f"❌ Executable not found: {exe_path}")
            return False
        
        return True
    
    def build_all(self):
        """Build for all platforms"""
        current_platform = platform.system().lower()
        
        if current_platform == "windows":
            platforms = ["windows"]
        elif current_platform == "darwin":
            platforms = ["mac"]
        else:
            platforms = ["linux"]
        
        success = True
        for platform_name in platforms:
            if not self.build_platform(platform_name):
                success = False
        
        return success

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Build standalone executable for Bivicom Radar Bot")
    parser.add_argument("--platform", choices=["windows", "mac", "all"], 
                       default="all", help="Platform to build for")
    
    args = parser.parse_args()
    
    builder = StandaloneBuilder()
    
    if args.platform == "all":
        success = builder.build_all()
    else:
        success = builder.build_platform(args.platform)
    
    if success:
        print(f"\n🎉 All builds completed successfully!")
        sys.exit(0)
    else:
        print(f"\n❌ Build failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
