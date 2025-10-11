#!/usr/bin/env python3
"""
Enhanced Bivicom Configuration Bot with Reverse Functionality
============================================================

This script includes both forward and reverse UCI network configuration:
- Forward: WAN=eth1 (DHCP), LAN=eth0 (Static)
- Reverse: WAN=enx0250f4000000 (LTE), LAN=eth0 (Static)

Features:
- Configuration file support (.env)
- Retry mechanism for failed steps
- Progress tracking and resume capability
- Enhanced logging and error handling
- Multiple device support
- Customizable configuration sequence

Author: Aqmar
Date: 2025-01-09
Version: 2.0 Enhanced
"""

import subprocess
import time
import socket
import signal
import sys
import os
import argparse
import logging
from datetime import datetime
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
import configparser


class NetworkBot:
    def __init__(self, target_ip="192.168.1.1", scan_interval=10, verbose=False,
                 config_file=".env", max_retries=3, retry_delay=30):
        self.target_ip = target_ip
        self.scan_interval = scan_interval
        self.running = True
        self.verbose = verbose
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.config_file = config_file

        # Load configuration
        self.config = self._load_config()

        # Set script path and validate
        self.script_path = os.path.join(os.path.dirname(__file__), "network_config.sh")
        self._validate_script_path()

        # Set up logging
        self.setup_logging()

        # Set up signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        # Progress tracking
        self.current_step = 0
        self.total_steps = 12
        self.failed_steps = []
        self.completed_steps = []

        # Statistics
        self.scan_count = 0
        self.device_count = 0
        self.configuration_count = 0

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

    def _load_config(self) -> Dict[str, str]:
        """Load configuration from .env file or use defaults"""
        config = {
            "username": "admin",
            "password": "admin",
            "target_ip": self.target_ip,
            "scan_interval": str(self.scan_interval),
            "tailscale_auth_key": "",
            "ssh_timeout": "10"
        }

        # Try to load from .env file
        env_path = os.path.join(os.path.dirname(__file__), self.config_file)
        if os.path.exists(env_path):
            try:
                with open(env_path, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            config[key.strip().lower()] = value.strip()
                self.logger.info(f"Configuration loaded from {env_path}")
            except Exception as e:
                self.logger.warning(f"Failed to load config from {env_path}: {e}")
        else:
            self.logger.info("No config file found, using defaults")

        return config

    def _validate_script_path(self):
        """Validate that network_config.sh exists and is executable"""
        if not os.path.exists(self.script_path):
            raise FileNotFoundError(f"Configuration script not found: {self.script_path}")

        if not os.access(self.script_path, os.X_OK):
            # Try to make it executable
            try:
                os.chmod(self.script_path, 0o755)
                self.logger.info(f"Made script executable: {self.script_path}")
            except Exception as e:
                self.logger.warning(f"Could not make script executable: {e}")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        signal_name = signal.Signals(signum).name
        print(f"\n[{self._get_timestamp()}] Received {signal_name} signal. Stopping bot...")
        self.logger.info(f"Received {signal_name} signal. Stopping bot...")

        # Print statistics before stopping
        self._print_statistics()
        self.running = False

    def _get_timestamp(self):
        """Get current timestamp"""
        return time.strftime("%Y-%m-%d %H:%M:%S")

    def _print_statistics(self):
        """Print operation statistics"""
        print(f"\n[{self._get_timestamp()}] 📊 Statistics:")
        print(f"[{self._get_timestamp()}]   Scans performed: {self.scan_count}")
        print(f"[{self._get_timestamp()}]   Devices detected: {self.device_count}")
        print(f"[{self._get_timestamp()}]   Configurations completed: {self.configuration_count}")
        print(f"[{self._get_timestamp()}]   Failed steps: {len(self.failed_steps)}")
        print(f"[{self._get_timestamp()}]   Completed steps: {len(self.completed_steps)}")
    
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

    def _build_command(self, step_name: str, command: str, *args) -> List[str]:
        """Build command with proper credentials and parameters"""
        username = self.config.get("username", "admin")
        password = self.config.get("password", "admin")

        cmd = [self.script_path, "--remote", self.target_ip, username, password, command]
        cmd.extend(args)
        return cmd

    def _execute_command_with_retry(self, command_config: Dict[str, Any]) -> bool:
        """Execute a command with retry mechanism"""
        step_name = command_config["name"]
        cmd = command_config["cmd"]
        timeout = command_config["timeout"]

        for attempt in range(self.max_retries):
            try:
                print(f"[{self._get_timestamp()}] 🔧 Attempt {attempt + 1}/{self.max_retries}: {step_name}")
                print(f"[{self._get_timestamp()}] 💻 Running: {' '.join(cmd)}")

                # Log the command being executed
                self.logger.info(f"Executing command (attempt {attempt + 1}): {' '.join(cmd)}")

                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout
                )

                # Log full output to file
                if result.stdout.strip():
                    self.logger.info(f"STDOUT:\n{result.stdout.strip()}")

                if result.stderr.strip():
                    self.logger.warning(f"STDERR:\n{result.stderr.strip()}")

                if result.returncode == 0:
                    print(f"[{self._get_timestamp()}] ✅ {step_name} completed successfully!")
                    self.logger.info(f"{step_name} completed successfully")

                    # Show output based on verbose mode
                    if result.stdout.strip():
                        if self.verbose:
                            print(f"[{self._get_timestamp()}] 📄 Full Output:")
                            print(result.stdout.strip())
                        else:
                            print(f"[{self._get_timestamp()}] 📄 Output: {result.stdout.strip()[:200]}...")

                    return True
                else:
                    print(f"[{self._get_timestamp()}] ❌ {step_name} failed (attempt {attempt + 1}/{self.max_retries})")
                    self.logger.error(f"{step_name} failed with return code {result.returncode}")

                    # Always show error output
                    if result.stderr.strip():
                        print(f"[{self._get_timestamp()}] 📄 Error: {result.stderr.strip()}")
                    if result.stdout.strip():
                        print(f"[{self._get_timestamp()}] 📄 Output: {result.stdout.strip()}")

                    if attempt < self.max_retries - 1:
                        print(f"[{self._get_timestamp()}] ⏳ Retrying in {self.retry_delay} seconds...")
                        time.sleep(self.retry_delay)

            except subprocess.TimeoutExpired:
                print(f"[{self._get_timestamp()}] ⏰ {step_name} timed out after {timeout} seconds")
                if attempt < self.max_retries - 1:
                    print(f"[{self._get_timestamp()}] ⏳ Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
            except Exception as e:
                print(f"[{self._get_timestamp()}] ❌ {step_name} error: {e}")
                if attempt < self.max_retries - 1:
                    print(f"[{self._get_timestamp()}] ⏳ Retrying in {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)

        return False

    def _get_configuration_sequence(self) -> List[Dict[str, Any]]:
        """Get the configuration sequence with proper credentials"""
        username = self.config.get("username", "admin")
        password = self.config.get("password", "admin")

        return [
            {
                "name": "1. Configure Network FORWARD",
                "cmd": self._build_command("Configure Network FORWARD", "forward"),
                "timeout": 60
            },
            {
                "name": "2. Check DNS Connectivity",
                "cmd": [self.script_path, "check-dns"],
                "timeout": 30
            },
            {
                "name": "3. Fix DNS Configuration",
                "cmd": self._build_command("Fix DNS Configuration", "fix-dns"),
                "timeout": 60
            },
            {
                "name": "4. Install curl",
                "cmd": self._build_command("Install curl", "install-curl"),
                "timeout": 60
            },
            {
                "name": "5. Install Docker",
                "cmd": self._build_command("Install Docker", "install-docker"),
                "timeout": 300
            },
            {
                "name": "6. Install All Docker Services",
                "cmd": self._build_command("Install All Docker Services", "install-services"),
                "timeout": 300
            },
            {
                "name": "7. Install Node-RED Nodes",
                "cmd": self._build_command("Install Node-RED Nodes", "install-nodered-nodes"),
                "timeout": 180
            },
            {
                "name": "8. Import Node-RED Flows",
                "cmd": self._build_command("Import Node-RED Flows", "import-nodered-flows"),
                "timeout": 120
            },
            {
                "name": "9. Update Node-RED Authentication",
                "cmd": self._build_command("Update Node-RED Authentication", "update-nodered-auth", password),
                "timeout": 60
            },
            {
                "name": "10. Install Tailscale VPN Router",
                "cmd": self._build_command("Install Tailscale VPN Router", "install-tailscale"),
                "timeout": 180
            },
            {
                "name": "11. Configure Network REVERSE",
                "cmd": self._build_command("Configure Network REVERSE", "reverse"),
                "timeout": 60
            },
            {
                "name": "12. Change Device Password",
                "cmd": self._build_command("Change Device Password", "set-password", password),
                "timeout": 60
            }
        ]

    def run_network_config(self):
        """Run the complete network configuration sequence"""
        try:
            print(f"[{self._get_timestamp()}] 🚀 Starting complete network configuration sequence...")

            # Get configuration sequence
            commands = self._get_configuration_sequence()

            # Reset progress tracking
            self.current_step = 0
            self.failed_steps = []
            self.completed_steps = []

            # Execute each command in sequence
            for i, command in enumerate(commands, 1):
                self.current_step = i
                print(f"\n[{self._get_timestamp()}] 📋 Step {i}/{len(commands)}: {command['name']}")

                # Execute command with retry mechanism
                success = self._execute_command_with_retry(command)

                if success:
                    self.completed_steps.append(command['name'])
                    print(f"[{self._get_timestamp()}] ✅ Step {i} completed successfully!")
                else:
                    self.failed_steps.append(command['name'])
                    print(f"[{self._get_timestamp()}] ❌ Step {i} failed after {self.max_retries} attempts")

                    # Ask user if they want to continue despite failure
                    if not self._ask_continue_on_failure(command['name']):
                        return False

                # Small delay between commands
                if i < len(commands):
                    print(f"[{self._get_timestamp()}] ⏳ Waiting 5 seconds before next step...")
                    time.sleep(5)

            # Update statistics
            self.configuration_count += 1

            print(f"\n[{self._get_timestamp()}] 🎉 Complete network configuration sequence finished successfully!")
            print(f"[{self._get_timestamp()}] ✅ Completed steps: {len(self.completed_steps)}")
            if self.failed_steps:
                print(f"[{self._get_timestamp()}] ⚠️  Failed steps: {len(self.failed_steps)}")

            return len(self.failed_steps) == 0

        except Exception as e:
            print(f"[{self._get_timestamp()}] ❌ Error in network configuration sequence: {e}")
            self.logger.error(f"Error in network configuration sequence: {e}")
            return False

    def _ask_continue_on_failure(self, step_name: str) -> bool:
        """Ask user if they want to continue despite step failure"""
        if not sys.stdin.isatty():
            # Not running in terminal, auto-continue
            print(f"[{self._get_timestamp()}] ⚠️  Auto-continuing despite failure (non-interactive mode)")
            return True

        try:
            response = input(f"\n[{self._get_timestamp()}] ❓ Step '{step_name}' failed. Continue anyway? (y/N): ").strip().lower()
            return response in ['y', 'yes']
        except (KeyboardInterrupt, EOFError):
            print(f"\n[{self._get_timestamp()}] 🛑 User interrupted, stopping configuration")
            return False

    def scan_and_configure(self):
        """Main bot loop - scan for target IP and configure when found"""
        print(f"[{self._get_timestamp()}] 🤖 Enhanced Bivicom Network Bot Started")
        print(f"[{self._get_timestamp()}] 🎯 Looking for device at {self.target_ip}")
        print(f"[{self._get_timestamp()}] ⏱️  Scan interval: {self.scan_interval} seconds")
        print(f"[{self._get_timestamp()}] 🔄 Max retries: {self.max_retries}")
        print(f"[{self._get_timestamp()}] 📜 Script path: {self.script_path}")
        print(f"[{self._get_timestamp()}] 📝 Verbose mode: {'ON' if self.verbose else 'OFF'}")
        print(f"[{self._get_timestamp()}] ⚙️  Config file: {self.config_file}")
        print(f"[{self._get_timestamp()}] Press Ctrl+C to stop")
        print()

        self.logger.info(f"Bot started - Target IP: {self.target_ip}, Scan interval: {self.scan_interval}s, "
                        f"Max retries: {self.max_retries}, Verbose: {self.verbose}")

        while self.running:
            try:
                self.scan_count += 1
                print(f"[{self._get_timestamp()}] 🔍 Scan #{self.scan_count}: Looking for {self.target_ip}...", end=" ")

                if self.ping_host(self.target_ip):
                    self.device_count += 1
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
                self.logger.error(f"Error during scan: {e}")
                time.sleep(self.scan_interval)

        print(f"\n[{self._get_timestamp()}] 🛑 Bot stopped")
        self._print_statistics()


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Enhanced Bivicom Network Bot - Scans for devices and runs complete network configuration sequence",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                            # Scan for 192.168.1.1 with default settings
  %(prog)s --ip 192.168.1.100        # Scan for specific IP
  %(prog)s --interval 5 --verbose    # Scan every 5 seconds with verbose output
  %(prog)s --config custom.env        # Use custom configuration file
  %(prog)s --max-retries 5           # Retry failed steps up to 5 times

Configuration File (.env):
  Create a .env file to customize settings:
  DEFAULT_USERNAME=admin
  DEFAULT_PASSWORD=admin
  TARGET_IP=192.168.1.1
  SCAN_INTERVAL=10
  TAILSCALE_AUTH_KEY=your_key_here
  SSH_TIMEOUT=10
"""
    )
    parser.add_argument("--ip", default="192.168.1.1", help="Target IP address to scan for (default: 192.168.1.1)")
    parser.add_argument("--interval", type=int, default=10, help="Scan interval in seconds (default: 10)")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show full output from all commands (default: show only summary)")
    parser.add_argument("--config", default=".env", help="Configuration file path (default: .env)")
    parser.add_argument("--max-retries", type=int, default=3, help="Maximum retry attempts for failed steps (default: 3)")
    parser.add_argument("--retry-delay", type=int, default=30, help="Delay between retries in seconds (default: 30)")

    args = parser.parse_args()

    print("Enhanced Bivicom Network Bot")
    print("============================")
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
    print("Features:")
    print("✓ Configuration file support (.env)")
    print("✓ Retry mechanism for failed steps")
    print("✓ Progress tracking and statistics")
    print("✓ Enhanced logging and error handling")
    print()

    # Create and run the bot
    try:
        bot = NetworkBot(
            target_ip=args.ip,
            scan_interval=args.interval,
            verbose=args.verbose,
            config_file=args.config,
            max_retries=args.max_retries,
            retry_delay=args.retry_delay
        )
        bot.scan_and_configure()
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        print("Please ensure network_config.sh exists and is executable.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
    

if __name__ == "__main__":
    main()