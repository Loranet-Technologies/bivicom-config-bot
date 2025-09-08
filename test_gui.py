#!/usr/bin/env python3
"""
Test Script for Bivicom Radar Bot GUI
=====================================

This script tests the GUI application functionality without requiring
actual device connections.

Usage:
    python test_gui.py

Author: AI Assistant
Date: 2025-01-09
"""

import sys
import os
import time
import threading
from unittest.mock import Mock, patch

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_gui_imports():
    """Test that all GUI components can be imported"""
    print("Testing GUI imports...")
    
    try:
        import tkinter as tk
        from tkinter import ttk, scrolledtext, messagebox
        print("✅ tkinter imports - OK")
    except ImportError as e:
        print(f"❌ tkinter import failed: {e}")
        return False
    
    try:
        from radar_bot_gui import RadarBotGUI
        print("✅ RadarBotGUI import - OK")
    except ImportError as e:
        print(f"❌ RadarBotGUI import failed: {e}")
        return False
    
    return True

def test_bot_imports():
    """Test that all bot components can be imported"""
    print("Testing bot imports...")
    
    try:
        from master_bot import MasterBot
        print("✅ MasterBot import - OK")
    except ImportError as e:
        print(f"❌ MasterBot import failed: {e}")
        return False
    
    try:
        from script_no1 import ScriptNo1
        print("✅ ScriptNo1 import - OK")
    except ImportError as e:
        print(f"❌ ScriptNo1 import failed: {e}")
        return False
    
    try:
        from script_no2 import ScriptNo2
        print("✅ ScriptNo2 import - OK")
    except ImportError as e:
        print(f"❌ ScriptNo2 import failed: {e}")
        return False
    
    try:
        from script_no3 import ScriptNo3
        print("✅ ScriptNo3 import - OK")
    except ImportError as e:
        print(f"❌ ScriptNo3 import failed: {e}")
        return False
    
    return True

def test_config_file():
    """Test that config file exists and is valid"""
    print("Testing config file...")
    
    if not os.path.exists("bot_config.json"):
        print("❌ bot_config.json not found")
        return False
    
    try:
        import json
        with open("bot_config.json", 'r') as f:
            config = json.load(f)
        print("✅ bot_config.json is valid JSON")
        
        # Check required keys
        required_keys = ["network_range", "default_credentials", "target_mac_prefixes"]
        for key in required_keys:
            if key not in config:
                print(f"❌ Missing required key: {key}")
                return False
        
        print("✅ bot_config.json has required keys")
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ bot_config.json is invalid JSON: {e}")
        return False

def test_gui_creation():
    """Test GUI creation without displaying"""
    print("Testing GUI creation...")
    
    try:
        # Mock tkinter to avoid displaying window
        with patch('tkinter.Tk') as mock_tk:
            mock_root = Mock()
            mock_tk.return_value = mock_root
            
            from radar_bot_gui import RadarBotGUI
            app = RadarBotGUI()
            
            print("✅ GUI creation - OK")
            return True
            
    except Exception as e:
        print(f"❌ GUI creation failed: {e}")
        return False

def test_bot_creation():
    """Test bot creation"""
    print("Testing bot creation...")
    
    try:
        from master_bot import MasterBot
        bot = MasterBot()
        
        # Test basic properties
        assert bot.target_ip == "192.168.1.1"
        assert bot.username == "admin"
        assert bot.password == "admin"
        
        print("✅ Bot creation - OK")
        return True
        
    except Exception as e:
        print(f"❌ Bot creation failed: {e}")
        return False

def test_logging():
    """Test logging functionality"""
    print("Testing logging...")
    
    try:
        from master_bot import MasterBot
        bot = MasterBot()
        
        # Test log method
        bot.log("Test message", "INFO")
        
        print("✅ Logging - OK")
        return True
        
    except Exception as e:
        print(f"❌ Logging failed: {e}")
        return False

def test_gui_logging():
    """Test GUI logging functionality"""
    print("Testing GUI logging...")
    
    try:
        with patch('tkinter.Tk'):
            from radar_bot_gui import RadarBotGUI
            app = RadarBotGUI()
            
            # Test log message
            app.log_message("Test GUI message", "INFO")
            
            print("✅ GUI logging - OK")
            return True
            
    except Exception as e:
        print(f"❌ GUI logging failed: {e}")
        return False

def run_all_tests():
    """Run all tests"""
    print("Bivicom Radar Bot GUI - Test Suite")
    print("=" * 40)
    
    tests = [
        test_gui_imports,
        test_bot_imports,
        test_config_file,
        test_gui_creation,
        test_bot_creation,
        test_logging,
        test_gui_logging
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
            print()
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            print()
    
    print("=" * 40)
    print(f"Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed!")
        return True
    else:
        print("❌ Some tests failed!")
        return False

def main():
    """Main function"""
    success = run_all_tests()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
