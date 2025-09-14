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
                    "cmd": [self.script_path, "--remote", self.target_ip, self.username, self.password, "install-tailscale", self.tailscale_auth_key_var.get()],
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
    
    def execute_single_command(self, command, *args):
        """Execute a single command on the target device"""
        try:
            # Build command
            cmd = [self.script_path, "--remote", self.target_ip, self.username, self.password, command]
            if args:
                cmd.extend(args)
            
            self.log_message(f"🔧 Executing: {' '.join(cmd)}", "INFO")
            
            # Execute command
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.log_message("✅ Command executed successfully", "SUCCESS")
                if result.stdout:
                    self.log_message(f"📤 Output: {result.stdout.strip()}", "INFO")
                return True
            else:
                self.log_message(f"❌ Command failed with return code {result.returncode}", "ERROR")
                if result.stderr:
                    self.log_message(f"📤 Error: {result.stderr.strip()}", "ERROR")
                return False
                
        except subprocess.TimeoutExpired:
            self.log_message("⏰ Command timed out after 5 minutes", "ERROR")
            return False
        except Exception as e:
            self.log_message(f"❌ Error executing command: {str(e)}", "ERROR")
            return False

class NetworkBotGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Bivicom Network Bot - Device Configuration")
        self.root.geometry("1200x900")
        self.root.minsize(1100, 800)
        
        # Modern color scheme
        self.colors = {
            'primary': '#2E86AB',      # Professional blue
            'secondary': '#A23B72',    # Accent purple
            'success': '#28A745',      # Green
            'warning': '#FFC107',      # Amber
            'danger': '#DC3545',       # Red
            'info': '#17A2B8',         # Cyan
            'light': '#F8F9FA',        # Light gray
            'dark': '#343A40',         # Dark gray
            'white': '#FFFFFF',        # White
            'border': '#DEE2E6',       # Light border
            'text_primary': '#212529', # Dark text
            'text_secondary': '#6C757D', # Muted text
            'background': '#F5F7FA'    # Main background
        }
        
        self.root.configure(bg=self.colors['background'])
        
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
        """Create and arrange GUI widgets with modern design"""
        # Main container with padding
        main_container = tk.Frame(self.root, bg=self.colors['background'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Configure grid weights for 3-column layout with equal sizing
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # Set equal column weights and uniform sizing
        main_container.columnconfigure(0, weight=1, uniform="column")  # Column 1
        main_container.columnconfigure(1, weight=1, uniform="column")  # Column 2
        main_container.columnconfigure(2, weight=1, uniform="column")  # Column 3
        main_container.rowconfigure(0, weight=1)
        
        # Create header
        self.create_header(main_container)
        
        # Create column 1 (Device Config + File Upload)
        column1_panel = self.create_column1_panel(main_container)
        
        # Create column 2 (Tailscale + Control Buttons)
        column2_panel = self.create_column2_panel(main_container)
        
        # Create column 3 (Log + Function Selection)
        column3_panel = self.create_column3_panel(main_container)
        
        # Create footer
        self.create_footer(main_container)
    
    def create_header(self, parent):
        """Create modern header with title and status"""
        header_frame = tk.Frame(parent, bg=self.colors['white'], relief=tk.FLAT, bd=0)
        header_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))
        header_frame.columnconfigure(0, weight=1)
        
        # Main title
        title_label = tk.Label(header_frame, 
                              text="🚀 Bivicom Network Bot", 
                              font=("SF Pro Display", 10, "bold"),
                              fg=self.colors['primary'],
                              bg=self.colors['white'])
        title_label.grid(row=0, column=0, pady=20, padx=30, sticky=tk.W)
        
        # Subtitle
        subtitle_label = tk.Label(header_frame,
                                 text="Professional Device Configuration & Management",
                                 font=("SF Pro Text", 10),
                                 fg=self.colors['text_secondary'],
                                 bg=self.colors['white'])
        subtitle_label.grid(row=1, column=0, pady=(0, 20), padx=30, sticky=tk.W)
        
        # Status indicator
        self.status_frame = tk.Frame(header_frame, bg=self.colors['white'])
        self.status_frame.grid(row=0, column=1, rowspan=2, padx=30, pady=20, sticky=tk.E)
        
        self.status_indicator = tk.Label(self.status_frame,
                                        text="●",
                                        font=("Arial", 10),
                                        fg=self.colors['success'],
                                        bg=self.colors['white'])
        self.status_indicator.pack(side=tk.LEFT, padx=(0, 8))
        
        self.status_label = tk.Label(self.status_frame,
                                    text="Ready",
                                    font=("SF Pro Text", 10, "bold"),
                                            fg="black",
                                    bg=self.colors['white'])
        self.status_label.pack(side=tk.LEFT)
    
    def create_column1_panel(self, parent):
        """Create column 1 with device configuration, file upload, and Tailscale configuration"""
        column1_panel = tk.Frame(parent, bg=self.colors['background'])
        column1_panel.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 7))
        column1_panel.columnconfigure(0, weight=1)
        column1_panel.rowconfigure(0, weight=1)
        
        # Device Configuration Section
        self.create_device_config_section(column1_panel)
        
        # File Upload Section
        self.create_file_upload_section(column1_panel)
        
        # Tailscale Configuration Section
        self.create_tailscale_section(column1_panel)
        
        return column1_panel
    
    def create_column2_panel(self, parent):
        """Create column 2 with control buttons and function selection"""
        column2_panel = tk.Frame(parent, bg=self.colors['background'])
        column2_panel.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 7))
        column2_panel.columnconfigure(0, weight=1)
        column2_panel.rowconfigure(0, weight=1)  # Control buttons
        column2_panel.rowconfigure(1, weight=4)  # Function selection (more space)
        
        # Control Buttons Section
        self.create_control_buttons_section(column2_panel)
        
        # Function Selection Section
        self.create_function_selection_section(column2_panel)
        
        return column2_panel
    
    def create_column3_panel(self, parent):
        """Create column 3 with log output only"""
        column3_panel = tk.Frame(parent, bg=self.colors['background'])
        column3_panel.grid(row=1, column=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        column3_panel.columnconfigure(0, weight=1)
        column3_panel.rowconfigure(0, weight=1)  # Log output fills entire column
        
        # Log Output Section
        self.create_log_section(column3_panel)
        
        return column3_panel
    
    def create_footer(self, parent):
        """Create footer with statistics"""
        footer_frame = tk.Frame(parent, bg=self.colors['white'], relief=tk.FLAT, bd=0)
        footer_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(20, 0))
        footer_frame.columnconfigure(0, weight=1)
        
        # Statistics
        stats_frame = tk.Frame(footer_frame, bg=self.colors['white'])
        stats_frame.grid(row=0, column=0, padx=30, pady=15, sticky=tk.W)
        
        self.scans_label = tk.Label(stats_frame,
                                   text="Scans: 0",
                                   font=("SF Pro Text", 10),
                                   fg=self.colors['text_secondary'],
                                   bg=self.colors['white'])
        self.scans_label.pack(side=tk.LEFT, padx=(0, 20))
        
        self.configs_label = tk.Label(stats_frame,
                                     text="Configurations: 0",
                                     font=("SF Pro Text", 10),
                                     fg=self.colors['text_secondary'],
                                     bg=self.colors['white'])
        self.configs_label.pack(side=tk.LEFT, padx=(0, 20))
        
        # Timestamp
        self.timestamp_label = tk.Label(stats_frame,
                                       text=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                       font=("SF Pro Text", 10),
                                       fg=self.colors['text_secondary'],
                                       bg=self.colors['white'])
        self.timestamp_label.pack(side=tk.RIGHT)
    
    def create_device_config_section(self, parent):
        """Create device configuration section with modern styling"""
        # Section container
        config_frame = tk.Frame(parent, bg=self.colors['white'], relief=tk.FLAT, bd=0)
        config_frame.pack(fill=tk.X, pady=(0, 15))
        config_frame.columnconfigure(0, weight=1)
        
        # Section header
        header_frame = tk.Frame(config_frame, bg=self.colors['primary'], height=40)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        header_label = tk.Label(header_frame,
                               text="⚙️ Device Configuration",
                               font=("SF Pro Text", 10, "bold"),
                               fg=self.colors['white'],
                               bg=self.colors['primary'])
        header_label.pack(side=tk.LEFT, padx=20, pady=10)
        
        # Content frame
        content_frame = tk.Frame(config_frame, bg=self.colors['white'])
        content_frame.pack(fill=tk.X, padx=20, pady=20)
        content_frame.columnconfigure(1, weight=1)
        
        # Target IP
        tk.Label(content_frame, text="Target LAN IP:", 
                font=("SF Pro Text", 10, "bold"),
                                            fg="black",
                bg=self.colors['white']).grid(row=0, column=0, sticky=tk.W, pady=(0, 8))
        
        self.target_ip_var = tk.StringVar(value="192.168.1.1")
        self.target_ip_entry = tk.Entry(content_frame, 
                                       textvariable=self.target_ip_var,
                                       font=("SF Pro Text", 10),
                                       relief=tk.SUNKEN,
                                       bd=2,
                                       bg="white",
                                       fg="black")
        self.target_ip_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=(0, 8), padx=(10, 0))
        
        tk.Label(content_frame, text="(Default: 192.168.1.1)", 
                font=("SF Pro Text", 10),
                fg=self.colors['text_secondary'],
                bg=self.colors['white']).grid(row=0, column=2, sticky=tk.W, pady=(0, 8), padx=(10, 0))
        
        # Username
        tk.Label(content_frame, text="Username:", 
                font=("SF Pro Text", 10, "bold"),
                                            fg="black",
                bg=self.colors['white']).grid(row=1, column=0, sticky=tk.W, pady=(0, 8))
        
        self.username_var = tk.StringVar(value="admin")
        self.username_entry = tk.Entry(content_frame, 
                                      textvariable=self.username_var,
                                      font=("SF Pro Text", 10),
                                      relief=tk.SUNKEN,
                                      bd=2,
                                      bg="white",
                                      fg="black")
        self.username_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), pady=(0, 8), padx=(10, 0))
        
        tk.Label(content_frame, text="(Default: admin)", 
                font=("SF Pro Text", 10),
                fg=self.colors['text_secondary'],
                bg=self.colors['white']).grid(row=1, column=2, sticky=tk.W, pady=(0, 8), padx=(10, 0))
        
        # Password
        tk.Label(content_frame, text="Password:", 
                font=("SF Pro Text", 10, "bold"),
                                            fg="black",
                bg=self.colors['white']).grid(row=2, column=0, sticky=tk.W, pady=(0, 8))
        
        password_frame = tk.Frame(content_frame, bg=self.colors['white'])
        password_frame.grid(row=2, column=1, sticky=(tk.W, tk.E), pady=(0, 8), padx=(10, 0))
        password_frame.columnconfigure(0, weight=1)
        
        self.password_var = tk.StringVar(value="admin")
        self.password_entry = tk.Entry(password_frame, 
                                      textvariable=self.password_var,
                                      font=("SF Pro Text", 10),
                                      relief=tk.SUNKEN,
                                      bd=2,
                                      bg="white",
                                            fg="black",
                                      show="*")
        self.password_entry.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        self.show_password_var = tk.BooleanVar()
        self.show_password_check = tk.Checkbutton(password_frame,
                                                 text="Show",
                                                 variable=self.show_password_var,
                                                 command=self.toggle_password_visibility,
                                                 font=("SF Pro Text", 10),
                                                 fg=self.colors['text_secondary'],
                                                 bg=self.colors['white'],
                                                 selectcolor=self.colors['light'],
                                                 activebackground=self.colors['white'])
        self.show_password_check.grid(row=0, column=1, padx=(10, 0))
        
        tk.Label(content_frame, text="(Default: admin)", 
                font=("SF Pro Text", 10),
                fg=self.colors['text_secondary'],
                bg=self.colors['white']).grid(row=2, column=2, sticky=tk.W, pady=(0, 8), padx=(10, 0))
        
        # Scan Interval
        tk.Label(content_frame, text="Scan Interval:", 
                font=("SF Pro Text", 10, "bold"),
                                            fg="black",
                bg=self.colors['white']).grid(row=3, column=0, sticky=tk.W, pady=(0, 8))
        
        self.scan_interval_var = tk.StringVar(value="10")
        self.scan_interval_entry = tk.Entry(content_frame, 
                                           textvariable=self.scan_interval_var,
                                           font=("SF Pro Text", 10),
                                           relief=tk.FLAT,
                                           bd=1,
                                           bg="white",
                                           fg="black",
                                           width=10)
        self.scan_interval_entry.grid(row=3, column=1, sticky=tk.W, pady=(0, 8), padx=(10, 0))
        
        tk.Label(content_frame, text="seconds (Default: 10)", 
                font=("SF Pro Text", 10),
                fg=self.colors['text_secondary'],
                bg=self.colors['white']).grid(row=3, column=2, sticky=tk.W, pady=(0, 8), padx=(10, 0))
        
        # Final LAN IP
        tk.Label(content_frame, text="Final LAN IP:", 
                font=("SF Pro Text", 10, "bold"),
                                            fg="black",
                bg=self.colors['white']).grid(row=4, column=0, sticky=tk.W, pady=(0, 8))
        
        self.final_ip_var = tk.StringVar(value="192.168.1.1")
        self.final_ip_entry = tk.Entry(content_frame, 
                                      textvariable=self.final_ip_var,
                                      font=("SF Pro Text", 10),
                                      relief=tk.SUNKEN,
                                      bd=2,
                                      bg="white",
                                      fg="black")
        self.final_ip_entry.grid(row=4, column=1, sticky=(tk.W, tk.E), pady=(0, 8), padx=(10, 0))
        
        tk.Label(content_frame, text="(Step 10 - Default: 192.168.1.1)", 
                font=("SF Pro Text", 10),
                fg=self.colors['text_secondary'],
                bg=self.colors['white']).grid(row=4, column=2, sticky=tk.W, pady=(0, 8), padx=(10, 0))
        
        # Final Password
        tk.Label(content_frame, text="Final Password:", 
                font=("SF Pro Text", 10, "bold"),
                                            fg="black",
                bg=self.colors['white']).grid(row=5, column=0, sticky=tk.W, pady=(0, 8))
        
        final_password_frame = tk.Frame(content_frame, bg=self.colors['white'])
        final_password_frame.grid(row=5, column=1, sticky=(tk.W, tk.E), pady=(0, 8), padx=(10, 0))
        final_password_frame.columnconfigure(0, weight=1)
        
        self.final_password_var = tk.StringVar(value="admin")
        self.final_password_entry = tk.Entry(final_password_frame, 
                                            textvariable=self.final_password_var,
                                            font=("SF Pro Text", 10),
                                            relief=tk.FLAT,
                                            bd=1,
                                            bg="white",
                                            fg="black",
                                            show="*")
        self.final_password_entry.grid(row=0, column=0, sticky=(tk.W, tk.E))
        
        self.show_final_password_var = tk.BooleanVar()
        self.show_final_password_check = tk.Checkbutton(final_password_frame,
                                                       text="Show",
                                                       variable=self.show_final_password_var,
                                                       command=self.toggle_final_password_visibility,
                                                       font=("SF Pro Text", 10),
                                                       fg=self.colors['text_secondary'],
                                                       bg=self.colors['white'],
                                                       selectcolor=self.colors['light'],
                                                       activebackground=self.colors['white'])
        self.show_final_password_check.grid(row=0, column=1, padx=(10, 0))
        
        tk.Label(content_frame, text="(Step 11 - Default: admin)", 
                font=("SF Pro Text", 10),
                fg=self.colors['text_secondary'],
                bg=self.colors['white']).grid(row=5, column=2, sticky=tk.W, pady=(0, 8), padx=(10, 0))
        
        # Flows Source
        tk.Label(content_frame, text="Flows Source:", 
                font=("SF Pro Text", 10, "bold"),
                                            fg="black",
                bg=self.colors['white']).grid(row=6, column=0, sticky=tk.W, pady=(0, 8))
        
        self.flows_source_var = tk.StringVar(value="github")
        flows_source_combo = ttk.Combobox(content_frame, 
                                         textvariable=self.flows_source_var,
                                         values=("auto", "local", "github", "uploaded"),
                                         state="readonly",
                                         font=("SF Pro Text", 10))
        flows_source_combo.grid(row=6, column=1, sticky=(tk.W, tk.E), pady=(0, 8), padx=(10, 0))
        
        tk.Label(content_frame, text="(auto=detect, local=./nodered_flows_backup, github=download, uploaded=use uploaded files)", 
                font=("SF Pro Text", 10),
                fg=self.colors['text_secondary'],
                bg=self.colors['white']).grid(row=6, column=2, sticky=tk.W, pady=(0, 8), padx=(10, 0))
        
        # Package Source
        tk.Label(content_frame, text="Package Source:", 
                font=("SF Pro Text", 10, "bold"),
                                            fg="black",
                bg=self.colors['white']).grid(row=7, column=0, sticky=tk.W, pady=(0, 8))
        
        self.package_source_var = tk.StringVar(value="github")
        package_source_combo = ttk.Combobox(content_frame, 
                                           textvariable=self.package_source_var,
                                           values=("auto", "local", "github", "uploaded"),
                                           state="readonly",
                                           font=("SF Pro Text", 10))
        package_source_combo.grid(row=7, column=1, sticky=(tk.W, tk.E), pady=(0, 8), padx=(10, 0))
        
        tk.Label(content_frame, text="(auto=detect, local=./nodered_flows_backup, github=download, uploaded=use uploaded files)", 
                font=("SF Pro Text", 10),
                fg=self.colors['text_secondary'],
                bg=self.colors['white']).grid(row=7, column=2, sticky=tk.W, pady=(0, 8), padx=(10, 0))
    
    def create_file_upload_section(self, parent):
        """Create file upload section with modern styling"""
        # Section container
        upload_frame = tk.Frame(parent, bg=self.colors['white'], relief=tk.FLAT, bd=0)
        upload_frame.pack(fill=tk.X, pady=(0, 15))
        upload_frame.columnconfigure(0, weight=1)
        
        # Section header
        header_frame = tk.Frame(upload_frame, bg=self.colors['secondary'], height=40)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        header_label = tk.Label(header_frame,
                               text="📁 File Upload",
                               font=("SF Pro Text", 10, "bold"),
                               fg=self.colors['white'],
                               bg=self.colors['secondary'])
        header_label.pack(side=tk.LEFT, padx=20, pady=10)
        
        # Content frame
        content_frame = tk.Frame(upload_frame, bg=self.colors['white'])
        content_frame.pack(fill=tk.X, padx=20, pady=20)
        content_frame.columnconfigure(1, weight=1)
        
        # Upload flows.json
        tk.Label(content_frame, text="Upload flows.json:", 
                font=("SF Pro Text", 10, "bold"),
                                            fg="black",
                bg=self.colors['white']).grid(row=0, column=0, sticky=tk.W, pady=(0, 8))
        
        self.upload_flows_button = tk.Button(content_frame,
                                           text="Choose File",
                                           command=self.upload_flows_file,
                                           font=("SF Pro Text", 10, "bold"),
                                           bg=self.colors['info'],
                                           fg="black",
                                           relief=tk.FLAT,
                                           bd=0,
                                           padx=20,
                                           pady=8,
                                           cursor="hand2")
        self.upload_flows_button.grid(row=0, column=1, sticky=tk.W, pady=(0, 8), padx=(10, 0))
        
        self.flows_status_label = tk.Label(content_frame,
                                          text="No file selected",
                                          font=("SF Pro Text", 10),
                                          fg=self.colors['text_secondary'],
                                          bg=self.colors['white'])
        self.flows_status_label.grid(row=0, column=2, sticky=tk.W, pady=(0, 8), padx=(10, 0))
        
        # Upload package.json
        tk.Label(content_frame, text="Upload package.json:", 
                font=("SF Pro Text", 10, "bold"),
                                            fg="black",
                bg=self.colors['white']).grid(row=1, column=0, sticky=tk.W, pady=(0, 8))
        
        self.upload_package_button = tk.Button(content_frame,
                                             text="Choose File",
                                             command=self.upload_package_file,
                                             font=("SF Pro Text", 10, "bold"),
                                             bg=self.colors['info'],
                                             fg="black",
                                             relief=tk.FLAT,
                                             bd=0,
                                             padx=20,
                                             pady=8,
                                             cursor="hand2")
        self.upload_package_button.grid(row=1, column=1, sticky=tk.W, pady=(0, 8), padx=(10, 0))
        
        self.package_status_label = tk.Label(content_frame,
                                            text="No file selected",
                                            font=("SF Pro Text", 10),
                                            fg=self.colors['text_secondary'],
                                            bg=self.colors['white'])
        self.package_status_label.grid(row=1, column=2, sticky=tk.W, pady=(0, 8), padx=(10, 0))
        
        # Clear uploaded files button
        self.clear_files_button = tk.Button(content_frame,
                                           text="🗑️ Clear Uploaded Files",
                                           command=self.clear_uploaded_files,
                                           font=("SF Pro Text", 10, "bold"),
                                           bg=self.colors['warning'],
                                           fg="black",
                                           relief=tk.FLAT,
                                           bd=0,
                                           padx=20,
                                           pady=8,
                                           cursor="hand2")
        self.clear_files_button.grid(row=2, column=0, columnspan=3, pady=(15, 0))
        
        # Initialize uploaded files tracking
        self.uploaded_flows_file = None
        self.uploaded_package_file = None
        self.upload_dir = os.path.join(os.path.dirname(__file__), "uploaded_files")
        
        # Create upload directory if it doesn't exist
        if not os.path.exists(self.upload_dir):
            os.makedirs(self.upload_dir)
        
    def create_tailscale_section(self, parent):
        """Create Tailscale configuration section with modern styling"""
        # Section container
        tailscale_frame = tk.Frame(parent, bg=self.colors['white'], relief=tk.FLAT, bd=0)
        tailscale_frame.pack(fill=tk.X, pady=(0, 15))
        tailscale_frame.columnconfigure(0, weight=1)
        
        # Section header
        header_frame = tk.Frame(tailscale_frame, bg=self.colors['info'], height=40)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        header_label = tk.Label(header_frame,
                               text="🔗 Tailscale Configuration",
                               font=("SF Pro Text", 10, "bold"),
                               fg=self.colors['white'],
                               bg=self.colors['info'])
        header_label.pack(side=tk.LEFT, padx=20, pady=10)
        
        # Content frame
        content_frame = tk.Frame(tailscale_frame, bg=self.colors['white'])
        content_frame.pack(fill=tk.X, padx=20, pady=20)
        content_frame.columnconfigure(1, weight=1)
        
        # Auth Key
        tk.Label(content_frame, text="Auth Key:", 
                font=("SF Pro Text", 10, "bold"),
                                            fg="black",
                bg=self.colors['white']).grid(row=0, column=0, sticky=tk.W, pady=(0, 8))
        
        self.tailscale_auth_key_var = tk.StringVar()
        # Set default auth key
        self.tailscale_auth_key_var.set("tskey-auth-kvwRxYc6o321CNTRL-6kggdogXnMdAdewR7Y7cMdNSp7yrJsSC")
        
        self.tailscale_auth_key_entry = tk.Entry(content_frame, 
                                                textvariable=self.tailscale_auth_key_var,
                                                font=("SF Pro Text", 10),
                                                relief=tk.FLAT,
                                                bd=1,
                                                bg="white",
                                                fg="black",
                                                show="*")
        self.tailscale_auth_key_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=(0, 8), padx=(10, 0))
        
        # Add validation for auth key format
        self.tailscale_auth_key_var.trace('w', self.validate_tailscale_auth_key)
        
        # Validation status label
        self.tailscale_validation_label = tk.Label(content_frame, 
                                                  text="",
                                                  font=("SF Pro Text", 9),
                                                  fg=self.colors['success'],
                                                  bg=self.colors['white'])
        self.tailscale_validation_label.grid(row=1, column=1, sticky=tk.W, pady=(0, 8), padx=(10, 0))
        
        # Button frame for Tailscale controls
        button_frame = tk.Frame(content_frame, bg=self.colors['white'])
        button_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        button_frame.columnconfigure(0, weight=1)
        button_frame.columnconfigure(1, weight=1)
        button_frame.columnconfigure(2, weight=1)
        button_frame.columnconfigure(3, weight=1)
        
        # Submit Auth Key button
        self.tailscale_submit_button = tk.Button(button_frame,
                                                text="🔑 Submit Auth Key",
                                                font=("SF Pro Text", 10, "bold"),
                                                bg=self.colors['primary'],
                                                fg=self.colors['white'],
                                                relief=tk.FLAT,
                                                bd=0,
                                                padx=20,
                                                pady=8,
                                                cursor="hand2",
                                                command=self.tailscale_submit_auth_key)
        self.tailscale_submit_button.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
        
        # Tailscale Down button
        self.tailscale_down_button = tk.Button(button_frame,
                                              text="🔴 Tailscale Down",
                                              font=("SF Pro Text", 10, "bold"),
                                              bg=self.colors['danger'],
                                              fg=self.colors['white'],
                                              relief=tk.FLAT,
                                              bd=0,
                                              padx=20,
                                              pady=8,
                                              cursor="hand2",
                                              command=self.tailscale_down)
        self.tailscale_down_button.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=5)
        
        # Tailscale Up button
        self.tailscale_up_button = tk.Button(button_frame,
                                            text="🟢 Tailscale Up",
                                            font=("SF Pro Text", 10, "bold"),
                                            bg=self.colors['success'],
                                            fg=self.colors['white'],
                                            relief=tk.FLAT,
                                            bd=0,
                                            padx=20,
                                            pady=8,
                                            cursor="hand2",
                                            command=self.tailscale_up)
        self.tailscale_up_button.grid(row=0, column=2, sticky=(tk.W, tk.E), padx=5)
        
        # Restart Tailscale button (Down + Up)
        self.tailscale_restart_button = tk.Button(button_frame,
                                                 text="🔄 Restart Tailscale",
                                                 font=("SF Pro Text", 10, "bold"),
                                                 bg=self.colors['warning'],
                                                 fg=self.colors['white'],
                                                 relief=tk.FLAT,
                                                 bd=0,
                                                 padx=20,
                                                 pady=8,
                                                 cursor="hand2",
                                                 command=self.tailscale_restart)
        self.tailscale_restart_button.grid(row=0, column=3, sticky=(tk.W, tk.E), padx=(5, 0))
        
        # Add tooltips to clarify these work on remote devices
        self.create_tooltip(self.tailscale_submit_button, "Update Tailscale auth key on remote device and restart container")
        self.create_tooltip(self.tailscale_down_button, "Stop Tailscale container on remote device")
        self.create_tooltip(self.tailscale_up_button, "Start Tailscale container on remote device with current auth key")
        self.create_tooltip(self.tailscale_restart_button, "Restart Tailscale container on remote device (stop then start)")
        
    
    def create_control_buttons_section(self, parent):
        """Create control buttons section with modern styling"""
        # Section container
        control_frame = tk.Frame(parent, bg=self.colors['white'], relief=tk.FLAT, bd=0)
        control_frame.pack(fill=tk.X, pady=(0, 15))
        control_frame.columnconfigure(0, weight=1)
        
        # Section header
        header_frame = tk.Frame(control_frame, bg=self.colors['success'], height=40)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        header_label = tk.Label(header_frame,
                               text="🎮 Control Panel",
                               font=("SF Pro Text", 10, "bold"),
                               fg=self.colors['white'],
                               bg=self.colors['success'])
        header_label.pack(side=tk.LEFT, padx=20, pady=10)
        
        # Content frame
        content_frame = tk.Frame(control_frame, bg=self.colors['white'])
        content_frame.pack(fill=tk.X, padx=20, pady=20)
        content_frame.columnconfigure(0, weight=1)
        content_frame.columnconfigure(1, weight=1)
        
        # Start Bot button
        self.start_bot_button = tk.Button(content_frame,
                                         text="🚀 Start Bot",
                                         command=self.start_bot,
                                         font=("SF Pro Text", 10, "bold"),
                                         bg=self.colors['success'],
                                         fg="black",
                                         relief=tk.FLAT,
                                         bd=0,
                                         padx=30,
                                         pady=12,
                                         cursor="hand2")
        self.start_bot_button.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # Reset Device button
        self.reset_device_button = tk.Button(content_frame,
                                            text="🔄 Reset Device",
                                            command=self.reset_device,
                                            font=("SF Pro Text", 10, "bold"),
                                            bg=self.colors['danger'],
                                            fg="black",
                                            relief=tk.FLAT,
                                            bd=0,
                                            padx=30,
                                            pady=12,
                                            cursor="hand2")
        self.reset_device_button.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0))
    
    def create_log_section(self, parent):
        """Create log output section with modern styling"""
        # Section container
        log_frame = tk.Frame(parent, bg=self.colors['white'], relief=tk.FLAT, bd=0)
        log_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(1, weight=1)
        
        # Section header
        header_frame = tk.Frame(log_frame, bg=self.colors['dark'], height=40)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        header_label = tk.Label(header_frame,
                               text="📋 Log Output",
                               font=("SF Pro Text", 10, "bold"),
                               fg=self.colors['white'],
                               bg=self.colors['dark'])
        header_label.pack(side=tk.LEFT, padx=20, pady=10)
        
        # Log text area
        self.log_text = scrolledtext.ScrolledText(log_frame,
                                                 font=("SF Mono", 10),
                                                 bg=self.colors['dark'],
                                                 fg="black",
                                                 relief=tk.FLAT,
                                                 bd=0,
                                                 wrap=tk.WORD,
                                                 state=tk.DISABLED)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        # Configure text tags for colored output
        self.log_text.tag_configure("SUCCESS", foreground=self.colors['success'])
        self.log_text.tag_configure("ERROR", foreground=self.colors['danger'])
        self.log_text.tag_configure("WARNING", foreground=self.colors['warning'])
        self.log_text.tag_configure("INFO", foreground=self.colors['info'])
        self.log_text.tag_configure("DEBUG", foreground=self.colors['text_secondary'])
    
    def create_function_selection_section(self, parent):
        """Create function selection section with modern styling"""
        # Section container
        selection_frame = tk.Frame(parent, bg=self.colors['white'], relief=tk.FLAT, bd=0)
        selection_frame.pack(fill=tk.BOTH, expand=True)
        selection_frame.columnconfigure(0, weight=1)
        selection_frame.rowconfigure(1, weight=1)
        
        # Section header
        header_frame = tk.Frame(selection_frame, bg=self.colors['primary'], height=40)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        header_label = tk.Label(header_frame,
                               text="⚡ Function Selection",
                               font=("SF Pro Text", 10, "bold"),
                               fg=self.colors['white'],
                               bg=self.colors['primary'])
        header_label.pack(side=tk.LEFT, padx=20, pady=10)
        
        # Control buttons
        button_frame = tk.Frame(selection_frame, bg=self.colors['white'])
        button_frame.pack(fill=tk.X, padx=20, pady=(15, 10))
        
        self.select_all_button = tk.Button(button_frame,
                                          text="✅ Select All",
                                          command=self.select_all_functions,
                                          font=("SF Pro Text", 10, "bold"),
                                          bg=self.colors['success'],
                                          fg="black",
                                          relief=tk.FLAT,
                                          bd=0,
                                          padx=15,
                                          pady=8,
                                          cursor="hand2")
        self.select_all_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.select_none_button = tk.Button(button_frame,
                                           text="❌ Select None",
                                           command=self.select_none_functions,
                                           font=("SF Pro Text", 10, "bold"),
                                           bg=self.colors['danger'],
                                           fg="black",
                                           relief=tk.FLAT,
                                           bd=0,
                                           padx=15,
                                           pady=8,
                                           cursor="hand2")
        self.select_none_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.quick_setup_button = tk.Button(button_frame,
                                           text="⚡ Quick Setup",
                                           command=self.select_quick_setup,
                                           font=("SF Pro Text", 10, "bold"),
                                           bg=self.colors['warning'],
                                           fg="black",
                                           relief=tk.FLAT,
                                           bd=0,
                                           padx=15,
                                           pady=8,
                                           cursor="hand2")
        self.quick_setup_button.pack(side=tk.LEFT)
        
        # Function list frame
        list_frame = tk.Frame(selection_frame, bg=self.colors['white'])
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        list_frame.columnconfigure(0, weight=1)
        
        # Create scrollable function list
        self.create_function_list(list_frame)
    
    def create_function_list(self, parent):
        """Create scrollable function list with modern styling"""
        # Create canvas and scrollbar for scrollable list
        canvas = tk.Canvas(parent, bg=self.colors['light'], highlightthickness=0)
        scrollbar = tk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.colors['light'])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Pack canvas and scrollbar
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
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
            ("update-nodered-auth", "Update Node-RED Authentication (uses GUI password)", ["import-nodered-flows"]),
            ("install-tailscale", "Install Tailscale VPN Router", ["install-services"]),
            ("reverse", "Configure Network REVERSE (uses Final LAN IP)", []),
            ("set-password", "Change Device Password (uses Final Password)", [])
        ]
        
        for i, (func_id, description, dependencies) in enumerate(self.function_descriptions):
            # Create function item frame
            item_frame = tk.Frame(scrollable_frame, bg=self.colors['white'], relief=tk.FLAT, bd=1)
            item_frame.pack(fill=tk.X, padx=5, pady=1)
            item_frame.columnconfigure(1, weight=1)
            
            # Checkbox
            var = tk.BooleanVar()
            self.function_vars.append(var)
            
            checkbox = tk.Checkbutton(item_frame,
                                    variable=var,
                                    bg=self.colors['white'],
                                    activebackground=self.colors['white'],
                                    selectcolor=self.colors['light'],
                                    relief=tk.FLAT,
                                    bd=0)
            checkbox.grid(row=0, column=0, padx=10, pady=4, sticky=tk.N)
            
            # Description label
            label = tk.Label(item_frame,
                           text=f"{i+1}. {description}",
                           font=("SF Pro Text", 10),
                                            fg="black",
                           bg=self.colors['white'],
                           wraplength=400,
                           justify=tk.LEFT)
            label.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 10), pady=4)
            self.function_labels.append(label)
            
            # Store dependencies
            checkbox.dependencies = dependencies
            checkbox.func_id = func_id
        
        # Selection counter
        self.selection_counter = tk.Label(parent,
                                        text="Selected: 0 functions",
                                        font=("SF Pro Text", 10, "bold"),
                                        fg=self.colors['text_secondary'],
                                        bg=self.colors['light'])
        self.selection_counter.pack(pady=(10, 0))
        
        # Bind selection change events
        for var in self.function_vars:
            var.trace_add('write', lambda *args: self.update_selection_counter())
    
    def update_selection_counter(self, *args):
        """Update the selection counter"""
        selected_count = sum(1 for var in self.function_vars if var.get())
        self.selection_counter.config(text=f"Selected: {selected_count} functions")
    
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
        file_path = filedialog.askopenfilename(
            title="Select flows.json file",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            try:
                # Copy file to upload directory
                filename = os.path.basename(file_path)
                dest_path = os.path.join(self.upload_dir, filename)
                shutil.copy2(file_path, dest_path)
                self.uploaded_flows_file = dest_path
                self.flows_status_label.config(text=f"✓ {filename}", fg=self.colors['success'])
                self.log_message(f"📁 Uploaded flows file: {filename}", "SUCCESS")
            except Exception as e:
                self.log_message(f"❌ Error uploading flows file: {e}", "ERROR")
    
    def upload_package_file(self):
        """Upload package.json file"""
        file_path = filedialog.askopenfilename(
            title="Select package.json file",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if file_path:
            try:
                # Copy file to upload directory
                filename = os.path.basename(file_path)
                dest_path = os.path.join(self.upload_dir, filename)
                shutil.copy2(file_path, dest_path)
                self.uploaded_package_file = dest_path
                self.package_status_label.config(text=f"✓ {filename}", fg=self.colors['success'])
                self.log_message(f"📁 Uploaded package file: {filename}", "SUCCESS")
            except Exception as e:
                self.log_message(f"❌ Error uploading package file: {e}", "ERROR")
    
    def clear_uploaded_files(self):
        """Clear uploaded files"""
        try:
            if os.path.exists(self.upload_dir):
                for file in os.listdir(self.upload_dir):
                    os.remove(os.path.join(self.upload_dir, file))
                self.uploaded_flows_file = None
                self.uploaded_package_file = None
            self.flows_status_label.config(text="No file selected", fg=self.colors['text_secondary'])
            self.package_status_label.config(text="No file selected", fg=self.colors['text_secondary'])
            self.log_message("🗑️ Cleared uploaded files", "INFO")
        except Exception as e:
            self.log_message(f"❌ Error clearing uploaded files: {e}", "ERROR")
    
    def select_all_functions(self):
        """Select all functions"""
        for var in self.function_vars:
            var.set(True)
        self.log_message("✅ Selected all functions", "INFO")
    
    def select_none_functions(self):
        """Deselect all functions"""
        for var in self.function_vars:
            var.set(False)
        self.log_message("❌ Deselected all functions", "INFO")
    
    def select_quick_setup(self):
        """Select quick setup functions"""
        # Deselect all first
        for var in self.function_vars:
            var.set(False)
        
        # Select quick setup functions
        quick_setup_functions = ["forward", "install-docker", "install-services", "install-nodered-nodes", "import-nodered-flows", "update-nodered-auth"]
        for i, (func_id, _, _) in enumerate(self.function_descriptions):
            if func_id in quick_setup_functions:
                self.function_vars[i].set(True)
        
        self.log_message("⚡ Selected quick setup functions", "INFO")
    
    def start_bot(self):
        """Start the network bot"""
        if self.is_running:
            self.log_message("⚠️ Bot is already running", "WARNING")
            return
        
        # Get selected functions
        selected_functions = []
        for i, var in enumerate(self.function_vars):
            if var.get():
                func_id, _, _ = self.function_descriptions[i]
                selected_functions.append(func_id)
        
        if not selected_functions:
            self.log_message("❌ Please select at least one function", "ERROR")
            return
        
        # Validate Tailscale auth key if install-tailscale is selected
        if "install-tailscale" in selected_functions:
            if not self.validate_tailscale_auth_key():
                self.log_message("❌ Invalid Tailscale auth key. Please fix the auth key format before proceeding.", "ERROR")
                return
        
        # Update status
        self.is_running = True
        self.status_indicator.config(fg=self.colors['warning'])
        self.status_label.config(text="Running")
        self.start_bot_button.config(state=tk.DISABLED, text="🔄 Running...")
        
        self.log_message("🚀 Starting Bivicom Network Bot...", "INFO")
        self.log_message(f"📋 Selected functions: {', '.join(selected_functions)}", "INFO")
        
        # Start bot in separate thread
        self.bot_thread = threading.Thread(target=self.run_bot, args=(selected_functions,))
        self.bot_thread.daemon = True
        self.bot_thread.start()
    
    def reset_device(self):
        """Reset device to default state"""
        if self.is_running:
            self.log_message("⚠️ Cannot reset device while bot is running", "WARNING")
            return
        
        # Confirmation dialog
        result = messagebox.askyesno(
            "Reset Device",
            "⚠️ WARNING: This will completely reset the device to default state!\n\n"
            "This will:\n"
                                     "• Remove all Docker containers, images, and volumes\n"
            "• Uninstall Docker completely\n"
                                     "• Reset network to REVERSE mode (LTE WAN)\n"
            "• Reset password to admin/admin\n"
                                     "• Remove all custom configurations\n\n"
            "Are you sure you want to continue?",
            icon="warning"
        )
        
        if not result:
                return
            
        # Update status
        self.status_indicator.config(fg=self.colors['warning'])
        self.status_label.config(text="Resetting...")
        self.reset_device_button.config(state=tk.DISABLED, text="🔄 Resetting...")
        
        self.log_message("🔄 Starting device reset...", "WARNING")
        
        # Start reset in separate thread
        reset_thread = threading.Thread(target=self.run_reset_device)
        reset_thread.daemon = True
        reset_thread.start()
            
    def run_reset_device(self):
        """Run device reset in separate thread"""
        try:
            # Create bot wrapper for reset
            bot = GUIBotWrapper(
                gui_log_callback=self.log_message,
                target_ip=self.target_ip_var.get(),
                username=self.username_var.get(),
                password=self.password_var.get()
            )
            
            # Run reset device command
            success = bot.reset_device()
            
            if success:
                self.log_message("✅ Device reset completed successfully!", "SUCCESS")
                play_sound("success")
            else:
                self.log_message("❌ Device reset failed", "ERROR")
                play_sound("error")
                
        except Exception as e:
            self.log_message(f"❌ Error during device reset: {e}", "ERROR")
            play_sound("error")
        finally:
            # Reset UI state
            self.root.after(0, self.reset_ui_after_operation)
    
    def run_bot(self, selected_functions):
        """Run the network bot in separate thread"""
        try:
            # Create bot wrapper
            self.bot = GUIBotWrapper(
                gui_log_callback=self.log_message,
                target_ip=self.target_ip_var.get(),
                scan_interval=int(self.scan_interval_var.get()),
                username=self.username_var.get(),
                password=self.password_var.get(),
                final_ip=self.final_ip_var.get(),
                final_password=self.final_password_var.get(),
                flows_source=self.flows_source_var.get(),
                package_source=self.package_source_var.get(),
                uploaded_flows_file=self.uploaded_flows_file,
                uploaded_package_file=self.uploaded_package_file,
                step_progress_callback=self.update_progress,
                step_highlight_callback=self.highlight_step
            )
            
            # Run the bot
            success = self.bot.run_network_configuration_sequence(selected_functions)
            
            if success:
                self.log_message("🎉 Network configuration completed successfully!", "SUCCESS")
                play_sound("completion")
                self.config_count += 1
            else:
                self.log_message("❌ Network configuration failed", "ERROR")
                play_sound("error")
            
        except Exception as e:
            self.log_message(f"❌ Error during network configuration: {e}", "ERROR")
            play_sound("error")
        finally:
            # Reset UI state
            self.root.after(0, self.reset_ui_after_operation)
    
    def reset_ui_after_operation(self):
        """Reset UI state after operation completes"""
        self.is_running = False
        self.status_indicator.config(fg=self.colors['success'])
        self.status_label.config(text="Ready")
        self.start_bot_button.config(state=tk.NORMAL, text="🚀 Start Bot")
        self.reset_device_button.config(state=tk.NORMAL, text="🔄 Reset Device")
        
        # Update statistics
        self.scans_label.config(text=f"Scans: {self.scan_count}")
        self.configs_label.config(text=f"Configurations: {self.config_count}")
        self.timestamp_label.config(text=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    def update_progress(self, current_step, total_steps):
        """Update progress indicator"""
        self.current_step = current_step
        self.total_steps = total_steps
        progress_text = f"Step {current_step}/{total_steps}"
        self.log_message(f"📊 Progress: {progress_text}", "INFO")
    
    def highlight_step(self, step_number):
        """Highlight current step in function list"""
        # This could be enhanced to visually highlight the current step
        pass
    
    def log_message(self, message, level="INFO"):
        """Add message to log queue"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        self.log_queue.put((log_entry, level))
    
    def process_log_queue(self):
        """Process log messages from queue"""
        try:
            while True:
                message, level = self.log_queue.get_nowait()
                self.add_log_message(message, level)
        except queue.Empty:
            pass
        
        # Schedule next check
        self.root.after(100, self.process_log_queue)
    
    def add_log_message(self, message, level="INFO"):
        """Add message to log display"""
        try:
            if hasattr(self, 'log_text') and self.log_text.winfo_exists():
                self.log_text.config(state=tk.NORMAL)
                self.log_text.insert(tk.END, message + "\n", level)
                self.log_text.see(tk.END)
                self.log_text.config(state=tk.DISABLED)
        except tk.TclError:
            # Widget doesn't exist yet, skip this message
            pass
    
    def signal_handler(self, signum, frame):
        """Handle system signals for graceful shutdown"""
        self.log_message("🛑 Received shutdown signal", "WARNING")
        self.shutdown_requested = True
        self.on_closing()
    
    def on_closing(self):
        """Handle window closing"""
        if self.is_running:
            self.log_message("🛑 Stopping bot...", "WARNING")
            self.is_running = False
            if self.bot:
                self.bot.running = False
        
        self.log_message("👋 Bivicom Network Bot GUI closed", "INFO")
        self.root.quit()
        self.root.destroy()
    
    def validate_tailscale_auth_key(self, *args):
        """Validate Tailscale auth key format"""
        try:
            auth_key = self.tailscale_auth_key_var.get()
            
            if not auth_key:
                self.tailscale_validation_label.config(text="⚠️ Auth key is required", fg=self.colors['warning'])
                return False
            
            # Check if it starts with tskey-auth- and has proper length
            if not auth_key.startswith('tskey-auth-'):
                self.tailscale_validation_label.config(text="❌ Invalid format: must start with 'tskey-auth-'", fg=self.colors['danger'])
                return False
            
            # Check minimum length (tskey-auth- + at least 20 characters)
            if len(auth_key) < 30:
                self.tailscale_validation_label.config(text="❌ Invalid format: auth key too short", fg=self.colors['danger'])
                return False
            
            # Check for valid characters (alphanumeric and hyphens)
            import re
            if not re.match(r'^tskey-auth-[a-zA-Z0-9\-]+$', auth_key):
                self.tailscale_validation_label.config(text="❌ Invalid format: contains invalid characters", fg=self.colors['danger'])
                return False
            
            self.tailscale_validation_label.config(text="✅ Valid auth key format", fg=self.colors['success'])
            return True
            
        except Exception as e:
            self.tailscale_validation_label.config(text=f"❌ Validation error: {str(e)}", fg=self.colors['danger'])
            return False
    
    def create_tooltip(self, widget, text):
        """Create a tooltip for a widget"""
        def show_tooltip(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = tk.Label(tooltip, text=text, 
                           font=("SF Pro Text", 9),
                           bg="#2C2C2C", fg="white",
                           relief=tk.SOLID, borderwidth=1,
                           padx=8, pady=4)
            label.pack()
            
            widget.tooltip = tooltip
        
        def hide_tooltip(event):
            if hasattr(widget, 'tooltip'):
                widget.tooltip.destroy()
                del widget.tooltip
        
        widget.bind("<Enter>", show_tooltip)
        widget.bind("<Leave>", hide_tooltip)
    
    def tailscale_down(self):
        """Stop Tailscale container on remote device"""
        if not self.validate_tailscale_auth_key():
            self.log_message("❌ Invalid auth key format. Please fix before proceeding.", "ERROR")
            return
        
        target_ip = self.target_ip_var.get()
        username = self.username_var.get()
        password = self.password_var.get()
        
        self.log_message(f"🔴 Stopping Tailscale container on remote device {target_ip}...", "INFO")
        
        # Create a simple bot wrapper for this single command
        try:
            bot = GUIBotWrapper(
                gui_log_callback=self.log_message,
                target_ip=target_ip,
                username=username,
                password=password
            )
            
            # Execute tailscale-down command
            result = bot.execute_single_command("tailscale-down")
            
            if result:
                self.log_message("✅ Tailscale stopped successfully on remote device", "SUCCESS")
            else:
                self.log_message("❌ Failed to stop Tailscale on remote device", "ERROR")
                
        except Exception as e:
            self.log_message(f"❌ Error stopping Tailscale on remote device: {str(e)}", "ERROR")
    
    def tailscale_up(self):
        """Start Tailscale container with current auth key on remote device"""
        if not self.validate_tailscale_auth_key():
            self.log_message("❌ Invalid auth key format. Please fix before proceeding.", "ERROR")
            return
        
        target_ip = self.target_ip_var.get()
        username = self.username_var.get()
        password = self.password_var.get()
        auth_key = self.tailscale_auth_key_var.get()
        
        self.log_message(f"🟢 Starting Tailscale container on remote device {target_ip} with new auth key...", "INFO")
        
        # Create a simple bot wrapper for this single command
        try:
            bot = GUIBotWrapper(
                gui_log_callback=self.log_message,
                target_ip=target_ip,
                username=username,
                password=password
            )
            
            # Execute tailscale-up command with auth key
            result = bot.execute_single_command("tailscale-up", auth_key)
            
            if result:
                self.log_message("✅ Tailscale started successfully on remote device", "SUCCESS")
            else:
                self.log_message("❌ Failed to start Tailscale on remote device", "ERROR")
                
        except Exception as e:
            self.log_message(f"❌ Error starting Tailscale on remote device: {str(e)}", "ERROR")
    
    def tailscale_restart(self):
        """Restart Tailscale container on remote device (down then up)"""
        if not self.validate_tailscale_auth_key():
            self.log_message("❌ Invalid auth key format. Please fix before proceeding.", "ERROR")
            return
        
        target_ip = self.target_ip_var.get()
        self.log_message(f"🔄 Restarting Tailscale container on remote device {target_ip}...", "INFO")
        
        # First stop
        self.tailscale_down()
        
        # Wait a moment
        import time
        time.sleep(2)
        
        # Then start
        self.tailscale_up()
    
    def tailscale_submit_auth_key(self):
        """Submit new auth key to remote device and restart Tailscale"""
        if not self.validate_tailscale_auth_key():
            self.log_message("❌ Invalid auth key format. Please fix before proceeding.", "ERROR")
            return
        
        target_ip = self.target_ip_var.get()
        username = self.username_var.get()
        password = self.password_var.get()
        auth_key = self.tailscale_auth_key_var.get()
        
        self.log_message(f"🔑 Submitting new auth key to remote device {target_ip}...", "INFO")
        
        # Create a simple bot wrapper for this single command
        try:
            bot = GUIBotWrapper(
                gui_log_callback=self.log_message,
                target_ip=target_ip,
                username=username,
                password=password
            )
            
            # Restart Tailscale with new auth key
            result = bot.execute_single_command("tailscale-restart", auth_key)
            
            if result:
                self.log_message("✅ Auth key submitted and Tailscale restarted successfully on remote device", "SUCCESS")
            else:
                self.log_message("❌ Failed to restart Tailscale with new auth key on remote device", "ERROR")
                
        except Exception as e:
            self.log_message(f"❌ Error submitting auth key to remote device: {str(e)}", "ERROR")
    
    def run(self):
        """Start the GUI main loop"""
        self.log_message("✅ Bivicom Network Bot GUI started", "SUCCESS")
        self.log_message("ℹ️ Configure settings and click 'Start Bot' to begin", "INFO")
        self.root.mainloop()


def main():
    """Main function to start the GUI application"""
    try:
        app = NetworkBotGUI()
        app.run()
    except KeyboardInterrupt:
        print("\n👋 Application interrupted by user")
    except Exception as e:
        print(f"❌ Error starting GUI: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
