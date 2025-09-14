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
from tkinter import ttk, scrolledtext, messagebox, filedialog
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
import shutil
import json

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
        elif sound_type == "completion":
            if system == "darwin":  # macOS
                # Play a celebratory sound sequence
                os.system("afplay /System/Library/Sounds/Glass.aiff")
                time.sleep(0.3)
                os.system("afplay /System/Library/Sounds/Glass.aiff")
                time.sleep(0.3)
                os.system("afplay /System/Library/Sounds/Glass.aiff")
            elif system == "linux":
                # Play a celebratory beep sequence
                os.system("echo -e '\a'")
                time.sleep(0.3)
                os.system("echo -e '\a'")
                time.sleep(0.3)
                os.system("echo -e '\a'")
            elif system == "windows":
                import winsound
                # Play a celebratory beep sequence
                winsound.MessageBeep(winsound.MB_OK)
                time.sleep(0.3)
                winsound.MessageBeep(winsound.MB_OK)
                time.sleep(0.3)
                winsound.MessageBeep(winsound.MB_OK)
    except Exception:
        # Fallback to system beep if sound playing fails
        print("\a", end="", flush=True)

class GUIBotWrapper(NetworkBot):
    """Wrapper for NetworkBot that integrates with GUI logging"""
    
    def __init__(self, gui_log_callback, target_ip="192.168.1.1", scan_interval=10, step_progress_callback=None, username="admin", password="admin", step_highlight_callback=None, final_ip="192.168.1.1", final_password="admin", flows_source="auto", package_source="auto", uploaded_flows_file=None, uploaded_package_file=None):
        # Initialize parent class but skip logging setup for GUI mode
        self.target_ip = target_ip
        self.scan_interval = scan_interval
        self.running = True
        self.verbose = False
        self.script_path = os.path.join(os.path.dirname(__file__), "network_config.sh")
        self.username = username
        self.password = password
        self.final_ip = final_ip
        self.final_password = final_password
        self.flows_source = flows_source
        self.package_source = package_source
        self.uploaded_flows_file = uploaded_flows_file
        self.uploaded_package_file = uploaded_package_file
        
        # Set up signal handlers (but not logging)
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        # GUI-specific attributes
        self.gui_log_callback = gui_log_callback
        self.step_progress_callback = step_progress_callback
        self.step_highlight_callback = step_highlight_callback
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
            # Get selected functions from GUI (we need to access the main GUI instance)
            # This will be set by the GUI when creating the bot
            selected_functions = getattr(self, 'selected_functions', [])
            
            if not selected_functions:
                self.log_message("❌ No functions selected! Please select functions to run.", "ERROR")
                return False
            
            self.log_message(f"🚀 Starting configuration with {len(selected_functions)} selected functions...", "SUCCESS")
            self.log_message(f"📋 Selected functions: {', '.join(selected_functions)}", "INFO")
            
            # Define command templates (built dynamically with current values)
            command_templates = {
                "forward": {
                    "name": "Configure Network FORWARD",
                    "cmd": [self.script_path, "--remote", self.target_ip, self.username, self.password, "forward"],
                    "timeout": 60
                },
                "check-dns": {
                    "name": "Check DNS Connectivity", 
                    "cmd": [self.script_path, "--remote", self.target_ip, self.username, self.password, "check-dns"],
                    "timeout": 30
                },
                "fix-dns": {
                    "name": "Fix DNS Configuration",
                    "cmd": [self.script_path, "--remote", self.target_ip, self.username, self.password, "fix-dns"],
                    "timeout": 60
                },
                "install-curl": {
                    "name": "Install curl",
                    "cmd": [self.script_path, "--remote", self.target_ip, self.username, self.password, "install-curl"],
                    "timeout": 60
                },
                "install-docker": {
                    "name": "Install Docker",
                    "cmd": [self.script_path, "--remote", self.target_ip, self.username, self.password, "install-docker"],
                    "timeout": 300
                },
                "install-services": {
                    "name": "Install All Docker Services",
                    "cmd": [self.script_path, "--remote", self.target_ip, self.username, self.password, "install-services"],
                    "timeout": 300
                },
                "install-nodered-nodes": {
                    "name": "Install Node-RED Nodes",
                    "cmd": [self.script_path, "--remote", self.target_ip, self.username, self.password, "install-nodered-nodes", self.package_source, self.uploaded_package_file or ""],
                    "timeout": 180
                },
                "import-nodered-flows": {
                    "name": "Import Node-RED Flows",
                    "cmd": [self.script_path, "--remote", self.target_ip, self.username, self.password, "import-nodered-flows", self.flows_source, self.uploaded_flows_file or ""],
                    "timeout": 120
                },
                "update-nodered-auth": {
                    "name": "Update Node-RED Authentication",
                    "cmd": [self.script_path, "--remote", self.target_ip, self.username, self.password, "update-nodered-auth", self.password],
                    "timeout": 60
                },
                "install-tailscale": {
                    "name": "Install Tailscale VPN Router",
                    "cmd": [self.script_path, "--remote", self.target_ip, self.username, self.password, "install-tailscale"],
                    "timeout": 180
                },
                "reverse": {
                    "name": "Configure Network REVERSE",
                    "cmd": [self.script_path, "--remote", self.final_ip, self.username, self.password, "reverse", self.final_ip],
                    "timeout": 60
                },
                "set-password": {
                    "name": "Change Device Password",
                    "cmd": [self.script_path, "--remote", self.final_ip, self.username, self.password, "set-password", self.final_password],
                    "timeout": 60
                }
            }
            
            # Debug: Log the script path and target info
            self.log_message(f"🔧 Script path: {self.script_path}", "DEBUG")
            self.log_message(f"🔧 Target IP: {self.target_ip}", "DEBUG")
            self.log_message(f"🔧 Username: {self.username}", "DEBUG")
            self.log_message(f"🔧 Password: {self.password}", "DEBUG")
            
            # Build commands list from selected functions
            commands = []
            for i, func in enumerate(selected_functions):
                if func in command_templates:
                    cmd = command_templates[func].copy()
                    cmd["name"] = f"{i+1}. {cmd['name']}"
                    # Debug: Log the command being built
                    self.log_message(f"🔧 Building command for {func}: {cmd['cmd']}", "DEBUG")
                    commands.append(cmd)
                else:
                    self.log_message(f"⚠️ Unknown function: {func}", "WARNING")
            
            # Execute each command in sequence
            for i, command in enumerate(commands, 1):
                self.log_message(f"📋 Step {i}/{len(commands)}: {command['name']}", "INFO")
                self.log_message(f"🔧 Running: {' '.join(command['cmd'])}", "INFO")
                
                # Highlight current step in GUI
                if self.step_highlight_callback:
                    self.step_highlight_callback(i)
                
                try:
                    # Run command with real-time output streaming
                    self.log_message(f"🚀 Starting command execution...", "INFO")
                    
                    process = subprocess.Popen(
                        command['cmd'], 
                        stdout=subprocess.PIPE, 
                        stderr=subprocess.STDOUT,  # Merge stderr into stdout
                        text=True, 
                        bufsize=1,  # Line buffered
                        universal_newlines=True
                    )
                    
                    # Stream output in real-time with timeout handling
                    output_lines = []
                    import select
                    import sys
                    
                    # Use select for timeout handling (Unix/macOS)
                    if hasattr(select, 'select'):
                        while True:
                            # Check if process is still running
                            if process.poll() is not None:
                                # Process finished, read any remaining output
                                remaining_output = process.stdout.read()
                                if remaining_output:
                                    for line in remaining_output.splitlines():
                                        if line.strip():
                                            self.log_message(f"📄 {line.strip()}", "INFO")
                                            print(f"[SCRIPT OUTPUT] {line.strip()}")
                                break
                            
                            # Check for output with timeout
                            ready, _, _ = select.select([process.stdout], [], [], 1.0)  # 1 second timeout
                            if ready:
                                output = process.stdout.readline()
                                if output:
                                    output_line = output.strip()
                                    if output_line:  # Only log non-empty lines
                                        self.log_message(f"📄 {output_line}", "INFO")
                                        output_lines.append(output_line)
                                        # Also print to Python terminal
                                        print(f"[SCRIPT OUTPUT] {output_line}")
                            else:
                                # Timeout - check if we should continue waiting
                                # This allows for long-running commands while still being responsive
                                pass
                    else:
                        # Fallback for Windows (no select module)
                        while True:
                            output = process.stdout.readline()
                            if output == '' and process.poll() is not None:
                                break
                            if output:
                                output_line = output.strip()
                                if output_line:  # Only log non-empty lines
                                    self.log_message(f"📄 {output_line}", "INFO")
                                    output_lines.append(output_line)
                                    # Also print to Python terminal
                                    print(f"[SCRIPT OUTPUT] {output_line}")
                    
                    # Wait for process to complete and get return code
                    return_code = process.wait()
                    
                    if return_code == 0:
                        self.log_message(f"✅ Step {i} completed successfully!", "SUCCESS")
                        
                        # Update GUI step progress
                        if self.step_progress_callback:
                            self.step_progress_callback(i, True)
                    else:
                        self.log_message(f"❌ Step {i} failed with return code {return_code}!", "ERROR")
                        
                        # Update GUI step progress (failed)
                        if self.step_progress_callback:
                            self.step_progress_callback(i, False)
                        return False
                        
                except Exception as e:
                    # Handle any other errors (including timeout if we implement it)
                    if "timeout" in str(e).lower():
                        self.log_message(f"⏰ Step {i} timed out after {command['timeout']} seconds", "ERROR")
                    else:
                        self.log_message(f"❌ Step {i} error: {e}", "ERROR")
                    
                    # Kill the process if it's still running
                    if 'process' in locals() and process.poll() is None:
                        process.terminate()
                        try:
                            process.wait(timeout=5)
                        except subprocess.TimeoutExpired:
                            process.kill()
                    
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
        self.total_steps = 11
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
        
        # Configure grid weights for left-right layout
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=2)  # Left column (controls) - more space
        main_frame.columnconfigure(1, weight=1)  # Right column (log) - half space
        main_frame.rowconfigure(0, weight=1)
        
        # Create left and right frames
        left_frame = ttk.Frame(main_frame)  # Controls frame (left side)
        left_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        left_frame.columnconfigure(0, weight=1)
        left_frame.rowconfigure(0, weight=1)
        
        right_frame = ttk.Frame(main_frame)  # Log frame (right side)
        right_frame.grid(row=0, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(0, weight=1)  # Log output
        right_frame.rowconfigure(1, weight=0)  # Function selection (fixed height)
        
        # Title for left panel (controls)
        title_label = ttk.Label(left_frame, text="Bivicom Network Bot", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, pady=(0, 20))
        
        # Target IP configuration frame
        ip_frame = ttk.LabelFrame(left_frame, text="Target Device Configuration", padding="5")
        ip_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(ip_frame, text="Target LAN IP:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10))
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
        
        # Final LAN IP configuration (for REVERSE step)
        ttk.Label(ip_frame, text="Final LAN IP (Step 10):").grid(row=4, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        self.final_ip_var = tk.StringVar(value="192.168.1.1")
        self.final_ip_entry = ttk.Entry(ip_frame, textvariable=self.final_ip_var, width=15)
        self.final_ip_entry.grid(row=4, column=1, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        
        ttk.Label(ip_frame, text="(Default: 192.168.1.1)", 
                 font=("Arial", 8), foreground="gray").grid(row=4, column=2, sticky=tk.W, pady=(5, 0))
        
        # Final password configuration (for set-password step)
        ttk.Label(ip_frame, text="Final Password (Step 11):").grid(row=5, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        self.final_password_var = tk.StringVar(value="admin")
        self.final_password_entry = ttk.Entry(ip_frame, textvariable=self.final_password_var, width=15, show="*")
        self.final_password_entry.grid(row=5, column=1, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        
        # Show/Hide final password button
        self.show_final_password_var = tk.BooleanVar()
        self.show_final_password_check = ttk.Checkbutton(ip_frame, text="Show", variable=self.show_final_password_var, 
                                                       command=self.toggle_final_password_visibility)
        self.show_final_password_check.grid(row=5, column=2, sticky=tk.W, padx=(5, 0), pady=(5, 0))
        
        ttk.Label(ip_frame, text="(Default: admin)", 
                 font=("Arial", 8), foreground="gray").grid(row=5, column=3, sticky=tk.W, pady=(5, 0))
        
        # Node-RED Flows Configuration
        ttk.Label(ip_frame, text="Flows Source:").grid(row=6, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        self.flows_source_var = tk.StringVar(value="github")
        flows_source_combo = ttk.Combobox(ip_frame, textvariable=self.flows_source_var, width=15, state="readonly")
        flows_source_combo['values'] = ("auto", "local", "github", "uploaded")
        flows_source_combo.grid(row=6, column=1, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        
        ttk.Label(ip_frame, text="(auto=detect, local=./nodered_flows_backup, github=download, uploaded=use uploaded files)", 
                 font=("Arial", 8), foreground="gray").grid(row=6, column=2, columnspan=2, sticky=tk.W, pady=(5, 0))
        
        # Package.json Source Configuration
        ttk.Label(ip_frame, text="Package Source:").grid(row=7, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        self.package_source_var = tk.StringVar(value="github")
        package_source_combo = ttk.Combobox(ip_frame, textvariable=self.package_source_var, width=15, state="readonly")
        package_source_combo['values'] = ("auto", "local", "github", "uploaded")
        package_source_combo.grid(row=7, column=1, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        
        ttk.Label(ip_frame, text="(auto=detect, local=./nodered_flows_backup, github=download, uploaded=use uploaded files)", 
                 font=("Arial", 8), foreground="gray").grid(row=7, column=2, columnspan=2, sticky=tk.W, pady=(5, 0))
        
        
        # File Upload Configuration
        upload_frame = ttk.LabelFrame(left_frame, text="File Upload", padding="5")
        upload_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(10, 10))
        
        # Upload flows.json button
        ttk.Label(upload_frame, text="Upload flows.json:").grid(row=0, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        self.upload_flows_button = ttk.Button(upload_frame, text="Choose File", command=self.upload_flows_file)
        self.upload_flows_button.grid(row=0, column=1, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        
        # Upload package.json button
        ttk.Label(upload_frame, text="Upload package.json:").grid(row=1, column=0, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        self.upload_package_button = ttk.Button(upload_frame, text="Choose File", command=self.upload_package_file)
        self.upload_package_button.grid(row=1, column=1, sticky=tk.W, padx=(0, 10), pady=(5, 0))
        
        # File status labels
        self.flows_status_label = ttk.Label(upload_frame, text="No file selected", font=("Arial", 8), foreground="gray")
        self.flows_status_label.grid(row=0, column=2, sticky=tk.W, padx=(10, 0), pady=(5, 0))
        
        self.package_status_label = ttk.Label(upload_frame, text="No file selected", font=("Arial", 8), foreground="gray")
        self.package_status_label.grid(row=1, column=2, sticky=tk.W, padx=(10, 0), pady=(5, 0))
        
        # Clear uploaded files button
        self.clear_files_button = ttk.Button(upload_frame, text="Clear Uploaded Files", command=self.clear_uploaded_files)
        self.clear_files_button.grid(row=2, column=0, columnspan=3, pady=(10, 0))
        
        # Initialize uploaded files tracking
        self.uploaded_flows_file = None
        self.uploaded_package_file = None
        self.upload_dir = os.path.join(os.path.dirname(__file__), "uploaded_files")
        
        # Create upload directory if it doesn't exist
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)
        
        # Function selection frame (moved to right panel under log output)
        selection_frame = ttk.LabelFrame(right_frame, text="Function Selection", padding="5")
        selection_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        
        # Select All/None buttons
        button_frame = ttk.Frame(selection_frame)
        button_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Button(button_frame, text="Select All", command=self.select_all_functions).grid(row=0, column=0, padx=(0, 10))
        ttk.Button(button_frame, text="Select None", command=self.select_none_functions).grid(row=0, column=1, padx=(0, 10))
        ttk.Button(button_frame, text="Quick Setup", command=self.select_quick_setup).grid(row=0, column=2, padx=(0, 10))
        
        # Create function selection checkboxes with dependencies
        self.function_vars = []
        self.function_labels = []
        self.function_descriptions = [
            ("forward", "Configure Network FORWARD (WAN=eth1 DHCP, LAN=eth0 static)", []),
            ("check-dns", "Check DNS Connectivity", []),
            ("fix-dns", "Fix DNS Configuration (add Google DNS)", []),
            ("install-curl", "Install curl package", []),
            ("install-docker", "Install Docker (after network config)", ["forward"]),
            ("install-services", "Install All Docker Services (Node-RED, Portainer, Restreamer)", ["install-docker"]),
            ("install-nodered-nodes", "Install Node-RED Nodes (ffmpeg, queue-gate, sqlite, serialport)", ["install-services"]),
            ("import-nodered-flows", "Import Node-RED Flows", ["install-services"]),
            ("update-nodered-auth", "Update Node-RED Authentication (uses GUI password)", ["install-services"]),
            ("install-tailscale", "Install Tailscale VPN Router", ["install-docker"]),
            ("reverse", "Configure Network REVERSE (uses Final LAN IP)", []),
            ("set-password", "Change Device Password (uses Final Password)", [])
        ]
        
        for i, (command, description, dependencies) in enumerate(self.function_descriptions):
            # Create checkbox variable
            var = tk.BooleanVar()
            self.function_vars.append((var, command, dependencies))
            
            # Create checkbox
            checkbox = ttk.Checkbutton(selection_frame, variable=var, 
                                     command=self.update_selected_functions)
            checkbox.grid(row=i+1, column=0, sticky=tk.W, padx=(0, 10), pady=2)
            
            # Create label
            label = ttk.Label(selection_frame, text=f"{i+1}. {description}", 
                             font=("Arial", 9))
            label.grid(row=i+1, column=1, sticky=tk.W, pady=2)
            self.function_labels.append(label)
        
        # Selected functions summary
        self.selected_summary = ttk.Label(selection_frame, text="Selected: 0 functions", 
                                         font=("Arial", 10, "bold"), foreground="blue")
        self.selected_summary.grid(row=12, column=0, columnspan=2, sticky=tk.W, pady=(10, 0))
        
        # Configuration sequence progress frame (moved to end of function selection)
        sequence_frame = ttk.LabelFrame(selection_frame, text="Execution Progress", padding="3")
        sequence_frame.grid(row=13, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # Add toggle button for execution progress
        self.show_progress_var = tk.BooleanVar(value=False)  # Hidden by default
        self.show_progress_check = ttk.Checkbutton(sequence_frame, text="Show Progress Details", 
                                                 variable=self.show_progress_var, 
                                                 command=self.toggle_progress_display)
        self.show_progress_check.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 2))
        
        # Progress summary
        self.progress_summary = ttk.Label(sequence_frame, text="Ready to execute selected functions", 
                                         font=("Arial", 8, "bold"), foreground="blue")
        self.progress_summary.grid(row=1, column=0, sticky=tk.W, pady=(0, 2))
        
        # Step progress indicators
        self.step_indicators = []
        self.step_labels = []
        
        # Create step indicators for each possible function
        step_descriptions = [
            "Configure Network FORWARD",
            "Check DNS Connectivity", 
            "Fix DNS Configuration",
            "Install curl",
            "Install Docker",
            "Install All Docker Services",
            "Install Node-RED Nodes",
            "Import Node-RED Flows",
            "Update Node-RED Authentication",
            "Install Tailscale VPN Router",
            "Configure Network REVERSE",
            "Change Device Password"
        ]
        
        # Create a scrollable frame for step indicators
        canvas = tk.Canvas(sequence_frame, height=40, bg="white")
        scrollbar = ttk.Scrollbar(sequence_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Create step indicators
        for i, description in enumerate(step_descriptions):
            # Create frame for each step
            step_frame = ttk.Frame(scrollable_frame)
            step_frame.grid(row=i, column=0, sticky=(tk.W, tk.E), pady=1)
            
            # Status indicator (circle/checkmark) - smaller
            status_label = ttk.Label(step_frame, text="○", font=("Arial", 10), foreground="gray")
            status_label.grid(row=0, column=0, padx=(0, 5))
            self.step_indicators.append(status_label)
            
            # Step description - smaller font
            step_label = ttk.Label(step_frame, text=f"{i+1}. {description}", 
                                 font=("Arial", 8), foreground="gray")
            step_label.grid(row=0, column=1, sticky=tk.W)
            self.step_labels.append(step_label)
        
        # Place canvas and scrollbar
        canvas.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 1))
        scrollbar.grid(row=2, column=1, sticky=(tk.N, tk.S), pady=(0, 1))
        
        # Configure grid weights for scrolling
        sequence_frame.rowconfigure(2, weight=1)
        sequence_frame.columnconfigure(0, weight=1)
        
        # Store references for toggle functionality
        self.progress_canvas = canvas
        self.progress_scrollbar = scrollbar
        
        # Tailscale Auth Key configuration frame
        tailscale_frame = ttk.LabelFrame(left_frame, text="Tailscale Configuration", padding="5")
        tailscale_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
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
        control_frame = ttk.Frame(left_frame)
        control_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
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
        
        # Log display (in right frame)
        log_frame = ttk.LabelFrame(right_frame, text="Log Output", padding="5")
        log_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # Create scrolled text widget with custom tags for colors
        self.log_text = scrolledtext.ScrolledText(log_frame, height=20, width=80,
                                                 font=("Consolas", 9), wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure text tags for colored output (more vibrant colors)
        self.log_text.tag_configure("INFO", foreground="#2E7D32", font=("Consolas", 9))  # Dark green for info
        self.log_text.tag_configure("SUCCESS", foreground="#00C853", font=("Consolas", 9, "bold"))  # Bright green for success
        self.log_text.tag_configure("WARNING", foreground="#FF6F00", font=("Consolas", 9, "bold"))  # Orange for warnings
        self.log_text.tag_configure("ERROR", foreground="#D32F2F", font=("Consolas", 9, "bold"))  # Red for errors
        self.log_text.tag_configure("DEBUG", foreground="#616161", font=("Consolas", 8))  # Gray for debug
        
        # Progress bar (moved to left frame)
        self.progress = ttk.Progressbar(left_frame, mode='indeterminate')
        self.progress.grid(row=5, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Bottom info frame (moved to left frame)
        info_frame = ttk.Frame(left_frame)
        info_frame.grid(row=6, column=0, sticky=(tk.W, tk.E), pady=(10, 0))
        
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
    
    def toggle_final_password_visibility(self):
        """Toggle final password visibility"""
        if self.show_final_password_var.get():
            self.final_password_entry.config(show="")
        else:
            self.final_password_entry.config(show="*")
    
    def upload_flows_file(self):
        """Upload flows.json file"""
        try:
            file_path = filedialog.askopenfilename(
                title="Select flows.json file",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if file_path:
                # Validate Node-RED flows.json structure
                is_valid, message = self.validate_flows_json(file_path)
                
                if not is_valid:
                    messagebox.showerror("Invalid flows.json", f"The selected file is not a valid Node-RED flows.json file.\n\nError: {message}")
                    self.log_message(f"❌ Invalid flows.json structure: {message}", "ERROR")
                    return
                
                try:
                    # Copy file to upload directory
                    dest_path = os.path.join(self.upload_dir, "flows.json")
                    shutil.copy2(file_path, dest_path)
                    
                    self.uploaded_flows_file = dest_path
                    filename = os.path.basename(file_path)
                    self.flows_status_label.config(text=f"✓ {filename}", foreground="green")
                    
                    self.log_message(f"✅ Uploaded valid flows.json: {filename}", "SUCCESS")
                    self.log_message(f"📋 Validation: {message}", "INFO")
                    
                    # Update flows source to use uploaded file
                    self.flows_source_var.set("uploaded")
                    
                except Exception as e:
                    messagebox.showerror("Upload Error", f"Failed to upload flows.json: {e}")
                    self.log_message(f"❌ Failed to upload flows.json: {e}", "ERROR")
                    
        except Exception as e:
            self.log_message(f"❌ Error selecting flows.json file: {e}", "ERROR")
    
    def upload_package_file(self):
        """Upload package.json file"""
        try:
            file_path = filedialog.askopenfilename(
                title="Select package.json file",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            
            if file_path:
                # Validate Node-RED package.json structure
                is_valid, message = self.validate_package_json(file_path)
                
                if not is_valid:
                    messagebox.showerror("Invalid package.json", f"The selected file is not a valid Node-RED package.json file.\n\nError: {message}")
                    self.log_message(f"❌ Invalid package.json structure: {message}", "ERROR")
                    return
                
                try:
                    # Copy file to upload directory
                    dest_path = os.path.join(self.upload_dir, "package.json")
                    shutil.copy2(file_path, dest_path)
                    
                    self.uploaded_package_file = dest_path
                    filename = os.path.basename(file_path)
                    self.package_status_label.config(text=f"✓ {filename}", foreground="green")
                    
                    self.log_message(f"✅ Uploaded valid package.json: {filename}", "SUCCESS")
                    self.log_message(f"📋 Validation: {message}", "INFO")
                    
                    # Update package source to use uploaded file
                    self.package_source_var.set("uploaded")
                    
                except Exception as e:
                    messagebox.showerror("Upload Error", f"Failed to upload package.json: {e}")
                    self.log_message(f"❌ Failed to upload package.json: {e}", "ERROR")
                    
        except Exception as e:
            self.log_message(f"❌ Error selecting package.json file: {e}", "ERROR")
    
    def clear_uploaded_files(self):
        """Clear all uploaded files"""
        try:
            # Remove uploaded files
            if self.uploaded_flows_file and os.path.exists(self.uploaded_flows_file):
                os.remove(self.uploaded_flows_file)
                self.uploaded_flows_file = None
                self.flows_status_label.config(text="No file selected", foreground="gray")
                
            if self.uploaded_package_file and os.path.exists(self.uploaded_package_file):
                os.remove(self.uploaded_package_file)
                self.uploaded_package_file = None
                self.package_status_label.config(text="No file selected", foreground="gray")
            
            # Reset flows source to github if it was set to uploaded
            if self.flows_source_var.get() == "uploaded":
                self.flows_source_var.set("github")
            
            # Reset package source to github if it was set to uploaded
            if self.package_source_var.get() == "uploaded":
                self.package_source_var.set("github")
            
            self.log_message("🗑️ Cleared all uploaded files", "INFO")
            
        except Exception as e:
            self.log_message(f"❌ Error clearing uploaded files: {e}", "ERROR")
    
    def toggle_progress_display(self):
        """Toggle the display of detailed progress indicators"""
        if self.show_progress_var.get():
            # Show progress details
            self.progress_canvas.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 1))
            self.progress_scrollbar.grid(row=2, column=1, sticky=(tk.N, tk.S), pady=(0, 1))
        else:
            # Hide progress details
            self.progress_canvas.grid_remove()
            self.progress_scrollbar.grid_remove()
    
    def get_effective_flows_source(self):
        """Get the effective flows source based on uploaded files and user selection"""
        # If both files are uploaded, use uploaded version
        if self.uploaded_flows_file and self.uploaded_package_file:
            return "uploaded"
        
        # If only flows.json is uploaded, use uploaded version
        if self.uploaded_flows_file:
            return "uploaded"
        
        # Otherwise use user selection
        return self.flows_source_var.get()
    
    def get_effective_package_source(self):
        """Get the effective package source based on uploaded files and user selection"""
        # If both files are uploaded, use uploaded version
        if self.uploaded_flows_file and self.uploaded_package_file:
            return "uploaded"
        
        # If only package.json is uploaded, use uploaded version
        if self.uploaded_package_file:
            return "uploaded"
        
        # Otherwise use user selection
        return self.package_source_var.get()
    
    def validate_flows_json(self, file_path):
        """Validate Node-RED flows.json structure"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                flows_data = json.load(f)
            
            # Check if it's a list (Node-RED flows format)
            if not isinstance(flows_data, list):
                return False, "flows.json must be a JSON array"
            
            # Check for required Node-RED flow structure
            has_tab = False
            has_node = False
            
            for item in flows_data:
                if not isinstance(item, dict):
                    return False, "Each flow item must be a JSON object"
                
                # Check for required fields
                if 'id' not in item or 'type' not in item:
                    return False, "Each flow item must have 'id' and 'type' fields"
                
                # Check for tab (workspace) or node types
                if item.get('type') == 'tab':
                    has_tab = True
                    # Validate tab structure
                    if 'label' not in item:
                        return False, "Tab items must have a 'label' field"
                elif item.get('type') in ['inject', 'debug', 'function', 'switch', 'change', 'http in', 'http response', 'mqtt in', 'mqtt out', 'serial in', 'serial out']:
                    has_node = True
                elif item.get('type') == 'group':
                    # Groups are valid but don't count as nodes
                    pass
                else:
                    # Unknown type, but don't fail validation for custom nodes
                    has_node = True
            
            # At minimum, should have at least one tab or one node
            if not has_tab and not has_node:
                return False, "flows.json should contain at least one tab or node"
            
            return True, "Valid Node-RED flows.json structure"
            
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON format: {e}"
        except Exception as e:
            return False, f"Error reading file: {e}"
    
    def validate_package_json(self, file_path):
        """Validate Node-RED package.json structure"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                package_data = json.load(f)
            
            # Check if it's an object
            if not isinstance(package_data, dict):
                return False, "package.json must be a JSON object"
            
            # Check for required fields
            required_fields = ['name', 'version']
            for field in required_fields:
                if field not in package_data:
                    return False, f"package.json must have '{field}' field"
            
            # Validate name field
            if not isinstance(package_data['name'], str) or not package_data['name'].strip():
                return False, "package.json 'name' field must be a non-empty string"
            
            # Validate version field
            if not isinstance(package_data['version'], str) or not package_data['version'].strip():
                return False, "package.json 'version' field must be a non-empty string"
            
            # Check for dependencies (optional but common)
            if 'dependencies' in package_data:
                if not isinstance(package_data['dependencies'], dict):
                    return False, "package.json 'dependencies' must be an object"
                
                # Validate dependency format
                for dep_name, dep_version in package_data['dependencies'].items():
                    if not isinstance(dep_name, str) or not dep_name.strip():
                        return False, f"Invalid dependency name: {dep_name}"
                    if not isinstance(dep_version, str) or not dep_version.strip():
                        return False, f"Invalid dependency version for {dep_name}: {dep_version}"
            
            # Check for Node-RED specific fields (optional)
            if 'node-red' in package_data:
                if not isinstance(package_data['node-red'], dict):
                    return False, "package.json 'node-red' field must be an object"
            
            return True, "Valid Node-RED package.json structure"
            
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON format: {e}"
        except Exception as e:
            return False, f"Error reading file: {e}"
    
    def select_all_functions(self):
        """Select all functions"""
        for var, command, dependencies in self.function_vars:
            var.set(True)
        self.update_selected_functions()
    
    def select_none_functions(self):
        """Select no functions"""
        for var, command, dependencies in self.function_vars:
            var.set(False)
        self.update_selected_functions()
    
    def select_quick_setup(self):
        """Select essential functions for quick setup"""
        # Reset all first
        self.select_none_functions()
        
        # Select essential functions
        essential_commands = ["forward", "install-docker", "install-services", "install-nodered-nodes", "import-nodered-flows", "update-nodered-auth", "reverse"]
        for var, command, dependencies in self.function_vars:
            if command in essential_commands:
                var.set(True)
        
        self.update_selected_functions()
    
    def update_selected_functions(self):
        """Update function selection and check dependencies"""
        selected_count = 0
        dependency_warnings = []
        
        # Check each selected function for dependencies
        for var, command, dependencies in self.function_vars:
            if var.get():
                selected_count += 1
                # Check if dependencies are met
                for dep in dependencies:
                    dep_var = next((v for v, c, d in self.function_vars if c == dep), None)
                    if not dep_var or not dep_var.get():
                        dependency_warnings.append(f"{command} requires {dep}")
        
        # Update summary
        self.selected_summary.config(text=f"Selected: {selected_count} functions")
        
        # Show dependency warnings
        if dependency_warnings:
            warning_text = "⚠️ Dependencies: " + "; ".join(dependency_warnings)
            self.selected_summary.config(text=f"Selected: {selected_count} functions - {warning_text}", foreground="orange")
        else:
            self.selected_summary.config(foreground="blue")
    
    def get_selected_functions(self):
        """Get list of selected function commands in dependency order"""
        # Create a mapping of command to index for ordering
        command_order = {command: i for i, (command, _, _) in enumerate(self.function_descriptions)}
        
        # Get selected functions
        selected = []
        for var, command, dependencies in self.function_vars:
            if var.get():
                selected.append((command, command_order[command]))
        
        # Sort by original order
        selected.sort(key=lambda x: x[1])
        return [command for command, _ in selected]
    
    def update_step_progress(self, step_number, success=True):
        """Update step progress with visual feedback"""
        # Update progress summary
        if success:
            self.progress_summary.config(text=f"Step {step_number} completed successfully", foreground="green")
            # Play success sound for completed steps
            threading.Thread(target=lambda: play_sound("success"), daemon=True).start()
        else:
            self.progress_summary.config(text=f"Step {step_number} failed", foreground="red")
            # Play error sound for failed steps
            threading.Thread(target=lambda: play_sound("error"), daemon=True).start()
        
        # Update visual step indicators
        if 0 <= step_number - 1 < len(self.step_indicators):
            if success:
                # Show checkmark for completed step
                self.step_indicators[step_number - 1].config(text="✓", foreground="green", font=("Arial", 12, "bold"))
                self.step_labels[step_number - 1].config(foreground="green")
            else:
                # Show X for failed step
                self.step_indicators[step_number - 1].config(text="✗", foreground="red", font=("Arial", 12, "bold"))
                self.step_labels[step_number - 1].config(foreground="red")
    
    def reset_step_indicators(self):
        """Reset all step indicators to default state"""
        for i in range(len(self.step_indicators)):
            self.step_indicators[i].config(text="○", foreground="gray", font=("Arial", 10))
            self.step_labels[i].config(foreground="gray")
    
    def highlight_current_step(self, step_number):
        """Highlight the current step being executed"""
        if 0 <= step_number - 1 < len(self.step_indicators):
            # Reset all indicators first
            self.reset_step_indicators()
            # Highlight current step
            self.step_indicators[step_number - 1].config(text="●", foreground="blue", font=("Arial", 12, "bold"))
            self.step_labels[step_number - 1].config(foreground="blue")
    
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
            
            # Reset progress summary and step indicators
            self.progress_summary.config(text="Starting execution...", foreground="blue")
            self.reset_step_indicators()
            
            # Get configuration from GUI
            target_ip = self.target_ip_var.get().strip() or "192.168.1.1"
            scan_interval = int(self.scan_interval_var.get().strip() or "10")
            username = self.username_var.get().strip() or "admin"
            password = self.password_var.get().strip() or "admin"
            final_ip = self.final_ip_var.get().strip() or "192.168.1.1"
            final_password = self.final_password_var.get().strip() or "admin"
            flows_source = self.get_effective_flows_source()
            package_source = self.get_effective_package_source()
            
            # Create bot instance with GUI logging integration
            self.bot = GUIBotWrapper(self.log_message, target_ip, scan_interval, self.update_step_progress, username, password, self.highlight_current_step, final_ip, final_password, flows_source, package_source, self.uploaded_flows_file, self.uploaded_package_file)
            
            # Set selected functions for the bot
            selected_functions = self.get_selected_functions()
            self.bot.selected_functions = selected_functions
            
            # Validate that functions are selected
            if not selected_functions:
                raise ValueError("No functions selected. Please select at least one function to run.")
            
            # Log the effective sources being used
            self.log_message(f"📋 Using flows source: {flows_source}", "INFO")
            self.log_message(f"📦 Using package source: {package_source}", "INFO")
            
            # Log uploaded files status
            if self.uploaded_flows_file:
                self.log_message(f"📁 Uploaded flows.json: {os.path.basename(self.uploaded_flows_file)}", "INFO")
            if self.uploaded_package_file:
                self.log_message(f"📁 Uploaded package.json: {os.path.basename(self.uploaded_package_file)}", "INFO")
            
            # Set Tailscale auth key from GUI input (do this in main thread)
            tailscale_auth = self.tailscale_auth_var.get().strip()
            if tailscale_auth and tailscale_auth != "YOUR_TAILSCALE_AUTH_KEY_HERE":
                os.environ["TAILSCALE_AUTH_KEY"] = tailscale_auth
            
            # Start bot in separate thread
            self.bot_thread = threading.Thread(target=self.run_bot, daemon=True)
            self.bot_thread.start()
            
            self.log_message("Bot started successfully", "SUCCESS")
            
        except Exception as e:
            self.log_message(f"Failed to start bot: {e}", "ERROR")
            self.log_message("Please check your function selections and try again", "INFO")
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
            
            # Get configuration from GUI (do this in main thread)
            target_ip = self.target_ip_var.get().strip() or "192.168.1.1"
            username = self.username_var.get().strip() or "admin"
            password = self.password_var.get().strip() or "admin"
            
            # Start reset in separate thread to avoid blocking GUI
            self.reset_button.config(text="Resetting...", state="disabled")
            self.status_label.config(text="Status: Resetting Device...")
            
            # Start reset thread
            reset_thread = threading.Thread(target=self.run_reset_device, args=(target_ip, username, password))
            reset_thread.daemon = True
            reset_thread.start()
            
        except Exception as e:
            self.log_message(f"Failed to start reset: {e}", "ERROR")
            self.reset_button.config(text="Reset Device", state="normal")
            self.status_label.config(text="Status: Error")
    
    def run_reset_device(self, target_ip, username, password):
        """Run reset device command in separate thread"""
        try:
            self.log_message("🔄 Starting device reset...", "WARNING")
            self.log_message(f"🎯 Target device: {target_ip}", "INFO")
            self.log_message(f"👤 Username: {username}", "INFO")
            
            # Reset progress summary
            self.progress_summary.config(text="Starting device reset...", foreground="blue")
            
            # Run reset command with real-time output
            cmd = [self.script_path, "--remote", target_ip, username, password, "reset-device"]
            self.log_message(f"🔧 Running reset command: {' '.join(cmd)}", "INFO")
            
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,  # Merge stderr into stdout
                text=True, 
                bufsize=1,  # Line buffered
                universal_newlines=True
            )
            
            # Stream output in real-time
            output_lines = []
            import select
            
            # Use select for timeout handling (Unix/macOS)
            if hasattr(select, 'select'):
                while True:
                    # Check if process is still running
                    if process.poll() is not None:
                        # Process finished, read any remaining output
                        remaining_output = process.stdout.read()
                        if remaining_output:
                            for line in remaining_output.splitlines():
                                if line.strip():
                                    self.log_message(f"📄 {line.strip()}", "INFO")
                                    print(f"[RESET OUTPUT] {line.strip()}")
                        break
                    
                    # Check for output with timeout
                    ready, _, _ = select.select([process.stdout], [], [], 1.0)  # 1 second timeout
                    if ready:
                        output = process.stdout.readline()
                        if output:
                            output_line = output.strip()
                            if output_line:  # Only log non-empty lines
                                self.log_message(f"📄 {output_line}", "INFO")
                                output_lines.append(output_line)
                                # Also print to Python terminal
                                print(f"[RESET OUTPUT] {output_line}")
            else:
                # Fallback for Windows (no select module)
                while True:
                    output = process.stdout.readline()
                    if output == '' and process.poll() is not None:
                        break
                    if output:
                        output_line = output.strip()
                        if output_line:  # Only log non-empty lines
                            self.log_message(f"📄 {output_line}", "INFO")
                            output_lines.append(output_line)
                            # Also print to Python terminal
                            print(f"[RESET OUTPUT] {output_line}")
            
            # Wait for process to complete and get return code
            return_code = process.wait()
            
            if return_code == 0:
                self.log_message("✅ Device reset completed successfully!", "SUCCESS")
                # Show success notification
                self.show_notification("Device Reset", "Device has been reset to default state successfully!")
                # Play completion sound
                threading.Thread(target=lambda: play_sound("completion"), daemon=True).start()
            else:
                self.log_message(f"❌ Device reset failed with return code {return_code}!", "ERROR")
                
                # Show error notification with more details
                error_msg = "Device reset encountered errors."
                if any("uci: command not found" in line for line in output_lines):
                    error_msg += "\n\nThis device may not be running OpenWrt or UCI is not installed."
                elif any("Permission denied" in line for line in output_lines):
                    error_msg += "\n\nPermission denied. Please check your username and password."
                elif any("Connection refused" in line for line in output_lines):
                    error_msg += "\n\nConnection refused. Please check if the device is reachable."
                else:
                    error_msg += f"\n\nReturn code: {return_code}"
                self.show_notification("Device Reset Failed", error_msg)
            
            # Update UI elements in main thread
            self.root.after(0, lambda: self.reset_button.config(text="Reset Device", state="normal"))
            self.root.after(0, lambda: self.status_label.config(text="Status: Ready"))
            self.root.after(0, lambda: self.progress_summary.config(text="Device reset completed", foreground="green"))
                
        except subprocess.TimeoutExpired:
            self.log_message("⏰ Device reset timed out after 10 minutes", "ERROR")
            self.show_notification("Device Reset Timeout", "Device reset timed out. Check device connectivity.")
            # Update UI elements in main thread
            self.root.after(0, lambda: self.reset_button.config(text="Reset Device", state="normal"))
            self.root.after(0, lambda: self.status_label.config(text="Status: Timeout"))
        except Exception as e:
            self.log_message(f"❌ Error during device reset: {e}", "ERROR")
            self.show_notification("Device Reset Error", f"Error during reset: {e}")
            # Update UI elements in main thread
            self.root.after(0, lambda: self.reset_button.config(text="Reset Device", state="normal"))
            self.root.after(0, lambda: self.status_label.config(text="Status: Error"))
    
    def run_bot(self):
        """Run the bot (called in separate thread)"""
        try:
            self.log_message("Starting network bot with 12-step configuration sequence", "INFO")
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
                # Play completion sound
                threading.Thread(target=lambda: play_sound("completion"), daemon=True).start()
            
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
