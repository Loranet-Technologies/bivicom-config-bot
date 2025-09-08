#!/usr/bin/env python3
"""
Script No. 3: Loranet Infrastructure Deployment Bot
==================================================

This script automatically discovers devices on the network, identifies them by MAC address,
and deploys the Loranet infrastructure setup via SSH.

Author: Aqmar
Date: 2025-01-08
"""

import subprocess
import paramiko
import socket
import threading
import time
import json
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple
import ipaddress
import re

class LoranetDeploymentBot:
    def __init__(self, config_file: str = "bot_config.json"):
        self.config = self.load_config(config_file)
        self.ssh_client = None
        self.discovered_devices = []
        self.target_devices = []
        
        # Default configuration
        self.default_config = {
            "network_range": "192.168.1.0/24",
            "default_credentials": {
                "username": "admin",
                "password": "admin"
            },
            "target_mac_prefixes": [
                "00:52:24",  # Bivicom devices
                "02:52:24",  # Alternative Bivicom prefix
                "aa:bb:cc"   # Add your specific MAC prefixes
            ],
            "deployment_mode": "auto",  # auto, interactive, or manual
            "ssh_timeout": 10,
            "scan_timeout": 5,
            "max_threads": 50,
            "log_level": "INFO",
            "backup_before_deploy": True,
            "verify_deployment": True
        }
        
        # Merge with loaded config
        if self.config:
            self.default_config.update(self.config)
        self.config = self.default_config

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

    def save_config(self, config_file: str = "bot_config.json"):
        """Save current configuration to JSON file"""
        try:
            with open(config_file, 'w') as f:
                json.dump(self.config, f, indent=2)
            print(f"[SUCCESS] Configuration saved to {config_file}")
        except Exception as e:
            print(f"[ERROR] Failed to save config: {e}")

    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")

    def scan_network(self, network_range: str) -> List[str]:
        """Scan network range for active hosts"""
        self.log(f"Scanning network range: {network_range}")
        active_hosts = []
        
        try:
            network = ipaddress.ip_network(network_range, strict=False)
        except ValueError as e:
            self.log(f"Invalid network range: {e}", "ERROR")
            return active_hosts

        def ping_host(ip):
            """Ping a single host"""
            try:
                result = subprocess.run(
                    ['ping', '-c', '1', '-W', str(self.config['scan_timeout']), str(ip)],
                    capture_output=True,
                    timeout=self.config['scan_timeout'] + 2
                )
                if result.returncode == 0:
                    return str(ip)
            except (subprocess.TimeoutExpired, Exception):
                pass
            return None

        # Use ThreadPoolExecutor for concurrent scanning
        with ThreadPoolExecutor(max_workers=self.config['max_threads']) as executor:
            futures = {executor.submit(ping_host, ip): ip for ip in network.hosts()}
            
            for future in as_completed(futures):
                result = future.result()
                if result:
                    active_hosts.append(result)
                    self.log(f"Found active host: {result}")

        self.log(f"Network scan completed. Found {len(active_hosts)} active hosts")
        return active_hosts

    def get_mac_address(self, ip: str) -> Optional[str]:
        """Get MAC address of a host using ARP table"""
        try:
            # Try to get MAC from ARP table
            result = subprocess.run(['arp', '-n', ip], capture_output=True, text=True)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if ip in line:
                        # Extract MAC address from ARP output
                        mac_match = re.search(r'([0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}', line)
                        if mac_match:
                            return mac_match.group(0).replace('-', ':').lower()
            
            # Alternative method using nmap if available
            try:
                result = subprocess.run(['nmap', '-sn', ip], capture_output=True, text=True)
                if result.returncode == 0:
                    mac_match = re.search(r'([0-9a-fA-F]{2}[:-]){5}[0-9a-fA-F]{2}', result.stdout)
                    if mac_match:
                        return mac_match.group(0).replace('-', ':').lower()
            except FileNotFoundError:
                pass
                
        except Exception as e:
            self.log(f"Failed to get MAC for {ip}: {e}", "WARNING")
        
        return None

    def validate_mac_address(self, mac: str) -> Dict:
        """Validate MAC address and check against authorized manufacturers"""
        if not mac:
            return {'valid': False, 'reason': 'Empty MAC address'}
        
        mac_lower = mac.lower()
        
        # Validate MAC format
        import re
        if not re.match(r'^([0-9a-f]{2}[:-]){5}[0-9a-f]{2}$', mac_lower):
            return {'valid': False, 'reason': 'Invalid MAC address format'}
        
        # Extract OUI (first 3 octets)
        oui = mac_lower[:8]  # XX:XX:XX format
        
        # Known Bivicom manufacturer prefixes
        authorized_ouis = {
            "a4:7a:cf": "VIBICOM COMMUNICATIONS INC.",
            "00:06:2c": "Bivio Networks", 
            "00:24:d9": "BICOM, Inc.",
            "00:52:24": "Bivicom (custom/private)",
            "02:52:24": "Bivicom (alternative)"
        }
        
        # Check against configured target prefixes
        for prefix in self.config['target_mac_prefixes']:
            if mac_lower.startswith(prefix.lower()):
                return {
                    'valid': True, 
                    'authorized': True,
                    'oui': oui,
                    'manufacturer': f"Configured prefix: {prefix}",
                    'reason': 'Matches configured target prefix'
                }
        
        # Check against known Bivicom OUIs
        if oui in authorized_ouis:
            return {
                'valid': True,
                'authorized': True, 
                'oui': oui,
                'manufacturer': authorized_ouis[oui],
                'reason': 'Matches authorized Bivicom OUI'
            }
        
        return {
            'valid': True,
            'authorized': False,
            'oui': oui,
            'manufacturer': 'Unknown',
            'reason': 'Not in authorized Bivicom OUI list'
        }

    def is_target_device(self, mac: str) -> bool:
        """Check if MAC address matches target device prefixes"""
        # Skip MAC validation if strict_mac_validation is disabled
        if not self.config.get('strict_mac_validation', True):
            self.log(f"MAC validation disabled - accepting device {mac}", "INFO")
            return True
        
        validation = self.validate_mac_address(mac)
        
        if not validation['valid']:
            self.log(f"Invalid MAC address {mac}: {validation['reason']}", "ERROR")
            return False
        
        if validation['authorized']:
            self.log(f"Device {mac} ({validation['oui']}) authorized: {validation['manufacturer']}", "SUCCESS")
            return True
        else:
            self.log(f"Device {mac} ({validation['oui']}) not authorized: {validation['reason']}", "WARNING")
            return False

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

    def log_security_event(self, event_type: str, ip: str, mac: str, details: str):
        """Log security events for auditing"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] SECURITY [{event_type}] IP: {ip} MAC: {mac} Details: {details}"
        
        # Log to console
        self.log(f"SECURITY [{event_type}] {ip} ({mac}): {details}", "WARNING")
        
        # Log to file
        try:
            with open("security_audit.log", "a") as f:
                f.write(log_entry + "\n")
        except Exception as e:
            self.log(f"Failed to write security log: {e}", "ERROR")

    def discover_devices(self) -> List[Dict]:
        """Discover and identify target devices on the network"""
        self.log("Starting device discovery...")
        
        # Scan network for active hosts
        active_hosts = self.scan_network(self.config['network_range'])
        
        discovered_devices = []
        unauthorized_devices = []
        
        for ip in active_hosts:
            self.log(f"Analyzing host: {ip}")
            
            # Get MAC address
            mac = self.get_mac_address(ip)
            if not mac:
                self.log(f"Could not determine MAC for {ip}", "WARNING")
                continue
            
            # Check if MAC validation is enabled
            if self.config.get('strict_mac_validation', True):
                # Validate MAC address and check authorization
                validation = self.validate_mac_address(mac)
                
                if not validation['valid']:
                    self.log_security_event("INVALID_MAC", ip, mac, validation['reason'])
                    continue
                
                if validation['authorized']:
                    self.log(f"Found authorized device: {ip} (MAC: {mac}) - {validation['manufacturer']}")
                    
                    # Test SSH connection
                    if self.test_ssh_connection(ip, self.config['default_credentials']['username'], 
                                             self.config['default_credentials']['password']):
                        device_info = {
                            'ip': ip,
                            'mac': mac,
                            'oui': validation['oui'],
                            'manufacturer': validation['manufacturer'],
                            'username': self.config['default_credentials']['username'],
                            'password': self.config['default_credentials']['password'],
                            'status': 'ready',
                            'authorized': True
                        }
                        discovered_devices.append(device_info)
                        self.log(f"Device {ip} is ready for deployment", "SUCCESS")
                    else:
                        self.log(f"Device {ip} found but SSH connection failed", "WARNING")
                else:
                    # Log unauthorized device attempt
                    self.log_security_event("UNAUTHORIZED_DEVICE", ip, mac, 
                                          f"OUI: {validation['oui']} - {validation['reason']}")
                    unauthorized_devices.append({
                        'ip': ip,
                        'mac': mac,
                        'oui': validation['oui'],
                        'manufacturer': validation['manufacturer'],
                        'reason': validation['reason']
                    })
                    self.log(f"Host {ip} (MAC: {mac}) is not authorized for deployment", "WARNING")
            else:
                # MAC validation disabled - accept all devices
                self.log(f"MAC validation disabled - accepting device: {ip} (MAC: {mac})")
                
                # Test SSH connection
                if self.test_ssh_connection(ip, self.config['default_credentials']['username'], 
                                         self.config['default_credentials']['password']):
                    device_info = {
                        'ip': ip,
                        'mac': mac,
                        'oui': 'unknown',
                        'manufacturer': 'Unknown',
                        'username': self.config['default_credentials']['username'],
                        'password': self.config['default_credentials']['password'],
                        'status': 'ready',
                        'authorized': True
                    }
                    discovered_devices.append(device_info)
                    self.log(f"Device {ip} is ready for deployment", "SUCCESS")
                else:
                    self.log(f"Device {ip} found but SSH connection failed", "WARNING")
        
        self.discovered_devices = discovered_devices
        
        # Summary
        self.log(f"Discovery completed:")
        self.log(f"  - Authorized devices found: {len(discovered_devices)}")
        self.log(f"  - Unauthorized devices detected: {len(unauthorized_devices)}")
        
        if unauthorized_devices:
            self.log("Unauthorized devices detected:", "WARNING")
            for device in unauthorized_devices:
                self.log(f"  - {device['ip']} ({device['mac']}) - {device['manufacturer']}", "WARNING")
        
        return discovered_devices

    def configure_network_settings(self, ssh, ip: str) -> bool:
        """Configure network settings on the device"""
        self.log(f"Configuring network settings on {ip}")
        
        try:
            # Get network configuration from config
            net_config = self.config.get('network_configuration', {})
            
            # Network configuration commands for OpenWrt/LEDE with improved error handling
            # Tested configuration: WAN=eth0 (DHCP), LAN=eth1 (DHCP), Bridge intact
            network_commands = [
                # Configure WAN interface (eth0) for DHCP internet access
                f"sudo uci set network.wan.proto='{net_config.get('wan_protocol', 'dhcp')}' 2>/dev/null || echo 'WAN protocol already set'",
                f"sudo uci set network.wan.ifname='{net_config.get('wan_interface', 'eth0')}' 2>/dev/null || echo 'WAN interface already set'",
                "sudo uci set network.wan.mtu=1500 2>/dev/null || echo 'WAN MTU already set'",
                
                # Configure LAN interface (eth1) for DHCP (will get IP from network)
                f"sudo uci set network.lan.proto='{net_config.get('lan_protocol', 'dhcp')}' 2>/dev/null || echo 'LAN protocol already set'",
                f"sudo uci set network.lan.ifname='{net_config.get('lan_interface', 'eth1')}' 2>/dev/null || echo 'LAN interface already set'",
                
                # Apply network configuration with error handling
                "sudo uci commit network 2>/dev/null || echo 'Network commit failed or no changes'",
                
                # Reload network configuration with fallback to restart
                "sudo /etc/init.d/network reload 2>/dev/null || sudo /etc/init.d/network restart 2>/dev/null || echo 'Network service restart failed'"
            ]
            
            for cmd in network_commands:
                self.log(f"[{ip}] Executing: {cmd}")
                stdin, stdout, stderr = ssh.exec_command(cmd)
                exit_status = stdout.channel.recv_exit_status()
                
                if exit_status != 0:
                    error_output = stderr.read().decode('utf-8').strip()
                    self.log(f"[{ip}] Command failed: {cmd} - {error_output}", "WARNING")
                else:
                    self.log(f"[{ip}] Command successful: {cmd}", "SUCCESS")
            
            self.log(f"Network configuration completed on {ip}", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"Network configuration failed on {ip}: {e}", "ERROR")
            return False

    def reboot_device(self, ssh, ip: str) -> bool:
        """Reboot the device to apply network changes"""
        self.log(f"Rebooting device {ip} to apply network configuration")
        
        try:
            # Execute reboot command
            stdin, stdout, stderr = ssh.exec_command("reboot")
            
            # Wait a moment for reboot to initiate
            time.sleep(2)
            
            self.log(f"Reboot command sent to {ip}", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"Reboot failed on {ip}: {e}", "ERROR")
            return False

    def wait_for_device_reboot(self, ip: str, max_wait_time: int = None) -> bool:
        """Wait for device to come back online after reboot"""
        if max_wait_time is None:
            max_wait_time = self.config.get('network_configuration', {}).get('reboot_timeout', 300)
        
        self.log(f"Waiting for {ip} to come back online after reboot...")
        
        start_time = time.time()
        while time.time() - start_time < max_wait_time:
            try:
                # Try to ping the device
                result = subprocess.run(
                    ['ping', '-c', '1', '-W', '2', ip],
                    capture_output=True,
                    timeout=5
                )
                if result.returncode == 0:
                    self.log(f"Device {ip} is back online", "SUCCESS")
                    return True
            except:
                pass
            
            time.sleep(10)  # Wait 10 seconds before next check
            elapsed = int(time.time() - start_time)
            self.log(f"Still waiting for {ip}... ({elapsed}s elapsed)")
        
        self.log(f"Timeout waiting for {ip} to come back online", "ERROR")
        return False

    def device_requires_network_config(self, ip: str) -> bool:
        """Check if device requires network configuration"""
        server_targets = self.config.get('server_targets', {})
        if ip in server_targets:
            return server_targets[ip].get('requires_network_config', False)
        
        # Check if network configuration is enabled globally
        return self.config.get('network_configuration', {}).get('enable_network_config', False)

    def test_network_configuration_commands(self):
        """Test network configuration commands without executing them"""
        print("=" * 80)
        print("Network Configuration Commands Test")
        print("=" * 80)
        
        # Get network configuration from config
        net_config = self.config.get('network_configuration', {})
        
        print(f"\nConfiguration Settings:")
        print(f"  - WAN Interface: {net_config.get('wan_interface', 'eth0')}")
        print(f"  - LAN Interface: {net_config.get('lan_interface', 'eth1')}")
        print(f"  - LAN IP: {net_config.get('lan_ip', '192.168.1.1')}")
        print(f"  - LAN Netmask: {net_config.get('lan_netmask', '255.255.255.0')}")
        print(f"  - WAN Protocol: {net_config.get('wan_protocol', 'dhcp')}")
        print(f"  - LAN Protocol: {net_config.get('lan_protocol', 'static')}")
        
        print(f"\nCommands that would be executed:")
        print("-" * 50)
        
        # Network configuration commands for OpenWrt/LEDE with improved error handling
        network_commands = [
            # Configure WAN interface with error handling
            f"uci set network.wan.proto='{net_config.get('wan_protocol', 'dhcp')}' 2>/dev/null || echo 'WAN protocol already set or not available'",
            f"uci set network.wan.ifname={net_config.get('wan_interface', 'eth0')} 2>/dev/null || echo 'WAN interface already set'",
            "uci set network.wan.mtu=1500 2>/dev/null || echo 'WAN MTU already set'",
            
            # Configure LAN interface with error handling
            f"uci set network.lan.proto='{net_config.get('lan_protocol', 'static')}' 2>/dev/null || echo 'LAN protocol already set'",
            f"uci set network.lan.ipaddr={net_config.get('lan_ip', '192.168.1.1')} 2>/dev/null || echo 'LAN IP already set'",
            f"uci set network.lan.netmask={net_config.get('lan_netmask', '255.255.255.0')} 2>/dev/null || echo 'LAN netmask already set'",
            f"uci set network.lan.ifname={net_config.get('lan_interface', 'eth1')} 2>/dev/null || echo 'LAN interface already set'",
            
            # Apply network configuration with error handling
            "uci commit network 2>/dev/null || echo 'Network commit failed or no changes'",
            
            # Reload network configuration with fallback to restart
            "/etc/init.d/network reload 2>/dev/null || /etc/init.d/network restart 2>/dev/null || echo 'Network service restart failed'"
        ]
        
        for i, cmd in enumerate(network_commands, 1):
            print(f"  {i:2d}. {cmd}")
        
        print(f"\nWorkflow:")
        print("  1. Connect to 192.168.1.1 via SSH")
        print("  2. Create backup of /etc/config")
        print("  3. Execute the above UCI commands")
        print("  4. Reboot device")
        print("  5. Wait for device to come back online")
        print("  6. Reconnect and deploy infrastructure")
        
        print(f"\nTo test on a real device:")
        print("  python3 loranet_deployment_bot.py --network-config-only")
        print("  # or")
        print("  python3 loranet_deployment_bot.py --server-only")
        
        print("=" * 80)

    def install_curl(self, ssh, ip: str) -> bool:
        """Install curl on the device using SSH connection and verify it works"""
        self.log(f"Checking curl availability on {ip}")
        
        # First check if curl is already available
        check_cmd = "which curl && curl --version"
        stdin, stdout, stderr = ssh.exec_command(check_cmd)
        check_exit_status = stdout.channel.recv_exit_status()
        
        if check_exit_status == 0:
            self.log(f"curl is already available on {ip}", "SUCCESS")
            return True
        
        self.log(f"curl not found on {ip}, attempting installation")
        
        # Try apt package manager first
        curl_install_cmd = "sudo apt update && sudo apt install -y curl"
        stdin, stdout, stderr = ssh.exec_command(curl_install_cmd)
        curl_exit_status = stdout.channel.recv_exit_status()
        
        # Wait for curl installation to complete
        time.sleep(5)
        
        if curl_exit_status == 0:
            # Verify curl installation
            verify_cmd = "curl --version"
            stdin, stdout, stderr = ssh.exec_command(verify_cmd)
            verify_exit_status = stdout.channel.recv_exit_status()
            
            if verify_exit_status == 0:
                self.log(f"curl installation successful on {ip}", "SUCCESS")
                time.sleep(2)
                return True
            else:
                self.log(f"curl installation failed verification on {ip}", "WARNING")
        else:
            self.log(f"apt installation failed on {ip}, trying opkg", "WARNING")
        
        # Try opkg package manager as fallback
        curl_install_cmd = "opkg update && opkg install curl"
        stdin, stdout, stderr = ssh.exec_command(curl_install_cmd)
        curl_exit_status = stdout.channel.recv_exit_status()
        
        # Wait for curl installation to complete
        time.sleep(5)
        
        if curl_exit_status == 0:
            # Verify curl installation
            verify_cmd = "curl --version"
            stdin, stdout, stderr = ssh.exec_command(verify_cmd)
            verify_exit_status = stdout.channel.recv_exit_status()
            
            if verify_exit_status == 0:
                self.log(f"curl installation successful with opkg on {ip}", "SUCCESS")
                time.sleep(2)
                return True
            else:
                self.log(f"curl installation failed verification with opkg on {ip}", "ERROR")
        else:
            self.log(f"opkg installation also failed on {ip}", "ERROR")
        
        self.log(f"All curl installation methods failed on {ip}", "ERROR")
        return False

    def deploy_to_device(self, device: Dict) -> bool:
        """Deploy infrastructure to a single device with network configuration"""
        ip = device['ip']
        username = device['username']
        password = device['password']
        
        self.log(f"Starting deployment to {ip}")
        
        try:
            # Create SSH connection
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(ip, username=username, password=password, timeout=self.config['ssh_timeout'])
            
            # Create backup if enabled
            if self.config['backup_before_deploy']:
                self.log(f"Creating backup for {ip}")
                backup_cmd = "mkdir -p /tmp/backup && cp -r /etc/config /tmp/backup/ 2>/dev/null || true"
                stdin, stdout, stderr = ssh.exec_command(backup_cmd)
                stdout.channel.recv_exit_status()
            
            # Check if device requires network configuration
            if self.device_requires_network_config(ip):
                # Step 1: Configure network settings
                self.log(f"Step 1: Configuring network settings on {ip}")
                network_success = self.configure_network_settings(ssh, ip)
                
                if not network_success:
                    self.log(f"Network configuration failed on {ip}", "ERROR")
                    ssh.close()
                    device['status'] = 'network_config_failed'
                    return False
                
                # Step 2: Reboot device to apply network changes
                self.log(f"Step 2: Rebooting {ip} to apply network configuration")
                reboot_success = self.reboot_device(ssh, ip)
                
                # Close SSH connection before reboot
                ssh.close()
                
                if not reboot_success:
                    self.log(f"Reboot command failed on {ip}", "ERROR")
                    device['status'] = 'reboot_failed'
                    return False
                
                # Step 3: Wait for device to come back online
                self.log(f"Step 3: Waiting for {ip} to come back online")
                online_success = self.wait_for_device_reboot(ip)
                
                if not online_success:
                    self.log(f"Device {ip} did not come back online after reboot", "ERROR")
                    device['status'] = 'reboot_timeout'
                    return False
                
                # Step 4: Reconnect and deploy infrastructure
                self.log(f"Step 4: Deploying infrastructure to {ip}")
                
                # Wait a bit more for SSH to be ready
                ssh_delay = self.config.get('network_configuration', {}).get('ssh_ready_delay', 30)
                time.sleep(ssh_delay)
                
                # Reconnect via SSH
                ssh = paramiko.SSHClient()
                ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
                ssh.connect(ip, username=username, password=password, timeout=self.config['ssh_timeout'])
                
                # Wait for SSH connection to stabilize
                self.log(f"SSH connection established to {ip}, waiting 3 seconds for stability")
                time.sleep(3)
            else:
                self.log(f"Device {ip} does not require network configuration, proceeding with deployment")
            
            # Install curl if not available
            if not self.install_curl(ssh, ip):
                self.log(f"curl installation failed on {ip}, cannot proceed with deployment", "ERROR")
                device['status'] = 'curl_install_failed'
                ssh.close()
                return False
            
            # Wait before starting deployment
            self.log(f"Waiting 5 seconds before starting deployment on {ip}")
            time.sleep(5)
            
            # Deploy with auto mode (always use --auto flag)
            deploy_cmd = "curl -sSL https://raw.githubusercontent.com/Loranet-Technologies/bivicom-radar/main/install.sh | bash -s -- --auto"
            
            self.log(f"Executing deployment command on {ip}")
            stdin, stdout, stderr = ssh.exec_command(deploy_cmd)
            
            # Monitor deployment progress
            deployment_success = self.monitor_deployment(ssh, stdout, stderr, ip)
            
            # Final verification: Check if curl is still working
            if deployment_success:
                self.log(f"Verifying curl functionality after deployment on {ip}")
                verify_cmd = "curl --version"
                stdin, stdout, stderr = ssh.exec_command(verify_cmd)
                verify_exit_status = stdout.channel.recv_exit_status()
                
                if verify_exit_status == 0:
                    self.log(f"curl verification successful on {ip}", "SUCCESS")
                else:
                    self.log(f"curl verification failed on {ip}", "WARNING")
                    deployment_success = False
            
            # Wait before closing SSH connection
            self.log(f"Deployment monitoring completed for {ip}, waiting 2 seconds before cleanup")
            time.sleep(2)
            
            ssh.close()
            
            if deployment_success:
                self.log(f"Deployment to {ip} completed successfully", "SUCCESS")
                device['status'] = 'deployed'
                return True
            else:
                self.log(f"Deployment to {ip} failed", "ERROR")
                device['status'] = 'deployment_failed'
                return False
                
        except Exception as e:
            self.log(f"Deployment to {ip} failed with error: {e}", "ERROR")
            device['status'] = 'error'
            return False

    def monitor_deployment(self, ssh, stdout, stderr, ip: str) -> bool:
        """Monitor deployment progress and return success status"""
        self.log(f"Monitoring deployment on {ip}")
        
        start_time = time.time()
        timeout = 1800  # 30 minutes timeout
        
        try:
            while True:
                if time.time() - start_time > timeout:
                    self.log(f"Deployment timeout on {ip}", "ERROR")
                    return False
                
                # Check if process is still running
                if stdout.channel.exit_status_ready():
                    exit_status = stdout.channel.recv_exit_status()
                    if exit_status == 0:
                        self.log(f"Deployment completed successfully on {ip}", "SUCCESS")
                        return True
                    else:
                        self.log(f"Deployment failed on {ip} with exit code {exit_status}", "ERROR")
                        return False
                
                # Read output
                if stdout.channel.recv_ready():
                    output = stdout.channel.recv(1024).decode('utf-8')
                    if output.strip():
                        self.log(f"[{ip}] {output.strip()}")
                
                # Check for errors
                if stderr.channel.recv_ready():
                    error = stderr.channel.recv(1024).decode('utf-8')
                    if error.strip():
                        self.log(f"[{ip}] ERROR: {error.strip()}", "ERROR")
                
                time.sleep(1)
                
        except Exception as e:
            self.log(f"Error monitoring deployment on {ip}: {e}", "ERROR")
            return False

    def verify_deployment(self, device: Dict) -> bool:
        """Verify that deployment was successful"""
        if not self.config['verify_deployment']:
            return True
            
        ip = device['ip']
        username = device['username']
        password = device['password']
        
        self.log(f"Verifying deployment on {ip}")
        
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(ip, username=username, password=password, timeout=self.config['ssh_timeout'])
            
            # Check if services are running
            checks = [
                ("Node-RED", "systemctl is-active nodered"),
                ("Docker", "systemctl is-active docker"),
                ("Tailscale", "systemctl is-active tailscaled")
            ]
            
            all_services_running = True
            for service_name, check_cmd in checks:
                stdin, stdout, stderr = ssh.exec_command(check_cmd)
                exit_status = stdout.channel.recv_exit_status()
                
                if exit_status == 0:
                    self.log(f"[{ip}] {service_name} is running", "SUCCESS")
                else:
                    self.log(f"[{ip}] {service_name} is not running", "WARNING")
                    all_services_running = False
            
            ssh.close()
            return all_services_running
            
        except Exception as e:
            self.log(f"Verification failed for {ip}: {e}", "ERROR")
            return False

    def deploy_all(self) -> Dict:
        """Deploy to all discovered devices"""
        self.log("Starting deployment to all devices")
        
        results = {
            'total': len(self.discovered_devices),
            'successful': 0,
            'failed': 0,
            'devices': []
        }
        
        for device in self.discovered_devices:
            success = self.deploy_to_device(device)
            
            if success:
                results['successful'] += 1
                # Verify deployment if enabled
                if self.config['verify_deployment']:
                    if self.verify_deployment(device):
                        device['verified'] = True
                    else:
                        device['verified'] = False
            else:
                results['failed'] += 1
            
            results['devices'].append(device)
        
        self.log(f"Deployment completed. Success: {results['successful']}, Failed: {results['failed']}")
        return results

    def generate_report(self, results: Dict) -> str:
        """Generate deployment report"""
        report = f"""
