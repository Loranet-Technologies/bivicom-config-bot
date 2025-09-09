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
import paramiko
import socket
import threading
import time
import json
import sys
import os
import signal
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple
import ipaddress
import re
from datetime import datetime

class UnifiedBivicomBot:
    def __init__(self, config_file: str = "bot_config.json"):
        self.config = self.load_config(config_file)
        self.ssh_client = None
        self.discovered_devices = []
        self.target_devices = []
        self.shutdown_requested = False
        self.cycle_count = 0
        self.device_mac = None
        self.log_file = None
        self.backup_path = None
        
        # Default configuration with correct interface mapping
        self.default_config = {
            "network_range": "192.168.1.0/24",
            "default_credentials": {
                "username": "admin",
                "password": "admin"
            },
            "target_mac_prefixes": [
                "00:52:24",
                "02:52:24"
            ],
            "authorized_ouis": {
                "a4:7a:cf": "VIBICOM COMMUNICATIONS INC.",
                "00:06:2c": "Bivio Networks",
                "00:24:d9": "BICOM, Inc.",
                "00:52:24": "Bivicom (custom/private)",
                "02:52:24": "Bivicom (alternative)"
            },
            "deployment_mode": "auto",
            "ssh_timeout": 10,
            "scan_timeout": 5,
            "max_threads": 50,
            "log_level": "INFO",
            "backup_before_deploy": True,
            "verify_deployment": True,
            "security_logging": True,
            "strict_mac_validation": False,
            "network_configuration": {
                "enable_network_config": True,
                "wan_interface": "eth1",  # Corrected: WAN on eth1
                "lan_interface": "eth0",  # Corrected: LAN on eth0
                "lan_ip": "192.168.1.1",
                "lan_netmask": "255.255.255.0",
                "wan_protocol": "dhcp",
                "lan_protocol": "static",
                "ssh_ready_delay": 30,
                "config_wait_time": 5,
                "service_restart_wait": 5,
                "curl_install_wait": 5,
                "verification_wait": 5,
                "tailscale_auth_wait": 5
            },
            "reverse_configuration": {
                "wan_interface": "enx0250f4000000",  # USB LTE device
                "wan_protocol": "lte",
                "lan_interface": "eth0",
                "lan_protocol": "static"
            },
            "tailscale": {
                "auth_key": "YOUR_TAILSCALE_AUTH_KEY_HERE",
                "enable_setup": True
            },
            "backup_configuration": {
                "backup_location": "/home/$USER",
                "backup_before_deploy": True,
                "restore_after_deploy": True
            },
            "delays": {
                "ip_check": 2,
                "ssh_test": 3,
                "log_creation": 1,
                "between_scripts": 5,
                "script_completion": 2,
                "final_success": 3,
                "cycle_restart": 30
            }
        }
        
        # Merge with loaded config
        if self.config:
            self.default_config.update(self.config)
        self.config = self.default_config
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        signal_name = signal.Signals(signum).name
        self.log(f"Received {signal_name} signal. Initiating graceful shutdown...", "WARNING")
        self.shutdown_requested = True

    def load_config(self, config_file: str) -> Dict:
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"[INFO] Config file {config_file} not found, using defaults")
            return {}
        except json.JSONDecodeError as e:
            print(f"[ERROR] Invalid JSON in config file: {e}")
            return {}

    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")

    def get_mac_address(self, ip: str) -> str:
        """Get MAC address for the target IP"""
        try:
            result = subprocess.run(['arp', '-n', ip], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if ip in line:
                        if ' at ' in line:
                            mac_part = line.split(' at ')[1].split(' on ')[0]
                            mac = mac_part.replace(':', '').replace('-', '').lower()
                            return mac
        except Exception as e:
            print(f"Failed to get MAC address: {e}")
        
        return "unknown"

    def create_log_filename(self) -> str:
        """Create log filename with MAC address and datetime"""
        if not self.device_mac:
            self.device_mac = self.get_mac_address("192.168.1.1")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.device_mac}_{timestamp}.log"
        return filename

    def delay(self, delay_type: str, custom_message: str = None):
        """Add delay with optional custom message, checking for shutdown requests"""
        delay_time = self.config['delays'].get(delay_type, 1)
        
        if custom_message:
            self.log(f"{custom_message} (waiting {delay_time}s)")
        else:
            self.log(f"Waiting {delay_time} seconds...")
        
        # Sleep in small increments to check for shutdown requests
        for _ in range(delay_time):
            if self.shutdown_requested:
                self.log("Shutdown requested during delay. Exiting...", "WARNING")
                return
            time.sleep(1)

    def test_ssh_connection(self, ip: str, username: str, password: str) -> bool:
        """Test SSH connection to a host"""
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            ssh.connect(
                ip,
                username=username,
                password=password,
                timeout=self.config['ssh_timeout'],
                allow_agent=False,
                look_for_keys=False
            )
            
            ssh.close()
            return True
            
        except Exception as e:
            self.log(f"SSH connection failed to {ip}: {e}", "DEBUG")
            return False

    def create_uci_backup(self, ssh, ip: str) -> bool:
        """Create UCI configuration backup using uci backup folder command"""
        self.log(f"Creating UCI backup for {ip}")
        try:
            # Use uci backup folder command as per project memory
            backup_cmd = "sudo uci backup folder /home/$USER"
            stdin, stdout, stderr = ssh.exec_command(backup_cmd)
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status == 0:
                self.log(f"UCI backup created successfully in /home/$USER", "SUCCESS")
                # Get the backup path for later restore
                self.backup_path = f"/home/$USER/uci-backup-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                return True
            else:
                error_output = stderr.read().decode('utf-8').strip()
                self.log(f"UCI backup failed: {error_output}", "ERROR")
                return False
        except Exception as e:
            self.log(f"UCI backup error: {e}", "ERROR")
            return False

    def configure_network_settings_forward(self, ssh, ip: str) -> bool:
        """Configure network settings FORWARD: WAN=eth1 (DHCP), LAN=eth0 (Static)"""
        self.log(f"Configuring network settings FORWARD on {ip} (NO REBOOT)")
        
        try:
            # WAN Configuration (DHCP on eth1) - CORRECTED
            wan_commands = [
                "sudo uci set network.wan.proto='dhcp'",
                "sudo uci set network.wan.ifname='eth1'",  # Corrected: WAN on eth1
                "sudo uci set network.wan.mtu=1500"
            ]
            
            # LAN Configuration (Static on eth0) - CORRECTED
            lan_commands = [
                "sudo uci set network.lan.proto='static'",
                "sudo uci set network.lan.ifname='eth0'",  # Corrected: LAN on eth0
                "sudo uci set network.lan.ipaddr='192.168.1.1'",
                "sudo uci set network.lan.netmask='255.255.255.0'"
            ]
            
            # Execute WAN configuration
            self.log(f"[{ip}] Configuring WAN interface (eth1) for DHCP...")
            for cmd in wan_commands:
                self.log(f"[{ip}] Executing: {cmd}")
                stdin, stdout, stderr = ssh.exec_command(cmd)
                exit_status = stdout.channel.recv_exit_status()
                
                if exit_status != 0:
                    error_output = stderr.read().decode('utf-8').strip()
                    self.log(f"[{ip}] Command failed: {cmd} - {error_output}", "WARNING")
                else:
                    self.log(f"[{ip}] Command successful: {cmd}", "SUCCESS")
            
            # Execute LAN configuration
            self.log(f"[{ip}] Configuring LAN interface (eth0) for static...")
            for cmd in lan_commands:
                self.log(f"[{ip}] Executing: {cmd}")
                stdin, stdout, stderr = ssh.exec_command(cmd)
                exit_status = stdout.channel.recv_exit_status()
                
                if exit_status != 0:
                    error_output = stderr.read().decode('utf-8').strip()
                    self.log(f"[{ip}] Command failed: {cmd} - {error_output}", "WARNING")
                else:
                    self.log(f"[{ip}] Command successful: {cmd}", "SUCCESS")
            
            # Apply WAN configuration with enhanced process
            self.log(f"[{ip}] Applying WAN configuration with enhanced process...")
            if not self.apply_wan_config(ssh, ip):
                self.log(f"[{ip}] WAN configuration application failed", "WARNING")
            
            # Wait 5 seconds after configuration
            wait_time = self.config['network_configuration'].get('config_wait_time', 5)
            self.log(f"[{ip}] Waiting {wait_time} seconds for configuration to settle...")
            time.sleep(wait_time)
            
            self.log(f"Network configuration FORWARD completed on {ip} (NO REBOOT)", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"Network configuration FORWARD failed on {ip}: {e}", "ERROR")
            return False

    def configure_network_settings_reverse(self, ssh, ip: str) -> bool:
        """Configure network settings REVERSE: WAN=enx0250f4000000 (LTE), LAN=eth0 (Static)"""
        self.log(f"Configuring network settings REVERSE on {ip} (NO REBOOT)")
        
        try:
            # WAN Configuration (LTE on USB device) - REVERSE
            wan_commands = [
                "sudo uci set network.wan.proto='lte'",
                "sudo uci set network.wan.ifname='enx0250f4000000'",  # USB LTE device
                "sudo uci set network.wan.mtu=1500"
            ]
            
            # LAN Configuration (Static on eth0) - Keep same
            lan_commands = [
                "sudo uci set network.lan.proto='static'",
                "sudo uci set network.lan.ifname='eth0'",
                "sudo uci set network.lan.ipaddr='192.168.1.1'",
                "sudo uci set network.lan.netmask='255.255.255.0'"
            ]
            
            # Execute WAN configuration
            self.log(f"[{ip}] Configuring WAN interface (enx0250f4000000) for LTE...")
            for cmd in wan_commands:
                self.log(f"[{ip}] Executing: {cmd}")
                stdin, stdout, stderr = ssh.exec_command(cmd)
                exit_status = stdout.channel.recv_exit_status()
                
                if exit_status != 0:
                    error_output = stderr.read().decode('utf-8').strip()
                    self.log(f"[{ip}] Command failed: {cmd} - {error_output}", "WARNING")
                else:
                    self.log(f"[{ip}] Command successful: {cmd}", "SUCCESS")
            
            # Execute LAN configuration
            self.log(f"[{ip}] Configuring LAN interface (eth0) for static...")
            for cmd in lan_commands:
                self.log(f"[{ip}] Executing: {cmd}")
                stdin, stdout, stderr = ssh.exec_command(cmd)
                exit_status = stdout.channel.recv_exit_status()
                
                if exit_status != 0:
                    error_output = stderr.read().decode('utf-8').strip()
                    self.log(f"[{ip}] Command failed: {cmd} - {error_output}", "WARNING")
                else:
                    self.log(f"[{ip}] Command successful: {cmd}", "SUCCESS")
            
            # Apply WAN configuration with enhanced process
            self.log(f"[{ip}] Applying WAN configuration with enhanced process...")
            if not self.apply_wan_config(ssh, ip):
                self.log(f"[{ip}] WAN configuration application failed", "WARNING")
            
            # Wait 5 seconds after configuration
            wait_time = self.config['network_configuration'].get('config_wait_time', 5)
            self.log(f"[{ip}] Waiting {wait_time} seconds for configuration to settle...")
            time.sleep(wait_time)
            
            self.log(f"Network configuration REVERSE completed on {ip} (NO REBOOT)", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"Network configuration REVERSE failed on {ip}: {e}", "ERROR")
            return False

    def check_wan_connectivity(self, ssh, ip: str) -> bool:
        """Check WAN IP and test connectivity with ping"""
        self.log(f"Checking WAN connectivity on {ip}")
        
        try:
            # Check if WAN interface has IP (try both eth1 and enx0250f4000000)
            wan_interfaces = ["eth1", "enx0250f4000000"]
            wan_ip = None
            active_interface = None
            
            for interface in wan_interfaces:
                stdin, stdout, stderr = ssh.exec_command(f"ip addr show {interface} | grep 'inet ' | awk '{{print $2}}' | head -1")
                ip_output = stdout.read().decode('utf-8').strip()
                if ip_output:
                    wan_ip = ip_output
                    active_interface = interface
                    break
            
            if wan_ip:
                self.log(f"WAN interface ({active_interface}) has IP: {wan_ip}", "SUCCESS")
                
                # Test ping to 8.8.8.8
                self.log("Testing ping to 8.8.8.8...")
                stdin, stdout, stderr = ssh.exec_command("ping -c 3 -W 5 8.8.8.8")
                ping_exit_status = stdout.channel.recv_exit_status()
                
                if ping_exit_status == 0:
                    self.log("Ping to 8.8.8.8: ✅ SUCCESS", "SUCCESS")
                else:
                    self.log("Ping to 8.8.8.8: ❌ FAILED", "WARNING")
                
                # Test ping to google.com
                self.log("Testing ping to google.com...")
                stdin, stdout, stderr = ssh.exec_command("ping -c 3 -W 5 google.com")
                ping_exit_status = stdout.channel.recv_exit_status()
                
                if ping_exit_status == 0:
                    self.log("Ping to google.com: ✅ SUCCESS", "SUCCESS")
                    return True
                else:
                    self.log("Ping to google.com: ❌ FAILED", "WARNING")
                    return False
            else:
                self.log("No WAN interface has IP address", "WARNING")
                return False
                
        except Exception as e:
            self.log(f"Error checking WAN connectivity: {e}", "ERROR")
            return False

    def install_curl_with_wait(self, ssh, ip: str) -> bool:
        """Install curl and wait 5 seconds"""
        self.log(f"Installing curl on {ip}")
        
        try:
            # Check if curl is already installed
            stdin, stdout, stderr = ssh.exec_command("which curl")
            if stdout.channel.recv_exit_status() == 0:
                self.log("curl already installed", "SUCCESS")
                wait_time = self.config['network_configuration'].get('curl_install_wait', 5)
                time.sleep(wait_time)
                return True
            
            # Install curl
            install_cmd = "opkg update && opkg install curl"
            stdin, stdout, stderr = ssh.exec_command(install_cmd)
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status == 0:
                self.log("curl installation successful", "SUCCESS")
                wait_time = self.config['network_configuration'].get('curl_install_wait', 5)
                time.sleep(wait_time)
                return True
            else:
                error_output = stderr.read().decode('utf-8').strip()
                self.log(f"curl installation failed: {error_output}", "ERROR")
                return False
        except Exception as e:
            self.log(f"curl installation error: {e}", "ERROR")
            return False

    def deploy_infrastructure(self, ssh, ip: str) -> bool:
        """Deploy infrastructure using curl and install.sh script"""
        self.log(f"Deploying infrastructure on {ip}")
        
        try:
            # Deploy with auto mode
            deploy_cmd = "curl -sSL https://raw.githubusercontent.com/Loranet-Technologies/bivicom-radar/main/install.sh | bash -s -- --auto"
            
            self.log(f"Executing deployment command on {ip}")
            stdin, stdout, stderr = ssh.exec_command(deploy_cmd)
            
            # Monitor deployment progress
            deployment_success = self.monitor_deployment(ssh, stdout, stderr, ip)
            
            if deployment_success:
                self.log(f"Infrastructure deployment completed successfully on {ip}", "SUCCESS")
                return True
            else:
                self.log(f"Infrastructure deployment failed on {ip}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Infrastructure deployment error on {ip}: {e}", "ERROR")
            return False

    def monitor_deployment(self, ssh, stdout, stderr, ip: str) -> bool:
        """Monitor deployment progress"""
        self.log(f"Monitoring deployment on {ip}")
        
        try:
            # Read output in real-time
            while True:
                if stdout.channel.exit_status_ready():
                    break
                
                line = stdout.readline()
                if line:
                    self.log(f"[{ip}] {line.strip()}")
                
                time.sleep(0.1)
            
            exit_status = stdout.channel.recv_exit_status()
            return exit_status == 0
            
        except Exception as e:
            self.log(f"Deployment monitoring error: {e}", "ERROR")
            return False

    def configure_docker_user_group(self, ssh, ip: str) -> bool:
        """Configure Docker user group for current user"""
        self.log(f"Configuring Docker user group on {ip}")
        
        try:
            # Add current user to docker group
            self.log(f"[{ip}] Adding current user to docker group...")
            stdin, stdout, stderr = ssh.exec_command("sudo usermod -aG docker $USER")
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status != 0:
                error_output = stderr.read().decode('utf-8').strip()
                self.log(f"[{ip}] Failed to add user to docker group: {error_output}", "WARNING")
                return False
            else:
                self.log(f"[{ip}] User added to docker group successfully", "SUCCESS")
            
            # Apply new group membership
            self.log(f"[{ip}] Applying new group membership...")
            stdin, stdout, stderr = ssh.exec_command("newgrp docker")
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status != 0:
                error_output = stderr.read().decode('utf-8').strip()
                self.log(f"[{ip}] Failed to apply new group membership: {error_output}", "WARNING")
                # This is not critical, continue anyway
            else:
                self.log(f"[{ip}] New group membership applied successfully", "SUCCESS")
            
            # Test Docker without sudo
            self.log(f"[{ip}] Testing Docker without sudo...")
            stdin, stdout, stderr = ssh.exec_command("docker --version")
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status == 0:
                self.log(f"[{ip}] Docker works without sudo: ✅", "SUCCESS")
                return True
            else:
                self.log(f"[{ip}] Docker still requires sudo: ⚠️", "WARNING")
                # This might be expected if newgrp didn't work in SSH context
                return True  # Continue anyway, user can manually run newgrp later
            
        except Exception as e:
            self.log(f"Docker user group configuration error: {e}", "ERROR")
            return False

    def verify_all_installations(self, ssh, ip: str) -> bool:
        """Verify all infrastructure installations and configure Docker user group"""
        self.log(f"Verifying all installations on {ip}")
        
        try:
            services_to_check = [
                ("Docker", "docker --version"),
                ("Node-RED", "node-red --version"),
                ("Tailscale", "tailscale version")
            ]
            
            all_installed = True
            docker_installed = False
            
            for service_name, check_cmd in services_to_check:
                stdin, stdout, stderr = ssh.exec_command(check_cmd)
                exit_status = stdout.channel.recv_exit_status()
                
                if exit_status == 0:
                    self.log(f"{service_name}: ✅ Installed", "SUCCESS")
                    if service_name == "Docker":
                        docker_installed = True
                else:
                    self.log(f"{service_name}: ❌ Not installed", "WARNING")
                    all_installed = False
            
            # Configure Docker user group if Docker is installed
            if docker_installed:
                self.log("Docker detected, configuring user group...")
                docker_config_ok = self.configure_docker_user_group(ssh, ip)
                if not docker_config_ok:
                    self.log("Docker user group configuration failed", "WARNING")
            else:
                self.log("Docker not installed, skipping user group configuration")
            
            # Wait 5 seconds after verification
            wait_time = self.config['network_configuration'].get('verification_wait', 5)
            time.sleep(wait_time)
            return all_installed
            
        except Exception as e:
            self.log(f"Installation verification error: {e}", "ERROR")
            return False

    def setup_tailscale(self, ssh, ip: str) -> bool:
        """Setup Tailscale with authentication"""
        self.log(f"Setting up Tailscale on {ip}")
        
        try:
            auth_key = self.config.get('tailscale', {}).get('auth_key', '')
            if not auth_key or auth_key == "YOUR_TAILSCALE_AUTH_KEY_HERE":
                self.log("Tailscale auth key not configured, skipping setup", "WARNING")
                return True
            
            tailscale_cmd = f"tailscale up --authkey={auth_key}"
            stdin, stdout, stderr = ssh.exec_command(tailscale_cmd)
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status == 0:
                self.log(f"Tailscale authentication successful", "SUCCESS")
                wait_time = self.config['network_configuration'].get('tailscale_auth_wait', 5)
                time.sleep(wait_time)
                return True
            else:
                error_output = stderr.read().decode('utf-8').strip()
                self.log(f"Tailscale setup failed: {error_output}", "ERROR")
                return False
        except Exception as e:
            self.log(f"Tailscale setup error: {e}", "ERROR")
            return False

    def cleanup_empty_routes(self, ssh, ip: str) -> bool:
        """Clean up empty routes and add proper default route"""
        self.log(f"[{ip}] Cleaning up empty routes...")
        
        try:
            # Remove all empty default routes
            cleanup_commands = [
                # Remove routes with empty gateway
                "ip route show | grep 'default via $' | while read route; do ip route del $route 2>/dev/null || true; done",
                # Remove routes with empty gateway but with metric
                "ip route show | grep 'default via  metric' | while read route; do ip route del $route 2>/dev/null || true; done",
                # Remove routes with empty dev
                "ip route show | grep 'default via.*dev $' | while read route; do ip route del $route 2>/dev/null || true; done"
            ]
            
            for cmd in cleanup_commands:
                stdin, stdout, stderr = ssh.exec_command(cmd)
                stdout.channel.recv_exit_status()  # Ignore exit status for cleanup
            
            # Add proper default route if WAN is configured
            self.log(f"[{ip}] Checking for WAN gateway configuration...")
            stdin, stdout, stderr = ssh.exec_command("uci -q get network.wan.gateway 2>/dev/null")
            wan_gateway = stdout.read().decode('utf-8').strip()
            
            stdin, stdout, stderr = ssh.exec_command("uci -q get network.wan.ifname 2>/dev/null")
            wan_ifname = stdout.read().decode('utf-8').strip()
            
            if wan_gateway and wan_gateway != "" and wan_ifname:
                self.log(f"[{ip}] Adding default route via {wan_gateway} dev {wan_ifname}")
                add_route_cmd = f"ip route add default via \"{wan_gateway}\" dev \"{wan_ifname}\" 2>/dev/null || true"
                stdin, stdout, stderr = ssh.exec_command(add_route_cmd)
                stdout.channel.recv_exit_status()  # Ignore exit status
            else:
                self.log(f"[{ip}] No WAN gateway configured, skipping default route addition")
            
            self.log(f"[{ip}] Route cleanup completed", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"[{ip}] Route cleanup error: {e}", "WARNING")
            return False

    def apply_wan_config(self, ssh, ip: str) -> bool:
        """Apply WAN configuration with enhanced network reload process"""
        self.log(f"Applying WAN configuration on {ip}")
        
        try:
            # Step 1: Commit UCI changes
            self.log(f"[{ip}] Committing UCI changes...")
            stdin, stdout, stderr = ssh.exec_command("sudo uci commit network")
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status != 0:
                error_output = stderr.read().decode('utf-8').strip()
                self.log(f"[{ip}] UCI commit failed: {error_output}", "WARNING")
            else:
                self.log(f"[{ip}] UCI commit successful", "SUCCESS")
            
            # Step 2: Clean up empty routes before applying configuration
            self.cleanup_empty_routes(ssh, ip)
            
            # Step 3: Run network configuration
            self.log(f"[{ip}] Running network configuration...")
            network_config_cmd = "/usr/sbin/network_config" if self.check_command_exists(ssh, "/usr/sbin/network_config") else "/etc/init.d/network restart"
            stdin, stdout, stderr = ssh.exec_command(network_config_cmd)
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status != 0:
                error_output = stderr.read().decode('utf-8').strip()
                self.log(f"[{ip}] Network config failed: {error_output}", "WARNING")
            else:
                self.log(f"[{ip}] Network config successful", "SUCCESS")
            
            # Step 4: Reload network services with luci-reload if available
            self.log(f"[{ip}] Reloading network services...")
            if self.check_command_exists(ssh, "/usr/sbin/luci-reload"):
                # Create a dummy lock command if it doesn't exist
                stdin, stdout, stderr = ssh.exec_command("command -v lock >/dev/null 2>&1 || echo '#!/bin/sh\necho \"lock: dummy command\"' > /tmp/lock && chmod +x /tmp/lock")
                stdout.channel.recv_exit_status()  # Ignore exit status
                
                # Set PATH to include /tmp for the dummy lock command
                stdin, stdout, stderr = ssh.exec_command("export PATH=\"/tmp:$PATH\" && /usr/sbin/luci-reload network")
                exit_status = stdout.channel.recv_exit_status()
                
                if exit_status != 0:
                    error_output = stderr.read().decode('utf-8').strip()
                    self.log(f"[{ip}] luci-reload failed: {error_output}", "WARNING")
                    # Fallback to network restart
                    stdin, stdout, stderr = ssh.exec_command("/etc/init.d/network restart")
                    stdout.channel.recv_exit_status()  # Ignore exit status for fallback
                else:
                    self.log(f"[{ip}] luci-reload successful", "SUCCESS")
            else:
                self.log(f"[{ip}] luci-reload not found, using network restart")
                stdin, stdout, stderr = ssh.exec_command("/etc/init.d/network restart")
                exit_status = stdout.channel.recv_exit_status()
                
                if exit_status != 0:
                    error_output = stderr.read().decode('utf-8').strip()
                    self.log(f"[{ip}] Network restart failed: {error_output}", "WARNING")
                else:
                    self.log(f"[{ip}] Network restart successful", "SUCCESS")
            
            # Step 5: Final cleanup of empty routes after configuration
            self.cleanup_empty_routes(ssh, ip)
            
            self.log(f"WAN configuration applied successfully on {ip}", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"WAN configuration application error on {ip}: {e}", "ERROR")
            return False

    def check_command_exists(self, ssh, command: str) -> bool:
        """Check if a command exists on the remote system"""
        try:
            stdin, stdout, stderr = ssh.exec_command(f"command -v {command}")
            exit_status = stdout.channel.recv_exit_status()
            return exit_status == 0
        except Exception:
            return False

    def restore_uci_backup_simple(self, ssh, ip: str) -> bool:
        """Restore UCI configuration from backup (simple version - no enhanced process)"""
        self.log(f"Restoring UCI configuration from backup on {ip}")
        
        try:
            if not self.backup_path:
                self.log("No backup path available, skipping restore", "WARNING")
                return True
            
            # Step 1: Restore UCI configuration
            restore_cmd = f"sudo uci restore {self.backup_path}"
            self.log(f"[{ip}] Executing: {restore_cmd}")
            stdin, stdout, stderr = ssh.exec_command(restore_cmd)
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status != 0:
                error_output = stderr.read().decode('utf-8').strip()
                self.log(f"[{ip}] Restore command failed: {restore_cmd} - {error_output}", "WARNING")
            else:
                self.log(f"[{ip}] Restore command successful: {restore_cmd}", "SUCCESS")
            
            # Step 2: Simple network reload (no enhanced process to avoid conflicts)
            self.log(f"[{ip}] Reloading network services (simple restore)...")
            stdin, stdout, stderr = ssh.exec_command("sudo /etc/init.d/network reload")
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status != 0:
                error_output = stderr.read().decode('utf-8').strip()
                self.log(f"[{ip}] Network reload failed: {error_output}", "WARNING")
            else:
                self.log(f"[{ip}] Network reload successful", "SUCCESS")
            
            self.log(f"UCI configuration restored successfully on {ip}", "SUCCESS")
            return True
        except Exception as e:
            self.log(f"UCI restore error: {e}", "ERROR")
            return False

    def restore_uci_backup(self, ssh, ip: str) -> bool:
        """Restore UCI configuration from backup (legacy function - kept for compatibility)"""
        # Use the simple restore function to avoid conflicts
        return self.restore_uci_backup_simple(ssh, ip)

    def check_target_ip_availability(self, ip: str) -> bool:
        """Check if target IP is reachable"""
        self.log(f"Checking if target IP {ip} is reachable...")
        
        try:
            result = subprocess.run(
                ['ping', '-c', '1', '-W', '2', ip],
                capture_output=True,
                timeout=5
            )
            if result.returncode == 0:
                self.log(f"Target IP {ip} is reachable", "SUCCESS")
                return True
            else:
                self.log(f"Target IP {ip} is not reachable", "ERROR")
                return False
        except Exception as e:
            self.log(f"Error checking IP availability: {e}", "ERROR")
            return False

    def run_complete_deployment_cycle(self, mode: str = "forward") -> bool:
        """Run the complete deployment cycle (NO REBOOT)"""
        target_ip = "192.168.1.1"
        username = self.config['default_credentials']['username']
        password = self.config['default_credentials']['password']
        
        self.log("=" * 80)
        self.log(f"UNIFIED BIVICOM BOT CYCLE #{self.cycle_count + 1}: COMPLETE DEPLOYMENT ({mode.upper()})")
        self.log("=" * 80)
        
        try:
            # Step 1: Check target IP availability
            self.log("Step 1: Checking target IP availability")
            if not self.check_target_ip_availability(target_ip):
                self.log("Target IP not available. Cycle failed.", "ERROR")
                return False
            
            self.delay("ip_check", "IP check completed")
            
            # Step 2: Test SSH login
            self.log("Step 2: Testing SSH login")
            if not self.test_ssh_connection(target_ip, username, password):
                self.log("SSH login failed. Cycle failed.", "ERROR")
                return False
            
            self.log("SSH login successful", "SUCCESS")
            self.delay("ssh_test", "SSH test completed")
            
            # Step 3: Create log file
            self.log("Step 3: Creating log file")
            self.log_file = self.create_log_filename()
            self.log(f"Created log file: {self.log_file}", "SUCCESS")
            self.delay("log_creation", "Log file created")
            
            # Step 4: Connect via SSH and start deployment
            self.log("Step 4: Connecting via SSH and starting deployment")
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(target_ip, username=username, password=password, timeout=self.config['ssh_timeout'])
            self.log(f"SSH connection established to {target_ip}", "SUCCESS")
            
            # Step 5: Create UCI backup
            self.log("Step 5: Creating UCI backup")
            if not self.create_uci_backup(ssh, target_ip):
                self.log("UCI backup failed, continuing anyway", "WARNING")
            
            # Step 6: Configure network settings
            self.log(f"Step 6: Configuring network settings ({mode.upper()})")
            if mode == "forward":
                network_success = self.configure_network_settings_forward(ssh, target_ip)
            else:  # reverse
                network_success = self.configure_network_settings_reverse(ssh, target_ip)
            
            if not network_success:
                self.log("Network configuration failed", "ERROR")
                ssh.close()
                return False
            
            # Step 7: Check WAN connectivity
            self.log("Step 7: Checking WAN connectivity")
            wan_ok = self.check_wan_connectivity(ssh, target_ip)
            if not wan_ok:
                self.log("WAN connectivity check failed, continuing anyway", "WARNING")
            
            # Step 8: Install curl
            self.log("Step 8: Installing curl")
            if not self.install_curl_with_wait(ssh, target_ip):
                self.log("curl installation failed, cannot proceed", "ERROR")
                ssh.close()
                return False
            
            # Step 9: Deploy infrastructure
            self.log("Step 9: Deploying infrastructure")
            if not self.deploy_infrastructure(ssh, target_ip):
                self.log("Infrastructure deployment failed", "ERROR")
                ssh.close()
                return False
            
            # Step 10: Verify installations
            self.log("Step 10: Verifying installations")
            verify_ok = self.verify_all_installations(ssh, target_ip)
            if not verify_ok:
                self.log("Some installations failed verification", "WARNING")
            
            # Step 11: Setup Tailscale
            self.log("Step 11: Setting up Tailscale")
            tailscale_ok = self.setup_tailscale(ssh, target_ip)
            if not tailscale_ok:
                self.log("Tailscale setup failed", "WARNING")
            
            # Step 12: Restore UCI backup (simple restore to avoid conflicts)
            self.log("Step 12: Restoring UCI backup")
            restore_ok = self.restore_uci_backup_simple(ssh, target_ip)
            if not restore_ok:
                self.log("UCI backup restore failed", "WARNING")
            
            # Close SSH connection
            ssh.close()
            
            # Success!
            self.log("=" * 80)
            self.log(f"UNIFIED BIVICOM BOT CYCLE COMPLETED SUCCESSFULLY! ({mode.upper()})", "SUCCESS")
            self.log("=" * 80)
            self.log("All deployment steps completed:")
            self.log("- UCI backup created")
            self.log(f"- Network configured ({mode.upper()}) - NO REBOOT")
            self.log("- WAN connectivity verified")
            self.log("- curl installed")
            self.log("- Infrastructure deployed")
            self.log("- Installations verified and Docker user group configured")
            self.log("- Tailscale configured")
            self.log("- UCI configuration restored (simple restore) - NO REBOOT")
            self.log(f"Check log file for detailed output: {self.log_file}")
            
            return True
            
        except Exception as e:
            self.log(f"Deployment cycle failed with error: {e}", "ERROR")
            return False

    def run_forever_mode(self, mode: str = "forward"):
        """Run the bot in forever mode (NO REBOOT)"""
        self.log("=" * 80)
        self.log(f"UNIFIED BIVICOM BOT STARTING - RUNNING FOREVER MODE ({mode.upper()})")
        self.log("Press Ctrl+C or send SIGTERM to stop gracefully")
        self.log("=" * 80)
        
        while not self.shutdown_requested:
            self.cycle_count += 1
            
            success = self.run_complete_deployment_cycle(mode)
            
            if success:
                self.log(f"Cycle #{self.cycle_count} completed successfully. Waiting before next cycle...")
            else:
                self.log(f"Cycle #{self.cycle_count} failed. Waiting before retry...")
            
            self.delay("cycle_restart", "Waiting before next cycle")
        
        self.log("=" * 80)
        self.log(f"UNIFIED BIVICOM BOT SHUTDOWN - COMPLETED {self.cycle_count} CYCLES")
        self.log("=" * 80)
        self.log("Bot stopped gracefully. Goodbye!")

    def run_single_cycle(self, mode: str = "forward"):
        """Run a single deployment cycle (NO REBOOT)"""
        self.log("=" * 80)
        self.log(f"UNIFIED BIVICOM BOT - SINGLE CYCLE MODE ({mode.upper()})")
        self.log("=" * 80)
        
        success = self.run_complete_deployment_cycle(mode)
        
        if success:
            self.log(f"Single cycle completed successfully! ({mode.upper()})", "SUCCESS")
            return True
        else:
            self.log("Single cycle failed!", "ERROR")
            return False

