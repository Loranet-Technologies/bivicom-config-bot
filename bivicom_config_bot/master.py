#!/usr/bin/env python3
"""
Unified Bivicom Configuration Bot with Reverse Functionality
==========================================================

This script includes both forward and reverse UCI network configuration:
- Forward: WAN=eth1 (DHCP), LAN=eth0 (Static)
- Reverse: WAN=enx0250f4000000 (LTE), LAN=eth0 (Static)

Author: Aqmar
Date: 2025-01-09
"""

import subprocess
import time
import socket
import signal
import sys
import os
import argparse
import logging
import shutil
import platform
from datetime import datetime


def check_requirements():
    """Check if all required dependencies are installed"""
    print("🔍 Checking system requirements...")

    missing_requirements = []
    warnings = []

    # Detect operating system
    system = platform.system().lower()
    if system == "darwin":
        os_name = "macOS"
        os_type = "macos"
    elif system == "windows":
        os_name = "Windows"
        os_type = "windows"
    elif system == "linux":
        # Try to detect specific Linux distribution
        try:
            with open("/etc/os-release", "r") as f:
                os_release = f.read().lower()
                if "ubuntu" in os_release or "debian" in os_release:
                    os_name = "Ubuntu/Debian Linux"
                    os_type = "ubuntu"
                elif "centos" in os_release or "rhel" in os_release or "fedora" in os_release:
                    os_name = "CentOS/RHEL/Fedora Linux"
                    os_type = "centos"
                else:
                    os_name = "Linux"
                    os_type = "linux"
        except:
            os_name = "Linux"
            os_type = "linux"
    else:
        os_name = system.title()
        os_type = "unknown"

    print(f"📍 Detected OS: {os_name}")

    # Check Python packages
    try:
        import paramiko
        print("✅ paramiko is installed")
    except ImportError:
        missing_requirements.append(("paramiko", "python"))

    # Check system utilities
    if shutil.which("sshpass"):
        print("✅ sshpass is installed")
    else:
        missing_requirements.append(("sshpass", "system"))

    # Check if network_config.sh script exists
    script_path = os.path.join(os.path.dirname(__file__), "network_config.sh")
    if os.path.exists(script_path) and os.access(script_path, os.X_OK):
        print("✅ network_config.sh script exists and is executable")
    else:
        missing_requirements.append((f"network_config.sh script (expected at {script_path})", "file"))

    # Check Python version
    if sys.version_info >= (3, 7):
        print(f"✅ Python {sys.version.split()[0]} is compatible")
    else:
        missing_requirements.append(("Python 3.7+ (current version is too old)", "python"))

    # Show results
    if missing_requirements:
        print("\n❌ Missing requirements:")
        for req, req_type in missing_requirements:
            print(f"   - {req}")

        print(f"\n💡 Installation instructions for {os_name}:")

        # Python packages installation
        python_reqs = [req for req, req_type in missing_requirements if req_type == "python"]
        if python_reqs:
            print("\n📦 Python packages:")
            if os_type == "windows":
                print("   pip install -r requirements.txt")
            else:
                print("   pip3 install -r requirements.txt")
                print("   # Or with pip:")
                print("   pip install -r requirements.txt")

        # System utilities installation
        system_reqs = [req for req, req_type in missing_requirements if req_type == "system"]
        if system_reqs:
            print(f"\n🔧 System utilities for {os_name}:")
            if os_type == "macos":
                print("   # Install sshpass:")
                print("   brew install hudochenkov/sshpass/sshpass")
            elif os_type == "ubuntu":
                print("   # Install sshpass:")
                print("   sudo apt-get update")
                print("   sudo apt-get install sshpass")
            elif os_type == "centos":
                print("   # Install sshpass:")
                print("   sudo yum install sshpass")
                print("   # Or on newer versions:")
                print("   sudo dnf install sshpass")
            elif os_type == "windows":
                print("   # Install sshpass:")
                print("   # Option 1: Using Chocolatey (recommended)")
                print("   choco install sshpass")
                print("   # Option 2: Using WSL")
                print("   # Install Windows Subsystem for Linux, then:")
                print("   wsl sudo apt-get install sshpass")
            else:
                print("   # Install sshpass:")
                print("   # Please check your package manager or visit:")
                print("   # https://sourceforge.net/projects/sshpass/")

        # File requirements
        file_reqs = [req for req, req_type in missing_requirements if req_type == "file"]
        if file_reqs:
            print("\n📁 Missing files:")
            print("   Please ensure all project files are properly extracted.")

        print("\n🔄 After installing requirements, run this command again.")
        return False

    if warnings:
        print("\n⚠️  Warnings:")
        for warning in warnings:
            print(f"   - {warning}")

    print("\n✅ All requirements met! Starting Bivicom Network Bot...\n")
    return True


