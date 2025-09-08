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
from master_bot import MasterBot
from script_no1 import ScriptNo1
from script_no2 import ScriptNo2
from script_no3 import ScriptNo3

class RadarBotGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Bivicom Radar Bot - Device Setup")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # Set window icon if available
        try:
            if platform.system() == "Windows":
                self.root.iconbitmap("icon.ico")
            else:
                # For macOS/Linux, you can add an icon file
                pass
        except:
            pass
        
        # Bot instance
        self.bot: Optional[MasterBot] = None
        self.bot_thread: Optional[threading.Thread] = None
        self.is_running = False
        self.is_paused = False
        
        # Queue for thread-safe communication
        self.log_queue = queue.Queue()
        self.status_queue = queue.Queue()
        
        # Statistics
        self.stats = {
            'cycles_completed': 0,
            'devices_setup': 0,
            'start_time': None,
            'last_activity': None
        }
        
        # Setup GUI
        self.setup_gui()
        self.setup_signal_handlers()
        
        # Start log processing
        self.process_logs()
        
    def setup_gui(self):
        """Setup the GUI components"""
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Bivicom Radar Bot", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 10))
        
        # Status frame
        status_frame = ttk.LabelFrame(main_frame, text="Status", padding="5")
        status_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        status_frame.columnconfigure(1, weight=1)
        
        # Status indicators
        self.status_label = ttk.Label(status_frame, text="Ready", font=("Arial", 10, "bold"))
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        self.progress_var = tk.StringVar(value="0/0 devices")
        self.progress_label = ttk.Label(status_frame, textvariable=self.progress_var)
        self.progress_label.grid(row=0, column=1, sticky=tk.E)
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(status_frame, mode='indeterminate')
        self.progress_bar.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # Log display frame
        log_frame = ttk.LabelFrame(main_frame, text="Activity Log", padding="5")
        log_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # Log text widget with scrollbar
        self.log_text = scrolledtext.ScrolledText(
            log_frame, 
            wrap=tk.WORD, 
            width=80, 
            height=25,
            font=("Consolas", 9),
            bg="#1e1e1e",
            fg="#ffffff",
            insertbackground="#ffffff"
        )
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure text tags for color coding
        self.log_text.tag_configure("INFO", foreground="#00ff00")
        self.log_text.tag_configure("SUCCESS", foreground="#00ff00", font=("Consolas", 9, "bold"))
        self.log_text.tag_configure("WARNING", foreground="#ffff00")
        self.log_text.tag_configure("ERROR", foreground="#ff0000", font=("Consolas", 9, "bold"))
        self.log_text.tag_configure("DEBUG", foreground="#888888")
        
        # Control buttons frame
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        control_frame.columnconfigure(0, weight=1)
        control_frame.columnconfigure(1, weight=1)
        control_frame.columnconfigure(2, weight=1)
        
        # Start/Stop button
        self.start_button = ttk.Button(control_frame, text="Start Bot", 
                                      command=self.toggle_bot, style="Accent.TButton")
        self.start_button.grid(row=0, column=0, padx=(0, 5), sticky=(tk.W, tk.E))
        
        # Pause/Resume button
        self.pause_button = ttk.Button(control_frame, text="Pause", 
                                      command=self.toggle_pause, state="disabled")
        self.pause_button.grid(row=0, column=1, padx=5, sticky=(tk.W, tk.E))
        
        # Exit button
        self.exit_button = ttk.Button(control_frame, text="Exit", 
                                     command=self.exit_application)
        self.exit_button.grid(row=0, column=2, padx=(5, 0), sticky=(tk.W, tk.E))
        
        # Statistics frame
        stats_frame = ttk.LabelFrame(main_frame, text="Statistics", padding="5")
        stats_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E))
        stats_frame.columnconfigure(1, weight=1)
        stats_frame.columnconfigure(3, weight=1)
        
        # Statistics labels
        ttk.Label(stats_frame, text="Cycles Completed:").grid(row=0, column=0, sticky=tk.W)
        self.cycles_label = ttk.Label(stats_frame, text="0", font=("Arial", 10, "bold"))
        self.cycles_label.grid(row=0, column=1, sticky=tk.W, padx=(5, 20))
        
        ttk.Label(stats_frame, text="Devices Setup:").grid(row=0, column=2, sticky=tk.W)
        self.devices_label = ttk.Label(stats_frame, text="0", font=("Arial", 10, "bold"))
        self.devices_label.grid(row=0, column=3, sticky=tk.W, padx=(5, 0))
        
        ttk.Label(stats_frame, text="Uptime:").grid(row=1, column=0, sticky=tk.W)
        self.uptime_label = ttk.Label(stats_frame, text="00:00:00", font=("Arial", 10, "bold"))
        self.uptime_label.grid(row=1, column=1, sticky=tk.W, padx=(5, 20))
        
        ttk.Label(stats_frame, text="Last Activity:").grid(row=1, column=2, sticky=tk.W)
        self.last_activity_label = ttk.Label(stats_frame, text="Never", font=("Arial", 10, "bold"))
        self.last_activity_label.grid(row=1, column=3, sticky=tk.W, padx=(5, 0))
        
        # Initial log message
        self.log_message("Bivicom Radar Bot GUI initialized", "INFO")
        self.log_message("Ready to start device setup process", "INFO")
        self.log_message("Click 'Start Bot' to begin device setup", "INFO")
        
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        def signal_handler(signum, frame):
            self.log_message(f"Received signal {signum}, shutting down gracefully...", "WARNING")
            self.exit_application()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
    def log_message(self, message: str, level: str = "INFO"):
        """Add a message to the log queue"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = {
            'timestamp': timestamp,
            'level': level,
            'message': message
        }
        self.log_queue.put(log_entry)
        
    def process_logs(self):
        """Process log messages from the queue (called from main thread)"""
        try:
            while True:
                log_entry = self.log_queue.get_nowait()
                self.display_log_entry(log_entry)
        except queue.Empty:
            pass
        
        # Schedule next processing
        self.root.after(100, self.process_logs)
        
    def display_log_entry(self, log_entry: Dict[str, Any]):
        """Display a log entry in the text widget"""
        timestamp = log_entry['timestamp']
        level = log_entry['level']
        message = log_entry['message']
        
        # Format the log entry
        log_line = f"[{timestamp}] [{level}] {message}\n"
        
        # Insert at the end
        self.log_text.insert(tk.END, log_line, level)
        
        # Auto-scroll to bottom
        self.log_text.see(tk.END)
        
        # Limit log size (keep last 1000 lines)
        lines = self.log_text.get("1.0", tk.END).split('\n')
        if len(lines) > 1000:
            self.log_text.delete("1.0", f"{len(lines) - 1000}.0")
        
        # Update last activity
        self.stats['last_activity'] = timestamp
        self.update_statistics()
        
    def update_statistics(self):
        """Update the statistics display"""
        self.cycles_label.config(text=str(self.stats['cycles_completed']))
        self.devices_label.config(text=str(self.stats['devices_setup']))
        
        # Update uptime
        if self.stats['start_time']:
            uptime_seconds = int(time.time() - self.stats['start_time'])
            hours = uptime_seconds // 3600
            minutes = (uptime_seconds % 3600) // 60
            seconds = uptime_seconds % 60
            self.uptime_label.config(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")
        
        # Update last activity
        if self.stats['last_activity']:
            self.last_activity_label.config(text=self.stats['last_activity'])
            
    def toggle_bot(self):
        """Start or stop the bot"""
        if not self.is_running:
            self.start_bot()
        else:
            self.stop_bot()
            
    def start_bot(self):
        """Start the bot in a separate thread"""
        if self.is_running:
            return
            
        self.log_message("Starting Bivicom Radar Bot...", "INFO")
        
        # Initialize bot
        self.bot = MasterBot()
        
        # Override bot's log method to use our GUI logging
        original_log = self.bot.log
        def gui_log(message: str, level: str = "INFO"):
            original_log(message, level)  # Keep original logging
            self.log_message(message, level)  # Add to GUI
        self.bot.log = gui_log
        
        # Start bot thread
        self.bot_thread = threading.Thread(target=self.run_bot, daemon=True)
        self.bot_thread.start()
        
        # Update UI
        self.is_running = True
        self.start_button.config(text="Stop Bot")
        self.pause_button.config(state="normal")
        self.progress_bar.start()
        self.status_label.config(text="Running", foreground="green")
        
        # Start statistics
        self.stats['start_time'] = time.time()
        self.stats['cycles_completed'] = 0
        self.stats['devices_setup'] = 0
        
        self.log_message("Bot started successfully", "SUCCESS")
        
    def stop_bot(self):
        """Stop the bot"""
        if not self.is_running:
            return
            
        self.log_message("Stopping Bivicom Radar Bot...", "WARNING")
        
        # Signal bot to stop
        if self.bot:
            self.bot.shutdown_requested = True
            
        # Update UI
        self.is_running = False
        self.is_paused = False
        self.start_button.config(text="Start Bot")
        self.pause_button.config(text="Pause", state="disabled")
        self.progress_bar.stop()
        self.status_label.config(text="Stopped", foreground="red")
        
        self.log_message("Bot stopped", "INFO")
        
    def toggle_pause(self):
        """Pause or resume the bot"""
        if not self.is_running:
            return
            
        if self.is_paused:
            self.resume_bot()
        else:
            self.pause_bot()
            
    def pause_bot(self):
        """Pause the bot"""
        self.is_paused = True
        self.pause_button.config(text="Resume")
        self.status_label.config(text="Paused", foreground="orange")
        self.log_message("Bot paused", "WARNING")
        
    def resume_bot(self):
        """Resume the bot"""
        self.is_paused = False
        self.pause_button.config(text="Pause")
        self.status_label.config(text="Running", foreground="green")
        self.log_message("Bot resumed", "SUCCESS")
        
    def run_bot(self):
        """Run the bot (called from bot thread)"""
        try:
            # Run a single cycle instead of forever mode
            success = self.bot.run_single_cycle()
            
            if success:
                self.stats['cycles_completed'] += 1
                self.stats['devices_setup'] += 1
                
                # Show notification
                self.show_completion_notification()
                
                # Update progress
                self.progress_var.set(f"{self.stats['devices_setup']} device(s) setup complete")
                
                self.log_message(f"Device setup completed successfully! (Cycle #{self.stats['cycles_completed']})", "SUCCESS")
            else:
                self.log_message("Device setup failed", "ERROR")
                
        except Exception as e:
            self.log_message(f"Bot error: {e}", "ERROR")
        finally:
            # Bot finished, update UI
            self.root.after(0, self.bot_finished)
            
    def bot_finished(self):
        """Called when bot finishes (from main thread)"""
        if self.is_running:
            self.stop_bot()
            
    def show_completion_notification(self):
        """Show system notification when device setup completes"""
        try:
            if platform.system() == "Darwin":  # macOS
                subprocess.run([
                    "osascript", "-e",
                    f'display notification "Device setup completed successfully!" with title "Bivicom Radar Bot"'
                ])
            elif platform.system() == "Windows":
                # Windows notification
                try:
                    import plyer
                    plyer.notification.notify(
                        title="Bivicom Radar Bot",
                        message="Device setup completed successfully!",
                        timeout=5
                    )
                except ImportError:
                    # Fallback to messagebox
                    messagebox.showinfo("Bivicom Radar Bot", "Device setup completed successfully!")
            else:  # Linux
                try:
                    subprocess.run([
                        "notify-send", 
                        "Bivicom Radar Bot", 
                        "Device setup completed successfully!"
                    ])
                except:
                    pass
                    
        except Exception as e:
            self.log_message(f"Failed to show notification: {e}", "WARNING")
            
    def exit_application(self):
        """Exit the application gracefully"""
        self.log_message("Exiting application...", "INFO")
        
        # Stop bot if running
        if self.is_running:
            self.stop_bot()
            
        # Wait for bot thread to finish
        if self.bot_thread and self.bot_thread.is_alive():
            self.log_message("Waiting for bot to finish...", "INFO")
            self.bot_thread.join(timeout=5)
            
        # Close the application
        self.root.quit()
        self.root.destroy()
        
    def run(self):
        """Run the GUI application"""
        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.exit_application()

def main():
    """Main function"""
    print("Starting Bivicom Radar Bot GUI...")
    
    # Check if required files exist
    required_files = ['master_bot.py', 'script_no1.py', 'script_no2.py', 'script_no3.py', 'bot_config.json']
    missing_files = [f for f in required_files if not os.path.exists(f)]
    
    if missing_files:
        print(f"Error: Missing required files: {', '.join(missing_files)}")
        sys.exit(1)
    
    # Create and run GUI
    app = RadarBotGUI()
    app.run()

if __name__ == "__main__":
    main()