Loranet Deployment Bot Report
============================
Date: {time.strftime('%Y-%m-%d %H:%M:%S')}
Total Devices: {results['total']}
Successful Deployments: {results['successful']}
Failed Deployments: {results['failed']}

Device Details:
"""
        
        for device in results['devices']:
            report += f"""
IP: {device['ip']}
MAC: {device['mac']}
Status: {device['status']}
Verified: {device.get('verified', 'N/A')}
"""
        
        return report

    def deploy_to_server_only(self, network_config_only: bool = False) -> bool:
        """Deploy specifically to the server at 192.168.1.1"""
        server_ip = "192.168.1.1"
        username = self.config['default_credentials']['username']
        password = self.config['default_credentials']['password']
        
        self.log(f"Starting server deployment to {server_ip}")
        
        # Create device info for server
        device = {
            'ip': server_ip,
            'mac': 'unknown',  # Will be determined during discovery if needed
            'username': username,
            'password': password,
            'status': 'pending',
            'authorized': True
        }
        
        try:
            # Create SSH connection
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(server_ip, username=username, password=password, timeout=self.config['ssh_timeout'])
            
            # Create backup if enabled
            if self.config['backup_before_deploy']:
                self.log(f"Creating backup for {server_ip}")
                backup_cmd = "mkdir -p /tmp/backup && cp -r /etc/config /tmp/backup/ 2>/dev/null || true"
                stdin, stdout, stderr = ssh.exec_command(backup_cmd)
                stdout.channel.recv_exit_status()
            
            # Step 1: Configure network settings
            self.log(f"Step 1: Configuring network settings on {server_ip}")
            network_success = self.configure_network_settings(ssh, server_ip)
            
            if not network_success:
                self.log(f"Network configuration failed on {server_ip}", "ERROR")
                ssh.close()
                return False
            
            # Step 2: Reboot device to apply network changes
            self.log(f"Step 2: Rebooting {server_ip} to apply network configuration")
            reboot_success = self.reboot_device(ssh, server_ip)
            
            # Close SSH connection before reboot
            ssh.close()
            
            if not reboot_success:
                self.log(f"Reboot command failed on {server_ip}", "ERROR")
                return False
            
            # Step 3: Wait for device to come back online
            self.log(f"Step 3: Waiting for {server_ip} to come back online")
            online_success = self.wait_for_device_reboot(server_ip)
            
            if not online_success:
                self.log(f"Device {server_ip} did not come back online after reboot", "ERROR")
                return False
            
            if network_config_only:
                self.log(f"Network configuration and reboot completed for {server_ip}", "SUCCESS")
                return True
            
            # Step 4: Reconnect and deploy infrastructure
            self.log(f"Step 4: Deploying infrastructure to {server_ip}")
            
            # Wait a bit more for SSH to be ready
            ssh_delay = self.config.get('network_configuration', {}).get('ssh_ready_delay', 30)
            time.sleep(ssh_delay)
            
            # Reconnect via SSH
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(server_ip, username=username, password=password, timeout=self.config['ssh_timeout'])
            
            # Wait for SSH connection to stabilize
            self.log(f"SSH connection established to {server_ip}, waiting 3 seconds for stability")
            time.sleep(3)
            
            # Install curl if not available
            if not self.install_curl(ssh, server_ip):
                self.log(f"curl installation failed on {server_ip}, cannot proceed with deployment", "ERROR")
                ssh.close()
                return False
            
            # Wait before starting deployment
            self.log(f"Waiting 5 seconds before starting deployment on {server_ip}")
            time.sleep(5)
            
            # Deploy with auto mode (always use --auto flag)
            deploy_cmd = "curl -sSL https://raw.githubusercontent.com/Loranet-Technologies/bivicom-radar/main/install.sh | bash -s -- --auto"
            
            self.log(f"Executing deployment command on {server_ip}")
            stdin, stdout, stderr = ssh.exec_command(deploy_cmd)
            
            # Monitor deployment progress
            deployment_success = self.monitor_deployment(ssh, stdout, stderr, server_ip)
            
            # Final verification: Check if curl is still working
            if deployment_success:
                self.log(f"Verifying curl functionality after deployment on {server_ip}")
                verify_cmd = "curl --version"
                stdin, stdout, stderr = ssh.exec_command(verify_cmd)
                verify_exit_status = stdout.channel.recv_exit_status()
                
                if verify_exit_status == 0:
                    self.log(f"curl verification successful on {server_ip}", "SUCCESS")
                else:
                    self.log(f"curl verification failed on {server_ip}", "WARNING")
                    deployment_success = False
            
            # Wait before closing SSH connection
            self.log(f"Deployment monitoring completed for {server_ip}, waiting 2 seconds before cleanup")
            time.sleep(2)
            
            ssh.close()
            
            if deployment_success:
                self.log(f"Deployment to {server_ip} completed successfully", "SUCCESS")
                return True
            else:
                self.log(f"Deployment to {server_ip} failed", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Deployment to {server_ip} failed with error: {e}", "ERROR")
            return False

    def run(self):
        """Main execution function"""
        self.log("Loranet Deployment Bot started")
        
        # Discover devices
        devices = self.discover_devices()
        
        if not devices:
            self.log("No target devices found. Exiting.", "WARNING")
            return
        
        # Confirm deployment
        if self.config['deployment_mode'] != 'auto':
            print(f"\nFound {len(devices)} target devices:")
            for device in devices:
                print(f"  - {device['ip']} (MAC: {device['mac']})")
            
            confirm = input("\nProceed with deployment? (y/N): ").strip().lower()
            if confirm != 'y':
                self.log("Deployment cancelled by user")
                return
        
        # Deploy to all devices
        results = self.deploy_all()
        
        # Generate and save report
        report = self.generate_report(results)
        report_file = f"deployment_report_{int(time.time())}.txt"
        
        try:
            with open(report_file, 'w') as f:
                f.write(report)
            self.log(f"Deployment report saved to {report_file}")
        except Exception as e:
            self.log(f"Failed to save report: {e}", "ERROR")
        
        print(report)


class ScriptNo3:
    """Script No. 3: Loranet Infrastructure Deployment Bot"""
    
    def __init__(self, config_file: str = "bot_config.json"):
        self.bot = LoranetDeploymentBot(config_file)
    
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    
    def run_full_deployment(self):
        """Run full infrastructure deployment"""
        self.log("=" * 60)
        self.log("SCRIPT NO. 3: FULL INFRASTRUCTURE DEPLOYMENT")
        self.log("=" * 60)
        
        self.bot.run()

def main():
    """Main function - runs full infrastructure deployment"""
    print("Script No. 3: Loranet Infrastructure Deployment Bot")
    print("=" * 60)
    print("This script will:")
    print("1. Discover devices on the network")
    print("2. Identify authorized Bivicom devices")
    print("3. Deploy infrastructure to discovered devices")
    print("4. Install Bivicom Radar system")
    print()
    
    # Initialize script
    script = ScriptNo3()
    
    # Run full deployment
    script.run_full_deployment()


if __name__ == "__main__":
    main()
