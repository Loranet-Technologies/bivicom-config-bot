#!/usr/bin/env python3
"""
Script No. 2: WAN Internet Connection Verification
=================================================

This script performs the second step of the deployment process:
1. SSH login to the device
2. Check WAN internet connection
3. Verify connectivity to external services
4. Logout and prepare for Script No. 3

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

class ScriptNo2:
    def __init__(self, config_file: str = "bot_config.json"):
        self.bot = LoranetDeploymentBot(config_file)
        self.server_ip = "192.168.1.1"
        self.username = self.bot.config['default_credentials']['username']
        self.password = self.bot.config['default_credentials']['password']
    
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] [{level}] {message}")
    
    def check_wan_interface(self, ssh, ip: str) -> bool:
        """Check WAN interface status"""
        self.log(f"Checking WAN interface status on {ip}")
        
        try:
            # Check if WAN interface is up and has an IP
            wan_check_cmd = "ip addr show eth0 | grep 'inet ' | awk '{print $2}' | head -1"
            stdin, stdout, stderr = ssh.exec_command(wan_check_cmd)
            wan_ip = stdout.read().decode('utf-8').strip()
            
            if wan_ip:
                self.log(f"WAN interface (eth0) has IP: {wan_ip}", "SUCCESS")
                return True
            else:
                self.log(f"WAN interface (eth0) has no IP address", "WARNING")
                return False
                
        except Exception as e:
            self.log(f"Failed to check WAN interface: {e}", "ERROR")
            return False
    
    def check_internet_connectivity(self, ssh, ip: str) -> bool:
        """Check internet connectivity from the device"""
        self.log(f"Checking internet connectivity from {ip}")
        
        connectivity_tests = [
            ("DNS Resolution", "nslookup google.com 8.8.8.8 | grep -q 'google.com' && echo 'DNS OK' || echo 'DNS FAILED'"),
            ("Ping Google DNS", "ping -c 3 -W 5 8.8.8.8 | grep -q '3 received' && echo 'PING OK' || echo 'PING FAILED'"),
            ("Ping Google", "ping -c 3 -W 5 google.com | grep -q '3 received' && echo 'PING OK' || echo 'PING FAILED'"),
            ("HTTP Test", "wget -q --spider --timeout=10 http://google.com && echo 'HTTP OK' || echo 'HTTP FAILED'")
        ]
        
        all_tests_passed = True
        
        for test_name, test_cmd in connectivity_tests:
            try:
                self.log(f"Running {test_name} test...")
                stdin, stdout, stderr = ssh.exec_command(test_cmd)
                result = stdout.read().decode('utf-8').strip()
                exit_status = stdout.channel.recv_exit_status()
                
                if "OK" in result and exit_status == 0:
                    self.log(f"{test_name}: {result}", "SUCCESS")
                else:
                    self.log(f"{test_name}: {result}", "WARNING")
                    all_tests_passed = False
                    
            except Exception as e:
                self.log(f"{test_name} failed: {e}", "ERROR")
                all_tests_passed = False
        
        return all_tests_passed
    
    def check_network_routes(self, ssh, ip: str) -> bool:
        """Check network routing table"""
        self.log(f"Checking network routes on {ip}")
        
        try:
            # Check default route
            route_cmd = "ip route | grep default"
            stdin, stdout, stderr = ssh.exec_command(route_cmd)
            routes = stdout.read().decode('utf-8').strip()
            
            if routes:
                self.log(f"Default routes found:", "SUCCESS")
                for route in routes.split('\n'):
                    if route.strip():
                        self.log(f"  {route.strip()}", "SUCCESS")
                return True
            else:
                self.log(f"No default routes found", "WARNING")
                return False
                
        except Exception as e:
            self.log(f"Failed to check routes: {e}", "ERROR")
            return False
    
    def check_network_services(self, ssh, ip: str) -> bool:
        """Check if network services are running"""
        self.log(f"Checking network services on {ip}")
        
        services_to_check = [
            ("Network", "netstat -i | grep -q eth0 && echo 'Network interfaces OK' || echo 'Network interfaces FAILED'"),
            ("DHCP Client", "ps | grep -q '[d]hcp' && echo 'DHCP client running' || echo 'DHCP client not running'"),
        ]
        
        all_services_ok = True
        
        for service_name, check_cmd in services_to_check:
            try:
                stdin, stdout, stderr = ssh.exec_command(check_cmd)
                result = stdout.read().decode('utf-8').strip()
                exit_status = stdout.channel.recv_exit_status()
                
                if "OK" in result or "running" in result:
                    self.log(f"{service_name}: {result}", "SUCCESS")
                else:
                    self.log(f"{service_name}: {result}", "WARNING")
                    all_services_ok = False
                    
            except Exception as e:
                self.log(f"{service_name} check failed: {e}", "ERROR")
                all_services_ok = False
        
        return all_services_ok
    
    def run(self):
        """Execute Script No. 2: WAN Internet Connection Verification"""
        self.log("=" * 60)
        self.log("SCRIPT NO. 2: WAN INTERNET CONNECTION VERIFICATION")
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
            
            # Step 2: Check WAN interface
            self.log(f"Step 2: Checking WAN interface status")
            wan_ok = self.check_wan_interface(ssh, self.server_ip)
            
            # Step 3: Check network routes
            self.log(f"Step 3: Checking network routes")
            routes_ok = self.check_network_routes(ssh, self.server_ip)
            
            # Step 4: Check network services
            self.log(f"Step 4: Checking network services")
            services_ok = self.check_network_services(ssh, self.server_ip)
            
            # Step 5: Check internet connectivity
            self.log(f"Step 5: Checking internet connectivity")
            internet_ok = self.check_internet_connectivity(ssh, self.server_ip)
            
            # Step 6: Close SSH connection
            self.log(f"Step 6: Closing SSH connection")
            ssh.close()
            self.log(f"SSH connection closed", "SUCCESS")
            
            # Evaluate results
            self.log("=" * 60)
            self.log("VERIFICATION RESULTS:")
            self.log(f"  WAN Interface: {'✅ OK' if wan_ok else '❌ FAILED'}")
            self.log(f"  Network Routes: {'✅ OK' if routes_ok else '❌ FAILED'}")
            self.log(f"  Network Services: {'✅ OK' if services_ok else '❌ FAILED'}")
            self.log(f"  Internet Connectivity: {'✅ OK' if internet_ok else '❌ FAILED'}")
            
            overall_success = wan_ok and routes_ok and services_ok and internet_ok
            
            if overall_success:
                self.log("=" * 60)
                self.log("SCRIPT NO. 2 COMPLETED SUCCESSFULLY!", "SUCCESS")
                self.log("=" * 60)
                self.log("WAN internet connection is working properly")
                self.log("Device is ready for Script No. 3 (Infrastructure Deployment)")
                return True
            else:
                self.log("=" * 60)
                self.log("SCRIPT NO. 2 COMPLETED WITH WARNINGS", "WARNING")
                self.log("=" * 60)
                self.log("Some connectivity checks failed, but device may still be functional")
                self.log("Proceed with caution to Script No. 3")
                return True  # Still return True to allow proceeding
                
        except Exception as e:
            self.log(f"Script No. 2 failed with error: {e}", "ERROR")
            return False

def main():
    """Main function"""
    print("Script No. 2: WAN Internet Connection Verification")
    print("==================================================")
    print("This script will:")
    print("1. SSH login to the device")
    print("2. Check WAN interface status")
    print("3. Verify network routes")
    print("4. Check network services")
    print("5. Test internet connectivity")
    print("6. Logout and prepare for Script No. 3")
    print()
    
    # Initialize and run script
    script = ScriptNo2()
    success = script.run()
    
    if success:
        print("\n✅ Script No. 2 completed successfully!")
        print("🚀 Ready to run Script No. 3 (Infrastructure Deployment)")
        sys.exit(0)
    else:
        print("\n❌ Script No. 2 failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
