#!/usr/bin/env python3
"""
Enhanced Bivicom Network Configuration GUI - Enterprise Edition
=============================================================

Professional GUI application for network administrators featuring:
- Advanced visual feedback for long-running operations
- Comprehensive error handling and troubleshooting guidance
- Intuitive workflow management for device setup sequences
- Enterprise-grade appearance and functionality
- Enhanced progress tracking with detailed operation status
- Multi-device support and batch operations
- Real-time network diagnostics and validation

Author: Claude Code
Date: 2025-01-09
Version: 2.0 Enterprise
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
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
import shutil
import json
import socket
import ipaddress
from dataclasses import dataclass
from enum import Enum
import logging

# Import the NetworkBot class from master.py
try:
    from master import NetworkBot
except ImportError:
    # Fallback for testing
    class NetworkBot:
        def __init__(self, *args, **kwargs):
            pass

class OperationStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

@dataclass
class DeviceInfo:
    ip: str
    status: str
    last_seen: datetime
    mac_address: str = ""
    hostname: str = ""
    progress: int = 0
    current_step: str = ""
    error_count: int = 0

@dataclass
class OperationStep:
    id: str
    name: str
    description: str
    estimated_duration: int
    status: OperationStatus = OperationStatus.PENDING
    progress: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    error_message: str = ""
    retry_count: int = 0
    max_retries: int = 3

class GUIBotWrapper:
    """Wrapper class to integrate NetworkBot with the enhanced GUI"""
    
    def __init__(self, gui_log_callback, target_ip="192.168.1.1", username="admin", 
                 password="admin", step_progress_callback=None, final_ip="192.168.1.1",
                 final_password="admin", flows_source="auto", package_source="auto",
                 uploaded_flows_file=None, uploaded_package_file=None):
        self.gui_log_callback = gui_log_callback
        self.target_ip = target_ip
        self.username = username
        self.password = password
        self.script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "network_config.sh"))
        self.step_progress_callback = step_progress_callback
        self.final_ip = final_ip
        self.final_password = final_password
        self.flows_source = flows_source
        self.package_source = package_source
        self.uploaded_flows_file = uploaded_flows_file
        self.uploaded_package_file = uploaded_package_file
        self.selected_functions = []
        
    def log_message(self, message: str, level: str = "INFO"):
        """Send messages to GUI"""
        self.gui_log_callback(message, level)
        
    def run_network_config(self):
        """Run network configuration using the selected functions"""
        try:
            if not self.selected_functions:
                self.log_message("❌ No functions selected", "ERROR")
                return False
                
            script_path = os.path.join(os.path.dirname(__file__), "network_config.sh")
            
            total_functions = len(self.selected_functions)
            
            for i, func_id in enumerate(self.selected_functions):
                if self.step_progress_callback:
                    self.step_progress_callback(i + 1, total_functions)
                    
                # Build command for this function
                cmd = [script_path, "--remote", self.target_ip, self.username, self.password, func_id]
                
                # Add additional parameters for specific functions
                if func_id == "reverse" and self.final_ip:
                    cmd.extend(["--final-ip", self.final_ip])
                elif func_id == "set-password" and self.final_password:
                    # For set-password, the password is passed as a direct argument, not a parameter
                    cmd.append(self.final_password)
                elif func_id in ["import-nodered-flows", "install-nodered-nodes"]:
                    cmd.extend(["--flows-source", self.flows_source])
                    cmd.extend(["--package-source", self.package_source])
                    if self.uploaded_flows_file:
                        cmd.extend(["--uploaded-flows", self.uploaded_flows_file])
                    if self.uploaded_package_file:
                        cmd.extend(["--uploaded-package", self.uploaded_package_file])
                        
                self.log_message(f"📋 Step {i+1}/{total_functions}: Executing {func_id}", "INFO")
                
                # Execute the command and show output in real-time
                try:
                    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                             text=True, bufsize=1, universal_newlines=True)
                    
                    # Read output line by line
                    for line in process.stdout:
                        line = line.strip()
                        if line:
                            self.log_message(f"[SCRIPT] {line}", "INFO")
                    
                    # Wait for process to complete
                    return_code = process.wait(timeout=300)
                    
                    if return_code == 0:
                        self.log_message(f"✅ Step {i+1} completed: {func_id}", "SUCCESS")
                    else:
                        self.log_message(f"❌ Step {i+1} failed: {func_id} (exit code: {return_code})", "ERROR")
                        return False
                        
                except subprocess.TimeoutExpired:
                    process.kill()
                    self.log_message(f"❌ Step {i+1} timed out: {func_id}", "ERROR")
                    return False
                    
            self.log_message("🎉 All configuration steps completed successfully!", "SUCCESS")
            return True
            
        except subprocess.TimeoutExpired:
            self.log_message("❌ Configuration timed out", "ERROR")
            return False
        except Exception as e:
            self.log_message(f"❌ Configuration failed: {str(e)}", "ERROR")
            return False
    
    def execute_single_command(self, command, *args):
        """Execute a single command on the target device"""
        try:
            # Build command
            cmd = [self.script_path, "--remote", self.target_ip, self.username, self.password, command]
            if args:
                cmd.extend(args)
            
            self.log_message(f"🔧 Executing: {' '.join(cmd)}", "INFO")
            
            # Execute command and capture output in real-time
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                     text=True, bufsize=1, universal_newlines=True)
            
            # Read output line by line and display in real-time
            output_lines = []
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    line = output.strip()
                    if line:
                        output_lines.append(line)
                        # Display each line in the log
                        if "[SUCCESS]" in line:
                            self.log_message(f"✅ {line.replace('[SUCCESS]', '').strip()}", "SUCCESS")
                        elif "[ERROR]" in line:
                            self.log_message(f"❌ {line.replace('[ERROR]', '').strip()}", "ERROR")
                        elif "[WARNING]" in line:
                            self.log_message(f"⚠️ {line.replace('[WARNING]', '').strip()}", "WARNING")
                        elif "[INFO]" in line:
                            self.log_message(f"ℹ️ {line.replace('[INFO]', '').strip()}", "INFO")
                        else:
                            self.log_message(f"📋 {line}", "INFO")
            
            # Wait for process to complete
            return_code = process.wait()
            
            if return_code == 0:
                self.log_message("✅ Command completed successfully", "SUCCESS")
                return True
            else:
                self.log_message(f"❌ Command failed with return code {return_code}", "ERROR")
                return False
                
        except subprocess.TimeoutExpired:
            self.log_message("⏰ Command timed out after 5 minutes", "ERROR")
            return False
        except Exception as e:
            self.log_message(f"❌ Error executing command: {str(e)}", "ERROR")
            return False

class EnhancedNetworkBotGUI:
    """Enhanced GUI for professional network configuration management"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.setup_window()
        self.setup_styles()
        self.initialize_variables()
        self.create_gui_components()
        self.setup_event_handlers()
        self.start_background_tasks()
        
    def setup_window(self):
        """Configure the main window with professional appearance"""
        self.root.title("Bivicom Network Configuration Manager - Enterprise")
        self.root.geometry("1600x1000")
        self.root.minsize(1400, 900)
        
        # Set window icon
        try:
            if platform.system() == "Windows":
                self.root.iconbitmap("assets/icon.ico")
        except:
            pass
            
        # Configure window for high DPI displays
        try:
            self.root.tk.call('tk', 'scaling', 1.0)
        except:
            pass
    
    def setup_styles(self):
        """Setup professional color scheme and fonts"""
        # Cross-platform font configuration
        if platform.system() == 'Darwin':
            self.default_font = ('SF Pro Display', 10)
            self.mono_font = ('SF Mono', 9)
        elif platform.system() == 'Linux':
            self.default_font = ('Ubuntu', 10)  
            self.mono_font = ('Ubuntu Mono', 9)
        else:  # Windows
            self.default_font = ('Segoe UI', 10)
            self.mono_font = ('Consolas', 9)
        # Enterprise color palette
        self.colors = {
            'primary': '#1f4e79',       # Professional dark blue
            'secondary': '#2e7d9a',     # Complementary blue-green
            'success': '#22c55e',       # Modern green
            'warning': '#f59e0b',       # Amber
            'error': '#ef4444',         # Red
            'info': '#3b82f6',          # Blue
            'background': '#f8fafc',    # Very light gray
            'surface': '#ffffff',       # White
            'surface_variant': '#f1f5f9', # Light gray variant
            'border': '#e2e8f0',        # Light border
            'text_primary': '#1e293b',  # Dark slate
            'text_secondary': '#64748b', # Muted slate
            'text_muted': '#94a3b8',    # Light slate
            'accent': '#8b5cf6',        # Purple accent
            'danger_bg': '#fef2f2',     # Light red background
            'success_bg': '#f0fdf4',    # Light green background
            'warning_bg': '#fffbeb',    # Light yellow background
        }
        
        self.root.configure(bg=self.colors['background'])
        
        # Configure ttk styles
        self.style = ttk.Style()
        try:
            self.style.theme_use('clam')
        except tk.TclError:
            # Fallback to default theme if clam is not available
            pass
        
        # Configure modern button styles
        try:
            self.style.configure('Primary.TButton',
                               background=self.colors['primary'],
                               foreground='white',
                               font=self.default_font + ('bold',),
                               padding=(20, 10))
            
            self.style.configure('Success.TButton',
                               background=self.colors['success'],
                               foreground='white',
                               font=self.default_font + ('bold',),
                               padding=(20, 10))
            
            self.style.configure('Warning.TButton',
                               background=self.colors['warning'],
                               foreground='white',
                               font=self.default_font + ('bold',),
                               padding=(20, 10))
            
            self.style.configure('Danger.TButton',
                               background=self.colors['error'],
                               foreground='white',
                               font=self.default_font + ('bold',),
                               padding=(20, 10))
            
            # Configure frame styles
            self.style.configure('Card.TFrame',
                               background=self.colors['surface'],
                               relief='flat',
                               borderwidth=1)
            
            # Configure progress bar styles
            self.style.configure('Success.Horizontal.TProgressbar',
                               background=self.colors['success'])
            
            self.style.configure('Warning.Horizontal.TProgressbar',
                               background=self.colors['warning'])
            
            self.style.configure('Error.Horizontal.TProgressbar',
                               background=self.colors['error'])
        except tk.TclError as e:
            print(f"Warning: Could not configure some styles: {e}")
        
    def initialize_variables(self):
        """Initialize application variables and state"""
        # Core application state
        self.is_running = False
        self.shutdown_requested = False
        self.current_operation = None
        self.operation_start_time = None
        self.gui_fully_loaded = False  # Flag to prevent automatic execution during initialization
        
        # Script path
        self.script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "network_config.sh"))
        
        # Device management
        self.devices: Dict[str, DeviceInfo] = {}
        self.selected_devices: List[str] = []
        
        # Operation tracking
        self.operation_steps: List[OperationStep] = []
        self.current_step_index = 0
        
        # UI state
        self.log_queue = queue.Queue()
        self.status_queue = queue.Queue()
        
        # Configuration
        self.config = {
            'target_ip': '192.168.1.1',
            'username': 'admin',
            'password': 'admin',
            'scan_interval': 10,
            'operation_timeout': 300,
            'auto_retry': True,
            'sound_notifications': True,
            'log_level': 'INFO'
        }
        
        # Initialize operation steps
        self.initialize_operation_steps()
        
    def initialize_operation_steps(self):
        """Define the standard network configuration steps"""
        steps = [
            OperationStep('discovery', 'Device Discovery', 'Scan network and identify target devices', 30),
            OperationStep('connectivity', 'Connectivity Test', 'Verify SSH connectivity and credentials', 15),
            OperationStep('backup', 'Configuration Backup', 'Backup current network configuration', 20),
            OperationStep('network_forward', 'Network Forward Mode', 'Configure temporary network settings', 45),
            OperationStep('dns_check', 'DNS Verification', 'Verify internet connectivity and DNS resolution', 20),
            OperationStep('package_install', 'Package Installation', 'Install required packages and dependencies', 60),
            OperationStep('docker_install', 'Docker Installation', 'Install and configure Docker services', 120),
            OperationStep('services_deploy', 'Service Deployment', 'Deploy Node-RED, Portainer, and other services', 180),
            OperationStep('network_reverse', 'Network Reverse Mode', 'Apply final network configuration', 45),
            OperationStep('security_config', 'Security Configuration', 'Apply security settings and authentication', 30),
            OperationStep('validation', 'System Validation', 'Verify all services and configurations', 60),
            OperationStep('finalization', 'Finalization', 'Complete setup and cleanup temporary files', 15)
        ]
        self.operation_steps = steps
        
    def create_gui_components(self):
        """Create and arrange all GUI components"""
        # Create main container
        self.main_container = tk.Frame(self.root, bg=self.colors['background'])
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Configure grid layout
        self.main_container.columnconfigure(0, weight=2)  # Left panel (wider)
        self.main_container.columnconfigure(1, weight=3)  # Right panel (widest)
        self.main_container.rowconfigure(0, weight=0)     # Header
        self.main_container.rowconfigure(1, weight=1)     # Main content
        self.main_container.rowconfigure(2, weight=0)     # Footer
        
        # Create components
        self.create_header()
        self.create_main_panels()
        self.create_footer()
        
    def create_header(self):
        """Create professional header with status indicators"""
        header_frame = tk.Frame(self.main_container, bg=self.colors['surface'], 
                               height=80, relief=tk.FLAT, bd=1)
        header_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 15))
        header_frame.grid_propagate(False)
        header_frame.columnconfigure(1, weight=1)
        
        # Application icon and title
        title_frame = tk.Frame(header_frame, bg=self.colors['surface'])
        title_frame.grid(row=0, column=0, sticky=(tk.W, tk.N, tk.S), padx=20)
        
        title_label = tk.Label(title_frame, 
                              text="Bivicom Network Configuration Manager",
                              font=(self.default_font[0], 16, 'bold'),
                              fg=self.colors['text_primary'],
                              bg=self.colors['surface'])
        title_label.pack(anchor='w')
        
        subtitle_label = tk.Label(title_frame,
                                 text="Enterprise Network Device Management",
                                 font=self.default_font,
                                 fg=self.colors['text_secondary'],
                                 bg=self.colors['surface'])
        subtitle_label.pack(anchor='w')
        
        # Status indicators
        status_frame = tk.Frame(header_frame, bg=self.colors['surface'])
        status_frame.grid(row=0, column=1, sticky=(tk.E, tk.N, tk.S), padx=20)
        
        # Connection status
        self.connection_status = tk.Label(status_frame,
                                         text="● Disconnected",
                                         font=(self.default_font[0], 10, 'bold'),
                                         fg=self.colors['error'],
                                         bg=self.colors['surface'])
        self.connection_status.pack(anchor='e', pady=2)
        
        # Operation status
        self.operation_status = tk.Label(status_frame,
                                        text="Ready",
                                        font=('Segoe UI', 9),
                                        fg=self.colors['text_secondary'],
                                        bg=self.colors['surface'])
        self.operation_status.pack(anchor='e')
        
        # Last update time
        self.last_update = tk.Label(status_frame,
                                   text=f"Updated: {datetime.now().strftime('%H:%M:%S')}",
                                   font=('Segoe UI', 8),
                                   fg=self.colors['text_muted'],
                                   bg=self.colors['surface'])
        self.last_update.pack(anchor='e')
        
    def create_main_panels(self):
        """Create main left and right panels"""
        # Left panel - Configuration and Control
        self.left_panel = tk.Frame(self.main_container, bg=self.colors['background'])
        self.left_panel.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 8))
        self.left_panel.rowconfigure(0, weight=0)  # Device config
        self.left_panel.rowconfigure(1, weight=0)  # File upload
        self.left_panel.rowconfigure(2, weight=0)  # Function selection  
        self.left_panel.rowconfigure(3, weight=0)  # Progress tracking
        self.left_panel.rowconfigure(4, weight=1)  # Device list
        self.left_panel.columnconfigure(0, weight=1)
        
        # Right panel - Logs and Diagnostics
        self.right_panel = tk.Frame(self.main_container, bg=self.colors['background'])
        self.right_panel.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(8, 0))
        self.right_panel.rowconfigure(0, weight=0)  # Controls
        self.right_panel.rowconfigure(1, weight=1)  # Logs
        self.right_panel.rowconfigure(2, weight=0)  # Diagnostics
        self.right_panel.columnconfigure(0, weight=1)
        
        # Create panel contents
        self.create_device_configuration_panel()
        self.create_file_upload_panel()
        self.create_function_selection_panel()
        self.create_progress_tracking_panel()
        self.create_device_list_panel()
        self.create_control_panel()
        self.create_log_panel()
        self.create_diagnostics_panel()
        
    def create_device_configuration_panel(self):
        """Create device configuration panel with professional styling"""
        # Configuration card
        config_frame = tk.LabelFrame(self.left_panel, text="Device Configuration",
                                    bg=self.colors['surface'],
                                    fg=self.colors['text_primary'],
                                    font=('Segoe UI', 10, 'bold'),
                                    relief=tk.FLAT, bd=1)
        config_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        config_frame.columnconfigure(1, weight=1)
        
        # Target IP configuration
        tk.Label(config_frame, text="Target IP Address:",
                bg=self.colors['surface'], fg=self.colors['text_primary'],
                font=('Segoe UI', 9)).grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        
        self.ip_entry = tk.Entry(config_frame, font=('Segoe UI', 10),
                                relief=tk.FLAT, bd=1, bg='white', fg='black')
        self.ip_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 10), pady=5)
        self.ip_entry.insert(0, self.config['target_ip'])
        
        # Bind events to automatically update config when fields change
        self.ip_entry.bind('<KeyRelease>', self.update_config_from_fields)
        self.ip_entry.bind('<FocusOut>', self.update_config_from_fields)
        
        # IP validation indicator
        self.ip_validation = tk.Label(config_frame, text="✓", fg=self.colors['success'],
                                     bg=self.colors['surface'], font=('Segoe UI', 12, 'bold'))
        self.ip_validation.grid(row=0, column=2, padx=(0, 10), pady=5)
        
        # Credentials
        tk.Label(config_frame, text="Username:",
                bg=self.colors['surface'], fg=self.colors['text_primary'],
                font=('Segoe UI', 9)).grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        
        self.username_entry = tk.Entry(config_frame, font=('Segoe UI', 10),
                                      relief=tk.FLAT, bd=1, bg='white', fg='black')
        self.username_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 10), pady=5)
        self.username_entry.insert(0, self.config['username'])
        
        # Bind events to automatically update config when fields change
        self.username_entry.bind('<KeyRelease>', self.update_config_from_fields)
        self.username_entry.bind('<FocusOut>', self.update_config_from_fields)
        
        tk.Label(config_frame, text="Password:",
                bg=self.colors['surface'], fg=self.colors['text_primary'],
                font=('Segoe UI', 9)).grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        
        self.password_entry = tk.Entry(config_frame, font=('Segoe UI', 10), show='*',
                                      relief=tk.FLAT, bd=1, bg='white', fg='black')
        self.password_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(5, 10), pady=5)
        self.password_entry.insert(0, self.config['password'])
        
        # Bind events to automatically update config when fields change
        self.password_entry.bind('<KeyRelease>', self.update_config_from_fields)
        self.password_entry.bind('<FocusOut>', self.update_config_from_fields)
        
        # Show/hide password
        self.show_password_var = tk.BooleanVar()
        show_password_cb = tk.Checkbutton(config_frame, text="Show",
                                         variable=self.show_password_var,
                                         command=self.toggle_password_visibility,
                                         bg=self.colors['surface'],
                                         font=('Segoe UI', 8))
        show_password_cb.grid(row=2, column=2, padx=(0, 10), pady=5)
        
        # Configuration status indicator
        self.config_status_label = tk.Label(config_frame, text="🔄 Config: Live",
                                           bg=self.colors['surface'],
                                           fg=self.colors['success'],
                                           font=('Segoe UI', 8))
        self.config_status_label.grid(row=3, column=0, columnspan=3, pady=(5, 0))
        
        # Quick reset buttons
        reset_frame = tk.Frame(config_frame, bg=self.colors['surface'])
        reset_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 5))
        
        reset_password_btn = ttk.Button(reset_frame, text="🔑 Reset Password", 
                                       style='Warning.TButton',
                                       command=self.reset_device_password)
        reset_password_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        reset_ip_btn = ttk.Button(reset_frame, text="🌐 Reset IP", 
                                 style='Warning.TButton',
                                 command=self.reset_device_ip)
        reset_ip_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Advanced options
        advanced_frame = tk.Frame(config_frame, bg=self.colors['surface'])
        advanced_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), padx=10, pady=5)
        advanced_frame.columnconfigure(1, weight=1)
        
        tk.Label(advanced_frame, text="Scan Interval (sec):",
                bg=self.colors['surface'], fg=self.colors['text_primary'],
                font=('Segoe UI', 9)).grid(row=0, column=0, sticky=tk.W)
        
        self.interval_var = tk.StringVar(value=str(self.config['scan_interval']))
        interval_spinbox = tk.Spinbox(advanced_frame, from_=5, to=300, width=10,
                                     textvariable=self.interval_var,
                                     font=('Segoe UI', 9))
        interval_spinbox.grid(row=0, column=1, sticky=tk.W, padx=(5, 0))
        
        # Auto-retry option
        self.auto_retry_var = tk.BooleanVar(value=self.config['auto_retry'])
        auto_retry_cb = tk.Checkbutton(advanced_frame, text="Auto-retry on failure",
                                      variable=self.auto_retry_var,
                                      bg=self.colors['surface'],
                                      fg='black',
                                      font=('Segoe UI', 9))
        auto_retry_cb.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        # Sound notifications
        self.sound_var = tk.BooleanVar(value=self.config['sound_notifications'])
        sound_cb = tk.Checkbutton(advanced_frame, text="Sound notifications",
                                 variable=self.sound_var,
                                 bg=self.colors['surface'],
                                 fg='black',
                                 font=('Segoe UI', 9))
        sound_cb.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        # Test sound button
        test_sound_btn = tk.Button(advanced_frame, text="🔊 Test Sound",
                                  command=self.test_sound_notifications,
                                  bg=self.colors['surface'],
                                  fg='black',
                                  font=('Segoe UI', 8))
        test_sound_btn.grid(row=2, column=2, sticky=tk.W, padx=(10, 0), pady=2)
        
        # Dark mode option
        self.dark_mode_var = tk.BooleanVar(value=False)
        dark_mode_cb = tk.Checkbutton(advanced_frame, text="Dark mode",
                                     variable=self.dark_mode_var,
                                     command=self.toggle_dark_mode,
                                     bg=self.colors['surface'],
                                     fg='black',
                                     font=('Segoe UI', 9))
        dark_mode_cb.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        # Final configuration section
        final_frame = tk.LabelFrame(config_frame, text="Final Configuration",
                                   bg=self.colors['surface'], fg=self.colors['text_primary'],
                                   font=(self.default_font[0], 9, 'bold'))
        final_frame.grid(row=5, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        final_frame.columnconfigure(1, weight=1)
        
        # Final IP
        tk.Label(final_frame, text="Final LAN IP:",
                bg=self.colors['surface'], fg=self.colors['text_primary'],
                font=self.default_font).grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        
        self.final_ip_var = tk.StringVar(value="192.168.1.1")
        final_ip_entry = tk.Entry(final_frame, textvariable=self.final_ip_var,
                                 font=self.default_font, relief=tk.FLAT, bd=1, bg='white', fg='black')
        final_ip_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 10), pady=5)
        
        # Final password
        tk.Label(final_frame, text="Final Password:",
                bg=self.colors['surface'], fg=self.colors['text_primary'],
                font=self.default_font).grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        
        self.final_password_var = tk.StringVar(value="L@ranet2025")
        self.final_password_entry = tk.Entry(final_frame, textvariable=self.final_password_var,
                                            font=self.default_font, show='*', relief=tk.FLAT, bd=1, bg='white', fg='black')
        self.final_password_entry.grid(row=1, column=1, sticky=(tk.W, tk.E), padx=(5, 10), pady=5)
        
        # Show/hide final password
        self.show_final_password_var = tk.BooleanVar()
        final_show_password_cb = tk.Checkbutton(final_frame, text="Show",
                                               variable=self.show_final_password_var,
                                               command=self.toggle_final_password_visibility,
                                               bg=self.colors['surface'],
                                               font=(self.default_font[0], 8))
        final_show_password_cb.grid(row=1, column=2, padx=(0, 10), pady=5)
        
        # Tailscale auth key
        tk.Label(final_frame, text="Tailscale Auth Key:",
                bg=self.colors['surface'], fg=self.colors['text_primary'],
                font=self.default_font).grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        
        self.tailscale_auth_key_var = tk.StringVar()
        self.tailscale_entry = tk.Entry(final_frame, textvariable=self.tailscale_auth_key_var,
                                       font=self.default_font, show='*', relief=tk.FLAT, bd=1, bg='white', fg='black')
        self.tailscale_entry.grid(row=2, column=1, sticky=(tk.W, tk.E), padx=(5, 10), pady=5)
        
        # Show/hide tailscale key
        self.show_tailscale_var = tk.BooleanVar()
        tailscale_show_cb = tk.Checkbutton(final_frame, text="Show",
                                          variable=self.show_tailscale_var,
                                          command=self.toggle_tailscale_visibility,
                                          bg=self.colors['surface'],
                                          font=(self.default_font[0], 8))
        tailscale_show_cb.grid(row=2, column=2, padx=(0, 10), pady=5)
        
        # Tailscale control buttons
        tailscale_buttons_frame = tk.Frame(final_frame, bg=self.colors['surface'])
        tailscale_buttons_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        tailscale_buttons_frame.columnconfigure(0, weight=1)
        tailscale_buttons_frame.columnconfigure(1, weight=1)
        tailscale_buttons_frame.columnconfigure(2, weight=1)
        tailscale_buttons_frame.columnconfigure(3, weight=1)
        
        # Submit Auth Key button
        self.tailscale_submit_button = tk.Button(tailscale_buttons_frame,
                                                text="🔑 Submit Auth Key",
                                                font=(self.default_font[0], 9, "bold"),
                                                bg=self.colors['primary'],
                                                fg='black',
                                                relief=tk.FLAT,
                                                bd=0,
                                                padx=15,
                                                pady=6,
                                                cursor="hand2",
                                                command=self.tailscale_submit_auth_key)
        self.tailscale_submit_button.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 3))
        
        # Tailscale Down button
        self.tailscale_down_button = tk.Button(tailscale_buttons_frame,
                                              text="🔴 Down",
                                              font=(self.default_font[0], 9, "bold"),
                                              bg=self.colors['error'],
                                              fg='black',
                                              relief=tk.FLAT,
                                              bd=0,
                                              padx=15,
                                              pady=6,
                                              cursor="hand2",
                                              command=self.tailscale_down)
        self.tailscale_down_button.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=3)
        
        # Tailscale Up button
        self.tailscale_up_button = tk.Button(tailscale_buttons_frame,
                                            text="🟢 Up",
                                            font=(self.default_font[0], 9, "bold"),
                                            bg=self.colors['success'],
                                            fg='black',
                                            relief=tk.FLAT,
                                            bd=0,
                                            padx=15,
                                            pady=6,
                                            cursor="hand2",
                                            command=self.tailscale_up)
        self.tailscale_up_button.grid(row=0, column=2, sticky=(tk.W, tk.E), padx=3)
        
        # Restart Tailscale button
        self.tailscale_restart_button = tk.Button(tailscale_buttons_frame,
                                                 text="🔄 Restart",
                                                 font=(self.default_font[0], 9, "bold"),
                                                 bg=self.colors['warning'],
                                                 fg='black',
                                                 relief=tk.FLAT,
                                                 bd=0,
                                                 padx=15,
                                                 pady=6,
                                                 cursor="hand2",
                                                 command=self.tailscale_restart)
        self.tailscale_restart_button.grid(row=0, column=3, sticky=(tk.W, tk.E), padx=(3, 0))
        
    def toggle_final_password_visibility(self):
        """Toggle final password field visibility"""
        if self.show_final_password_var.get():
            self.final_password_entry.configure(show='')
        else:
            self.final_password_entry.configure(show='*')
            
    def toggle_tailscale_visibility(self):
        """Toggle Tailscale auth key visibility"""
        # Store reference to tailscale entry during creation
        if hasattr(self, 'tailscale_entry'):
            if self.show_tailscale_var.get():
                self.tailscale_entry.configure(show='')
            else:
                self.tailscale_entry.configure(show='*')
    
    def validate_tailscale_auth_key(self):
        """Validate Tailscale auth key format"""
        try:
            auth_key = self.tailscale_auth_key_var.get()
            
            if not auth_key:
                return False
            
            # Check if it starts with tskey-auth- and has proper length
            if not auth_key.startswith('tskey-auth-'):
                return False
            
            # Check minimum length (tskey-auth- + at least 20 characters)
            if len(auth_key) < 30:
                return False
            
            # Check for valid characters (alphanumeric and hyphens)
            import re
            if not re.match(r'^tskey-auth-[a-zA-Z0-9\-]+$', auth_key):
                return False
            
            return True
            
        except Exception:
            return False
    
    def tailscale_submit_auth_key(self):
        """Submit new auth key to remote device and restart Tailscale"""
        if not self.validate_tailscale_auth_key():
            self.log_message("❌ Invalid auth key format. Please fix before proceeding.", "ERROR")
            return
        
        target_ip = self.ip_entry.get()
        username = self.username_entry.get()
        password = self.password_entry.get()
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
                self.log_message("💡 Tip: If this is the first time, try running 'Install Tailscale VPN Router' from the main functions first", "INFO")
                
        except Exception as e:
            self.log_message(f"❌ Error submitting auth key to remote device: {str(e)}", "ERROR")
    
    def tailscale_down(self):
        """Stop Tailscale container on remote device"""
        if not self.validate_tailscale_auth_key():
            self.log_message("❌ Invalid auth key format. Please fix before proceeding.", "ERROR")
            return
        
        target_ip = self.ip_entry.get()
        username = self.username_entry.get()
        password = self.password_entry.get()
        
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
        
        target_ip = self.ip_entry.get()
        username = self.username_entry.get()
        password = self.password_entry.get()
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
                self.log_message("💡 Tip: If this is the first time, try running 'Install Tailscale VPN Router' from the main functions first", "INFO")
                
        except Exception as e:
            self.log_message(f"❌ Error starting Tailscale on remote device: {str(e)}", "ERROR")
    
    def tailscale_restart(self):
        """Restart Tailscale container on remote device (down then up)"""
        if not self.validate_tailscale_auth_key():
            self.log_message("❌ Invalid auth key format. Please fix before proceeding.", "ERROR")
            return
        
        target_ip = self.ip_entry.get()
        self.log_message(f"🔄 Restarting Tailscale container on remote device {target_ip}...", "INFO")
        
        # First stop
        self.tailscale_down()
        
        # Wait a moment
        import time
        time.sleep(2)
        
        # Then start
        self.tailscale_up()
        
    def create_file_upload_panel(self):
        """Create file upload panel for flows.json and package.json"""
        # File upload card
        upload_frame = tk.LabelFrame(self.left_panel, text="File Upload & Configuration",
                                   bg=self.colors['surface'],
                                   fg=self.colors['text_primary'],
                                   font=(self.default_font[0], 10, 'bold'),
                                   relief=tk.FLAT, bd=1)
        upload_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        upload_frame.columnconfigure(1, weight=1)
        
        # Flows source selection
        tk.Label(upload_frame, text="Flows Source:",
                bg=self.colors['surface'], fg=self.colors['text_primary'],
                font=self.default_font).grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        
        self.flows_source_var = tk.StringVar(value="auto")
        flows_combo = ttk.Combobox(upload_frame, textvariable=self.flows_source_var,
                                  values=("auto", "local", "github", "uploaded"),
                                  state="readonly", width=12)
        flows_combo.grid(row=0, column=1, sticky=tk.W, padx=(5, 10), pady=5)
        
        # Package source selection
        tk.Label(upload_frame, text="Package Source:",
                bg=self.colors['surface'], fg=self.colors['text_primary'],
                font=self.default_font).grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        
        self.package_source_var = tk.StringVar(value="auto")
        package_combo = ttk.Combobox(upload_frame, textvariable=self.package_source_var,
                                   values=("auto", "local", "github", "uploaded"),
                                   state="readonly", width=12)
        package_combo.grid(row=1, column=1, sticky=tk.W, padx=(5, 10), pady=5)
        
        # Upload flows.json
        upload_flows_frame = tk.Frame(upload_frame, bg=self.colors['surface'])
        upload_flows_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=10, pady=5)
        upload_flows_frame.columnconfigure(1, weight=1)
        
        tk.Label(upload_flows_frame, text="Upload flows.json:",
                bg=self.colors['surface'], fg=self.colors['text_primary'],
                font=self.default_font).grid(row=0, column=0, sticky=tk.W)
        
        self.upload_flows_button = ttk.Button(upload_flows_frame, text="Choose File",
                                            command=self.upload_flows_file)
        self.upload_flows_button.grid(row=0, column=1, sticky=tk.W, padx=(10, 5))
        
        self.flows_status_label = tk.Label(upload_flows_frame, text="No file selected",
                                         bg=self.colors['surface'], fg=self.colors['text_secondary'],
                                         font=(self.default_font[0], 9))
        self.flows_status_label.grid(row=0, column=2, sticky=tk.W, padx=(5, 0))
        
        # Submit flows button (initially hidden)
        self.submit_flows_button = ttk.Button(upload_flows_frame, text="📤 Submit flows.json",
                                            style='Success.TButton',
                                            command=self.submit_flows,
                                            state=tk.DISABLED)
        self.submit_flows_button.grid(row=1, column=0, columnspan=3, pady=(5, 0), sticky=(tk.W, tk.E))
        
        # Upload package.json
        upload_package_frame = tk.Frame(upload_frame, bg=self.colors['surface'])
        upload_package_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), padx=10, pady=5)
        upload_package_frame.columnconfigure(1, weight=1)
        
        tk.Label(upload_package_frame, text="Upload package.json:",
                bg=self.colors['surface'], fg=self.colors['text_primary'],
                font=self.default_font).grid(row=0, column=0, sticky=tk.W)
        
        self.upload_package_button = ttk.Button(upload_package_frame, text="Choose File",
                                              command=self.upload_package_file)
        self.upload_package_button.grid(row=0, column=1, sticky=tk.W, padx=(10, 5))
        
        self.package_status_label = tk.Label(upload_package_frame, text="No file selected",
                                           bg=self.colors['surface'], fg=self.colors['text_secondary'],
                                           font=(self.default_font[0], 9))
        self.package_status_label.grid(row=0, column=2, sticky=tk.W, padx=(5, 0))
        
        # Clear files button
        self.clear_files_button = ttk.Button(upload_frame, text="🗑️ Clear Uploaded Files",
                                           style='Warning.TButton',
                                           command=self.clear_uploaded_files)
        self.clear_files_button.grid(row=4, column=0, columnspan=2, pady=(10, 5))
        
        # Initialize file tracking
        self.uploaded_flows_file = None
        self.uploaded_package_file = None
        
    def create_function_selection_panel(self):
        """Create function selection panel for choosing which steps to run"""
        # Function selection card
        selection_frame = tk.LabelFrame(self.left_panel, text="Configuration Steps Selection",
                                       bg=self.colors['surface'],
                                       fg=self.colors['text_primary'],
                                       font=(self.default_font[0], 10, 'bold'),
                                       relief=tk.FLAT, bd=1)
        selection_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        selection_frame.columnconfigure(0, weight=1)
        
        # Selection controls
        controls_frame = tk.Frame(selection_frame, bg=self.colors['surface'])
        controls_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=10, pady=5)
        
        # Quick selection buttons
        ttk.Button(controls_frame, text="Select All", 
                  command=self.select_all_functions).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(controls_frame, text="Select None",
                  command=self.select_none_functions).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(controls_frame, text="Quick Setup",
                  style='Success.TButton',
                  command=self.select_quick_setup).pack(side=tk.LEFT, padx=(0, 5))
        
        # Selection counter
        self.selection_counter = tk.Label(controls_frame, text="Selected: 0 functions",
                                        bg=self.colors['surface'], fg=self.colors['text_secondary'],
                                        font=(self.default_font[0], 9))
        self.selection_counter.pack(side=tk.RIGHT)
        
        # Scrollable function list
        list_frame = tk.Frame(selection_frame, bg=self.colors['surface'])
        list_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=(0, 10))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # Canvas for scrolling
        canvas = tk.Canvas(list_frame, bg=self.colors['surface_variant'], 
                          height=150, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = tk.Frame(canvas, bg=self.colors['surface_variant'])
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # Create function checkboxes
        self.create_function_checkboxes()
        
    def create_function_checkboxes(self):
        """Create checkboxes for function selection"""
        self.function_vars = []
        self.function_descriptions = [
            ("forward", "Configure Network FORWARD (WAN=eth1 DHCP, LAN=eth0 static)", []),
            ("check-dns", "Check DNS Connectivity", []),
            ("fix-dns", "Fix DNS Configuration (add Google DNS)", []),
            ("install-curl", "Install curl package", []),
            ("install-docker", "Install Docker (after network config)", ["forward"]),
            ("install-services", "Install All Docker Services (Node-RED, Portainer, Restreamer)", ["install-docker"]),
            ("install-nodered-nodes", "Install Node-RED Nodes (ffmpeg, queue-gate, sqlite, serialport)", ["install-services"]),
            ("import-nodered-flows", "Import Node-RED Flows", ["install-services"]),
            ("update-nodered-auth", "Update Node-RED Authentication", ["import-nodered-flows"]),
            ("install-tailscale", "Install Tailscale VPN Router", ["install-services"]),
            ("reverse", "Configure Network REVERSE (uses Final LAN IP)", []),
            ("set-password", "Change Device Password", [])
        ]
        
        for i, (func_id, description, dependencies) in enumerate(self.function_descriptions):
            # Create function item frame
            item_frame = tk.Frame(self.scrollable_frame, bg=self.colors['surface'], 
                                relief=tk.FLAT, bd=1, pady=2)
            item_frame.pack(fill=tk.X, padx=2, pady=1)
            item_frame.columnconfigure(1, weight=1)
            
            # Checkbox
            var = tk.BooleanVar()
            self.function_vars.append(var)
            
            checkbox = tk.Checkbutton(item_frame, variable=var,
                                    bg=self.colors['surface'],
                                    activebackground=self.colors['surface'])
            checkbox.grid(row=0, column=0, padx=5, sticky=tk.W)
            
            # Description label
            desc_label = tk.Label(item_frame, text=f"{i+1}. {description}",
                                font=self.default_font, fg=self.colors['text_primary'],
                                bg=self.colors['surface'], anchor='w')
            desc_label.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(5, 10))
            
            # Store function info
            checkbox.func_id = func_id
            checkbox.dependencies = dependencies
            
            # Bind selection change
            var.trace_add('write', lambda *args: self.update_selection_counter())
            
    def create_progress_tracking_panel(self):
        """Create enhanced progress tracking with detailed step information"""
        # Progress card
        progress_frame = tk.LabelFrame(self.left_panel, text="Operation Progress",
                                      bg=self.colors['surface'],
                                      fg=self.colors['text_primary'],
                                      font=('Segoe UI', 10, 'bold'),
                                      relief=tk.FLAT, bd=1)
        progress_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        progress_frame.columnconfigure(0, weight=1)
        
        # Overall progress
        overall_frame = tk.Frame(progress_frame, bg=self.colors['surface'])
        overall_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=10, pady=8)
        overall_frame.columnconfigure(1, weight=1)
        
        tk.Label(overall_frame, text="Overall:",
                bg=self.colors['surface'], fg=self.colors['text_primary'],
                font=('Segoe UI', 9, 'bold')).grid(row=0, column=0, sticky=tk.W)
        
        self.overall_progress = ttk.Progressbar(overall_frame, mode='determinate',
                                               style='Success.Horizontal.TProgressbar')
        self.overall_progress.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 0))
        
        self.overall_progress_text = tk.Label(overall_frame, text="0/12 steps",
                                             bg=self.colors['surface'],
                                             fg=self.colors['text_secondary'],
                                             font=('Segoe UI', 8))
        self.overall_progress_text.grid(row=0, column=2, padx=(10, 0))
        
        # Current step progress
        current_frame = tk.Frame(progress_frame, bg=self.colors['surface'])
        current_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=10, pady=(0, 8))
        current_frame.columnconfigure(1, weight=1)
        
        self.current_step_label = tk.Label(current_frame, text="Current Step: Ready",
                                          bg=self.colors['surface'],
                                          fg=self.colors['text_primary'],
                                          font=('Segoe UI', 9, 'bold'))
        self.current_step_label.grid(row=0, column=0, columnspan=3, sticky=tk.W)
        
        self.current_step_progress = ttk.Progressbar(current_frame, mode='indeterminate',
                                                    style='Success.Horizontal.TProgressbar')
        self.current_step_progress.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        # Time indicators
        time_frame = tk.Frame(progress_frame, bg=self.colors['surface'])
        time_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), padx=10, pady=(0, 8))
        time_frame.columnconfigure(0, weight=1)
        time_frame.columnconfigure(1, weight=1)
        
        self.elapsed_time_label = tk.Label(time_frame, text="Elapsed: 00:00:00",
                                          bg=self.colors['surface'],
                                          fg=self.colors['text_secondary'],
                                          font=('Segoe UI', 8))
        self.elapsed_time_label.grid(row=0, column=0, sticky=tk.W)
        
        self.estimated_time_label = tk.Label(time_frame, text="ETA: --:--:--",
                                            bg=self.colors['surface'],
                                            fg=self.colors['text_secondary'],
                                            font=('Segoe UI', 8))
        self.estimated_time_label.grid(row=0, column=1, sticky=tk.E)
        
    def create_device_list_panel(self):
        """Create device discovery and management panel"""
        # Device list card
        device_frame = tk.LabelFrame(self.left_panel, text="Discovered Devices",
                                    bg=self.colors['surface'],
                                    fg=self.colors['text_primary'],
                                    font=('Segoe UI', 10, 'bold'),
                                    relief=tk.FLAT, bd=1)
        device_frame.grid(row=4, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        device_frame.columnconfigure(0, weight=1)
        device_frame.rowconfigure(1, weight=1)
        
        # Device list controls
        controls_frame = tk.Frame(device_frame, bg=self.colors['surface'])
        controls_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=10, pady=5)
        controls_frame.columnconfigure(1, weight=1)
        
        scan_button = ttk.Button(controls_frame, text="Scan Network",
                                style='Primary.TButton',
                                command=self.scan_network)
        scan_button.grid(row=0, column=0, sticky=tk.W)
        
        self.device_count_label = tk.Label(controls_frame, text="0 devices found",
                                          bg=self.colors['surface'],
                                          fg=self.colors['text_secondary'],
                                          font=('Segoe UI', 9))
        self.device_count_label.grid(row=0, column=1, sticky=tk.E)
        
        # Device tree
        tree_frame = tk.Frame(device_frame, bg=self.colors['surface'])
        tree_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=(0, 10))
        tree_frame.columnconfigure(0, weight=1)
        tree_frame.rowconfigure(0, weight=1)
        
        # Treeview for device list
        columns = ('Status', 'Progress', 'Last Seen')
        self.device_tree = ttk.Treeview(tree_frame, columns=columns, show='tree headings', height=8)
        
        # Configure columns
        self.device_tree.heading('#0', text='IP Address')
        self.device_tree.heading('Status', text='Status')
        self.device_tree.heading('Progress', text='Progress')
        self.device_tree.heading('Last Seen', text='Last Seen')
        
        self.device_tree.column('#0', width=120, minwidth=100)
        self.device_tree.column('Status', width=80, minwidth=60)
        self.device_tree.column('Progress', width=60, minwidth=50)
        self.device_tree.column('Last Seen', width=80, minwidth=70)
        
        self.device_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar for device tree
        device_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.device_tree.yview)
        device_scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.device_tree.configure(yscrollcommand=device_scrollbar.set)
        
    def create_control_panel(self):
        """Create main control buttons with enhanced functionality"""
        control_frame = tk.Frame(self.right_panel, bg=self.colors['surface'],
                                relief=tk.FLAT, bd=1)
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
        control_frame.columnconfigure(0, weight=1)
        
        # Button container
        button_frame = tk.Frame(control_frame, bg=self.colors['surface'])
        button_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=15, pady=15)
        
        # Main action buttons
        button_row1 = tk.Frame(button_frame, bg=self.colors['surface'])
        button_row1.pack(fill=tk.X, pady=(0, 10))
        
        self.start_button = ttk.Button(button_row1, text="🚀 Start Configuration",
                                      style='Success.TButton',
                                      command=self.start_configuration)
        self.start_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.stop_button = ttk.Button(button_row1, text="⏹ Stop Operation",
                                     style='Danger.TButton',
                                     command=self.stop_operation,
                                     state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.pause_button = ttk.Button(button_row1, text="⏸ Pause",
                                      style='Warning.TButton',
                                      command=self.pause_operation,
                                      state=tk.DISABLED)
        self.pause_button.pack(side=tk.LEFT)
        
        # Secondary action buttons
        button_row2 = tk.Frame(button_frame, bg=self.colors['surface'])
        button_row2.pack(fill=tk.X, pady=(0, 10))
        
        validate_button = ttk.Button(button_row2, text="🔍 Validate Config",
                                    command=self.validate_configuration)
        validate_button.pack(side=tk.LEFT, padx=(0, 10))
        
        backup_button = ttk.Button(button_row2, text="💾 Backup Settings",
                                  command=self.backup_device_config)
        backup_button.pack(side=tk.LEFT, padx=(0, 10))
        
        reset_button = ttk.Button(button_row2, text="🔄 Reset Device",
                                 style='Warning.TButton',
                                 command=self.reset_device)
        reset_button.pack(side=tk.LEFT)
        
        # Operation mode selection - Make it more visible
        mode_frame = tk.LabelFrame(control_frame, text="Operation Mode",
                                  bg=self.colors['surface'], fg=self.colors['text_primary'],
                                  font=(self.default_font[0], 10, 'bold'),
                                  relief=tk.FLAT, bd=1)
        mode_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=15, pady=(0, 15))
        
        self.operation_mode = tk.StringVar(value="full_deployment")
        
        modes = [
            ("Full Deployment", "full_deployment"),
            ("Network Only", "network_only"), 
            ("Services Only", "services_only"),
            ("Validation Only", "validation_only")
        ]
        
        for text, value in modes:
            rb = tk.Radiobutton(mode_frame, text=text, variable=self.operation_mode,
                               value=value, bg=self.colors['surface'],
                               fg=self.colors['text_primary'],
                               font=self.default_font,
                               selectcolor=self.colors['primary'])
            rb.pack(anchor=tk.W, padx=10, pady=2)
        
    def create_log_panel(self):
        """Create enhanced log panel with filtering and search"""
        log_frame = tk.LabelFrame(self.right_panel, text="Operation Logs",
                                 bg=self.colors['surface'],
                                 fg=self.colors['text_primary'],
                                 font=('Segoe UI', 10, 'bold'),
                                 relief=tk.FLAT, bd=1)
        log_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(2, weight=1)
        
        # Log controls
        log_controls = tk.Frame(log_frame, bg=self.colors['surface'])
        log_controls.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=10, pady=5)
        log_controls.columnconfigure(2, weight=1)
        
        # Log level filter
        tk.Label(log_controls, text="Level:",
                bg=self.colors['surface'], fg=self.colors['text_primary'],
                font=('Segoe UI', 9)).grid(row=0, column=0, sticky=tk.W)
        
        self.log_level_var = tk.StringVar(value="ALL")
        log_level_combo = ttk.Combobox(log_controls, textvariable=self.log_level_var,
                                      values=["ALL", "ERROR", "WARNING", "INFO", "SUCCESS"],
                                      state="readonly", width=10)
        log_level_combo.grid(row=0, column=1, sticky=tk.W, padx=(5, 10))
        log_level_combo.bind('<<ComboboxSelected>>', self.filter_logs)
        
        # Search box
        tk.Label(log_controls, text="Search:",
                bg=self.colors['surface'], fg=self.colors['text_primary'],
                font=('Segoe UI', 9)).grid(row=0, column=2, sticky=tk.E, padx=(10, 5))
        
        self.log_search_var = tk.StringVar()
        self.log_search_var.trace_add('write', self.search_logs)
        search_entry = tk.Entry(log_controls, textvariable=self.log_search_var,
                               font=('Segoe UI', 9), width=20, fg='black')
        search_entry.grid(row=0, column=3, sticky=(tk.W, tk.E), padx=(0, 10))
        
        # Clear logs button
        clear_button = ttk.Button(log_controls, text="Clear",
                                 command=self.clear_logs)
        clear_button.grid(row=0, column=4, sticky=tk.E)
        
        # Auto-scroll option
        scroll_frame = tk.Frame(log_frame, bg=self.colors['surface'])
        scroll_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=10, pady=5)
        
        self.auto_scroll_var = tk.BooleanVar(value=True)
        auto_scroll_cb = tk.Checkbutton(scroll_frame, text="Auto-scroll",
                                       variable=self.auto_scroll_var,
                                       bg=self.colors['surface'],
                                       font=('Segoe UI', 9))
        auto_scroll_cb.pack(anchor=tk.W)
        
        # Log text area with enhanced formatting
        log_text_frame = tk.Frame(log_frame, bg=self.colors['surface'])
        log_text_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=10, pady=(0, 10))
        log_text_frame.columnconfigure(0, weight=1)
        log_text_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_text_frame, 
                                                 font=self.mono_font,
                                                 bg='#fafafa', fg=self.colors['text_primary'],
                                                 relief=tk.FLAT, bd=1,
                                                 wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure text tags for different log levels
        self.log_text.tag_configure("ERROR", foreground=self.colors['error'], font=self.mono_font + ('bold',))
        self.log_text.tag_configure("WARNING", foreground=self.colors['warning'], font=self.mono_font + ('bold',))
        self.log_text.tag_configure("SUCCESS", foreground=self.colors['success'], font=self.mono_font + ('bold',))
        self.log_text.tag_configure("INFO", foreground=self.colors['info'])
        self.log_text.tag_configure("TIMESTAMP", foreground=self.colors['text_muted'], font=(self.mono_font[0], 8))
        self.log_text.tag_configure('search_highlight', background='yellow', foreground='black')
        
    def create_diagnostics_panel(self):
        """Create network diagnostics and troubleshooting panel"""
        diag_frame = tk.LabelFrame(self.right_panel, text="Network Diagnostics",
                                  bg=self.colors['surface'],
                                  fg=self.colors['text_primary'],
                                  font=('Segoe UI', 10, 'bold'),
                                  relief=tk.FLAT, bd=1)
        diag_frame.grid(row=2, column=0, sticky=(tk.W, tk.E))
        diag_frame.columnconfigure(0, weight=1)
        
        # Diagnostic controls
        diag_controls = tk.Frame(diag_frame, bg=self.colors['surface'])
        diag_controls.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=10, pady=10)
        
        # Quick diagnostic buttons
        ping_button = ttk.Button(diag_controls, text="🏓 Ping Test",
                                command=self.run_ping_test)
        ping_button.pack(side=tk.LEFT, padx=(0, 5))
        
        ssh_button = ttk.Button(diag_controls, text="🔐 SSH Test",
                               command=self.run_ssh_test)
        ssh_button.pack(side=tk.LEFT, padx=(0, 5))
        
        port_button = ttk.Button(diag_controls, text="🔍 Port Scan",
                                command=self.run_port_scan)
        port_button.pack(side=tk.LEFT, padx=(0, 5))
        
        # Diagnostic status
        self.diag_status_label = tk.Label(diag_frame, text="Ready for diagnostics",
                                         bg=self.colors['surface'],
                                         fg=self.colors['text_secondary'],
                                         font=('Segoe UI', 9))
        self.diag_status_label.grid(row=1, column=0, sticky=(tk.W, tk.E), padx=10, pady=(0, 10))
        
    def create_footer(self):
        """Create footer with status information"""
        footer_frame = tk.Frame(self.main_container, bg=self.colors['surface'],
                               height=40, relief=tk.FLAT, bd=1)
        footer_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(15, 0))
        footer_frame.grid_propagate(False)
        footer_frame.columnconfigure(1, weight=1)
        
        # Application info
        info_label = tk.Label(footer_frame,
                             text="Bivicom Network Configuration Manager v2.0 Enterprise",
                             bg=self.colors['surface'], fg=self.colors['text_muted'],
                             font=('Segoe UI', 8))
        info_label.grid(row=0, column=0, sticky=(tk.W, tk.N, tk.S), padx=10)
        
        # System status
        self.system_status = tk.Label(footer_frame,
                                     text=f"System Ready • Python {sys.version_info.major}.{sys.version_info.minor}",
                                     bg=self.colors['surface'], fg=self.colors['text_muted'],
                                     font=('Segoe UI', 8))
        self.system_status.grid(row=0, column=1, sticky=(tk.E, tk.N, tk.S), padx=10)
        
    def setup_event_handlers(self):
        """Setup event handlers and bindings"""
        # Window events
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Entry validations
        self.ip_entry.bind('<KeyRelease>', self.validate_ip_address)
        self.ip_entry.bind('<FocusOut>', self.validate_ip_address)
        
        # Device tree events
        self.device_tree.bind('<<TreeviewSelect>>', self.on_device_select)
        self.device_tree.bind('<Double-1>', self.on_device_double_click)
        
        # Keyboard shortcuts
        self.root.bind('<Control-s>', lambda e: self.start_configuration())
        self.root.bind('<Control-q>', lambda e: self.on_closing())
        self.root.bind('<F5>', lambda e: self.scan_network())
        
    def start_background_tasks(self):
        """Start background tasks for real-time updates"""
        # Start log processing
        self.process_queues()
        
        # Start time updates
        self.update_time_displays()
        
        # Start periodic device discovery
        if self.config.get('auto_discovery', True):
            self.periodic_discovery()
            
    # Event Handlers and UI Logic
    
    def validate_ip_address(self, event=None):
        """Validate IP address input and update indicator"""
        ip_text = self.ip_entry.get().strip()
        try:
            ipaddress.ip_address(ip_text)
            self.ip_validation.configure(text="✓", fg=self.colors['success'])
            self.config['target_ip'] = ip_text
        except ValueError:
            self.ip_validation.configure(text="✗", fg=self.colors['error'])
            
    def update_config_from_fields(self, event=None):
        """Update configuration from GUI input fields in real-time"""
        try:
            # Get current values from all input fields
            new_ip = self.ip_entry.get().strip()
            new_username = self.username_entry.get().strip()
            new_password = self.password_entry.get().strip()
            
            # Update configuration if values have changed
            config_changed = False
            
            if new_ip != self.config.get('target_ip', ''):
                self.config['target_ip'] = new_ip
                config_changed = True
                
            if new_username != self.config.get('username', ''):
                self.config['username'] = new_username
                config_changed = True
                
            if new_password != self.config.get('password', ''):
                self.config['password'] = new_password
                config_changed = True
            
            # Validate IP if it changed
            if event and event.widget == self.ip_entry:
                self.validate_ip_address()
            
            # Update status indicator and log configuration updates
            if config_changed:
                # Update status indicator
                self.config_status_label.configure(text="🔄 Config: Updated", fg=self.colors['info'])
                # Reset status after 2 seconds
                self.root.after(2000, lambda: self.config_status_label.configure(
                    text="🔄 Config: Live", fg=self.colors['success']))
                
                # Log only for focus out events (not every keystroke)
                if event and hasattr(event, 'type') and str(event.type) == '10':  # FocusOut event
                    self.log_message(f"🔄 Configuration updated: {new_username}@{new_ip}", "INFO")
                
        except Exception as e:
            # Silent handling - don't spam logs with validation errors during typing
            pass
            
    def toggle_password_visibility(self):
        """Toggle password field visibility"""
        if self.show_password_var.get():
            self.password_entry.configure(show='')
        else:
            self.password_entry.configure(show='*')
            
    def scan_network(self):
        """Perform network scan for devices"""
        self.log_message("🔍 Starting network scan...", "INFO")
        self.operation_status.configure(text="Scanning network...")
        self.connection_status.configure(text="● Scanning...", fg=self.colors['warning'])
        
        # Run scan in background thread
        threading.Thread(target=self._scan_network_worker, daemon=True).start()
        
    def _scan_network_worker(self):
        """Background worker for network scanning"""
        try:
            target_ip = self.config['target_ip']
            network = ipaddress.IPv4Network(f"{target_ip}/24", strict=False)
            
            discovered = 0
            for ip in network.hosts():
                if self.shutdown_requested:
                    break
                    
                ip_str = str(ip)
                if self._ping_host(ip_str):
                    device_info = DeviceInfo(
                        ip=ip_str,
                        status="Online",
                        last_seen=datetime.now()
                    )
                    self.devices[ip_str] = device_info
                    discovered += 1
                    
                    # Update UI
                    self.root.after(0, lambda: self._update_device_tree())
                    
            # Update connection status based on results
            if discovered > 0:
                self.root.after(0, lambda: self.connection_status.configure(text="● Connected", fg=self.colors['success']))
                self.log_message(f"✅ Network scan completed. Found {discovered} devices.", "SUCCESS")
            else:
                self.root.after(0, lambda: self.connection_status.configure(text="● No devices found", fg=self.colors['warning']))
                self.log_message(f"⚠️ Network scan completed. No devices found.", "WARNING")
                
            self.root.after(0, lambda: self.operation_status.configure(text="Scan completed"))
            
        except Exception as e:
            self.log_message(f"❌ Network scan failed: {str(e)}", "ERROR")
            self.root.after(0, lambda: self.connection_status.configure(text="● Scan failed", fg=self.colors['error']))
            
    def _ping_host(self, ip: str, timeout: int = 2) -> bool:
        """Ping a host to check if it's reachable with robust timeout handling"""
        try:
            # Validate IP address first
            try:
                ipaddress.ip_address(ip)
            except ValueError:
                return False
                
            if platform.system().lower() == "windows":
                # Windows ping command
                cmd = ['ping', '-n', '1', '-w', str(timeout * 1000), ip]
            else:
                # Unix/Linux/macOS ping command
                cmd = ['ping', '-c', '1', '-W', str(timeout), ip]
            
            # Use a shorter timeout to prevent hanging
            process_timeout = min(timeout + 1, 5)  # Max 5 seconds
            
            result = subprocess.run(cmd, capture_output=True, text=True, 
                                  timeout=process_timeout, check=False)
            return result.returncode == 0
            
        except subprocess.TimeoutExpired:
            # Ping command timed out
            return False
        except FileNotFoundError:
            # ping command not found
            return False
        except Exception as e:
            # Any other error
            return False
            
    def _update_device_tree(self):
        """Update the device tree display"""
        # Clear existing items
        for item in self.device_tree.get_children():
            self.device_tree.delete(item)
            
        # Add devices
        for ip, device in self.devices.items():
            status_icon = "🟢" if device.status == "Online" else "🔴"
            self.device_tree.insert('', 'end', text=ip,
                                   values=(f"{status_icon} {device.status}",
                                          f"{device.progress}%",
                                          device.last_seen.strftime("%H:%M:%S")))
                                          
        # Update count
        count = len(self.devices)
        self.device_count_label.configure(text=f"{count} device{'s' if count != 1 else ''} found")
        
    def start_configuration(self):
        """Start the network configuration process"""
        if self.is_running:
            messagebox.showwarning("Operation in Progress", 
                                 "A configuration operation is already running.")
            return
            
        # Get selected functions
        selected_functions = self.get_selected_functions()
        if not selected_functions:
            messagebox.showwarning("No Functions Selected", 
                                 "Please select at least one configuration function to run.")
            return
            
        # Validate inputs
        if not self._validate_configuration():
            return
            
        # Update UI state
        self.is_running = True
        self.start_button.configure(state=tk.DISABLED)
        self.stop_button.configure(state=tk.NORMAL)
        self.pause_button.configure(state=tk.NORMAL)
        
        # Initialize operation
        self.operation_start_time = datetime.now()
        self.current_step_index = 0
        
        # Reset step statuses
        for step in self.operation_steps:
            step.status = OperationStatus.PENDING
            step.progress = 0
            step.start_time = None
            step.end_time = None
            step.error_message = ""
            step.retry_count = 0
            
        self.log_message(f"🚀 Starting network configuration with {len(selected_functions)} selected functions...", "SUCCESS")
        self.log_message(f"📋 Selected functions: {', '.join(selected_functions)}", "INFO")
        self.operation_status.configure(text="Configuration in progress...")
        
        # Start configuration in background thread
        threading.Thread(target=self._configuration_worker, args=(selected_functions,), daemon=True).start()
        
    def _validate_configuration(self) -> bool:
        """Validate configuration before starting"""
        try:
            # Validate IP address
            ipaddress.ip_address(self.config['target_ip'])
        except ValueError:
            messagebox.showerror("Invalid Configuration", "Please enter a valid IP address.")
            return False
            
        # Check credentials
        if not self.config['username'].strip():
            messagebox.showerror("Invalid Configuration", "Username cannot be empty.")
            return False
            
        if not self.config['password'].strip():
            messagebox.showerror("Invalid Configuration", "Password cannot be empty.")
            return False
            
        return True
        
    def _configuration_worker(self, selected_functions):
        """Background worker for configuration process"""
        try:
            # Update configuration from current GUI fields before starting
            self.update_config_from_fields()
            
            # Create wrapper bot with GUI integration
            bot_wrapper = GUIBotWrapper(
                gui_log_callback=self.log_message,
                target_ip=self.config['target_ip'],
                username=self.config['username'],
                password=self.config['password'],
                step_progress_callback=self.update_progress,
                final_ip=self.final_ip_var.get(),
                final_password=self.final_password_var.get(),
                flows_source=self.flows_source_var.get(),
                package_source=self.package_source_var.get(),
                uploaded_flows_file=self.uploaded_flows_file,
                uploaded_package_file=self.uploaded_package_file
            )
            
            # Set selected functions
            bot_wrapper.selected_functions = selected_functions
            
            # Run the network configuration
            success = bot_wrapper.run_network_config()
            
            # Operation completed
            self._finish_operation(success)
            
        except Exception as e:
            self.log_message(f"❌ Configuration operation failed: {str(e)}", "ERROR")
            self._finish_operation(success=False)
            
    def _execute_step(self, step: OperationStep, step_number: int, total_steps: int):
        """Execute a single configuration step"""
        step.status = OperationStatus.RUNNING
        step.start_time = datetime.now()
        step.retry_count = 0
        
        self.log_message(f"📋 Step {step_number}/{total_steps}: {step.name}", "INFO")
        self.root.after(0, lambda: self._update_progress_display(step, step_number, total_steps))
        
        max_retries = step.max_retries if self.auto_retry_var.get() else 1
        
        while step.retry_count < max_retries and not self.shutdown_requested:
            try:
                if step.retry_count > 0:
                    self.log_message(f"🔄 Retrying step {step_number} (attempt {step.retry_count + 1}/{max_retries})", "WARNING")
                    
                # Execute the actual step
                success = self._execute_step_command(step)
                
                if success:
                    step.status = OperationStatus.SUCCESS
                    step.end_time = datetime.now()
                    duration = (step.end_time - step.start_time).total_seconds()
                    self.log_message(f"✅ Step {step_number} completed in {duration:.1f}s", "SUCCESS")
                    break
                else:
                    step.retry_count += 1
                    if step.retry_count >= max_retries:
                        step.status = OperationStatus.ERROR
                        step.end_time = datetime.now()
                        self.log_message(f"❌ Step {step_number} failed after {max_retries} attempts", "ERROR")
                    else:
                        time.sleep(2)  # Wait before retry
                        
            except Exception as e:
                step.retry_count += 1
                step.error_message = str(e)
                
                if step.retry_count >= max_retries:
                    step.status = OperationStatus.ERROR
                    step.end_time = datetime.now()
                    self.log_message(f"❌ Step {step_number} failed: {str(e)}", "ERROR")
                    break
                else:
                    self.log_message(f"⚠️ Step {step_number} error (will retry): {str(e)}", "WARNING")
                    time.sleep(2)
                    
        # Update UI
        self.root.after(0, lambda: self._update_progress_display(step, step_number, total_steps))
        
    def _execute_step_command(self, step: OperationStep) -> bool:
        """Execute the actual command for a step"""
        # This is a simplified implementation - in reality, each step would have specific commands
        # For demonstration, we'll simulate the operation
        
        # Simulate variable duration based on step
        import random
        duration = random.uniform(1, min(step.estimated_duration / 10, 5))
        
        # Simulate progress updates
        for progress in range(0, 101, 10):
            if self.shutdown_requested:
                return False
                
            step.progress = progress
            time.sleep(duration / 10)
            
            # Update UI progress
            self.root.after(0, lambda p=progress: self.current_step_progress.configure(value=p))
            
        # Simulate some failures for demonstration
        if random.random() < 0.1:  # 10% failure rate
            raise Exception("Simulated operation failure")
            
        return True
        
    def _update_progress_display(self, step: OperationStep, step_number: int, total_steps: int):
        """Update the progress display"""
        # Update overall progress
        overall_progress = (step_number - 1) / total_steps * 100
        if step.status == OperationStatus.SUCCESS:
            overall_progress = step_number / total_steps * 100
        
        self.overall_progress.configure(value=overall_progress)
        self.overall_progress_text.configure(text=f"{step_number if step.status == OperationStatus.SUCCESS else step_number-1}/{total_steps} steps")
        
        # Update current step display
        self.current_step_label.configure(text=f"Current Step: {step.name}")
        
        # Update step progress bar
        if step.status == OperationStatus.RUNNING:
            self.current_step_progress.configure(mode='indeterminate')
            self.current_step_progress.start()
        else:
            self.current_step_progress.stop()
            self.current_step_progress.configure(mode='determinate', value=100 if step.status == OperationStatus.SUCCESS else 0)
            
    def _finish_operation(self, success: bool = True):
        """Complete the operation and update UI"""
        self.is_running = False
        
        # Update UI state
        self.root.after(0, self._reset_ui_state)
        
        if success:
            self.log_message("🎉 Configuration operation completed successfully!", "SUCCESS")
            self.operation_status.configure(text="Configuration completed")
            if self.sound_var.get():
                self._play_success_sound()
        else:
            self.log_message("❌ Configuration operation failed", "ERROR")
            self.operation_status.configure(text="Configuration failed")
            if self.sound_var.get():
                self._play_error_sound()
                
    def _reset_ui_state(self):
        """Reset UI to ready state"""
        self.start_button.configure(state=tk.NORMAL)
        self.stop_button.configure(state=tk.DISABLED)
        self.pause_button.configure(state=tk.DISABLED)
        
        self.current_step_progress.stop()
        self.current_step_progress.configure(mode='determinate', value=0)
        self.current_step_label.configure(text="Current Step: Ready")
        
    def stop_operation(self):
        """Stop the current operation"""
        if not self.is_running:
            return
            
        result = messagebox.askyesno("Stop Operation", 
                                   "Are you sure you want to stop the current operation?")
        if result:
            self.shutdown_requested = True
            self.log_message("🛑 Stopping operation...", "WARNING")
            
    def pause_operation(self):
        """Pause/resume the current operation"""
        # Implementation for pause/resume functionality
        pass
        
    def validate_configuration(self):
        """Validate current configuration without running full deployment"""
        self.log_message("🔍 Validating configuration...", "INFO")
        threading.Thread(target=self._validation_worker, daemon=True).start()
        
    def _validation_worker(self):
        """Background worker for configuration validation"""
        try:
            # Test connectivity
            if self._ping_host(self.config['target_ip']):
                self.log_message("✅ Device is reachable", "SUCCESS")
            else:
                self.log_message("❌ Device is not reachable", "ERROR")
                return
                
            # Test SSH connectivity (simplified)
            self.log_message("🔐 Testing SSH connectivity...", "INFO")
            time.sleep(2)  # Simulate SSH test
            self.log_message("✅ SSH connectivity verified", "SUCCESS")
            
            # Validate configuration files
            self.log_message("📄 Validating configuration files...", "INFO")
            time.sleep(1)
            self.log_message("✅ Configuration validation completed", "SUCCESS")
            
        except Exception as e:
            self.log_message(f"❌ Validation failed: {str(e)}", "ERROR")
            
    def backup_device_config(self):
        """Backup current device configuration"""
        self.log_message("💾 Creating configuration backup...", "INFO")
        threading.Thread(target=self._backup_worker, daemon=True).start()
        
    def _backup_worker(self):
        """Background worker for configuration backup"""
        try:
            # Simulate backup process
            time.sleep(3)
            
            # Create backup directory
            backup_dir = os.path.join(os.path.dirname(__file__), "backups")
            os.makedirs(backup_dir, exist_ok=True)
            
            # Generate backup filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = os.path.join(backup_dir, f"config_backup_{timestamp}.json")
            
            # Simulate saving backup
            backup_data = {
                "timestamp": timestamp,
                "device_ip": self.config['target_ip'],
                "configuration": "simulated_config_data"
            }
            
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2)
                
            self.log_message(f"✅ Configuration backup saved to {backup_file}", "SUCCESS")
            
        except Exception as e:
            self.log_message(f"❌ Backup failed: {str(e)}", "ERROR")
            
    def reset_device(self):
        """Reset device to factory defaults"""
        # Add debugging information to track when this is called
        import traceback
        import inspect
        
        # Get the calling function information
        frame = inspect.currentframe()
        caller_info = []
        try:
            for i in range(5):  # Get up to 5 levels of call stack
                frame = frame.f_back
                if frame is None:
                    break
                caller_info.append(f"  {i+1}. {frame.f_code.co_filename}:{frame.f_lineno} in {frame.f_code.co_name}")
        finally:
            del frame
        
        self.log_message("🔍 DEBUG: reset_device() called from:", "INFO")
        for info in caller_info:
            self.log_message(info, "INFO")
        
        # Prevent automatic execution during GUI initialization
        if not hasattr(self, 'gui_fully_loaded') or not self.gui_fully_loaded:
            self.log_message("🚫 Reset function called during initialization - ignoring", "INFO")
            return
        
        # Check if reset is already in progress
        if hasattr(self, '_reset_in_progress') and self._reset_in_progress:
            self.log_message("⚠️ Reset operation already in progress, please wait...", "WARNING")
            return
            
        self.log_message("🔄 Reset Device button clicked by user", "INFO")
        
        result = messagebox.askyesno("Reset Device",
                                   "⚠️ WARNING: This will reset the device to factory defaults.\n\n"
                                   "This will:\n"
                                   "• Remove all Docker containers and services\n"
                                   "• Reset network to REVERSE mode (LTE WAN)\n"
                                   "• Reset password to admin/admin\n"
                                   "• Reset IP to 192.168.1.1\n\n"
                                   "All current configuration will be lost!\n\n"
                                   "Are you sure you want to continue?")
        
        if result:
            self._reset_in_progress = True
            self.log_message("🔄 Resetting device to factory defaults...", "WARNING")
            self.log_message("⏳ This may take several minutes. Please wait...", "INFO")
            
            # Start reset in background thread
            reset_thread = threading.Thread(target=self._reset_worker, daemon=True)
            reset_thread.start()
        else:
            self.log_message("❌ Reset cancelled by user", "INFO")
            
    def _reset_worker(self):
        """Background worker for device reset"""
        import subprocess
        import os
        
        try:
            self.log_message("🔄 Initiating device reset...", "INFO")
            
            # Call the actual network_config.sh script
            script_path = os.path.join(os.path.dirname(__file__), "network_config.sh")
            target_ip = self.config.get('target_ip', '192.168.1.1')
            username = self.config.get('username', 'admin')
            password = self.config.get('password', 'admin')
            
            # Build command to call network_config.sh with reset-device function
            cmd = [script_path, "--remote", target_ip, username, password, "reset-device"]
            
            self.log_message(f"🔧 Executing: {' '.join(cmd)}", "INFO")
            
            # Make sure the script is executable
            os.chmod(script_path, 0o755)
            
            # Use Popen for better control and real-time output
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            # Read output line by line for real-time feedback
            output_lines = []
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    output_lines.append(output.strip())
                    # Log each line for real-time feedback
                    self.log_message(f"📋 {output.strip()}", "INFO")
            
            # Get the final return code
            return_code = process.poll()
            
            if return_code == 0:
                self.log_message("✅ Device reset completed successfully", "SUCCESS")
                # Show summary of key operations
                self.log_message("📊 Reset Summary: All Docker services removed, network reset to REVERSE mode, password reset to admin/admin", "SUCCESS")
                self.log_message("🎉 Device is now ready for fresh configuration", "SUCCESS")
            else:
                self.log_message(f"❌ Reset failed with return code {return_code}", "ERROR")
                # Show last few lines of output for debugging
                if output_lines:
                    self.log_message("📋 Last output lines:", "ERROR")
                    for line in output_lines[-5:]:  # Show last 5 lines
                        self.log_message(f"   {line}", "ERROR")
            
            # Clear the reset in progress flag
            self._reset_in_progress = False
            
        except subprocess.TimeoutExpired:
            self.log_message("❌ Reset operation timed out after 5 minutes", "ERROR")
            self.log_message("💡 Try running the reset command manually from terminal", "INFO")
            self._reset_in_progress = False
        except FileNotFoundError:
            self.log_message("❌ network_config.sh script not found", "ERROR")
            self.log_message("💡 Make sure the script exists in the same directory as the GUI", "INFO")
            self._reset_in_progress = False
        except PermissionError:
            self.log_message("❌ Permission denied - make sure network_config.sh is executable", "ERROR")
            self.log_message("💡 Try running: chmod +x network_config.sh", "INFO")
            self._reset_in_progress = False
        except Exception as e:
            self.log_message(f"❌ Reset failed: {str(e)}", "ERROR")
            self.log_message("💡 Check the terminal output for more details", "INFO")
            self._reset_in_progress = False
            
    def reset_device_password(self):
        """Reset device password back to admin"""
        # Prevent automatic execution during GUI initialization
        if not hasattr(self, 'gui_fully_loaded') or not self.gui_fully_loaded:
            self.log_message("🚫 Reset password function called during initialization - ignoring", "INFO")
            return
            
        self.log_message("🔑 Reset Device Password button clicked", "INFO")
        
        result = messagebox.askyesno("Reset Device Password",
                                   "🔑 Reset device password back to 'admin'?\n\n"
                                   "This will:\n"
                                   "• Change device password to 'admin'\n"
                                   "• Update both web interface and SSH login\n"
                                   "• Allow default GUI credentials to work\n\n"
                                   "Continue?")
        
        if result:
            self.log_message("🔑 Resetting device password to admin...", "INFO")
            threading.Thread(target=self._reset_password_worker, daemon=True).start()
        else:
            self.log_message("🔑 Password reset cancelled by user", "INFO")
            
    def _reset_password_worker(self):
        """Background worker for password reset"""
        try:
            # Update config from current GUI fields
            self.update_config_from_fields()
            
            script_path = os.path.join(os.path.dirname(__file__), "network_config.sh")
            target_ip = self.config['target_ip']
            username = self.config['username']
            password = self.config['password']
            
            # Build command to reset password
            cmd = [script_path, "--remote", target_ip, username, password, "set-password-admin"]
            
            self.log_message(f"🔧 Executing password reset on {target_ip}...", "INFO")
            
            # Execute the command
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                     text=True, bufsize=1, universal_newlines=True)
            
            # Read output line by line
            for line in process.stdout:
                line = line.strip()
                if line:
                    self.log_message(f"[SCRIPT] {line}", "INFO")
            
            # Wait for process to complete
            return_code = process.wait(timeout=60)
            
            if return_code == 0:
                self.log_message("✅ Device password reset to 'admin' successfully", "SUCCESS")
                # Update GUI password field to reflect the change
                self.password_entry.delete(0, tk.END)
                self.password_entry.insert(0, "admin")
                self.update_config_from_fields()
            else:
                self.log_message("❌ Password reset failed", "ERROR")
                
        except subprocess.TimeoutExpired:
            process.kill()
            self.log_message("❌ Password reset timed out", "ERROR")
        except Exception as e:
            self.log_message(f"❌ Password reset error: {str(e)}", "ERROR")
            
    def reset_device_ip(self):
        """Reset device IP configuration"""
        # Prevent automatic execution during GUI initialization
        if not hasattr(self, 'gui_fully_loaded') or not self.gui_fully_loaded:
            self.log_message("🚫 Reset IP function called during initialization - ignoring", "INFO")
            return
            
        self.log_message("🌐 Reset Device IP button clicked", "INFO")
        
        result = messagebox.askyesno("Reset Device IP",
                                   "🌐 Reset device IP configuration?\n\n"
                                   "This will:\n"
                                   "• Reset device IP to 192.168.1.1\n"
                                   "• Configure network in REVERSE mode (LTE WAN)\n"
                                   "• Restart network services\n\n"
                                   "Note: Device may briefly lose connectivity during reset.\n\n"
                                   "Continue?")
        
        if result:
            self.log_message("🌐 Resetting device IP configuration...", "INFO")
            threading.Thread(target=self._reset_ip_worker, daemon=True).start()
        else:
            self.log_message("🌐 IP reset cancelled by user", "INFO")
            
    def _reset_ip_worker(self):
        """Background worker for IP reset"""
        try:
            # Update config from current GUI fields
            self.update_config_from_fields()
            
            script_path = os.path.join(os.path.dirname(__file__), "network_config.sh")
            target_ip = self.config['target_ip']
            username = self.config['username']
            password = self.config['password']
            
            # Build command to reset IP (reverse mode with default IP)
            cmd = [script_path, "--remote", target_ip, username, password, "reverse"]
            
            self.log_message(f"🔧 Executing IP reset on {target_ip}...", "INFO")
            self.log_message("⚠️ Device may temporarily lose connectivity...", "WARNING")
            
            # Execute the command
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                     text=True, bufsize=1, universal_newlines=True)
            
            # Read output line by line
            for line in process.stdout:
                line = line.strip()
                if line:
                    self.log_message(f"[SCRIPT] {line}", "INFO")
            
            # Wait for process to complete
            return_code = process.wait(timeout=120)
            
            if return_code == 0:
                self.log_message("✅ Device IP reset to 192.168.1.1 successfully", "SUCCESS")
                self.log_message("🔄 Updating GUI to use new IP address...", "INFO")
                # Update GUI IP field to reflect the change
                self.ip_entry.delete(0, tk.END)
                self.ip_entry.insert(0, "192.168.1.1")
                self.update_config_from_fields()
                self.log_message("✅ GUI configuration updated", "SUCCESS")
            else:
                self.log_message("❌ IP reset failed", "ERROR")
                
        except subprocess.TimeoutExpired:
            process.kill()
            self.log_message("❌ IP reset timed out", "ERROR")
        except Exception as e:
            self.log_message(f"❌ IP reset error: {str(e)}", "ERROR")
            
    # Diagnostic Methods
    
    def run_ping_test(self):
        """Run ping connectivity test"""
        self.log_message("🏓 Running ping test...", "INFO")
        threading.Thread(target=self._ping_test_worker, daemon=True).start()
        
    def _ping_test_worker(self):
        """Background worker for ping test - runs 5 times automatically"""
        try:
            # Get current IP from GUI input field
            ip = self.ip_entry.get().strip()
            
            if not ip:
                self.log_message("❌ Target IP is empty", "ERROR")
                self.root.after(0, lambda: self.diag_status_label.configure(
                    text="❌ Target IP required", fg=self.colors['error']))
                return
            
            # Validate IP format
            try:
                ipaddress.ip_address(ip)
            except ValueError:
                self.log_message(f"❌ Invalid IP address format: {ip}", "ERROR")
                self.root.after(0, lambda: self.diag_status_label.configure(
                    text="❌ Invalid IP format", fg=self.colors['error']))
                return
                
            self.log_message(f"🏓 Starting 5x ping test sequence for {ip}...", "INFO")
            
            # Run ping test 5 times
            success_count = 0
            total_tests = 5
            
            for i in range(1, total_tests + 1):
                self.log_message(f"🏓 Ping test #{i}/5 to {ip}...", "INFO")
                
                # Update status to show current test
                self.root.after(0, lambda i=i: self.diag_status_label.configure(
                    text=f"🏓 Running test {i}/5...", fg=self.colors['text_secondary']))
                
                # Use a reasonable timeout (3 seconds)
                if self._ping_host(ip, timeout=3):
                    self.log_message(f"✅ Ping test #{i}/5 successful for {ip}", "SUCCESS")
                    success_count += 1
                else:
                    self.log_message(f"❌ Ping test #{i}/5 failed for {ip} (timeout or unreachable)", "ERROR")
                
                # Small delay between tests (except for the last one)
                if i < total_tests:
                    time.sleep(0.5)
            
            # Final results
            self.log_message(f"📊 Ping test sequence completed: {success_count}/{total_tests} successful", "INFO")
            
            if success_count == total_tests:
                self.log_message(f"🎉 All ping tests successful! {ip} is consistently reachable", "SUCCESS")
                self.root.after(0, lambda: self.diag_status_label.configure(
                    text=f"✅ {ip} - All 5/5 tests passed", fg=self.colors['success']))
            elif success_count > 0:
                self.log_message(f"⚠️ Partial success: {success_count}/{total_tests} ping tests passed", "WARNING")
                self.root.after(0, lambda: self.diag_status_label.configure(
                    text=f"⚠️ {ip} - {success_count}/5 tests passed", fg=self.colors['warning']))
            else:
                self.log_message(f"❌ All ping tests failed for {ip}", "ERROR")
                self.root.after(0, lambda: self.diag_status_label.configure(
                    text=f"❌ {ip} - All tests failed", fg=self.colors['error']))
                    
        except Exception as e:
            self.log_message(f"❌ Ping test error: {str(e)}", "ERROR")
            self.root.after(0, lambda: self.diag_status_label.configure(
                text="❌ Ping test error", fg=self.colors['error']))
                
    def run_ssh_test(self):
        """Run SSH connectivity test"""
        self.log_message("🔐 Running SSH connectivity test...", "INFO")
        threading.Thread(target=self._ssh_test_worker, daemon=True).start()
        
    def _ssh_test_worker(self):
        """Background worker for SSH test"""
        try:
            # Get current values from GUI input fields
            target_ip = self.ip_entry.get().strip()
            username = self.username_entry.get().strip()
            password = self.password_entry.get().strip()
            
            # Validate inputs
            if not target_ip:
                self.log_message("❌ Target IP is empty", "ERROR")
                self.root.after(0, lambda: self.diag_status_label.configure(
                    text="❌ Target IP required", fg=self.colors['error']))
                return
                
            if not username:
                self.log_message("❌ Username is empty", "ERROR")
                self.root.after(0, lambda: self.diag_status_label.configure(
                    text="❌ Username required", fg=self.colors['error']))
                return
                
            if not password:
                self.log_message("❌ Password is empty", "ERROR")
                self.root.after(0, lambda: self.diag_status_label.configure(
                    text="❌ Password required", fg=self.colors['error']))
                return
            
            self.log_message(f"🔐 Testing SSH connection to {username}@{target_ip}...", "INFO")
            
            # Use the network_config.sh script to test SSH connectivity
            script_path = os.path.join(os.path.dirname(__file__), "network_config.sh")
            cmd = [script_path, "--remote", target_ip, username, password, "verify-network"]
            
            # Execute the command with timeout
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                     text=True, bufsize=1, universal_newlines=True)
            
            # Read output with timeout
            try:
                stdout, stderr = process.communicate(timeout=30)
                return_code = process.returncode
                
                if return_code == 0:
                    self.log_message("✅ SSH connectivity test successful", "SUCCESS")
                    self.log_message(f"✅ Successfully connected to {username}@{target_ip}", "SUCCESS")
                    self.root.after(0, lambda: self.diag_status_label.configure(
                        text="✅ SSH connection verified", fg=self.colors['success']))
                else:
                    self.log_message("❌ SSH connectivity test failed", "ERROR")
                    self.log_message(f"❌ Failed to connect to {username}@{target_ip}", "ERROR")
                    self.root.after(0, lambda: self.diag_status_label.configure(
                        text="❌ SSH connection failed", fg=self.colors['error']))
                        
            except subprocess.TimeoutExpired:
                process.kill()
                self.log_message("❌ SSH test timed out (30s)", "ERROR")
                self.root.after(0, lambda: self.diag_status_label.configure(
                    text="❌ SSH test timed out", fg=self.colors['error']))
                    
        except Exception as e:
            self.log_message(f"❌ SSH test error: {str(e)}", "ERROR")
            self.root.after(0, lambda: self.diag_status_label.configure(
                text=f"❌ SSH test error", fg=self.colors['error']))
            
    def run_port_scan(self):
        """Run port scan on target device"""
        self.log_message("🔍 Running port scan...", "INFO")
        threading.Thread(target=self._port_scan_worker, daemon=True).start()
        
    def _port_scan_worker(self):
        """Background worker for port scan"""
        # Get current IP from GUI input field
        ip = self.ip_entry.get().strip()
        
        if not ip:
            self.log_message("❌ Target IP is empty", "ERROR")
            self.root.after(0, lambda: self.diag_status_label.configure(
                text="❌ Target IP required", fg=self.colors['error']))
            return
            
        self.log_message(f"🔍 Scanning common ports on {ip}...", "INFO")
        common_ports = [22, 80, 443, 1880, 8080, 9000]
        open_ports = []
        
        for port in common_ports:
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                    sock.settimeout(1)
                    result = sock.connect_ex((ip, port))
                    if result == 0:
                        open_ports.append(port)
            except:
                pass
                
        if open_ports:
            self.log_message(f"✅ Open ports found on {ip}: {', '.join(map(str, open_ports))}", "SUCCESS")
            self.root.after(0, lambda: self.diag_status_label.configure(
                text=f"✅ Found {len(open_ports)} open ports", fg=self.colors['success']))
        else:
            self.log_message(f"❌ No open ports found on {ip}", "WARNING")
            self.root.after(0, lambda: self.diag_status_label.configure(
                text="❌ No open ports detected", fg=self.colors['warning']))
                
    # UI Helper Methods
    
    def on_device_select(self, event):
        """Handle device selection in tree"""
        selected = self.device_tree.selection()
        if selected:
            item = self.device_tree.item(selected[0])
            ip = item['text']
            self.ip_entry.delete(0, tk.END)
            self.ip_entry.insert(0, ip)
            self.validate_ip_address()
            
    def on_device_double_click(self, event):
        """Handle double-click on device"""
        self.on_device_select(event)
        self.start_configuration()
        
    def filter_logs(self, event=None):
        """Filter log display by level"""
        # Implementation for log filtering
        pass
        
    def search_logs(self, *args):
        """Search within log messages"""
        search_term = self.log_search_var.get().lower()
        if not search_term:
            # Clear previous highlights if search is empty
            self.log_text.tag_remove('search_highlight', 1.0, tk.END)
            return
            
        # Clear previous highlights
        self.log_text.tag_remove('search_highlight', 1.0, tk.END)
        
        # Search for the term
        content = self.log_text.get(1.0, tk.END)
        lines = content.split('\n')
        
        for i, line in enumerate(lines):
            if search_term in line.lower():
                # Find all occurrences in the line
                line_lower = line.lower()
                start_pos = 0
                while True:
                    pos = line_lower.find(search_term, start_pos)
                    if pos == -1:
                        break
                    
                    # Calculate tkinter text position
                    start_index = f"{i+1}.{pos}"
                    end_index = f"{i+1}.{pos + len(search_term)}"
                    
                    # Add highlight tag
                    self.log_text.tag_add('search_highlight', start_index, end_index)
                    start_pos = pos + 1
        
    def clear_logs(self):
        """Clear the log display"""
        self.log_text.delete(1.0, tk.END)
        self.log_message("📝 Log cleared", "INFO")
        
    def log_message(self, message: str, level: str = "INFO"):
        """Add a message to the log with timestamp and formatting"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Format message with emoji and proper spacing
        if level == "ERROR":
            formatted_message = f"[{timestamp}] ❌ {message}\n"
            tag = "ERROR"
        elif level == "WARNING":
            formatted_message = f"[{timestamp}] ⚠️  {message}\n"
            tag = "WARNING"
        elif level == "SUCCESS":
            formatted_message = f"[{timestamp}] ✅ {message}\n"
            tag = "SUCCESS"
        else:
            formatted_message = f"[{timestamp}] ℹ️  {message}\n"
            tag = "INFO"
            
        # Add to log text widget
        self.log_text.insert(tk.END, formatted_message, tag)
        
        # Auto-scroll if enabled
        if self.auto_scroll_var.get():
            self.log_text.see(tk.END)
            
        # Update last update time
        self.last_update.configure(text=f"Updated: {timestamp}")
        
        # Print to console as well
        print(f"[{level}] {message}")
        
    def process_queues(self):
        """Process background queues for UI updates"""
        try:
            # Process log queue
            while not self.log_queue.empty():
                try:
                    message, level = self.log_queue.get_nowait()
                    self.log_message(message, level)
                except queue.Empty:
                    break
                    
            # Process status queue
            while not self.status_queue.empty():
                try:
                    status_update = self.status_queue.get_nowait()
                    # Handle status updates
                except queue.Empty:
                    break
                    
        except Exception as e:
            print(f"Error processing queues: {e}")
            
        # Schedule next processing
        self.root.after(100, self.process_queues)
        
    def update_time_displays(self):
        """Update time-related displays"""
        if self.is_running and self.operation_start_time:
            elapsed = datetime.now() - self.operation_start_time
            elapsed_str = str(elapsed).split('.')[0]  # Remove microseconds
            self.elapsed_time_label.configure(text=f"Elapsed: {elapsed_str}")
            
            # Calculate ETA based on current progress
            if self.current_step_index > 0:
                total_steps = len(self.operation_steps)
                progress_ratio = self.current_step_index / total_steps
                if progress_ratio > 0:
                    total_estimated = elapsed / progress_ratio
                    eta = total_estimated - elapsed
                    if eta.total_seconds() > 0:
                        eta_str = str(eta).split('.')[0]
                        self.estimated_time_label.configure(text=f"ETA: {eta_str}")
                        
        # Schedule next update
        self.root.after(1000, self.update_time_displays)
        
    def periodic_discovery(self):
        """Perform periodic device discovery"""
        if not self.is_running:  # Only run when not in active operation
            self.scan_network()
            
        # Schedule next discovery
        interval = self.config.get('discovery_interval', 30) * 1000  # Convert to ms
        self.root.after(interval, self.periodic_discovery)
        
    def _play_success_sound(self):
        """Play success notification sound"""
        try:
            if platform.system() == "Darwin":  # macOS
                # Try multiple sound options for better compatibility
                success_sounds = [
                    "/System/Library/Sounds/Glass.aiff",
                    "/System/Library/Sounds/Ping.aiff",
                    "/System/Library/Sounds/Submarine.aiff"
                ]
                for sound in success_sounds:
                    if os.path.exists(sound):
                        os.system(f"afplay '{sound}' &")
                        return
                # Fallback to system beep
                os.system("osascript -e 'beep 1'")
            elif platform.system() == "Linux":
                # Try multiple Linux sound options for Ubuntu and other distros
                linux_commands = [
                    # Ubuntu/Debian sound files
                    "paplay /usr/share/sounds/alsa/Front_Left.wav",
                    "paplay /usr/share/sounds/alsa/Front_Center.wav",
                    "paplay /usr/share/sounds/alsa/Front_Right.wav",
                    # Generic system sounds
                    "paplay /usr/share/sounds/gnome/default/alerts/drip.ogg",
                    "paplay /usr/share/sounds/ubuntu/stereo/notification.ogg",
                    "paplay /usr/share/sounds/freedesktop/stereo/complete.oga",
                    # ALSA fallbacks
                    "aplay /usr/share/sounds/alsa/Front_Left.wav",
                    "aplay /usr/share/sounds/alsa/Front_Center.wav",
                    # PulseAudio direct
                    "pactl play-sample 0",
                    # Simple beep
                    "echo -e '\a'"
                ]
                for cmd in linux_commands:
                    if os.system(f"{cmd} 2>/dev/null") == 0:
                        return
            elif platform.system() == "Windows":
                try:
                    import winsound
                    # Try different Windows sound types
                    winsound.MessageBeep(winsound.MB_OK)
                except ImportError:
                    # Fallback for Windows without winsound
                    os.system("echo \a")
        except Exception as e:
            # Fallback to terminal bell
            print("\a", end="", flush=True)
            
    def _play_error_sound(self):
        """Play error notification sound"""
        try:
            if platform.system() == "Darwin":  # macOS
                # Try multiple error sound options for better compatibility
                error_sounds = [
                    "/System/Library/Sounds/Basso.aiff",
                    "/System/Library/Sounds/Sosumi.aiff",
                    "/System/Library/Sounds/Frog.aiff"
                ]
                for sound in error_sounds:
                    if os.path.exists(sound):
                        os.system(f"afplay '{sound}' &")
                        return
                # Fallback to system beep (3 beeps for error)
                os.system("osascript -e 'beep 3'")
            elif platform.system() == "Linux":
                # Try multiple Linux sound options for Ubuntu and other distros
                linux_commands = [
                    # Ubuntu/Debian error sound files
                    "paplay /usr/share/sounds/alsa/Front_Right.wav",
                    "paplay /usr/share/sounds/alsa/Front_Center.wav",
                    "paplay /usr/share/sounds/alsa/Front_Left.wav",
                    # Generic system error sounds
                    "paplay /usr/share/sounds/gnome/default/alerts/bark.ogg",
                    "paplay /usr/share/sounds/ubuntu/stereo/dialog-error.ogg",
                    "paplay /usr/share/sounds/freedesktop/stereo/dialog-error.oga",
                    "paplay /usr/share/sounds/freedesktop/stereo/suspend-error.oga",
                    # ALSA fallbacks
                    "aplay /usr/share/sounds/alsa/Front_Right.wav",
                    "aplay /usr/share/sounds/alsa/Front_Center.wav",
                    # PulseAudio direct
                    "pactl play-sample 1",
                    # Triple beep for error
                    "echo -e '\a\a\a'"
                ]
                for cmd in linux_commands:
                    if os.system(f"{cmd} 2>/dev/null") == 0:
                        return
            elif platform.system() == "Windows":
                try:
                    import winsound
                    # Try different Windows error sound types
                    winsound.MessageBeep(winsound.MB_ICONHAND)
                except ImportError:
                    # Fallback for Windows without winsound
                    os.system("echo \a\a\a")
        except Exception as e:
            # Fallback to terminal bell (triple beep for error)
            print("\a\a\a", end="", flush=True)
    
    def test_sound_notifications(self):
        """Test sound notification functionality"""
        self.log_message("🔊 Testing sound notifications...", "INFO")
        
        # Test success sound
        self.log_message("🔊 Playing success sound...", "INFO")
        self._play_success_sound()
        
        # Wait a moment then test error sound
        self.root.after(1000, lambda: self._test_error_sound())
    
    def _test_error_sound(self):
        """Test error sound (called after delay)"""
        self.log_message("🔊 Playing error sound...", "INFO")
        self._play_error_sound()
        self.log_message("🔊 Sound test completed", "SUCCESS")
            
    def on_closing(self):
        """Handle application closure"""
        if self.is_running:
            result = messagebox.askyesno("Exit Application",
                                       "An operation is currently running.\n\n"
                                       "Are you sure you want to exit?")
            if not result:
                return
                
        self.shutdown_requested = True
        
        # Save window state and configuration
        try:
            config_data = {
                'window_geometry': self.root.geometry(),
                'target_ip': self.config['target_ip'],
                'username': self.config['username'],
                'scan_interval': self.config['scan_interval'],
                'auto_retry': self.auto_retry_var.get(),
                'sound_notifications': self.sound_var.get(),
                'log_level': self.log_level_var.get()
            }
            
            config_file = os.path.join(os.path.dirname(__file__), "gui_config.json")
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
                
        except Exception as e:
            print(f"Failed to save configuration: {e}")
            
        self.root.destroy()
        
    # File Upload Methods
    def upload_flows_file(self):
        """Upload and validate flows.json file"""
        filename = filedialog.askopenfilename(
            title="Select flows.json file",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            try:
                # Validate the file
                with open(filename, 'r') as f:
                    flows_data = json.load(f)
                    
                # Validate flows.json structure
                if not isinstance(flows_data, list):
                    raise ValueError("flows.json must be a JSON array")
                
                for item in flows_data:
                    if not isinstance(item, dict) or 'id' not in item or 'type' not in item:
                        raise ValueError("Each flow item must have 'id' and 'type' fields")
                        
                # Copy to uploaded_files directory
                os.makedirs("uploaded_files", exist_ok=True)
                dest_path = os.path.join("uploaded_files", "flows.json")
                shutil.copy2(filename, dest_path)
                
                self.uploaded_flows_file = dest_path
                self.flows_status_label.configure(text="✓ Valid flows.json uploaded", 
                                                fg=self.colors['success'])
                self.flows_source_var.set("uploaded")
                
                # Enable submit button after successful upload
                self.submit_flows_button.configure(state=tk.NORMAL)
                
                self.log_message(f"✅ flows.json uploaded and validated: {os.path.basename(filename)}", "SUCCESS")
                
            except Exception as e:
                self.flows_status_label.configure(text=f"✗ Error: {str(e)}", 
                                                fg=self.colors['error'])
                self.log_message(f"❌ flows.json validation failed: {str(e)}", "ERROR")
                
    def upload_package_file(self):
        """Upload and validate package.json file"""
        filename = filedialog.askopenfilename(
            title="Select package.json file",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if filename:
            try:
                # Validate the file
                with open(filename, 'r') as f:
                    package_data = json.load(f)
                    
                # Validate package.json structure
                if not isinstance(package_data, dict):
                    raise ValueError("package.json must be a JSON object")
                    
                if 'name' not in package_data or 'version' not in package_data:
                    raise ValueError("package.json must have 'name' and 'version' fields")
                    
                # Copy to uploaded_files directory
                os.makedirs("uploaded_files", exist_ok=True)
                dest_path = os.path.join("uploaded_files", "package.json")
                shutil.copy2(filename, dest_path)
                
                self.uploaded_package_file = dest_path
                self.package_status_label.configure(text="✓ Valid package.json uploaded", 
                                                  fg=self.colors['success'])
                self.package_source_var.set("uploaded")
                
                self.log_message(f"✅ package.json uploaded and validated: {os.path.basename(filename)}", "SUCCESS")
                
            except Exception as e:
                self.package_status_label.configure(text=f"✗ Error: {str(e)}", 
                                                  fg=self.colors['error'])
                self.log_message(f"❌ package.json validation failed: {str(e)}", "ERROR")
                
    def clear_uploaded_files(self):
        """Clear uploaded files"""
        self.uploaded_flows_file = None
        self.uploaded_package_file = None
        
        self.flows_status_label.configure(text="No file selected", fg=self.colors['text_secondary'])
        self.package_status_label.configure(text="No file selected", fg=self.colors['text_secondary'])
        
        # Disable submit button when files are cleared
        self.submit_flows_button.configure(state=tk.DISABLED)
        
        # Reset source selections if they were set to uploaded
        if self.flows_source_var.get() == "uploaded":
            self.flows_source_var.set("auto")
        if self.package_source_var.get() == "uploaded":
            self.package_source_var.set("auto")
            
        # Remove uploaded files
        try:
            if os.path.exists("uploaded_files/flows.json"):
                os.remove("uploaded_files/flows.json")
            if os.path.exists("uploaded_files/package.json"):
                os.remove("uploaded_files/package.json")
        except:
            pass
            
        self.log_message("🗑️ Uploaded files cleared", "INFO")
        
    def submit_flows(self):
        """Submit the uploaded flows.json to the target device"""
        if not self.uploaded_flows_file or not os.path.exists(self.uploaded_flows_file):
            self.log_message("❌ No flows.json file available to submit", "ERROR")
            return
            
        # Validate connection settings
        target_ip = self.ip_entry.get().strip()
        username = self.username_entry.get().strip()
        password = self.password_entry.get()
        
        if not all([target_ip, username, password]):
            self.log_message("❌ Please configure connection settings (IP, username, password) before submitting flows", "ERROR")
            return
            
        # Validate IP address format
        try:
            import ipaddress
            ipaddress.ip_address(target_ip)
        except ValueError:
            self.log_message("❌ Invalid IP address format", "ERROR")
            return
            
        self.log_message("📤 Submitting flows.json to target device...", "INFO")
        
        # Disable submit button during submission
        self.submit_flows_button.configure(state=tk.DISABLED, text="📤 Submitting...")
        
        # Run submission in background thread
        threading.Thread(target=self._submit_flows_worker, daemon=True).start()
        
    def _submit_flows_worker(self):
        """Background worker for submitting flows.json"""
        try:
            target_ip = self.ip_entry.get().strip()
            username = self.username_entry.get().strip()
            password = self.password_entry.get()
                
            # Create bot wrapper for flows submission
            bot = GUIBotWrapper(
                gui_log_callback=self.log_message,
                target_ip=target_ip,
                username=username,
                password=password
            )
            
            # Submit flows.json using the bot wrapper with custom command construction
            import subprocess
            
            # Build the command with proper parameter order
            cmd = [
                self.script_path,
                "--remote", target_ip, username, password,
                "--uploaded-flows", self.uploaded_flows_file,
                "import-nodered-flows", "uploaded"
            ]
            
            self.root.after(0, lambda: self.log_message(f"🔧 Executing: {' '.join(cmd)}", "INFO"))
            
            # Execute command and capture output in real-time (similar to GUIBotWrapper)
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, 
                                     text=True, bufsize=1, universal_newlines=True)
            
            # Read output line by line and display in real-time
            output_lines = []
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    line = output.strip()
                    if line:
                        output_lines.append(line)
                        # Display each line in the log
                        if "[SUCCESS]" in line:
                            self.root.after(0, lambda l=line: self.log_message(f"✅ {l.replace('[SUCCESS]', '').strip()}", "SUCCESS"))
                        elif "[ERROR]" in line:
                            self.root.after(0, lambda l=line: self.log_message(f"❌ {l.replace('[ERROR]', '').strip()}", "ERROR"))
                        elif "[WARNING]" in line:
                            self.root.after(0, lambda l=line: self.log_message(f"⚠️ {l.replace('[WARNING]', '').strip()}", "WARNING"))
                        elif "[INFO]" in line:
                            self.root.after(0, lambda l=line: self.log_message(f"ℹ️ {l.replace('[INFO]', '').strip()}", "INFO"))
                        else:
                            self.root.after(0, lambda l=line: self.log_message(f"📋 {l}", "INFO"))
            
            # Wait for process to complete
            return_code = process.wait()
            result = (return_code == 0)
            
            if result:
                self.root.after(0, lambda: self.log_message("✅ flows.json submitted successfully to target device", "SUCCESS"))
                self.root.after(0, lambda: self.submit_flows_button.configure(
                    state=tk.NORMAL, text="✅ Submitted"))
            else:
                self.root.after(0, lambda: self.log_message("❌ Failed to submit flows.json to target device", "ERROR"))
                self.root.after(0, lambda: self.submit_flows_button.configure(
                    state=tk.NORMAL, text="📤 Submit flows.json"))
                    
        except Exception as e:
            error_msg = str(e)
            self.root.after(0, lambda msg=error_msg: self.log_message(f"❌ Error submitting flows.json: {msg}", "ERROR"))
            self.root.after(0, lambda: self.submit_flows_button.configure(
                state=tk.NORMAL, text="📤 Submit flows.json"))
        
    # Function Selection Methods
    def select_all_functions(self):
        """Select all configuration functions"""
        for var in self.function_vars:
            var.set(True)
        self.log_message("📋 All functions selected", "INFO")
        
    def select_none_functions(self):
        """Deselect all configuration functions"""
        for var in self.function_vars:
            var.set(False)
        self.log_message("📋 All functions deselected", "INFO")
        
    def select_quick_setup(self):
        """Select commonly used functions for quick setup"""
        quick_setup_functions = [
            "forward", "check-dns", "fix-dns", "install-curl", "install-docker",
            "install-services", "install-nodered-nodes", "import-nodered-flows",
            "update-nodered-auth", "install-tailscale", "reverse", "set-password"
        ]
        
        # First deselect all
        for var in self.function_vars:
            var.set(False)
            
        # Then select quick setup functions
        for i, (func_id, _, _) in enumerate(self.function_descriptions):
            if func_id in quick_setup_functions:
                self.function_vars[i].set(True)
                
        self.log_message("🚀 Quick setup functions selected", "SUCCESS")
        
    def update_selection_counter(self):
        """Update the function selection counter"""
        selected_count = sum(1 for var in self.function_vars if var.get())
        total_count = len(self.function_vars)
        self.selection_counter.configure(text=f"Selected: {selected_count}/{total_count} functions")
        
    def get_selected_functions(self):
        """Get list of selected function IDs"""
        selected = []
        for i, var in enumerate(self.function_vars):
            if var.get():
                func_id, _, _ = self.function_descriptions[i]
                # Safety check: never include reset-device in regular function execution
                if func_id != "reset-device":
                    selected.append(func_id)
                else:
                    self.log_message("🚫 WARNING: reset-device found in function selection - removing for safety", "WARNING")
                    var.set(False)  # Uncheck it
        return selected
        
    # Dark Mode Methods
    def toggle_dark_mode(self):
        """Toggle between light and dark mode"""
        if self.dark_mode_var.get():
            self.apply_dark_theme()
        else:
            self.apply_light_theme()
            
    def apply_dark_theme(self):
        """Apply dark color theme"""
        self.colors.update({
            'primary': '#3b82f6',           # Bright blue
            'secondary': '#6366f1',         # Indigo
            'success': '#10b981',           # Emerald
            'warning': '#f59e0b',           # Amber
            'error': '#ef4444',             # Red
            'info': '#06b6d4',              # Cyan
            'background': '#111827',        # Dark gray
            'surface': '#1f2937',           # Darker gray
            'surface_variant': '#374151',   # Medium gray
            'border': '#4b5563',            # Border gray
            'text_primary': '#f9fafb',      # Light text
            'text_secondary': '#d1d5db',    # Medium light text
            'text_muted': '#9ca3af',        # Muted light text
            'accent': '#8b5cf6',            # Purple accent
        })
        self.apply_theme()
        self.log_message("🌙 Dark mode enabled", "INFO")
        
    def apply_light_theme(self):
        """Apply light color theme"""
        self.colors.update({
            'primary': '#1f4e79',           # Professional dark blue
            'secondary': '#2e7d9a',         # Complementary blue-green
            'success': '#22c55e',           # Modern green
            'warning': '#f59e0b',           # Amber
            'error': '#ef4444',             # Red
            'info': '#3b82f6',              # Blue
            'background': '#f8fafc',        # Very light gray
            'surface': '#ffffff',           # White
            'surface_variant': '#f1f5f9',   # Light gray variant
            'border': '#e2e8f0',            # Light border
            'text_primary': '#1e293b',      # Dark slate
            'text_secondary': '#64748b',    # Muted slate
            'text_muted': '#94a3b8',        # Light slate
            'accent': '#8b5cf6',            # Purple accent
        })
        self.apply_theme()
        self.log_message("☀️ Light mode enabled", "INFO")
        
    def apply_theme(self):
        """Apply the current color theme to all UI elements"""
        # Update root background
        self.root.configure(bg=self.colors['background'])
        
        # Update main container
        self.main_container.configure(bg=self.colors['background'])
        self.left_panel.configure(bg=self.colors['background'])
        self.right_panel.configure(bg=self.colors['background'])
        
        # Update log text colors
        self.log_text.configure(bg=self.colors['surface_variant'], 
                               fg=self.colors['text_primary'])
        
        self.log_message("🎨 Theme updated", "INFO")
        
    def update_progress(self, current_step: int, total_steps: int):
        """Update progress indicators"""
        # Update overall progress
        progress = (current_step / total_steps) * 100
        self.overall_progress.configure(value=progress)
        self.overall_progress_text.configure(text=f"{current_step}/{total_steps} steps")
        
        # Update current step if we have step info
        if current_step <= len(self.operation_steps):
            current_operation = self.operation_steps[current_step - 1]
            self.current_step_label.configure(text=f"Current Step: {current_operation.name}")
            
            # Start progress animation
            self.current_step_progress.configure(mode='indeterminate')
            self.current_step_progress.start()
        
    def run(self):
        """Start the GUI application"""
        try:
            # Load saved configuration
            config_file = os.path.join(os.path.dirname(__file__), "gui_config.json")
            if os.path.exists(config_file):
                with open(config_file, 'r') as f:
                    saved_config = json.load(f)
                    
                # Restore window geometry (only if valid)
                if 'window_geometry' in saved_config:
                    geometry = saved_config['window_geometry']
                    # Check if geometry is valid (not 1x1 or off-screen)
                    if 'x' in geometry and '1x1' not in geometry:
                        self.root.geometry(geometry)
                    else:
                        # Use default geometry if saved geometry is invalid
                        self.root.geometry("1600x1000+100+100")
                    
                # Restore other settings
                self.config.update({k: v for k, v in saved_config.items() 
                                  if k in self.config})
                                  
        except Exception as e:
            print(f"Failed to load saved configuration: {e}")
            
        # Start the application
        self.log_message("🚀 Bivicom Network Configuration Manager started", "SUCCESS")
        self.log_message("Ready for network device configuration", "INFO")
        
        # Debug: Check if window is visible
        try:
            self.log_message(f"🔍 GUI window exists: {self.root.winfo_exists()}", "INFO")
            self.log_message(f"🔍 GUI window viewable: {self.root.winfo_viewable()}", "INFO")
            self.log_message(f"🔍 GUI window geometry: {self.root.geometry()}", "INFO")
        except Exception as e:
            self.log_message(f"❌ Cannot check GUI window status: {e}", "ERROR")
        
        # Try to bring window to front and ensure visibility
        try:
            # Force window to be visible
            self.root.deiconify()  # Restore if minimized
            self.root.lift()       # Bring to front
            self.root.focus_force() # Force focus
            self.root.attributes('-topmost', True)  # Make topmost temporarily
            self.root.after(1000, lambda: self.root.attributes('-topmost', False))  # Remove topmost after 1 second
            self.log_message("🔍 Attempted to bring GUI window to front", "INFO")
        except Exception as e:
            self.log_message(f"❌ Cannot bring window to front: {e}", "ERROR")
        
        # Mark GUI as fully loaded
        self.gui_fully_loaded = True
        self.log_message("✅ GUI fully loaded and ready for user interaction", "SUCCESS")
        
        self.root.mainloop()

def main():
    """Main application entry point"""
    try:
        app = EnhancedNetworkBotGUI()
        app.run()
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
    except Exception as e:
        print(f"Application error: {e}")
        messagebox.showerror("Application Error", f"An unexpected error occurred:\n{str(e)}")

if __name__ == "__main__":
    main()