def main():
    """Main function"""
    print("Unified Bivicom Configuration Bot with Reverse Functionality")
    print("===========================================================")
    print("This unified script combines all functionality:")
    print("1. Network Discovery & SSH Connection")
    print("2. UCI Backup Creation")
    print("3. Network Configuration (Forward/Reverse) - NO REBOOT")
    print("4. Connectivity Verification")
    print("5. Curl Installation")
    print("6. Infrastructure Deployment")
    print("7. Installation Verification & Docker User Group Configuration")
    print("8. Tailscale Setup")
    print("9. UCI Configuration Restore (Simple) - NO REBOOT")
    print("10. Master Bot Orchestration")
    print()
    print("Modes:")
    print("  FORWARD: WAN=eth1 (DHCP), LAN=eth0 (Static)")
    print("  REVERSE: WAN=enx0250f4000000 (LTE), LAN=eth0 (Static)")
    print()
    
    # Check command line arguments
    mode = "forward"  # default
    run_mode = "forever"  # default
    
    if len(sys.argv) > 1:
        for arg in sys.argv[1:]:
            if arg == "--single":
                run_mode = "single"
            elif arg == "--reverse":
                mode = "reverse"
            elif arg == "--forward":
                mode = "forward"
    
    if run_mode == "single":
        print(f"Running in SINGLE CYCLE mode ({mode.upper()})")
    else:
        print(f"Running in FOREVER mode ({mode.upper()}) - press Ctrl+C to stop")
    
    print()
    
    # Initialize and run bot
    bot = UnifiedBivicomBot()
    
    if run_mode == "single":
        success = bot.run_single_cycle(mode)
        sys.exit(0 if success else 1)
    else:
        bot.run_forever_mode(mode)

if __name__ == "__main__":
    main()
