#!/usr/bin/env python3
"""
Simple GUI Test for Bivicom Radar Bot
====================================

A simple test to verify the GUI is working properly.

Author: AI Assistant
Date: 2025-01-09
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import time
from datetime import datetime

class SimpleGUITest:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Bivicom Radar Bot - GUI Test")
        self.root.geometry("800x600")
        
        # Create GUI elements
        self.setup_gui()
        
    def setup_gui(self):
        """Setup the GUI components"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        title_label = ttk.Label(main_frame, text="Bivicom Radar Bot - GUI Test", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 10))
        
        # Status
        self.status_label = ttk.Label(main_frame, text="GUI is working! ✅", 
                                     font=("Arial", 12, "bold"), foreground="green")
        self.status_label.pack(pady=(0, 10))
        
        # Log display
        log_frame = ttk.LabelFrame(main_frame, text="Test Log", padding="5")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self.log_text = scrolledtext.ScrolledText(
            log_frame, 
            wrap=tk.WORD, 
            height=15,
            font=("Consolas", 10),
            bg="#1e1e1e",
            fg="#ffffff"
        )
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # Configure text tags for color coding
        self.log_text.tag_configure("INFO", foreground="#00ff00")
        self.log_text.tag_configure("SUCCESS", foreground="#00ff00", font=("Consolas", 10, "bold"))
        self.log_text.tag_configure("WARNING", foreground="#ffff00")
        self.log_text.tag_configure("ERROR", foreground="#ff0000", font=("Consolas", 10, "bold"))
        
        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(button_frame, text="Test Log", command=self.test_log).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="Test Notification", command=self.test_notification).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Exit", command=self.exit_app).pack(side=tk.RIGHT)
        
        # Add initial log message
        self.log_message("GUI Test Application Started", "SUCCESS")
        self.log_message("If you can see this window, the GUI is working!", "INFO")
        
    def log_message(self, message, level="INFO"):
        """Add a message to the log"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] [{level}] {message}\n"
        
        self.log_text.insert(tk.END, log_line, level)
        self.log_text.see(tk.END)
        
    def test_log(self):
        """Test logging functionality"""
        self.log_message("Testing log functionality...", "INFO")
        self.log_message("This is a success message", "SUCCESS")
        self.log_message("This is a warning message", "WARNING")
        self.log_message("This is an error message", "ERROR")
        
    def test_notification(self):
        """Test notification functionality"""
        self.log_message("Testing notification...", "INFO")
        messagebox.showinfo("Test Notification", "This is a test notification!\nIf you see this, notifications work!")
        self.log_message("Notification test completed", "SUCCESS")
        
    def exit_app(self):
        """Exit the application"""
        self.log_message("Exiting application...", "INFO")
        self.root.quit()
        
    def run(self):
        """Run the GUI"""
        self.root.mainloop()

def main():
    """Main function"""
    print("Starting Simple GUI Test...")
    
    try:
        app = SimpleGUITest()
        app.run()
        print("GUI Test completed successfully!")
    except Exception as e:
        print(f"GUI Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
