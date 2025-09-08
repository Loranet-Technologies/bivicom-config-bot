#!/usr/bin/env python3
"""
Simple Visible GUI Test
======================

A very simple GUI that will definitely be visible.

Author: AI Assistant
Date: 2025-01-09
"""

import tkinter as tk
from tkinter import ttk, messagebox
import time

class SimpleVisibleGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🎉 BIVICOM RADAR BOT - GUI IS WORKING! 🎉")
        self.root.geometry("600x400")
        self.root.configure(bg='#2E8B57')  # Sea green background
        
        # Make window stay on top
        self.root.attributes('-topmost', True)
        
        # Center the window
        self.center_window()
        
        self.setup_gui()
        
    def center_window(self):
        """Center the window on screen"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
    def setup_gui(self):
        """Setup the GUI components"""
        # Main frame
        main_frame = tk.Frame(self.root, bg='#2E8B57')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Title
        title_label = tk.Label(
            main_frame, 
            text="🎉 BIVICOM RADAR BOT 🎉", 
            font=("Arial", 24, "bold"),
            bg='#2E8B57',
            fg='white'
        )
        title_label.pack(pady=(0, 20))
        
        # Status
        status_label = tk.Label(
            main_frame, 
            text="✅ GUI IS WORKING PERFECTLY! ✅", 
            font=("Arial", 16, "bold"),
            bg='#2E8B57',
            fg='yellow'
        )
        status_label.pack(pady=(0, 20))
        
        # Info
        info_label = tk.Label(
            main_frame, 
            text="If you can see this window, your GUI is working!\nThe Bivicom Radar Bot GUI should also work.", 
            font=("Arial", 12),
            bg='#2E8B57',
            fg='white',
            justify=tk.CENTER
        )
        info_label.pack(pady=(0, 30))
        
        # Buttons
        button_frame = tk.Frame(main_frame, bg='#2E8B57')
        button_frame.pack(pady=(0, 20))
        
        # Test button
        test_button = tk.Button(
            button_frame,
            text="🔔 Test Notification",
            font=("Arial", 12, "bold"),
            bg='#FF6B6B',
            fg='white',
            command=self.test_notification,
            padx=20,
            pady=10
        )
        test_button.pack(side=tk.LEFT, padx=10)
        
        # Launch main app button
        launch_button = tk.Button(
            button_frame,
            text="🚀 Launch Main App",
            font=("Arial", 12, "bold"),
            bg='#4ECDC4',
            fg='white',
            command=self.launch_main_app,
            padx=20,
            pady=10
        )
        launch_button.pack(side=tk.LEFT, padx=10)
        
        # Exit button
        exit_button = tk.Button(
            button_frame,
            text="❌ Exit",
            font=("Arial", 12, "bold"),
            bg='#FF4757',
            fg='white',
            command=self.exit_app,
            padx=20,
            pady=10
        )
        exit_button.pack(side=tk.LEFT, padx=10)
        
        # Instructions
        instructions = tk.Label(
            main_frame,
            text="Instructions:\n1. If you see this window, GUI is working\n2. Click 'Launch Main App' to start the full application\n3. The main app window should appear\n4. Click 'Start Bot' in the main app to begin device setup",
            font=("Arial", 10),
            bg='#2E8B57',
            fg='lightgray',
            justify=tk.LEFT
        )
        instructions.pack(pady=(20, 0))
        
    def test_notification(self):
        """Test notification functionality"""
        messagebox.showinfo("Test Notification", "🎉 Notification Test Successful!\nIf you see this, notifications work!")
        
    def launch_main_app(self):
        """Launch the main application"""
        try:
            import subprocess
            import sys
            import os
            
            # Get the directory where this script is located
            script_dir = os.path.dirname(os.path.abspath(__file__))
            
            # Launch the main GUI
            subprocess.Popen([
                sys.executable, 
                os.path.join(script_dir, 'radar_bot_gui.py')
            ])
            
            messagebox.showinfo("Main App", "🚀 Main application launched!\nLook for the 'Bivicom Radar Bot - Device Setup' window.")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to launch main app: {e}")
            
    def exit_app(self):
        """Exit the application"""
        self.root.quit()
        
    def run(self):
        """Run the GUI"""
        print("🎉 Simple Visible GUI is starting...")
        print("Look for a bright green window with 'BIVICOM RADAR BOT' title!")
        self.root.mainloop()
        print("✅ Simple Visible GUI closed.")

def main():
    """Main function"""
    print("Starting Simple Visible GUI Test...")
    
    try:
        app = SimpleVisibleGUI()
        app.run()
        print("✅ Simple Visible GUI completed successfully!")
    except Exception as e:
        print(f"❌ Simple Visible GUI failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