class NetworkBot:
    def __init__(self, target_ip="192.168.1.1", scan_interval=10, verbose=False):
        self.target_ip = target_ip
        self.scan_interval = scan_interval
        self.running = True
        self.verbose = verbose
        self.script_path = os.path.join(os.path.dirname(__file__), "network_config.sh")
        self.username = "admin"
        self.password = "admin"
        
        # Set up logging
        self.setup_logging()
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def setup_logging(self):
        """Set up logging to file and console"""
        # Only set up logging if not already configured
        if hasattr(self, 'logger') and self.logger:
            return
            
        # Create logs directory if it doesn't exist
        log_dir = os.path.join(os.path.dirname(__file__), "logs")
        os.makedirs(log_dir, exist_ok=True)
        
        # Create log filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"bivicom_bot_{timestamp}.log")
        
        # Get or create logger
        self.logger = logging.getLogger(f"{__name__}_{id(self)}")
        
        # Only add handlers if they don't exist
        if not self.logger.handlers:
            # Configure logging
            self.logger.setLevel(logging.INFO)
            
            # Create formatter
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            
            # Add file handler
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            
            # Add console handler if verbose
            if self.verbose:
                console_handler = logging.StreamHandler(sys.stdout)
                console_handler.setFormatter(formatter)
                self.logger.addHandler(console_handler)
        
        self.logger.info(f"Logging initialized. Log file: {log_file}")
        print(f"[{self._get_timestamp()}] 📝 Logging to: {log_file}")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        signal_name = signal.Signals(signum).name
        print(f"\n[{self._get_timestamp()}] Received {signal_name} signal. Stopping bot...")
        self.logger.info(f"Received {signal_name} signal. Stopping bot...")
        self.running = False
    
    def _get_timestamp(self):
        """Get current timestamp"""
        return time.strftime("%Y-%m-%d %H:%M:%S")
    
    def ping_host(self, ip):
        """Ping a host to check if it's reachable"""
        try:
            # Use socket to check if port 22 (SSH) is open
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex((ip, 22))
            sock.close()
            return result == 0
        except Exception:
            return False

    def run_network_config(self):
        """Run the complete network configuration sequence"""
        try:
            print(f"[{self._get_timestamp()}] 🚀 Starting complete network configuration sequence...")
            
            # Define the sequence of commands to run
            commands = [
                {
                    "name": "1. Configure Network FORWARD",
                    "cmd": [self.script_path, "--remote", self.target_ip, "admin", "admin", "forward"],
                    "timeout": 60
                },
                {
                    "name": "2. Check DNS Connectivity", 
                    "cmd": [self.script_path, "check-dns"],
                    "timeout": 30
                },
                {
                    "name": "3. Fix DNS Configuration",
                    "cmd": [self.script_path, "--remote", self.target_ip, self.username, self.password, "fix-dns"],
                    "timeout": 60
                },
                {
                    "name": "4. Install curl",
                    "cmd": [self.script_path, "--remote", self.target_ip, self.username, self.password, "install-curl"],
                    "timeout": 60
                },
                {
                    "name": "5. Install Docker (after network config)",
                    "cmd": [self.script_path, "--remote", self.target_ip, self.username, self.password, "install-docker"],
                    "timeout": 300
                },
                {
                    "name": "6. Install All Docker Services",
                    "cmd": [self.script_path, "--remote", self.target_ip, self.username, self.password, "install-services"],
                    "timeout": 300
                },
                {
                    "name": "7. Install Node-RED Nodes",
                    "cmd": [self.script_path, "--remote", self.target_ip, self.username, self.password, "install-nodered-nodes"],
                    "timeout": 180
                },
                {
                    "name": "8. Import Node-RED Flows",
                    "cmd": [self.script_path, "--remote", self.target_ip, self.username, self.password, "import-nodered-flows"],
                    "timeout": 120
                },
                {
                    "name": "9. Update Node-RED Authentication",
                    "cmd": [self.script_path, "--remote", self.target_ip, self.username, self.password, "update-nodered-auth", self.password],
                    "timeout": 60
                },
                {
                    "name": "10. Install Tailscale VPN Router",
                    "cmd": [self.script_path, "--remote", self.target_ip, self.username, self.password, "install-tailscale"],
                    "timeout": 180
                },
                {
                    "name": "11. Configure Network REVERSE",
                    "cmd": [self.script_path, "--remote", self.target_ip, self.username, self.password, "reverse"],
                    "timeout": 60
                },
                {
                    "name": "12. Change Device Password",
                    "cmd": [self.script_path, "--remote", self.target_ip, self.username, self.password, "set-password", self.password],
                    "timeout": 60
                }
            ]
            
            # Execute each command in sequence
            for i, command in enumerate(commands, 1):
                print(f"[{self._get_timestamp()}] 📋 Step {i}/{len(commands)}: {command['name']}")
                print(f"[{self._get_timestamp()}] 🔧 Running: {' '.join(command['cmd'])}")
                
                try:
                    # Log the command being executed
                    self.logger.info(f"Executing command: {' '.join(command['cmd'])}")
                    
                    result = subprocess.run(
                        command['cmd'], 
                        capture_output=True, 
                        text=True, 
                        timeout=command['timeout']
                    )
                    
                    # Log full output to file
                    if result.stdout.strip():
                        self.logger.info(f"STDOUT:\n{result.stdout.strip()}")
                    
                    if result.stderr.strip():
                        self.logger.warning(f"STDERR:\n{result.stderr.strip()}")
                    
                    if result.returncode == 0:
                        print(f"[{self._get_timestamp()}] ✅ Step {i} completed successfully!")
                        self.logger.info(f"Step {i} completed successfully")
                        
                        # Show output based on verbose mode
                        if result.stdout.strip():
                            if self.verbose:
                                print(f"[{self._get_timestamp()}] 📄 Full Output:")
                                print(result.stdout.strip())
                            else:
                                print(f"[{self._get_timestamp()}] 📄 Output: {result.stdout.strip()[:200]}...")
                    else:
                        print(f"[{self._get_timestamp()}] ❌ Step {i} failed!")
                        self.logger.error(f"Step {i} failed with return code {result.returncode}")
                        
                        # Always show error output
                        if result.stderr.strip():
                            print(f"[{self._get_timestamp()}] 📄 Error: {result.stderr.strip()}")
                        if result.stdout.strip():
                            print(f"[{self._get_timestamp()}] 📄 Output: {result.stdout.strip()}")
                        
                        return False
                
                except subprocess.TimeoutExpired:
                    print(f"[{self._get_timestamp()}] ⏰ Step {i} timed out after {command['timeout']} seconds")
                    return False
                except Exception as e:
                    print(f"[{self._get_timestamp()}] ❌ Step {i} error: {e}")
                    return False
                
                # Small delay between commands
                if i < len(commands):
                    print(f"[{self._get_timestamp()}] ⏳ Waiting 5 seconds before next step...")
                    time.sleep(5)
            
            print(f"[{self._get_timestamp()}] 🎉 Complete network configuration sequence finished successfully!")
            return True
            
        except Exception as e:
            print(f"[{self._get_timestamp()}] ❌ Error in network configuration sequence: {e}")
            return False

    def scan_and_configure(self):
        """Main bot loop - scan for target IP and configure when found"""
        print(f"[{self._get_timestamp()}] 🤖 Bivicom Network Bot Started")
        print(f"[{self._get_timestamp()}] 🎯 Looking for device at {self.target_ip}")
        print(f"[{self._get_timestamp()}] ⏱️  Scan interval: {self.scan_interval} seconds")
        print(f"[{self._get_timestamp()}] 📜 Script path: {self.script_path}")
        print(f"[{self._get_timestamp()}] 📝 Verbose mode: {'ON' if self.verbose else 'OFF'}")
        print(f"[{self._get_timestamp()}] Press Ctrl+C to stop")
        print()
        
        self.logger.info(f"Bot started - Target IP: {self.target_ip}, Scan interval: {self.scan_interval}s, Verbose: {self.verbose}")
        
        while self.running:
            try:
                print(f"[{self._get_timestamp()}] 🔍 Scanning for {self.target_ip}...", end=" ")
                
                if self.ping_host(self.target_ip):
                    print("✅ FOUND!")
                    print(f"[{self._get_timestamp()}] 🚀 Device detected! Starting network configuration...")
                    
                    # Run network configuration
                    success = self.run_network_config()
                    
                    if success:
                        print(f"[{self._get_timestamp()}] 🎉 Configuration completed! Bot will continue monitoring...")
                    else:
                        print(f"[{self._get_timestamp()}] ⚠️  Configuration failed, will retry on next scan...")
                    
                    print()
                else:
                    print("❌ Not found")
                
                # Wait before next scan
                if self.running:
                    time.sleep(self.scan_interval)
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"[{self._get_timestamp()}] ❌ Error during scan: {e}")
                time.sleep(self.scan_interval)
        
        print(f"[{self._get_timestamp()}] 🛑 Bot stopped")


