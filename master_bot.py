#!/usr/bin/env python3
"""
Master Bot: Orchestrates Script No. 1, 2, and 3
==============================================

This master bot:
1. Checks for IP 192.168.1.1
2. Tests SSH login with admin/admin
3. Checks for log files and creates if missing
4. Runs Script No. 1 (Network Configuration) - logs to log1.txt
5. Runs Script No. 2 (Connectivity Verification) - logs to log2.txt
6. Runs Script No. 3 (Infrastructure Deployment) - logs to log3.txt
7. Skips stages if log files already exist

Author: Aqmar
Date: 2025-01-08
"""

import subprocess
import paramiko
import time
import os
import sys
import signal
from datetime import datetime

class MasterBot:
    def __init__(self):
        self.target_ip = "192.168.1.1"
        self.username = "admin"
        self.password = "admin"
        self.device_mac = None
        self.log_file = None
        self.shutdown_requested = False
        self.cycle_count = 0
        self.delays = {
            "ip_check": 2,           # Delay after IP check
            "ssh_test": 3,           # Delay after SSH test
            "log_creation": 1,       # Delay after log creation
            "between_scripts": 5,    # Delay between scripts
            "script_completion": 2,  # Delay after script completion
            "final_success": 3,      # Delay before final success message
            "cycle_restart": 30      # Delay before restarting cycle
        }
        self.scripts = {
            "script_no1.py": "Network Configuration and Reboot",
            "script_no2.py": "WAN Internet Connectivity Verification",
            "script_no3.py": "Loranet Infrastructure Deployment Bot"
        }
        
        # Set up signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        signal_name = signal.Signals(signum).name
        self.log(f"Received {signal_name} signal. Initiating graceful shutdown...", "WARNING")
        self.shutdown_requested = True
    
    def get_mac_address(self, ip: str) -> str:
        """Get MAC address for the target IP"""
        try:
            # Try to get MAC from ARP table
            result = subprocess.run(['arp', '-n', ip], capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if ip in line:
                        # Parse ARP output: ? (192.168.1.1) at a0:19:b2:d2:7a:f9 on en5 ifscope [ethernet]
                        if ' at ' in line:
                            mac_part = line.split(' at ')[1].split(' on ')[0]
                            # Clean MAC address format
                            mac = mac_part.replace(':', '').replace('-', '').lower()
                            return mac
        except Exception as e:
            print(f"Failed to get MAC address: {e}")
        
        # Fallback to timestamp-based filename
        return "unknown"
    
    def create_log_filename(self) -> str:
        """Create log filename with MAC address and datetime"""
        if not self.device_mac:
            self.device_mac = self.get_mac_address(self.target_ip)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self.device_mac}_{timestamp}.log"
        return filename
    
    def delay(self, delay_type: str, custom_message: str = None):
        """Add delay with optional custom message, checking for shutdown requests"""
        delay_time = self.delays.get(delay_type, 1)
        
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
    
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp to the main log file"""
        if not self.log_file:
            self.log_file = self.create_log_filename()
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] [{level}] {message}\n"
        
        # Print to console
        print(f"[{timestamp}] [{level}] {message}")
        
        # Write to log file
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(log_entry)
        except Exception as e:
            print(f"Failed to write to {self.log_file}: {e}")
    
    def check_ip_availability(self) -> bool:
        """Check if target IP 192.168.1.1 is reachable"""
        self.log("Checking if target IP 192.168.1.1 is reachable...")
        
        try:
            result = subprocess.run(
                ['ping', '-c', '3', '-W', '2', self.target_ip],
                capture_output=True,
                timeout=10
            )
            
            if result.returncode == 0:
                self.log(f"Target IP {self.target_ip} is reachable", "SUCCESS")
                return True
            else:
                self.log(f"Target IP {self.target_ip} is not reachable", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"Error checking IP availability: {e}", "ERROR")
            return False
    
    def test_ssh_login(self) -> bool:
        """Test SSH login with admin/admin credentials"""
        self.log(f"Testing SSH login to {self.target_ip} with admin/admin...")
        
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                self.target_ip,
                username=self.username,
                password=self.password,
                timeout=10
            )
            
            # Test a simple command
            stdin, stdout, stderr = ssh.exec_command("echo 'SSH connection successful'")
            output = stdout.read().decode('utf-8').strip()
            
            ssh.close()
            
            if "SSH connection successful" in output:
                self.log(f"SSH login successful to {self.target_ip}", "SUCCESS")
                return True
            else:
                self.log(f"SSH login failed to {self.target_ip}", "ERROR")
                return False
                
        except Exception as e:
            self.log(f"SSH login failed: {e}", "ERROR")
            return False
    
    def create_log_file(self):
        """Create the main log file with MAC address and datetime"""
        self.log("Creating log file...")
        
        if not self.log_file:
            self.log_file = self.create_log_filename()
        
        try:
            with open(self.log_file, "w", encoding="utf-8") as f:
                f.write(f"# Master Bot Log File\n")
                f.write(f"# Device IP: {self.target_ip}\n")
                f.write(f"# Device MAC: {self.device_mac}\n")
                f.write(f"# Created: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# Log File: {self.log_file}\n\n")
            self.log(f"Created log file: {self.log_file}", "SUCCESS")
        except Exception as e:
            self.log(f"Failed to create log file {self.log_file}: {e}", "ERROR")
    
    def run_script(self, script_name: str) -> bool:
        """Run a script and capture output to the main log file"""
        if not os.path.exists(script_name):
            self.log(f"Script {script_name} not found", "ERROR")
            return False
        
        self.log(f"Running {script_name} - {self.scripts[script_name]}")
        self.log(f"Output will be logged to {self.log_file}")
        
        try:
            # Run script and capture output
            with open(self.log_file, "a", encoding="utf-8") as log_f:
                log_f.write(f"\n{'='*60}\n")
                log_f.write(f"Starting {script_name} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                log_f.write(f"{'='*60}\n")
                
                # Run the script
                process = subprocess.Popen(
                    [sys.executable, script_name],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    bufsize=1
                )
                
                # Stream output to both console and log file
                for line in process.stdout:
                    print(line.rstrip())
                    log_f.write(line)
                    log_f.flush()
                
                # Wait for process to complete
                return_code = process.wait()
                
                log_f.write(f"\n{'='*60}\n")
                log_f.write(f"Script {script_name} completed with return code: {return_code}\n")
                log_f.write(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                log_f.write(f"{'='*60}\n\n")
                
                if return_code == 0:
                    self.log(f"Script {script_name} completed successfully", "SUCCESS")
                    return True
                else:
                    self.log(f"Script {script_name} failed with return code: {return_code}", "ERROR")
                    return False
                    
        except Exception as e:
            self.log(f"Error running script {script_name}: {e}", "ERROR")
            return False
    
    def check_stage_completion(self, script_name: str) -> bool:
        """Check if a stage is already completed by looking at the main log file"""
        if not self.log_file or not os.path.exists(self.log_file):
            return False
        
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                content = f.read()
                
            # Check for completion indicators for the specific script
            completion_indicators = [
                f"Script {script_name} completed successfully",
                f"Script {script_name} completed with return code: 0"
            ]
            
            for indicator in completion_indicators:
                if indicator.lower() in content.lower():
                    return True
            
            return False
            
        except Exception as e:
            self.log(f"Error checking stage completion for {script_name}: {e}", "ERROR")
            return False
    
    def check_internet_connectivity(self) -> bool:
        """Check if internet connectivity is available by analyzing Script No. 2 output"""
        if not self.log_file or not os.path.exists(self.log_file):
            return False
        
        try:
            with open(self.log_file, "r", encoding="utf-8") as f:
                content = f.read()
            
            # Look for internet connectivity indicators in Script No. 2 output
            internet_indicators = [
                "Internet Connectivity: ✅ OK",
                "Ping Google DNS: ✅ SUCCESS",
                "Ping Google DNS: ✅ OK",
                "Ping Google DNS: PING OK",
                "Ping Google: ✅ SUCCESS", 
                "Ping Google: ✅ OK",
                "Ping Google: PING OK",
                "HTTP Test: ✅ SUCCESS",
                "HTTP Test: ✅ OK",
                "HTTP Test: HTTP OK",
                "DNS Resolution: ✅ SUCCESS",
                "DNS Resolution: ✅ OK"
            ]
            
            # Check if any internet connectivity test passed
            for indicator in internet_indicators:
                if indicator in content:
                    return True
            
            # Check for failure indicators
            failure_indicators = [
                "Internet Connectivity: ❌ FAILED",
                "Ping Google DNS: ❌ FAILED",
                "Ping Google: ❌ FAILED", 
                "HTTP Test: ❌ FAILED",
                "DNS Resolution: ❌ FAILED"
            ]
            
            # If we see failure indicators, internet is not available
            for indicator in failure_indicators:
                if indicator in content:
                    return False
            
            # If no clear indicators found, assume no internet
            return False
            
        except Exception as e:
            self.log(f"Error checking internet connectivity: {e}", "ERROR")
            return False
    
    def reload_network_configuration(self) -> bool:
        """Reload network configuration on the target device"""
        self.log("Reloading network configuration on target device")
        
        try:
            import paramiko
            
            # Connect to device
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                self.target_ip,
                username=self.username,
                password=self.password,
                timeout=10
            )
            
            # Reload network configuration
            commands = [
                "sudo /etc/init.d/network reload",
                "sudo /etc/init.d/network restart"
            ]
            
            for cmd in commands:
                self.log(f"Executing: {cmd}")
                stdin, stdout, stderr = ssh.exec_command(cmd)
                exit_status = stdout.channel.recv_exit_status()
                
                if exit_status == 0:
                    self.log(f"Command successful: {cmd}", "SUCCESS")
                else:
                    self.log(f"Command failed: {cmd}", "WARNING")
            
            ssh.close()
            self.log("Network configuration reload completed", "SUCCESS")
            return True
            
        except Exception as e:
            self.log(f"Error reloading network configuration: {e}", "ERROR")
            return False
    
    def run_single_cycle(self):
        """Run a single cycle of the bot"""
        self.cycle_count += 1
        self.log("=" * 80)
        self.log(f"MASTER BOT CYCLE #{self.cycle_count}: ORCHESTRATING SCRIPT NO. 1, 2, AND 3")
        self.log("=" * 80)
        
        # Check for shutdown request
        if self.shutdown_requested:
            self.log("Shutdown requested. Exiting cycle.", "WARNING")
            return False
            
        # Step 1: Check IP availability
        self.log("Step 1: Checking target IP availability")
        if not self.check_ip_availability():
            self.log("Target IP not available. Cycle failed.", "ERROR")
            return False
        self.delay("ip_check", "IP check completed")
        
        if self.shutdown_requested:
            self.log("Shutdown requested. Exiting cycle.", "WARNING")
            return False
        
        # Step 2: Test SSH login
        self.log("Step 2: Testing SSH login")
        if not self.test_ssh_login():
            self.log("SSH login failed. Cycle failed.", "ERROR")
            return False
        self.delay("ssh_test", "SSH test completed")
        
        if self.shutdown_requested:
            self.log("Shutdown requested. Exiting cycle.", "WARNING")
            return False
        
        # Step 3: Create log file
        self.log("Step 3: Creating log file")
        self.create_log_file()
        self.delay("log_creation", "Log file created")
        
        if self.shutdown_requested:
            self.log("Shutdown requested. Exiting cycle.", "WARNING")
            return False
        
        # Step 4: Run Script No. 1 (Network Configuration)
        self.log("Step 4: Running Script No. 1 (Network Configuration)")
        if self.check_stage_completion("script_no1.py"):
            self.log("Script No. 1 already completed. Skipping.", "INFO")
        else:
            if not self.run_script("script_no1.py"):
                self.log("Script No. 1 failed. Cycle failed.", "ERROR")
                return False
            self.delay("script_completion", "Script No. 1 completed")
        
        if self.shutdown_requested:
            self.log("Shutdown requested. Exiting cycle.", "WARNING")
            return False
        
        self.delay("between_scripts", "Preparing for Script No. 2")
        
        if self.shutdown_requested:
            self.log("Shutdown requested. Exiting cycle.", "WARNING")
            return False
        
        # Step 5: Run Script No. 2 (Connectivity Verification) with retry logic
        self.log("Step 5: Running Script No. 2 (Connectivity Verification)")
        script2_success = False
        max_retries = 3
        retry_count = 0
        
        while not script2_success and retry_count < max_retries and not self.shutdown_requested:
            if retry_count > 0:
                self.log(f"Retry attempt {retry_count} for Script No. 2")
            
            if self.check_stage_completion("script_no2.py") and retry_count == 0:
                self.log("Script No. 2 already completed. Checking internet connectivity.", "INFO")
            else:
                if not self.run_script("script_no2.py"):
                    self.log("Script No. 2 failed. Cycle failed.", "ERROR")
                    return False
            
            # Check internet connectivity
            self.log("Checking internet connectivity after Script No. 2")
            if self.check_internet_connectivity():
                self.log("Internet connectivity verified. Proceeding to Script No. 3.", "SUCCESS")
                script2_success = True
            else:
                retry_count += 1
                if retry_count < max_retries and not self.shutdown_requested:
                    self.log(f"No internet connectivity detected. Retry {retry_count}/{max_retries}", "WARNING")
                    self.log("Reloading network configuration before retry...")
                    
                    # Reload network configuration
                    if self.reload_network_configuration():
                        self.log("Network configuration reloaded. Waiting 10 seconds before retry...")
                        # Sleep in increments to check for shutdown
                        for _ in range(10):
                            if self.shutdown_requested:
                                self.log("Shutdown requested during retry wait. Exiting cycle.", "WARNING")
                                return False
                            time.sleep(1)
                    else:
                        self.log("Failed to reload network configuration", "ERROR")
                else:
                    if self.shutdown_requested:
                        self.log("Shutdown requested during Script No. 2 retry. Exiting cycle.", "WARNING")
                        return False
                    self.log("Maximum retries reached for Script No. 2. Internet connectivity not available.", "ERROR")
                    self.log("Cannot proceed to Script No. 3 without internet connectivity.", "ERROR")
                    return False
            
            self.delay("script_completion", "Script No. 2 completed")
        
        self.delay("between_scripts", "Preparing for Script No. 3")
        
        if self.shutdown_requested:
            self.log("Shutdown requested. Exiting cycle.", "WARNING")
            return False
        
        # Step 6: Run Script No. 3 (Infrastructure Deployment)
        self.log("Step 6: Running Script No. 3 (Infrastructure Deployment)")
        if self.check_stage_completion("script_no3.py"):
            self.log("Script No. 3 already completed. Skipping.", "INFO")
        else:
            if not self.run_script("script_no3.py"):
                self.log("Script No. 3 failed. Cycle failed.", "ERROR")
                return False
            self.delay("script_completion", "Script No. 3 completed")
        
        if self.shutdown_requested:
            self.log("Shutdown requested. Exiting cycle.", "WARNING")
            return False
        
        # Success!
        self.delay("final_success", "Preparing final success message")
        self.log("=" * 80)
        self.log(f"MASTER BOT CYCLE #{self.cycle_count} COMPLETED SUCCESSFULLY!", "SUCCESS")
        self.log("=" * 80)
        self.log("All stages completed:")
        self.log("- Script No. 1: Network Configuration")
        self.log("- Script No. 2: Connectivity Verification")
        self.log("- Script No. 3: Infrastructure Deployment")
        self.log(f"Check log file for detailed output: {self.log_file}")
        
        return True
    
    def run_forever(self):
        """Run the bot forever until shutdown signal is received"""
        self.log("=" * 80)
        self.log("MASTER BOT STARTING - RUNNING FOREVER MODE")
        self.log("Press Ctrl+C or send SIGTERM to stop gracefully")
        self.log("=" * 80)
        
        try:
            while not self.shutdown_requested:
                # Run a single cycle
                cycle_success = self.run_single_cycle()
                
                if self.shutdown_requested:
                    self.log("Shutdown requested. Exiting main loop.", "WARNING")
                    break
                
                if cycle_success:
                    self.log(f"Cycle #{self.cycle_count} completed successfully. Waiting before next cycle...")
                else:
                    self.log(f"Cycle #{self.cycle_count} failed. Waiting before retry...")
                
                # Wait before next cycle (with shutdown checks)
                self.delay("cycle_restart", "Waiting before next cycle")
                
        except KeyboardInterrupt:
            self.log("KeyboardInterrupt received. Initiating graceful shutdown...", "WARNING")
            self.shutdown_requested = True
        
        # Final shutdown message
        self.log("=" * 80)
        self.log(f"MASTER BOT SHUTDOWN - COMPLETED {self.cycle_count} CYCLES")
        self.log("=" * 80)
        self.log("Bot stopped gracefully. Goodbye!")

def main():
    """Main function"""
    print("Master Bot: Orchestrating Script No. 1, 2, and 3 - FOREVER MODE")
    print("=" * 70)
    print("This bot will run FOREVER until you press Ctrl+C or send SIGTERM:")
    print("1. Check for IP 192.168.1.1")
    print("2. Test SSH login with admin/admin")
    print("3. Get device MAC address and create single log file")
    print("4. Run Script No. 1 (Network Configuration)")
    print("5. Run Script No. 2 (Connectivity Verification)")
    print("6. Run Script No. 3 (Infrastructure Deployment)")
    print("7. Wait 30 seconds and repeat the cycle")
    print("8. All output logged to single file: MAC_ADDRESS_DATETIME.log")
    print()
    print("Press Ctrl+C to stop gracefully")
    print()
    
    # Initialize and run master bot forever
    bot = MasterBot()
    bot.run_forever()
    
    print(f"\n✅ Master Bot stopped gracefully!")
    print(f"📁 Check log file for detailed output: {bot.log_file}")
    print(f"🔄 Completed {bot.cycle_count} cycles total")
    sys.exit(0)

if __name__ == "__main__":
    main()
