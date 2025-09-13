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


class NetworkBot:
    def __init__(self, target_ip="192.168.1.1", scan_interval=10):
        self.target_ip = target_ip
        self.scan_interval = scan_interval
        self.running = True
        self.script_path = os.path.join(os.path.dirname(__file__), "network_config.sh")
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        signal_name = signal.Signals(signum).name
        print(f"\n[{self._get_timestamp()}] Received {signal_name} signal. Stopping bot...")
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
                    "name": "3. Configure Network and Install Docker",
                    "cmd": [self.script_path, "forward-and-docker"],
                    "timeout": 300
                },
                {
                    "name": "4. Install All Docker Services",
                    "cmd": [self.script_path, "install-services"],
                    "timeout": 300
                },
                {
                    "name": "5. Install Node-RED Nodes",
                    "cmd": [self.script_path, "install-nodered-nodes"],
                    "timeout": 180
                },
                {
                    "name": "6. Import Node-RED Flows",
                    "cmd": [self.script_path, "import-nodered-flows"],
                    "timeout": 120
                },
                {
                    "name": "7. Install Tailscale VPN Router",
                    "cmd": [self.script_path, "install-tailscale"],
                    "timeout": 180
                },
                {
                    "name": "8. Configure Network REVERSE",
                    "cmd": [self.script_path, "--remote", self.target_ip, "admin", "admin", "reverse"],
                    "timeout": 60
                }
            ]
            
            # Execute each command in sequence
            for i, command in enumerate(commands, 1):
                print(f"[{self._get_timestamp()}] 📋 Step {i}/8: {command['name']}")
                print(f"[{self._get_timestamp()}] 🔧 Running: {' '.join(command['cmd'])}")
                
                try:
                    result = subprocess.run(
                        command['cmd'], 
                        capture_output=True, 
                        text=True, 
                        timeout=command['timeout']
                    )
                    
                    if result.returncode == 0:
                        print(f"[{self._get_timestamp()}] ✅ Step {i} completed successfully!")
                        if result.stdout.strip():
                            print(f"[{self._get_timestamp()}] 📄 Output: {result.stdout.strip()[:200]}...")
                    else:
                        print(f"[{self._get_timestamp()}] ❌ Step {i} failed!")
                        print(f"[{self._get_timestamp()}] 📄 Error: {result.stderr.strip()[:200]}...")
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
        print(f"[{self._get_timestamp()}] Press Ctrl+C to stop")
        print()
        
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
    parser = argparse.ArgumentParser(description="Bivicom Network Bot - Scans for devices and runs complete network configuration sequence")
    parser.add_argument("--ip", default="192.168.1.1", help="Target IP address to scan for (default: 192.168.1.1)")
    parser.add_argument("--interval", type=int, default=10, help="Scan interval in seconds (default: 10)")
    
    args = parser.parse_args()
    
    print("Bivicom Network Bot")
    print("==================")
    print(f"This bot continuously scans for {args.ip} and runs a complete")
    print("8-step network configuration sequence when the device is found:")
    print()
    print("Sequence:")
    print("1. Configure Network FORWARD")
    print("2. Check DNS Connectivity")
    print("3. Configure Network and Install Docker")
    print("4. Install All Docker Services (Node-RED, Portainer, Restreamer)")
    print("5. Install Node-RED Nodes")
    print("6. Import Node-RED Flows")
    print("7. Install Tailscale VPN Router")
    print("8. Configure Network REVERSE")
    print()
    
    # Create and run the bot
    bot = NetworkBot(target_ip=args.ip, scan_interval=args.interval)
    bot.scan_and_configure()
    

if __name__ == "__main__":
    main()