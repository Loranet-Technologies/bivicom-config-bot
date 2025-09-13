#!/usr/bin/env python3
"""
Bivicom Network Bot - GUI Application
====================================

A standalone GUI application for the Bivicom Network Bot that provides:
- Real-time log display with color-coded messages
- Progress indicators for device setup
- System notifications when setup completes
- Graceful exit handling
- Cross-platform compatibility (Windows, macOS, Linux)

Author: AI Assistant
Date: 2025-09-13
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import queue
import os
import time
import sys
import signal
import subprocess
import platform
from datetime import datetime
from typing import Optional, Dict, Any

# Import the NetworkBot class from master.py
from master import NetworkBot
import io
import contextlib

# Sound playing functions
def play_sound(sound_type="success"):
    """Play system sounds for success/error notifications"""
    try:
        system = platform.system().lower()
        
        if sound_type == "success":
            if system == "darwin":  # macOS
                os.system("afplay /System/Library/Sounds/Glass.aiff")
            elif system == "linux":
                os.system("paplay /usr/share/sounds/alsa/Front_Left.wav 2>/dev/null || echo -e '\a'")
            elif system == "windows":
                import winsound
                winsound.MessageBeep(winsound.MB_OK)
        elif sound_type == "error":
            if system == "darwin":  # macOS
                os.system("afplay /System/Library/Sounds/Basso.aiff")
            elif system == "linux":
                os.system("paplay /usr/share/sounds/alsa/Front_Right.wav 2>/dev/null || echo -e '\a'")
            elif system == "windows":
                import winsound
                winsound.MessageBeep(winsound.MB_ICONHAND)
    except Exception:
        # Fallback to system beep if sound playing fails
        print("\a", end="", flush=True)

class GUIBotWrapper(NetworkBot):
    """Wrapper for NetworkBot that integrates with GUI logging"""
    
    def __init__(self, gui_log_callback, target_ip="192.168.1.1", scan_interval=10, step_progress_callback=None, username="admin", password="admin"):
        super().__init__(target_ip, scan_interval)
        self.gui_log_callback = gui_log_callback
        self.step_progress_callback = step_progress_callback
        self.username = username
        self.password = password
        self.running = False
    
    def _get_timestamp(self):
        """Override to use GUI logging"""
        return time.strftime("%Y-%m-%d %H:%M:%S")
    
    def log_message(self, message: str, level: str = "INFO"):
        """Send messages to GUI"""
        timestamp = self._get_timestamp()
        formatted_message = f"[{timestamp}] {message}"
        self.gui_log_callback(formatted_message, level)
        # Also print to console for debugging
        print(f"[{timestamp}] [{level}] {message}")
    
    def scan_and_configure(self):
        """Override the main bot loop to integrate with GUI"""
        self.log_message("🤖 Bivicom Network Bot Started", "SUCCESS")
        self.log_message(f"🎯 Looking for device at {self.target_ip}", "INFO")
        self.log_message(f"⏱️  Scan interval: {self.scan_interval} seconds", "INFO")
        self.log_message(f"📜 Script path: {self.script_path}", "INFO")
        self.log_message("Press Stop Bot to stop", "INFO")
        
        self.running = True
        scan_count = 0
        config_count = 0
        
        while self.running:
            try:
                scan_count += 1
                self.log_message(f"🔍 Scanning for {self.target_ip}... (Scan #{scan_count})", "INFO")
                
                if self.ping_host(self.target_ip):
                    self.log_message("✅ FOUND!", "SUCCESS")
                    self.log_message("🚀 Device detected! Starting network configuration...", "SUCCESS")
                    
                    success = self.run_network_config()
                    if success:
                        config_count += 1
                        self.log_message("🎉 Configuration completed! Bot will continue monitoring...", "SUCCESS")
                        self.log_message(f"📊 Total configurations completed: {config_count}", "SUCCESS")
                    else:
                        self.log_message("⚠️  Configuration failed, will retry on next scan...", "WARNING")
                else:
                    self.log_message("❌ Not found", "INFO")
                
                if self.running:
                    time.sleep(self.scan_interval)
                    
            except Exception as e:
                self.log_message(f"❌ Error during scan: {e}", "ERROR")
                time.sleep(self.scan_interval)
        
        self.log_message("🛑 Bot stopped", "INFO")
    
    def run_network_config(self):
        """Override the network configuration to track step progress"""
        try:
            self.log_message("🚀 Starting complete network configuration sequence...", "SUCCESS")
            
            # Define the sequence of commands to run
            commands = [
                {
                    "name": "1. Configure Network FORWARD",
                    "cmd": [self.script_path, "--remote", self.target_ip, self.username, self.password, "forward"],
                    "timeout": 60
                },
                {
                    "name": "2. Check DNS Connectivity", 
                    "cmd": [self.script_path, "check-dns"],
                    "timeout": 30
                },
                {
                    "name": "3. Install Docker (after network config)",
                    "cmd": [self.script_path, "--remote", self.target_ip, self.username, self.password, "install-docker"],
                    "timeout": 300
                },
                {
                    "name": "4. Install All Docker Services",
                    "cmd": [self.script_path, "--remote", self.target_ip, self.username, self.password, "install-services"],
                    "timeout": 300
                },
                {
                    "name": "5. Install Node-RED Nodes",
                    "cmd": [self.script_path, "--remote", self.target_ip, self.username, self.password, "install-nodered-nodes"],
                    "timeout": 180
                },
                {
                    "name": "6. Import Node-RED Flows",
                    "cmd": [self.script_path, "--remote", self.target_ip, self.username, self.password, "import-nodered-flows"],
                    "timeout": 120
                },
                {
                    "name": "7. Install Tailscale VPN Router",
                    "cmd": [self.script_path, "--remote", self.target_ip, self.username, self.password, "install-tailscale"],
                    "timeout": 180
                },
                {
                    "name": "8. Configure Network REVERSE",
                    "cmd": [self.script_path, "--remote", self.target_ip, self.username, self.password, "reverse"],
                    "timeout": 60
                }
            ]
            
            # Execute each command in sequence
            for i, command in enumerate(commands, 1):
                self.log_message(f"📋 Step {i}/8: {command['name']}", "INFO")
                self.log_message(f"🔧 Running: {' '.join(command['cmd'])}", "INFO")
                
                try:
                    result = subprocess.run(
                        command['cmd'], 
                        capture_output=True, 
                        text=True, 
                        timeout=command['timeout']
                    )
                    
                    if result.returncode == 0:
                        self.log_message(f"✅ Step {i} completed successfully!", "SUCCESS")
                        if result.stdout.strip():
                            self.log_message(f"📄 Output: {result.stdout.strip()[:200]}...", "INFO")
                        
                        # Update GUI step progress
                        if self.step_progress_callback:
                            self.step_progress_callback(i, True)
                    else:
                        self.log_message(f"❌ Step {i} failed!", "ERROR")
                        self.log_message(f"📄 Error: {result.stderr.strip()[:200]}...", "ERROR")
                        
                        # Update GUI step progress (failed)
                        if self.step_progress_callback:
                            self.step_progress_callback(i, False)
                        return False
                        
                except subprocess.TimeoutExpired:
                    self.log_message(f"⏰ Step {i} timed out after {command['timeout']} seconds", "ERROR")
                    if self.step_progress_callback:
                        self.step_progress_callback(i, False)
                    return False
                except Exception as e:
                    self.log_message(f"❌ Step {i} error: {e}", "ERROR")
                    if self.step_progress_callback:
                        self.step_progress_callback(i, False)
                    return False
                
                # Small delay between commands
                if i < len(commands):
                    self.log_message(f"⏳ Waiting 5 seconds before next step...", "INFO")
                    time.sleep(5)
            
            self.log_message("🎉 Complete network configuration sequence finished successfully!", "SUCCESS")
            return True
                
        except Exception as e:
            self.log_message(f"❌ Error in network configuration sequence: {e}", "ERROR")
            return False

class NetworkBotGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Bivicom Network Bot - Device Configuration")
        self.root.geometry("1000x800")
        self.root.minsize(900, 700)
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
        self.scan_count = 0
        self.config_count = 0
        self.current_step = 0
        self.total_steps = 8
        self.script_path = os.path.join(os.path.dirname(__file__), "network_config.sh")
        
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
        main_frame.rowconfigure(5, weight=1)
        
        # Title
        title_label = ttk.Label(main_frame, text="Bivicom Network Bot", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Target IP configuration frame
        ip_frame = ttk.LabelFrame(main_frame, text="Target Device Configuration", padding="5")
        ip_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(ip_frame, text="Target IP:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.target_ip_var = tk.StringVar(value="192.168.1.1")
        self.target_ip_entry = ttk.Entry(ip_frame, textvariable=self.target_ip_var, width=15)
        self.target_ip_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 10))
        
        ttk.Label(ip_frame, text="(Default: 192.168.1.1)", 
                 font=("Arial", 8), foreground="gray").grid(row=0, column=2, sticky=tk.W)
        
        # Username configuration
        ttk.Label(ip_frame, text="Username:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        self.username_var = tk.StringVar(value="admin")
        self.username_entry = ttk.Entry(ip_frame, textvariable=self.username_var, width=15)
        self.username_entry.grid(row=1, column=1, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        
        ttk.Label(ip_frame, text="(Default: admin)", 
                 font=("Arial", 8), foreground="gray").grid(row=1, column=2, sticky=tk.W, pady=(5, 0))
        
        # Password configuration
        ttk.Label(ip_frame, text="Password:").grid(row=2, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        self.password_var = tk.StringVar(value="admin")
        self.password_entry = ttk.Entry(ip_frame, textvariable=self.password_var, width=15, show="*")
        self.password_entry.grid(row=2, column=1, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        
        # Show/Hide password button
        self.show_password_var = tk.BooleanVar()
        self.show_password_check = ttk.Checkbutton(ip_frame, text="Show", variable=self.show_password_var, 
                                                 command=self.toggle_password_visibility)
        self.show_password_check.grid(row=2, column=2, sticky=tk.W, padx=(5, 0), pady=(5, 0))
        
        ttk.Label(ip_frame, text="(Default: admin)", 
                 font=("Arial", 8), foreground="gray").grid(row=2, column=3, sticky=tk.W, pady=(5, 0))
        
        # Scan interval configuration
        ttk.Label(ip_frame, text="Scan Interval (seconds):").grid(row=3, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        self.scan_interval_var = tk.StringVar(value="10")
        self.scan_interval_entry = ttk.Entry(ip_frame, textvariable=self.scan_interval_var, width=10)
        self.scan_interval_entry.grid(row=3, column=1, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        
        ttk.Label(ip_frame, text="(Default: 10 seconds)", 
                 font=("Arial", 8), foreground="gray").grid(row=3, column=2, sticky=tk.W, pady=(5, 0))
        
        # Configuration sequence progress frame
        sequence_frame = ttk.LabelFrame(main_frame, text="8-Step Configuration Progress", padding="5")
        sequence_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Create step checkboxes
        self.step_vars = []
        self.step_labels = []
        self.step_descriptions = [
            "Configure Network FORWARD (WAN=eth1 DHCP, LAN=eth0 static)",
            "Check DNS Connectivity",
            "Install Docker (after network config)",
            "Install All Docker Services (Node-RED, Portainer, Restreamer)",
            "Install Node-RED Nodes (ffmpeg, queue-gate, sqlite, serialport)",
            "Import Node-RED Flows",
            "Install Tailscale VPN Router",
            "Configure Network REVERSE (WAN=enx0250f4000000 LTE, LAN=eth0 static)"
        ]
        
        for i, description in enumerate(self.step_descriptions):
            # Create checkbox variable
            var = tk.BooleanVar()
            self.step_vars.append(var)
            
            # Create checkbox
            checkbox = ttk.Checkbutton(sequence_frame, variable=var, state="disabled")
            checkbox.grid(row=i, column=0, sticky=tk.W, padx=(0, 10), pady=2)
            
            # Create label
            label = ttk.Label(sequence_frame, text=f"{i+1}. {description}", 
                             font=("Arial", 9), foreground="gray")
            label.grid(row=i, column=1, sticky=tk.W, pady=2)
            self.step_labels.append(label)
        
        # Progress summary
        self.progress_summary = ttk.Label(sequence_frame, text="Progress: 0/8 steps completed", 
                                         font=("Arial", 10, "bold"), foreground="blue")
        self.progress_summary.grid(row=8, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))
        
        # Tailscale Auth Key configuration frame
        tailscale_frame = ttk.LabelFrame(main_frame, text="Tailscale Configuration", padding="5")
        tailscale_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(tailscale_frame, text="Auth Key:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
        self.tailscale_auth_var = tk.StringVar(value="tskey-auth-kvwRxYc6o321CNTRL-6kggdogXnMdAdewR7Y7cMdNSp7yrJsSC")
        self.tailscale_auth_entry = ttk.Entry(tailscale_frame, textvariable=self.tailscale_auth_var, width=50, show="*")
        self.tailscale_auth_entry.grid(row=0, column=1, sticky=tk.W, padx=(0, 10))
        
        ttk.Label(tailscale_frame, text="(Valid for 90 days)", 
                 font=("Arial", 8), foreground="gray").grid(row=0, column=2, sticky=tk.W)
        
        # Route advertising info
        ttk.Label(tailscale_frame, text="Route Advertising:", 
                 font=("Arial", 9, "bold")).grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
        ttk.Label(tailscale_frame, text="Will advertise 192.168.1.0/24 and 192.168.14.0/24", 
                 font=("Arial", 8), foreground="blue").grid(row=1, column=1, columnspan=2, sticky=tk.W, pady=(5, 0))
        
        # Control buttons frame
        control_frame = ttk.Frame(main_frame)
        control_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        
        # Start/Stop button
        self.start_button = ttk.Button(control_frame, text="Start Bot", 
                                      command=self.toggle_bot, style="Accent.TButton")
        self.start_button.grid(row=0, column=0, padx=(0, 10))
        
        # Reset Device button
        self.reset_button = ttk.Button(control_frame, text="Reset Device", 
                                      command=self.reset_device, style="")
        self.reset_button.grid(row=0, column=1, padx=(0, 10))
        
        # Status label
        self.status_label = ttk.Label(control_frame, text="Status: Ready", 
                                     font=("Arial", 10, "bold"))
        self.status_label.grid(row=0, column=2, padx=(10, 0))
        
        # Scan count label
        self.scan_count_label = ttk.Label(control_frame, text="Scans: 0", 
                                         font=("Arial", 9))
        self.scan_count_label.grid(row=0, column=3, padx=(20, 0))
        
        # Log display
        log_frame = ttk.LabelFrame(main_frame, text="Log Output", padding="5")
        log_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S))
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
        self.progress.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Bottom info frame
        info_frame = ttk.Frame(main_frame)
        info_frame.grid(row=7, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Configuration count
        self.config_count_label = ttk.Label(info_frame, text="Configurations: 0")
        self.config_count_label.grid(row=0, column=0, sticky=tk.W)
        
        # Time label
        self.time_label = ttk.Label(info_frame, text="")
        self.time_label.grid(row=0, column=1, sticky=tk.E)
        
        # Update time display
        self.update_time()
    
    def toggle_password_visibility(self):
        """Toggle password visibility"""
        if self.show_password_var.get():
            self.password_entry.config(show="")
        else:
            self.password_entry.config(show="*")
    
    def reset_step_progress(self):
        """Reset all step checkboxes and progress"""
        for var in self.step_vars:
            var.set(False)
        for label in self.step_labels:
            label.config(foreground="gray")
        self.current_step = 0
        self.progress_summary.config(text="Progress: 0/8 steps completed", foreground="blue")
    
    def update_step_progress(self, step_number, success=True):
        """Update step progress with visual feedback"""
        if 1 <= step_number <= 8:
            step_index = step_number - 1
            self.step_vars[step_index].set(True)
            
            if success:
                self.step_labels[step_index].config(foreground="green")
                self.current_step = step_number
                # Play success sound for completed steps
                threading.Thread(target=lambda: play_sound("success"), daemon=True).start()
            else:
                self.step_labels[step_index].config(foreground="red")
                # Play error sound for failed steps
                threading.Thread(target=lambda: play_sound("error"), daemon=True).start()
            
            # Update progress summary
            completed = sum(1 for var in self.step_vars if var.get())
            self.progress_summary.config(text=f"Progress: {completed}/8 steps completed")
            
            if completed == 8:
                self.progress_summary.config(foreground="green", text="Progress: 8/8 steps completed - SUCCESS!")
            elif completed > 0:
                self.progress_summary.config(foreground="orange")
    
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
            
            # Reset step progress
            self.reset_step_progress()
            
            # Get configuration from GUI
            target_ip = self.target_ip_var.get().strip() or "192.168.1.1"
            scan_interval = int(self.scan_interval_var.get().strip() or "10")
            username = self.username_var.get().strip() or "admin"
            password = self.password_var.get().strip() or "admin"
            
            # Create bot instance with GUI logging integration
            self.bot = GUIBotWrapper(self.log_message, target_ip, scan_interval, self.update_step_progress, username, password)
            
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
                self.bot.running = False
            
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
    
    def reset_device(self):
        """Reset device to default state"""
        try:
            # Confirm reset action
            if not messagebox.askyesno("Confirm Reset", 
                                     "This will completely reset the device to default state:\n\n"
                                     "• Remove all Docker containers, images, and volumes\n"
                                     "• Reset network to REVERSE mode (LTE WAN)\n"
                                     "• Change password back to admin/admin\n"
                                     "• Reset IP address to 192.168.1.1\n"
                                     "• Remove all custom configurations\n\n"
                                     "Are you sure you want to continue?"):
                return
            
            # Get configuration from GUI
            target_ip = self.target_ip_var.get().strip() or "192.168.1.1"
            username = self.username_var.get().strip() or "admin"
            password = self.password_var.get().strip() or "admin"
            
            self.log_message("🔄 Starting device reset...", "WARNING")
            self.log_message(f"🎯 Target device: {target_ip}", "INFO")
            self.log_message(f"👤 Username: {username}", "INFO")
            
            # Reset step progress
            self.reset_step_progress()
            
            # Run reset command
            cmd = [self.script_path, "--remote", target_ip, username, password, "reset-device"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode == 0:
                self.log_message("✅ Device reset completed successfully!", "SUCCESS")
                self.log_message("📄 Reset output:", "INFO")
                for line in result.stdout.split('\n'):
                    if line.strip():
                        self.log_message(f"   {line.strip()}", "INFO")

                # Show success notification
                self.show_notification("Device Reset", "Device has been reset to default state successfully!")
            else:
                self.log_message("❌ Device reset failed!", "ERROR")
                self.log_message("📄 Error output:", "ERROR")
                
                # Show both stderr and stdout for better debugging
                if result.stderr.strip():
                    for line in result.stderr.split('\n'):
                        if line.strip():
                            self.log_message(f"   {line.strip()}", "ERROR")
                
                if result.stdout.strip():
                    self.log_message("📄 Standard output:", "ERROR")
                    for line in result.stdout.split('\n'):
                        if line.strip():
                            self.log_message(f"   {line.strip()}", "ERROR")

                # Show error notification with more details
                error_msg = "Device reset encountered errors."
                if "uci: command not found" in result.stderr or "uci: command not found" in result.stdout:
                    error_msg += "\n\nThis device may not be running OpenWrt or UCI is not installed."
                self.show_notification("Device Reset Failed", error_msg)
                
        except subprocess.TimeoutExpired:
            self.log_message("⏰ Device reset timed out after 10 minutes", "ERROR")
            self.show_notification("Device Reset Timeout", "Device reset timed out. Check device connectivity.")
        except Exception as e:
            self.log_message(f"❌ Error during device reset: {e}", "ERROR")
            self.show_notification("Device Reset Error", f"Error during reset: {e}")
    
    def run_bot(self):
        """Run the bot (called in separate thread)"""
        try:
            # Set Tailscale auth key from GUI input
            tailscale_auth = self.tailscale_auth_var.get().strip()
            if tailscale_auth and tailscale_auth != "YOUR_TAILSCALE_AUTH_KEY_HERE":
                os.environ["TAILSCALE_AUTH_KEY"] = tailscale_auth
            
            self.log_message("Starting network bot with 8-step configuration sequence", "INFO")
            self.log_message("Bot will continuously scan for devices until stopped", "INFO")
            
            # Run the bot's scan and configure loop
            self.bot.scan_and_configure()
            
            # Update status when bot ends
            if self.bot.running:
                self.log_message("Bot stopped by user request.", "INFO")
                self.show_notification("Bivicom Network Bot", "Bot stopped by user.")
            else:
                self.log_message("Bot completed successfully.", "SUCCESS")
                self.show_notification("Bivicom Network Bot", "Bot completed successfully.")
            
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
        
        # Play sound based on message level
        if level == "SUCCESS":
            # Play success sound for successful operations
            threading.Thread(target=lambda: play_sound("success"), daemon=True).start()
        elif level == "ERROR":
            # Play error sound for error messages
            threading.Thread(target=lambda: play_sound("error"), daemon=True).start()
    
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
        # Play sound based on notification type
        if "Error" in title or "Failed" in title or "Timeout" in title:
            threading.Thread(target=lambda: play_sound("error"), daemon=True).start()
        else:
            threading.Thread(target=lambda: play_sound("success"), daemon=True).start()
        
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
        self.log_message("Bivicom Network Bot GUI started", "SUCCESS")
        self.log_message("Configure settings and click 'Start Bot' to begin", "INFO")
        self.root.mainloop()

def main():
    """Main function"""
    try:
        app = NetworkBotGUI()
        app.run()
    except Exception as e:
        print(f"Error starting GUI: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