def main():
    """Main function"""
    # Check requirements before proceeding
    if not check_requirements():
        sys.exit(1)

    parser = argparse.ArgumentParser(description="Bivicom Network Bot - Scans for devices and runs complete network configuration sequence")
    parser.add_argument("--ip", default="192.168.1.1", help="Target IP address to scan for (default: 192.168.1.1)")
    parser.add_argument("--interval", type=int, default=10, help="Scan interval in seconds (default: 10)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show full output from all commands (default: show only summary)")

    args = parser.parse_args()
    
    print("Bivicom Network Bot")
    print("==================")
    print(f"This bot continuously scans for {args.ip} and runs a complete")
    print("12-step network configuration sequence when the device is found:")
    print()
    print("Sequence:")
    print("1. Configure Network FORWARD")
    print("2. Check DNS Connectivity")
    print("3. Fix DNS Configuration")
    print("4. Install curl")
    print("5. Install Docker")
    print("6. Install All Docker Services (Node-RED, Portainer, Restreamer)")
    print("7. Install Node-RED Nodes")
    print("8. Import Node-RED Flows")
    print("9. Update Node-RED Authentication (uses configured password)")
    print("10. Install Tailscale VPN Router")
    print("11. Configure Network REVERSE")
    print("12. Change Device Password (uses configured password)")
    print()
    
    # Create and run the bot
    bot = NetworkBot(target_ip=args.ip, scan_interval=args.interval, verbose=args.verbose)
    bot.scan_and_configure()
    

if __name__ == "__main__":
    main()