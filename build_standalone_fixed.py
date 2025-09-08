#!/usr/bin/env python3
"""
Fixed Build Script for Bivicom Radar Bot Standalone Executable
=============================================================

This script creates a standalone executable that properly includes tkinter
and all dependencies for macOS.

Author: AI Assistant
Date: 2025-01-09
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path

def build_standalone():
    """Build standalone executable with proper tkinter support"""
    print("Building Bivicom Radar Bot Standalone Executable...")
    print("=" * 60)
    
    # Clean previous builds
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    if os.path.exists("build"):
        shutil.rmtree("build")
    
    # PyInstaller command with proper tkinter support
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",  # Create single executable file
        "--windowed",  # No console window (GUI app)
        "--name", "BivicomRadarBot",
        "--add-data", "bot_config.json:.",
        "--hidden-import", "tkinter",
        "--hidden-import", "tkinter.ttk",
        "--hidden-import", "tkinter.scrolledtext",
        "--hidden-import", "tkinter.messagebox",
        "--hidden-import", "tkinter.filedialog",
        "--hidden-import", "_tkinter",
        "--hidden-import", "paramiko",
        "--hidden-import", "threading",
        "--hidden-import", "queue",
        "--hidden-import", "subprocess",
        "--hidden-import", "signal",
        "--hidden-import", "json",
        "--hidden-import", "time",
        "--hidden-import", "datetime",
        "--hidden-import", "ipaddress",
        "--hidden-import", "concurrent.futures",
        "--hidden-import", "socket",
        "--hidden-import", "re",
        "--collect-all", "tkinter",  # Collect all tkinter modules
        "--collect-all", "paramiko",  # Collect all paramiko modules
        "radar_bot_gui.py"
    ]
    
    print(f"Running: {' '.join(cmd)}")
    print()
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ Build completed successfully!")
        
        # Check if executable was created
        exe_path = Path("dist/BivicomRadarBot")
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"📁 Executable: {exe_path}")
            print(f"📊 Size: {size_mb:.1f} MB")
            print(f"🚀 Ready to distribute!")
            
            # Test the executable
            print("\nTesting executable...")
            test_result = subprocess.run([str(exe_path), "--help"], 
                                       capture_output=True, text=True, timeout=10)
            if test_result.returncode == 0:
                print("✅ Executable test passed!")
            else:
                print("⚠️  Executable test had issues, but file was created")
            
            return True
        else:
            print("❌ Executable not found!")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Build error: {e}")
        return False

def create_launcher_script():
    """Create a simple launcher script"""
    launcher_content = '''#!/bin/bash

# Bivicom Radar Bot Launcher
echo "Starting Bivicom Radar Bot..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Run the executable
./BivicomRadarBot
'''
    
    with open("dist/launch.sh", "w") as f:
        f.write(launcher_content)
    
    os.chmod("dist/launch.sh", 0o755)
    print("✅ Launcher script created: dist/launch.sh")

def create_readme():
    """Create README for the standalone executable"""
    readme_content = '''Bivicom Radar Bot - Standalone Application
==========================================

This is a standalone version of the Bivicom Radar Bot GUI.

USAGE:
1. Run: ./BivicomRadarBot
2. Or use the launcher: ./launch.sh

FEATURES:
- Real-time log display with color-coded messages
- Progress indicators for device setup
- System notifications when setup completes
- Cross-platform compatibility

REQUIREMENTS:
- Network access to 192.168.1.1
- SSH access with admin/admin credentials
- Target device must be reachable

TROUBLESHOOTING:
- If the application doesn't start, try running as administrator
- Check that the target device is reachable at 192.168.1.1
- Ensure SSH credentials are correct (admin/admin)

Version: 1.0
'''
    
    with open("dist/README.txt", "w") as f:
        f.write(readme_content)
    
    print("✅ README created: dist/README.txt")

def main():
    """Main function"""
    print("Bivicom Radar Bot - Standalone Build Script")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not os.path.exists("radar_bot_gui.py"):
        print("❌ Error: radar_bot_gui.py not found!")
        print("Please run this script from the bivicom-radar-bot directory")
        sys.exit(1)
    
    # Build the executable
    if build_standalone():
        create_launcher_script()
        create_readme()
        
        print("\n🎉 Build completed successfully!")
        print("📁 Files created:")
        print("   - dist/BivicomRadarBot (main executable)")
        print("   - dist/launch.sh (launcher script)")
        print("   - dist/README.txt (documentation)")
        print("\n🚀 Ready to distribute!")
    else:
        print("\n❌ Build failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
