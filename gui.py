#!/usr/bin/env python3
"""
Bivicom Radar Bot - GUI Application
===================================

A standalone GUI application for the Bivicom Radar Bot that provides:
- Real-time log display with color-coded messages
- Progress indicators for device setup
- System notifications when setup completes
- Graceful exit handling
- Cross-platform compatibility (Windows, macOS, Linux)

Author: AI Assistant
Date: 2025-01-09
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import queue
import time
import sys
import os
import signal
import subprocess
import platform
from datetime import datetime
from typing import Optional, Dict, Any

# Import the existing bot classes
from master import UnifiedBivicomBot
import io
import contextlib

class GUIBotWrapper(UnifiedBivicomBot):
    """Wrapper for UnifiedBivicomBot that integrates with GUI logging"""
    
    def __init__(self, gui_log_callback, config_file: str = ".env"):
        super().__init__(config_file)
        self.gui_log_callback = gui_log_callback
    
    def log(self, message: str, level: str = "INFO"):
        """Override the log method to send messages to GUI"""
        # Call the GUI log callback
        self.gui_log_callback(message, level)
        # Also print to console for debugging
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")

class RadarBotGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Bivicom Configurator V1 - Device Setup")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        self.root.configure(bg="#F5F5F5")  # Light gray background
        
        # Set window icon if available
        try:
            if platform.system() == "Windows":
                self.root.iconbitmap("icon.ico")
            else:
                # For macOS/Linux, you can add an icon file
                pass
        except:
            pass
        
        # Initialize variables
        self.bot = None
        self.bot_thread = None
        self.log_queue = queue.Queue()
        self.is_running = False
        self.shutdown_requested = False
        
        # Create GUI elements
        self.create_widgets()
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        # Start log processing
        self.process_log_queue()
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_widgets(self):
        """Create and arrange GUI widgets"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Bivicom Configurator V1", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Mode selection frame
        mode_frame = ttk.LabelFrame(main_frame, text="Operation Mode", padding="5")
        mode_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.mode_var = tk.StringVar(value="single")
        ttk.Radiobutton(mode_frame, text="Single Cycle", variable=self.mode_var, 
                       value="single").grid(row=0, column=0, padx=(0, 20), sticky=tk.W)
        ttk.Radiobutton(mode_frame, text="Run Forever (until stopped)", variable=self.mode_var, 
                       value="forever").grid(row=0, column=1, sticky=tk.W)
        
        # Control buttons frame
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Start/Stop button
        self.start_button = ttk.Button(control_frame, text="Start Bot", 
                                      command=self.toggle_bot, style="Accent.TButton")
        self.start_button.grid(row=0, column=0, padx=(0, 10))
        
        # Status label
        self.status_label = ttk.Label(control_frame, text="Status: Ready", 
                                     font=("Arial", 10, "bold"))
        self.status_label.grid(row=0, column=1, padx=(10, 0))
        
        # Log display
        log_frame = ttk.LabelFrame(main_frame, text="Log Output", padding="5")
        log_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # Create scrolled text widget with custom tags for colors
        self.log_text = scrolledtext.ScrolledText(log_frame, height=25, width=100,
                                                 font=("Consolas", 9), wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure text tags for colored output (lighter colors)
        self.log_text.tag_configure("INFO", foreground="#333333")
        self.log_text.tag_configure("SUCCESS", foreground="#4CAF50", font=("Consolas", 9, "bold"))
        self.log_text.tag_configure("WARNING", foreground="#FF9800", font=("Consolas", 9, "bold"))
        self.log_text.tag_configure("ERROR", foreground="#F44336", font=("Consolas", 9, "bold"))
        self.log_text.tag_configure("DEBUG", foreground="#9E9E9E")
        
        # Progress bar
        self.progress = ttk.Progressbar(main_frame, mode='indeterminate')
        self.progress.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Bottom info frame
        info_frame = ttk.Frame(main_frame)
        info_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Cycle count
        self.cycle_label = ttk.Label(info_frame, text="Cycles: 0")
        self.cycle_label.grid(row=0, column=0, sticky=tk.W)
        
        # Device count
        self.device_label = ttk.Label(info_frame, text="Devices: 0")
        self.device_label.grid(row=0, column=1, sticky=tk.W, padx=(20, 0))
        
        # Time label
        self.time_label = ttk.Label(info_frame, text="")
        self.time_label.grid(row=0, column=2, sticky=tk.E)
        
        # Update time display
        self.update_time()
    
    def update_time(self):
        """Update the time display"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.time_label.config(text=current_time)
        self.root.after(1000, self.update_time)
    
    def toggle_bot(self):
        """Start or stop the bot"""
        if not self.is_running:
            self.start_bot()
        else:
            self.stop_bot()
    
    def start_bot(self):
        """Start the bot in a separate thread"""
        try:
            self.is_running = True
            self.start_button.config(text="Stop Bot", style="")
            self.status_label.config(text="Status: Starting...")
            self.progress.start()
            
            # Create bot instance with GUI logging integration
            self.bot = GUIBotWrapper(self.log_message)
            
            # Start bot in separate thread
            self.bot_thread = threading.Thread(target=self.run_bot, daemon=True)
            self.bot_thread.start()
            
            self.log_message("Bot started successfully", "SUCCESS")
            
        except Exception as e:
            self.log_message(f"Failed to start bot: {e}", "ERROR")
            self.is_running = False
            self.start_button.config(text="Start Bot", style="Accent.TButton")
            self.status_label.config(text="Status: Error")
            self.progress.stop()
    
    def stop_bot(self):
        """Stop the bot gracefully"""
        try:
            self.shutdown_requested = True
            self.status_label.config(text="Status: Stopping...")
            self.log_message("Stopping bot...", "WARNING")
            
            if self.bot:
                self.bot.shutdown_requested = True
            
            # Wait for bot thread to finish
            if self.bot_thread and self.bot_thread.is_alive():
                self.bot_thread.join(timeout=5)
            
            self.is_running = False
            self.shutdown_requested = False
            self.start_button.config(text="Start Bot", style="Accent.TButton")
            self.status_label.config(text="Status: Stopped")
            self.progress.stop()
            
            self.log_message("Bot stopped successfully", "SUCCESS")
            
        except Exception as e:
            self.log_message(f"Error stopping bot: {e}", "ERROR")
    
    def run_bot(self):
        """Run the bot (called in separate thread)"""
        try:
            # Use fixed configuration mode (previously called "forward")
            mode = "forward"
            operation_mode = self.mode_var.get()
            
            if operation_mode == "forever":
                self.log_message("Starting bot in forever mode with standard configuration", "INFO")
                self.log_message("Bot will run continuously until stopped", "INFO")
                
                # Run forever mode
                self.bot.run_forever_mode(mode)
                
                # Update status when forever mode ends
                if self.bot.shutdown_requested:
                    self.log_message("Bot stopped by user request.", "INFO")
                    self.show_notification("Bivicom Configurator V1", "Bot stopped by user.")
                else:
                    self.log_message("Bot completed all cycles.", "SUCCESS")
                    self.show_notification("Bivicom Configurator V1", "Bot completed successfully.")
            else:
                self.log_message("Starting bot with single cycle configuration", "INFO")
                
                # Run a single cycle that can be stopped gracefully
                success = self.bot.run_single_cycle(mode)
                
                if success:
                    self.log_message("Bot cycle completed successfully!", "SUCCESS")
                    self.show_notification("Bivicom Configurator V1", "Device setup completed successfully!")
                else:
                    if self.bot.shutdown_requested:
                        self.log_message("Bot cycle stopped by user request.", "INFO")
                        self.show_notification("Bivicom Configurator V1", "Device setup stopped by user.")
                    else:
                        self.log_message("Bot cycle completed with issues (device may not be ready)", "WARNING")
                        self.show_notification("Bivicom Configurator V1", "Device setup completed with issues.")
            
            # Update status
            self.root.after(0, lambda: self.status_label.config(text="Status: Completed"))
            self.root.after(0, lambda: self.progress.stop())
            self.root.after(0, lambda: setattr(self, 'is_running', False))
            self.root.after(0, lambda: self.start_button.config(text="Start Bot", style="Accent.TButton"))
            
        except Exception as e:
            self.log_message(f"Bot error: {e}", "ERROR")
            self.root.after(0, lambda: self.status_label.config(text="Status: Error"))
            self.root.after(0, lambda: self.progress.stop())
            self.root.after(0, lambda: setattr(self, 'is_running', False))
            self.root.after(0, lambda: self.start_button.config(text="Start Bot", style="Accent.TButton"))
    
    def log_message(self, message: str, level: str = "INFO"):
        """Add a message to the log queue"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_message = f"[{timestamp}] [{level}] {message}\n"
        self.log_queue.put((formatted_message, level))
    
    def process_log_queue(self):
        """Process messages from the log queue"""
        try:
            while True:
                message, level = self.log_queue.get_nowait()
                
                # Insert message at the end
                self.log_text.insert(tk.END, message, level)
                
                # Auto-scroll to bottom
                self.log_text.see(tk.END)
                
                # Limit log size (keep last 1000 lines)
                lines = self.log_text.get("1.0", tk.END).split('\n')
                if len(lines) > 1000:
                    self.log_text.delete("1.0", f"{len(lines) - 1000}.0")
                
        except queue.Empty:
            pass
        
        # Schedule next processing
        self.root.after(100, self.process_log_queue)
    
    def show_notification(self, title: str, message: str):
        """Show system notification"""
        try:
            if platform.system() == "Darwin":  # macOS
                subprocess.run(["osascript", "-e", 
                              f'display notification "{message}" with title "{title}"'])
            elif platform.system() == "Windows":
                # Windows notification
                import winsound
                winsound.MessageBeep(winsound.MB_ICONINFORMATION)
                messagebox.showinfo(title, message)
            else:  # Linux
                subprocess.run(["notify-send", title, message])
        except Exception as e:
            # Fallback to messagebox
            messagebox.showinfo(title, message)
    
    def signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown"""
        self.log_message("Received shutdown signal", "WARNING")
        self.on_closing()
    
    def on_closing(self):
        """Handle window close event"""
        if self.is_running:
            if messagebox.askokcancel("Quit", "Bot is running. Do you want to stop it and quit?"):
                self.stop_bot()
                self.root.destroy()
        else:
            self.root.destroy()
    
    def run(self):
        """Start the GUI application"""
        self.log_message("Bivicom Setting Bot GUI started", "SUCCESS")
        self.log_message("Select mode and click 'Start Bot' to begin", "INFO")
        self.root.mainloop()

def main():
    """Main function"""
    try:
        app = RadarBotGUI()
        app.run()
    except Exception as e:
        print(f"Error starting GUI: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
