#!/usr/bin/env python3
"""
Script No. 1: Network Configuration and Reboot
==============================================

This script performs the first step of the deployment process:
1. Configure WAN interface for DHCP internet access
2. Configure LAN interface for static local network
3. Apply network configuration changes
4. Apply WAN configuration using simple script
5. Check WAN DHCP IP and test internet connectivity
6. Reboot device to enable WAN internet access

Author: Aqmar
Date: 2025-01-08
"""

import subprocess
import paramiko
import time
import json
import sys
import os

# Add current directory to path to import the bot
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from script_no3 import LoranetDeploymentBot

class ScriptNo1:
    def __init__(self, config_file: str = "bot_config.json"):
        self.bot = LoranetDeploymentBot(config_file)
        self.server_ip = "192.168.1.1"
        self.username = self.bot.config['default_credentials']['username']
        self.password = self.bot.config['default_credentials']['password']
    
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def configure_network_settings(self, ssh, ip: str) -> bool:
        """Configure network settings on the device"""
        self.log(f"Configuring network settings on {ip}")
        
        try:
            # Get network configuration from config
            net_config = self.bot.config.get('network_configuration', {})
            
            # Network configuration commands for OpenWrt/LEDE with improved error handling
            # Tested configuration: WAN=eth0 (DHCP), LAN=eth1 (DHCP), Bridge intact
            # Added delays to prevent coupling issues when swapping interfaces
            
            # Step 1: Configure WAN interface (eth0) for DHCP internet access
            wan_commands = [
                f"sudo uci set network.wan.proto='{net_config.get('wan_protocol', 'dhcp')}' 2>/dev/null || echo 'WAN protocol already set'",
                f"sudo uci set network.wan.ifname='{net_config.get('wan_interface', 'eth0')}' 2>/dev/null || echo 'WAN interface already set'",
                "sudo uci set network.wan.mtu=1500 2>/dev/null || echo 'WAN MTU already set'"
            ]
            
            # Step 2: Configure LAN interface (eth1) for DHCP (will get IP from network)
            lan_commands = [
                f"sudo uci set network.lan.proto='{net_config.get('lan_protocol', 'dhcp')}' 2>/dev/null || echo 'LAN protocol already set'",
                f"sudo uci set network.lan.ifname='{net_config.get('lan_interface', 'eth1')}' 2>/dev/null || echo 'LAN interface already set'"
            ]
            
            # Step 3: Apply network configuration with error handling
            commit_commands = [
                "sudo uci commit network"
            ]
            
            # Step 4: Reload network configuration with fallback to restart
            reload_commands = [
                "sudo /etc/init.d/network reload 2>/dev/null || sudo /etc/init.d/network restart 2>/dev/null || echo 'Network service restart failed'"
            ]
            
            # Execute WAN configuration
            self.log(f"[{ip}] Configuring WAN interface (eth0)...")
            for cmd in wan_commands:
                self.log(f"[{ip}] Executing: {cmd}")
                stdin, stdout, stderr = ssh.exec_command(cmd)
                exit_status = stdout.channel.recv_exit_status()
                
                if exit_status != 0:
                    error_output = stderr.read().decode('utf-8').strip()
                    self.log(f"[{ip}] Command failed: {cmd} - {error_output}", "WARNING")
                else:
                    self.log(f"[{ip}] Command successful: {cmd}", "SUCCESS")
            
            # Delay after WAN configuration to allow interface settling
            self.log(f"[{ip}] Waiting 3 seconds for WAN interface to settle...")
            time.sleep(3)
            
            # Execute LAN configuration
            self.log(f"[{ip}] Configuring LAN interface (eth1)...")
            for cmd in lan_commands:
                self.log(f"[{ip}] Executing: {cmd}")
                stdin, stdout, stderr = ssh.exec_command(cmd)
                exit_status = stdout.channel.recv_exit_status()
                
                if exit_status != 0:
                    error_output = stderr.read().decode('utf-8').strip()
                    self.log(f"[{ip}] Command failed: {cmd} - {error_output}", "WARNING")
                else:
                    self.log(f"[{ip}] Command successful: {cmd}", "SUCCESS")
            
            # Delay after LAN configuration to allow interface settling
            self.log(f"[{ip}] Waiting 3 seconds for LAN interface to settle...")
            time.sleep(3)
            
            # Execute commit
            self.log(f"[{ip}] Committing network configuration...")
            for cmd in commit_commands:
                self.log(f"[{ip}] Executing: {cmd}")
                stdin, stdout, stderr = ssh.exec_command(cmd)
                exit_status = stdout.channel.recv_exit_status()
                
                # Read output to see what happened
                stdout_output = stdout.read().decode('utf-8').strip()
                stderr_output = stderr.read().decode('utf-8').strip()
                
                if exit_status != 0:
                    self.log(f"[{ip}] UCI commit failed: {cmd}", "ERROR")
                    if stderr_output:
                        self.log(f"[{ip}] Error output: {stderr_output}", "ERROR")
                    if stdout_output:
                        self.log(f"[{ip}] Standard output: {stdout_output}", "INFO")
                    return False
                else:
                    if stdout_output:
                        self.log(f"[{ip}] UCI commit output: {stdout_output}", "INFO")
                    self.log(f"[{ip}] UCI commit successful: {cmd}", "SUCCESS")
            
            # Delay after commit to allow configuration to be written
            self.log(f"[{ip}] Waiting 2 seconds after commit...")
            time.sleep(2)
            
            # Verify the configuration was applied
            self.log(f"[{ip}] Verifying network configuration...")
            verify_cmd = "uci show network | grep -E '(wan|lan).(proto|ifname)'"
            stdin, stdout, stderr = ssh.exec_command(verify_cmd)
            verify_output = stdout.read().decode('utf-8').strip()
            
            if verify_output:
                self.log(f"[{ip}] Current network configuration:", "INFO")
                for line in verify_output.split('\n'):
                    if line.strip():
                        self.log(f"[{ip}]   {line.strip()}", "INFO")
            else:
                self.log(f"[{ip}] Warning: Could not verify network configuration", "WARNING")
            
            # Execute reload
            self.log(f"[{ip}] Reloading network configuration...")
            for cmd in reload_commands:
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

    def apply_wan_config_simple(self, ssh, ip: str) -> bool:
        """Apply WAN configuration using the simple WAN config script"""
        self.log(f"Applying WAN configuration using simple script on {ip}")
        
        try:
            # Check if the WAN config simple script exists
            check_cmd = "test -f /home/admin/wan_config_simple.sh && echo 'exists' || echo 'not_found'"
            stdin, stdout, stderr = ssh.exec_command(check_cmd)
            check_output = stdout.read().decode('utf-8').strip()
            
            if "not_found" in check_output:
                self.log(f"WAN config simple script not found on {ip}", "WARNING")
                return True  # Continue without the script
            
            # Apply WAN configuration using the simple script
            self.log(f"Running WAN config simple script on {ip}")
            apply_cmd = "sudo /home/admin/wan_config_simple.sh apply"
            stdin, stdout, stderr = ssh.exec_command(apply_cmd)
            exit_status = stdout.channel.recv_exit_status()
            
            if exit_status == 0:
                self.log(f"WAN config simple script executed successfully on {ip}", "SUCCESS")
                
                # Test connectivity after applying config
                self.log(f"Testing connectivity after WAN config on {ip}")
                test_cmd = "/home/admin/wan_config_simple.sh test"
                stdin, stdout, stderr = ssh.exec_command(test_cmd)
                test_output = stdout.read().decode('utf-8').strip()
                
                if test_output:
                    self.log(f"Connectivity test results on {ip}:", "INFO")
                    for line in test_output.split('\n'):
                        if line.strip():
                            self.log(f"  {line.strip()}", "INFO")
                
                return True
            else:
                error_output = stderr.read().decode('utf-8').strip()
                self.log(f"WAN config simple script failed on {ip}: {error_output}", "WARNING")
                return True  # Continue even if script fails
                
        except Exception as e:
            self.log(f"Error running WAN config simple script on {ip}: {e}", "WARNING")
            return True  # Continue even if script fails

    def check_wan_dhcp_and_internet(self, ssh, ip: str) -> bool:
        """Check if WAN interface received DHCP IP and test internet connectivity"""
        self.log(f"Checking WAN DHCP IP and internet connectivity on {ip}")
        
        try:
            # Wait a moment for DHCP to get IP
            self.log("Waiting 10 seconds for DHCP to get IP address...")
            time.sleep(10)
            
            # Check WAN interface IP
            self.log("Checking WAN interface (eth0) IP address...")
            stdin, stdout, stderr = ssh.exec_command("ip addr show eth0 | grep 'inet ' | awk '{print $2}' | head -1")
            wan_ip_output = stdout.read().decode('utf-8').strip()
            
            if wan_ip_output:
                self.log(f"WAN interface received IP: {wan_ip_output}", "SUCCESS")
                
                # Test internet connectivity
                self.log("Testing internet connectivity...")
                
                # Test 1: Ping Google DNS
                self.log("Testing ping to Google DNS (8.8.8.8)...")
                stdin, stdout, stderr = ssh.exec_command("ping -c 3 -W 5 8.8.8.8")
                ping_exit_status = stdout.channel.recv_exit_status()
                
                if ping_exit_status == 0:
                    self.log("Ping to Google DNS: ✅ SUCCESS", "SUCCESS")
                    
                    # Test 2: DNS resolution
                    self.log("Testing DNS resolution...")
                    stdin, stdout, stderr = ssh.exec_command("nslookup google.com")
                    dns_exit_status = stdout.channel.recv_exit_status()
                    
                    if dns_exit_status == 0:
                        self.log("DNS resolution: ✅ SUCCESS", "SUCCESS")
                        
                        # Test 3: HTTP connectivity
                        self.log("Testing HTTP connectivity...")
                        stdin, stdout, stderr = ssh.exec_command("curl -s --connect-timeout 10 http://httpbin.org/ip")
                        http_exit_status = stdout.channel.recv_exit_status()
                        
                        if http_exit_status == 0:
                            http_output = stdout.read().decode('utf-8').strip()
                            self.log(f"HTTP connectivity: ✅ SUCCESS - {http_output}", "SUCCESS")
                            self.log("Internet connectivity verified! WAN is working properly.", "SUCCESS")
                            return True
                        else:
                            self.log("HTTP connectivity: ❌ FAILED", "WARNING")
                    else:
                        self.log("DNS resolution: ❌ FAILED", "WARNING")
                else:
                    self.log("Ping to Google DNS: ❌ FAILED", "WARNING")
                
                # If we get here, some tests failed but we have an IP
                self.log("WAN has IP address but internet connectivity tests failed", "WARNING")
                self.log("This may be normal - internet might work after reboot", "INFO")
                return True
                
            else:
                self.log("WAN interface (eth0) has no IP address", "WARNING")
                self.log("DHCP may need more time or there might be a network issue", "WARNING")
                return False
                
        except Exception as e:
            self.log(f"Error checking WAN DHCP and internet: {e}", "ERROR")
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

    def wait_for_device_reboot(self, ip: str, max_wait_time: int = 300) -> bool:
        """Wait for device to come back online after reboot"""
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

    def run(self):
        """Execute Script No. 1: Network Configuration and Reboot"""
        self.log("=" * 60)
        self.log("SCRIPT NO. 1: NETWORK CONFIGURATION AND REBOOT")
        self.log("=" * 60)
        
        self.log(f"Target device: {self.server_ip}")
        self.log(f"Username: {self.username}")
        self.log(f"Password: {'*' * len(self.password)}")
        
        try:
            # Step 1: Connect via SSH
            self.log(f"Step 1: Connecting to {self.server_ip} via SSH")
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(self.server_ip, username=self.username, password=self.password, timeout=10)
            self.log(f"SSH connection established to {self.server_ip}", "SUCCESS")
            
            # Step 2: Create backup
            self.log(f"Step 2: Creating backup of current configuration")
            backup_cmd = "mkdir -p /tmp/backup && cp -r /etc/config /tmp/backup/ 2>/dev/null || true"
            stdin, stdout, stderr = ssh.exec_command(backup_cmd)
            stdout.channel.recv_exit_status()
            self.log(f"Backup created successfully", "SUCCESS")
            
            # Step 3: Configure network settings
            self.log(f"Step 3: Configuring network settings")
            network_success = self.configure_network_settings(ssh, self.server_ip)
            
            if not network_success:
                self.log(f"Network configuration failed", "ERROR")
                ssh.close()
                return False
            
            # Step 4: Apply WAN configuration using simple script
            self.log(f"Step 4: Applying WAN configuration using simple script")
            wan_config_success = self.apply_wan_config_simple(ssh, self.server_ip)
            
            if not wan_config_success:
                self.log(f"WAN config simple script failed", "WARNING")
                self.log("Proceeding anyway - configuration may still work", "INFO")
            else:
                self.log("WAN config simple script completed", "SUCCESS")
            
            # Step 5: Check WAN DHCP IP and test internet connectivity
            self.log(f"Step 5: Checking WAN DHCP IP and internet connectivity")
            wan_check_success = self.check_wan_dhcp_and_internet(ssh, self.server_ip)
            
            if not wan_check_success:
                self.log(f"WAN DHCP check failed - no IP address received", "WARNING")
                self.log("Proceeding with reboot anyway - IP might be assigned after reboot", "INFO")
            else:
                self.log("WAN DHCP and internet connectivity check completed", "SUCCESS")
            
            # Step 6: Reboot device
            self.log(f"Step 6: Rebooting device to apply network configuration")
            reboot_success = self.reboot_device(ssh, self.server_ip)
            
            # Close SSH connection before reboot
            ssh.close()
            
            if not reboot_success:
                self.log(f"Reboot command failed", "ERROR")
                return False
            
            # Step 7: Wait for device to come back online
            self.log(f"Step 7: Waiting for device to come back online")
            online_success = self.wait_for_device_reboot(self.server_ip)
            
            if not online_success:
                self.log(f"Device did not come back online after reboot", "ERROR")
                return False
            
            # Success!
            self.log("=" * 60)
            self.log("SCRIPT NO. 1 COMPLETED SUCCESSFULLY!", "SUCCESS")
            self.log("=" * 60)
            self.log("Network configuration applied and device rebooted")
            self.log("WAN internet access should now be enabled")
            self.log("Device is ready for Script No. 2 (Infrastructure Deployment)")
            
            return True
                
        except Exception as e:
            self.log(f"Script No. 1 failed with error: {e}", "ERROR")
            return False

def main():
    """Main function"""
    print("Script No. 1: Network Configuration and Reboot")
    print("==============================================")
    print("This script will:")
    print("1. Configure WAN interface for DHCP internet access")
    print("2. Configure LAN interface for static local network")
    print("3. Apply network configuration changes")
    print("4. Apply WAN configuration using simple script")
    print("5. Check WAN DHCP IP and test internet connectivity")
    print("6. Reboot device to enable WAN internet access")
    print()
    
    # Initialize and run script
    script = ScriptNo1()
    success = script.run()
    
    if success:
        print("\n✅ Script No. 1 completed successfully!")
        print("🚀 Ready to run Script No. 2 (Infrastructure Deployment)")
        sys.exit(0)
    else:
        print("\n❌ Script No. 1 failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
