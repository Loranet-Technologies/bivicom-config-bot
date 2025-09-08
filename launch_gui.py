#!/usr/bin/env python3
"""
Bivicom Radar Bot GUI Launcher
==============================

Simple launcher script for the GUI application.
This script checks dependencies and launches the GUI.

Usage:
    python launch_gui.py

Author: AI Assistant
Date: 2025-01-09
"""

import sys
import os
import subprocess
import platform

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 7):
        print("❌ Python 3.7 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    
    print(f"✅ Python version: {sys.version.split()[0]}")
    return True

def check_dependencies():
    """Check if required dependencies are installed"""
    required_modules = ['tkinter', 'paramiko', 'threading', 'queue']
    missing_modules = []
    
    for module in required_modules:
        try:
            __import__(module)
            print(f"✅ {module} - OK")
        except ImportError:
            missing_modules.append(module)
            print(f"❌ {module} - Missing")
    
    if missing_modules:
        print(f"\nMissing dependencies: {', '.join(missing_modules)}")
        print("Installing missing dependencies...")
        
        # Install paramiko if missing
        if 'paramiko' in missing_modules:
            try:
                subprocess.run([sys.executable, "-m", "pip", "install", "paramiko"], check=True)
                print("✅ paramiko installed")
            except subprocess.CalledProcessError:
                print("❌ Failed to install paramiko")
                return False
        
        # Check tkinter (should be included with Python)
        if 'tkinter' in missing_modules:
            print("❌ tkinter is not available")
            print("On Linux, install python3-tk: sudo apt-get install python3-tk")
            return False
    
    return True

def check_required_files():
    """Check if all required files exist"""
    required_files = [
        'radar_bot_gui.py',
        'master_bot.py',
        'script_no1.py', 
        'script_no2.py',
        'script_no3.py',
        'bot_config.json'
    ]
    
    missing_files = []
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
        else:
            print(f"✅ {file} - Found")
    
    if missing_files:
        print(f"❌ Missing files: {', '.join(missing_files)}")
        return False
    
    return True

def launch_gui():
    """Launch the GUI application"""
    try:
        print("\n🚀 Launching Bivicom Radar Bot GUI...")
        
        # Import and run the GUI
        from radar_bot_gui import RadarBotGUI
        
        app = RadarBotGUI()
        app.run()
        
    except Exception as e:
        print(f"❌ Failed to launch GUI: {e}")
        return False
    
    return True

def main():
    """Main function"""
    print("Bivicom Radar Bot GUI Launcher")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check dependencies
    print("\nChecking dependencies...")
    if not check_dependencies():
        sys.exit(1)
    
    # Check required files
    print("\nChecking required files...")
    if not check_required_files():
        sys.exit(1)
    
    # Launch GUI
    print("\nAll checks passed!")
    if not launch_gui():
        sys.exit(1)

if __name__ == "__main__":
    main()
