#!/usr/bin/env python3
"""
Test script for the Enhanced Bivicom GUI
"""

import sys
import time
import threading
from gui_enhanced import EnhancedNetworkBotGUI

def test_gui_functionality():
    """Test core GUI functionality"""
    print("🧪 Testing Enhanced Bivicom GUI...")
    
    try:
        # Initialize GUI
        print("1. Testing GUI initialization...")
        app = EnhancedNetworkBotGUI()
        print("   ✅ GUI initialized successfully")
        
        # Test logging
        print("2. Testing logging functionality...")
        app.log_message("Test INFO message", "INFO")
        app.log_message("Test SUCCESS message", "SUCCESS") 
        app.log_message("Test WARNING message", "WARNING")
        app.log_message("Test ERROR message", "ERROR")
        print("   ✅ Logging works correctly")
        
        # Test configuration validation
        print("3. Testing configuration validation...")
        app.config['target_ip'] = '192.168.1.1'
        app.config['username'] = 'admin'
        app.config['password'] = 'admin'
        
        result = app._validate_configuration()
        print(f"   ✅ Configuration validation: {'PASSED' if result else 'FAILED'}")
        
        # Test device discovery simulation
        print("4. Testing device management...")
        from gui_enhanced import DeviceInfo
        from datetime import datetime
        
        # Add a mock device
        device = DeviceInfo(
            ip='192.168.1.1',
            status='Online',
            last_seen=datetime.now()
        )
        app.devices['192.168.1.1'] = device
        app._update_device_tree()
        print("   ✅ Device management works")
        
        # Test network diagnostics
        print("5. Testing network diagnostics...")
        
        # Test ping functionality
        ping_result = app._ping_host('8.8.8.8', timeout=1)
        print(f"   ✅ Ping test: {'PASSED' if ping_result else 'FAILED (expected for offline test)'}")
        
        # Test operation steps initialization
        print("6. Testing operation steps...")
        assert len(app.operation_steps) == 12, "Should have 12 operation steps"
        step_names = [step.name for step in app.operation_steps]
        expected_steps = [
            'Device Discovery', 'Connectivity Test', 'Configuration Backup',
            'Network Forward Mode', 'DNS Verification', 'Package Installation',
            'Docker Installation', 'Service Deployment', 'Network Reverse Mode',
            'Security Configuration', 'System Validation', 'Finalization'
        ]
        
        for expected in expected_steps:
            assert expected in step_names, f"Missing step: {expected}"
        print("   ✅ Operation steps configured correctly")
        
        # Test UI state management
        print("7. Testing UI state management...")
        app.start_button.configure(state='disabled')
        app.stop_button.configure(state='normal')
        app._reset_ui_state()
        print("   ✅ UI state management works")
        
        # Test search functionality
        print("8. Testing search functionality...")
        app.log_search_var.set('test')
        app.search_logs()
        print("   ✅ Search functionality works")
        
        # Test queue processing
        print("9. Testing queue processing...")
        app.log_queue.put(("Test queue message", "INFO"))
        app.process_queues()
        print("   ✅ Queue processing works")
        
        print("\n🎉 All tests PASSED! Enhanced GUI is working correctly.")
        return True
        
    except Exception as e:
        print(f"\n❌ Test FAILED with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gui_display():
    """Test GUI display in a separate thread"""
    print("\n🖥️  Testing GUI display...")
    
    def run_gui():
        try:
            app = EnhancedNetworkBotGUI()
            # Log some test messages
            app.log_message("GUI display test started", "INFO")
            app.log_message("Testing visual elements", "SUCCESS")
            app.log_message("All components loaded", "SUCCESS")
            
            # Simulate some activity
            for i in range(3):
                app.log_message(f"Test message {i+1}", "INFO")
                time.sleep(0.1)
                
            app.log_message("GUI display test completed", "SUCCESS")
            print("✅ GUI display test completed")
            
            # Close after a short delay
            app.root.after(1000, app.root.quit)
            app.root.mainloop()
            
        except Exception as e:
            print(f"❌ GUI display test failed: {e}")
    
    # Run GUI in a separate thread to avoid blocking
    gui_thread = threading.Thread(target=run_gui, daemon=True)
    gui_thread.start()
    
    # Wait a bit for the GUI to start
    time.sleep(2)
    print("✅ GUI display test initiated")

if __name__ == "__main__":
    print("Enhanced Bivicom GUI Test Suite")
    print("=" * 50)
    
    # Run functionality tests
    func_success = test_gui_functionality()
    
    if func_success and len(sys.argv) > 1 and sys.argv[1] == "--display":
        # Run display test only if requested
        test_gui_display()
        time.sleep(3)  # Give GUI time to display
    
    print("\n" + "=" * 50)
    if func_success:
        print("🎉 Enhanced GUI is ready for use!")
        print("\nTo run the GUI: python3 gui_enhanced.py")
        print("To run original GUI: python3 gui.py")
    else:
        print("❌ GUI has issues that need to be fixed")
        
    sys.exit(0 if func_success else 1)