# Unified Bivicom Configuration Bot with Enhanced WAN Config Documentation

## Overview
The Unified Bivicom Configuration Bot with Enhanced WAN Config is a comprehensive deployment script that combines all functionality from the original Script No. 1, 2, 3, and Master Bot into a single, streamlined solution. This version operates **WITHOUT REBOOTS** and includes **ENHANCED WAN CONFIGURATION** with clean separation between configuration application and restoration.

## Key Features

### ✅ **Enhanced WAN Configuration Process**
- **Advanced Network Reload**: Uses `/usr/sbin/network_config` and `luci-reload` when available
- **Route Management**: Automatic cleanup of empty/invalid routes
- **Default Route Management**: Adds proper default routes when WAN is configured
- **Fallback Mechanisms**: Multiple fallback options for network reload
- **Comprehensive Error Handling**: Robust error handling with detailed logging

### ✅ **Clean Separation Architecture**
- **Enhanced Process**: For Forward/Reverse configurations (new setups)
- **Simple Process**: For UCI restore (reverting to original config)
- **No Conflicts**: Prevents interference between restored and applied configurations
- **Backward Compatibility**: Legacy functions maintained

### ✅ **Forward/Reverse Configuration Modes**
- **FORWARD Mode**: WAN=eth1 (DHCP), LAN=eth0 (Static)
- **REVERSE Mode**: WAN=enx0250f4000000 (LTE), LAN=eth0 (Static)
- **Command-line Mode Selection**: Easy switching between modes
- **Automatic Interface Detection**: Smart interface detection and configuration

### ✅ **Complete Flow Implementation**
1. **SSH Connection & UCI Backup**
2. **Network Configuration (Enhanced Forward/Reverse)**
3. **Connectivity Verification**
4. **Curl Installation**
5. **Infrastructure Deployment**
6. **Installation Verification**
7. **Tailscale Setup**
8. **UCI Configuration Restore (Simple)**

## Installation & Setup

### Prerequisites
```bash
# Install required Python packages
pip install paramiko ipaddress plyer

# Or use virtual environment
python3 -m venv venv
source venv/bin/activate
pip install paramiko ipaddress plyer
```

### Configuration
Update your `bot_config.json` file:

```json
{
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
  "backup_before_deploy": true,
  "verify_deployment": true,
  "security_logging": true,
  "strict_mac_validation": false,
  "network_configuration": {
    "enable_network_config": true,
    "wan_interface": "eth1",
    "lan_interface": "eth0",
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
    "wan_interface": "enx0250f4000000",
    "wan_protocol": "lte",
    "lan_interface": "eth0",
    "lan_protocol": "static"
  },
  "tailscale": {
    "auth_key": "YOUR_TAILSCALE_AUTH_KEY_HERE",
    "enable_setup": true
  },
  "backup_configuration": {
    "backup_location": "/home/$USER",
    "backup_before_deploy": true,
    "restore_after_deploy": true
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
```

## Usage

### Forward Mode (Default)
```bash
# Run in forever mode with forward configuration
python3 unified_bivicom_bot_with_wan_config.py

# Run single cycle with forward configuration
python3 unified_bivicom_bot_with_wan_config.py --single

# Explicit forward mode
python3 unified_bivicom_bot_with_wan_config.py --forward
```

### Reverse Mode
```bash
# Run in forever mode with reverse configuration
python3 unified_bivicom_bot_with_wan_config.py --reverse

# Run single cycle with reverse configuration
python3 unified_bivicom_bot_with_wan_config.py --single --reverse
```

### Command Line Options
- `--forward`: Use forward configuration (WAN=eth1 DHCP, LAN=eth0 Static)
- `--reverse`: Use reverse configuration (WAN=enx0250f4000000 LTE, LAN=eth0 Static)
- `--single`: Run single cycle instead of forever mode

## Enhanced WAN Configuration Architecture

### **Enhanced Process (Forward/Reverse Configurations)**

#### **Function: `apply_wan_config(ssh, ip)`**
This function provides the enhanced WAN configuration process for new setups:

```python
def apply_wan_config(self, ssh, ip: str) -> bool:
    """Apply WAN configuration with enhanced network reload process"""
    
    # Step 1: Commit UCI changes
    sudo uci commit network
    
    # Step 2: Clean up empty routes before applying configuration
    cleanup_empty_routes(ssh, ip)
    
    # Step 3: Run network configuration
    /usr/sbin/network_config OR /etc/init.d/network restart
    
    # Step 4: Reload network services with luci-reload if available
    luci-reload network OR /etc/init.d/network restart
    
    # Step 5: Final cleanup of empty routes after configuration
    cleanup_empty_routes(ssh, ip)
```

#### **Function: `cleanup_empty_routes(ssh, ip)`**
This function manages route cleanup and default route addition:

```python
def cleanup_empty_routes(self, ssh, ip: str) -> bool:
    """Clean up empty routes and add proper default route"""
    
    # Remove routes with empty gateway
    ip route show | grep 'default via $' | while read route; do ip route del $route; done
    
    # Remove routes with empty gateway but with metric
    ip route show | grep 'default via  metric' | while read route; do ip route del $route; done
    
    # Remove routes with empty dev
    ip route show | grep 'default via.*dev $' | while read route; do ip route del $route; done
    
    # Add proper default route if WAN is configured
    wan_gateway = uci -q get network.wan.gateway
    wan_ifname = uci -q get network.wan.ifname
    if wan_gateway and wan_ifname:
        ip route add default via "$wan_gateway" dev "$wan_ifname"
```

### **Simple Process (UCI Restore)**

#### **Function: `restore_uci_backup_simple(ssh, ip)`**
This function provides a clean, non-interfering restore process:

```python
def restore_uci_backup_simple(self, ssh, ip: str) -> bool:
    """Restore UCI configuration from backup (simple version - no enhanced process)"""
    
    # Step 1: Restore UCI configuration
    sudo uci restore /home/$USER/uci-backup-<timestamp>
    
    # Step 2: Simple network reload (no enhanced process to avoid conflicts)
    sudo /etc/init.d/network reload
```

## Network Configuration Modes

### Forward Mode Configuration
**Target**: WAN=eth1 (DHCP), LAN=eth0 (Static)

```bash
# WAN Configuration
sudo uci set network.wan.proto='dhcp'
sudo uci set network.wan.ifname='eth1'
sudo uci set network.wan.mtu=1500

# LAN Configuration
sudo uci set network.lan.proto='static'
sudo uci set network.lan.ifname='eth0'
sudo uci set network.lan.ipaddr='192.168.1.1'
sudo uci set network.lan.netmask='255.255.255.0'

# Enhanced Application Process
apply_wan_config()  # Includes commit, cleanup, reload, cleanup
```

### Reverse Mode Configuration
**Target**: WAN=enx0250f4000000 (LTE), LAN=eth0 (Static)

```bash
# WAN Configuration
sudo uci set network.wan.proto='lte'
sudo uci set network.wan.ifname='enx0250f4000000'
sudo uci set network.wan.mtu=1500

# LAN Configuration
sudo uci set network.lan.proto='static'
sudo uci set network.lan.ifname='eth0'
sudo uci set network.lan.ipaddr='192.168.1.1'
sudo uci set network.lan.netmask='255.255.255.0'

# Enhanced Application Process
apply_wan_config()  # Includes commit, cleanup, reload, cleanup
```

## Deployment Flow

### Step-by-Step Process

#### 1. **SSH Connection & UCI Backup**
- Establishes SSH connection to target device (192.168.1.1)
- Creates UCI configuration backup using `sudo uci backup folder /home/$USER`
- Backup stored for later restoration

#### 2. **Network Configuration (Enhanced Forward/Reverse)**
- **Forward Mode**: Configures WAN=eth1 (DHCP), LAN=eth0 (Static)
- **Reverse Mode**: Configures WAN=enx0250f4000000 (LTE), LAN=eth0 (Static)
- **Enhanced Process**: `apply_wan_config()` with route cleanup and advanced reload
- **Wait**: 5 seconds for configuration to settle

#### 3. **WAN Connectivity Check**
- Verifies WAN interface received IP (checks both eth1 and enx0250f4000000)
- Tests connectivity with ping to 8.8.8.8
- Tests connectivity with ping to google.com
- Logs results for monitoring

#### 4. **Curl Installation**
- Checks if curl is already installed
- Installs curl if needed: `opkg update && opkg install curl`
- **Wait**: 5 seconds after installation

#### 5. **Infrastructure Deployment**
- Downloads and executes install.sh script
- Command: `curl -sSL https://raw.githubusercontent.com/Loranet-Technologies/bivicom-radar/main/install.sh | bash -s -- --auto`
- Monitors deployment progress in real-time
- Logs all output for debugging

#### 6. **Installation Verification**
- Verifies Docker installation: `docker --version`
- Verifies Node-RED installation: `node-red --version`
- Verifies Tailscale installation: `tailscale version`
- **Wait**: 5 seconds after verification

#### 7. **Tailscale Setup**
- Authenticates Tailscale using configured auth key
- Command: `tailscale up --authkey=<AUTH_KEY>`
- **Wait**: 5 seconds after authentication

#### 8. **UCI Configuration Restore (Simple)**
- Restores original UCI configuration from backup
- **Simple Process**: `restore_uci_backup_simple()` with basic reload only
- Commands:
  ```bash
  sudo uci restore /home/$USER/uci-backup-<timestamp>
  sudo /etc/init.d/network reload
  ```

## Enhanced WAN Configuration Features

### **Advanced Network Reload Methods**

#### **Primary Method: `/usr/sbin/network_config`**
- Uses OpenWrt's native network configuration tool
- More reliable than basic network restart
- Automatically detected and used when available

#### **Secondary Method: `luci-reload network`**
- Uses LuCI's network reload functionality
- Creates dummy lock command if missing
- Falls back to network restart if unavailable

#### **Fallback Method: `/etc/init.d/network restart`**
- Standard OpenWrt network restart
- Used when advanced methods are unavailable
- Ensures compatibility across all OpenWrt versions

### **Route Management Features**

#### **Empty Route Cleanup**
- Removes routes with empty gateway (`default via $`)
- Removes routes with empty gateway but with metric
- Removes routes with empty dev interface
- Prevents routing conflicts and issues

#### **Default Route Management**
- Automatically detects WAN gateway from UCI configuration
- Adds proper default route when WAN is configured
- Uses correct interface for default route
- Ensures proper internet connectivity

### **Error Handling & Fallbacks**

#### **Command Availability Detection**
- Checks for `/usr/sbin/network_config` availability
- Checks for `/usr/sbin/luci-reload` availability
- Automatically selects best available method
- Graceful fallback to basic methods

#### **Lock Command Management**
- Creates dummy lock command for luci-reload if missing
- Sets PATH to include temporary lock command
- Ensures luci-reload compatibility
- Handles missing dependencies gracefully

## Function Architecture

### **Enhanced Configuration Functions**

#### **`apply_wan_config(ssh, ip)`**
- **Purpose**: Enhanced WAN configuration application
- **Usage**: Forward/Reverse configurations
- **Features**: Route cleanup, advanced reload, error handling
- **Fallbacks**: Multiple reload methods with graceful degradation

#### **`cleanup_empty_routes(ssh, ip)`**
- **Purpose**: Route cleanup and default route management
- **Usage**: Called by apply_wan_config()
- **Features**: Empty route removal, default route addition
- **Safety**: Ignores errors for cleanup operations

#### **`check_command_exists(ssh, command)`**
- **Purpose**: Command availability detection
- **Usage**: Used by apply_wan_config()
- **Features**: Remote command checking
- **Reliability**: Handles connection errors gracefully

### **Simple Restore Functions**

#### **`restore_uci_backup_simple(ssh, ip)`**
- **Purpose**: Clean UCI configuration restore
- **Usage**: UCI backup restoration
- **Features**: Simple restore + basic reload
- **Safety**: No interference with restored configuration

#### **`restore_uci_backup(ssh, ip)`**
- **Purpose**: Legacy compatibility wrapper
- **Usage**: Backward compatibility
- **Features**: Calls restore_uci_backup_simple()
- **Maintenance**: Keeps existing code working

## Logging & Monitoring

### Log Files
- **Format**: `{MAC_ADDRESS}_{TIMESTAMP}.log`
- **Example**: `a019b2d27afa_20250109_143709.log`
- **Location**: Current working directory
- **Content**: Complete deployment cycle output with enhanced WAN config details

### Log Levels
- **INFO**: General information and progress
- **SUCCESS**: Successful operations
- **WARNING**: Non-critical issues
- **ERROR**: Critical failures
- **DEBUG**: Detailed debugging information

### Enhanced Logging Features
- **Route Cleanup Logging**: Detailed route management operations
- **Network Reload Logging**: Advanced reload method selection and results
- **Fallback Logging**: Fallback method usage and results
- **Command Detection Logging**: Available command detection results

## Error Handling

### Network Configuration Errors
- **UCI Command Failures**: Logged as warnings, operation continues
- **Advanced Reload Failures**: Falls back to basic methods
- **Route Cleanup Failures**: Logged but deployment continues
- **Interface Detection Failures**: Checks multiple interfaces

### Enhanced WAN Config Errors
- **Network Config Failures**: Falls back to network restart
- **luci-reload Failures**: Falls back to network restart
- **Lock Command Failures**: Creates dummy command and retries
- **Route Cleanup Failures**: Logged as warnings, continues

### Infrastructure Deployment Errors
- **Curl Installation Failures**: Stops deployment (critical dependency)
- **Script Download Failures**: Retries with exponential backoff
- **Installation Failures**: Detailed error logging for debugging
- **Tailscale Authentication Failures**: Logged as warnings, continues

### Configuration Restore Errors
- **Backup Not Found**: Logged as warning, skips restore
- **Restore Command Failures**: Logged as warnings, continues
- **Network Reload Failures**: Attempts manual restart

## Security Considerations

### Backup Security
- **Location**: Uses `/home/$USER` for backup storage
- **Permissions**: Maintains proper file permissions
- **Cleanup**: Consider implementing automatic cleanup of old backups

### Tailscale Security
- **Auth Key**: Store securely in configuration
- **Key Rotation**: Implement key rotation mechanism
- **Access Control**: Verify Tailscale access policies

### Network Security
- **Static IP**: Ensures LAN static IP doesn't conflict
- **Firewall**: Verify firewall rules after configuration changes
- **SSH Access**: Maintains SSH access throughout process
- **Route Security**: Proper default route management prevents routing issues

## Performance Benefits

### Enhanced WAN Config Advantages
- ⚡ **Faster Execution**: Advanced reload methods are more efficient
- 🔄 **Better Reliability**: Multiple fallback options ensure success
- 🛡️ **Route Management**: Automatic cleanup prevents routing issues
- 📊 **Better Monitoring**: Enhanced logging for all network operations
- 🐛 **Easier Debugging**: Detailed logging of all network operations

### No Reboot Advantages
- ⚡ **Faster Execution**: No waiting for device restart
- 🔄 **Continuous Operation**: No interruption in SSH connection
- 🛡️ **More Reliable**: No risk of device not coming back online
- 📊 **Better Monitoring**: Can monitor all steps in real-time
- 🐛 **Easier Debugging**: No need to reconnect after reboot

### Timing Optimizations
- **Configurable Delays**: All wait times configurable in bot_config.json
- **Smart Timing**: Delays only where necessary for stability
- **Parallel Operations**: Where possible, operations run in parallel

## Troubleshooting

### Common Issues

#### SSH Connection Failures
```bash
# Check if device is reachable
ping 192.168.1.1

# Verify SSH service is running
ssh admin@192.168.1.1
```

#### Network Configuration Issues
```bash
# Check current UCI configuration
uci show network

# Verify network interfaces
ip addr show

# Check specific interfaces
ip addr show eth0
ip addr show eth1
ip addr show enx0250f4000000

# Check routes
ip route show
```

#### Enhanced WAN Config Issues
```bash
# Check available network tools
ls -la /usr/sbin/network_config
ls -la /usr/sbin/luci-reload

# Check lock command
which lock

# Test network reload manually
/etc/init.d/network restart
```

#### Infrastructure Deployment Failures
```bash
# Check curl installation
which curl

# Test manual script download
curl -sSL https://raw.githubusercontent.com/Loranet-Technologies/bivicom-radar/main/install.sh
```

#### Tailscale Authentication Issues
- Verify auth key is valid and not expired
- Check Tailscale service status
- Ensure network connectivity for authentication

### Debug Mode
Enable debug logging by setting log level in configuration:
```json
{
  "log_level": "DEBUG"
}
```

## Configuration Reference

### Network Configuration Parameters
- `wan_interface`: WAN network interface (forward: eth1, reverse: enx0250f4000000)
- `lan_interface`: LAN network interface (default: eth0)
- `lan_ip`: Static IP for LAN interface (default: 192.168.1.1)
- `lan_netmask`: LAN subnet mask (default: 255.255.255.0)
- `wan_protocol`: WAN protocol (forward: dhcp, reverse: lte)
- `lan_protocol`: LAN protocol (default: static)

### Enhanced WAN Config Parameters
- `config_wait_time`: Wait after network configuration (default: 5s)
- `service_restart_wait`: Wait after service restart (default: 5s)
- `curl_install_wait`: Wait after curl installation (default: 5s)
- `verification_wait`: Wait after installation verification (default: 5s)
- `tailscale_auth_wait`: Wait after Tailscale authentication (default: 5s)

### Deployment Parameters
- `deployment_mode`: auto, interactive, or manual (default: auto)
- `backup_before_deploy`: Create backup before deployment (default: true)
- `restore_after_deploy`: Restore backup after deployment (default: true)
- `verify_deployment`: Verify installations after deployment (default: true)

## Best Practices

### Pre-Deployment
1. **Verify Network Connectivity**: Ensure target device is reachable
2. **Check Credentials**: Verify SSH credentials are correct
3. **Update Configuration**: Review and update bot_config.json
4. **Test Single Cycle**: Run with `--single` flag first
5. **Choose Mode**: Decide between forward or reverse configuration

### During Deployment
1. **Monitor Logs**: Watch real-time output for issues
2. **Check Progress**: Verify each step completes successfully
3. **Handle Errors**: Address any warnings or errors promptly
4. **Maintain Connection**: Ensure stable network connection

### Post-Deployment
1. **Verify Services**: Check all services are running correctly
2. **Test Connectivity**: Verify network and internet connectivity
3. **Review Logs**: Check log files for any issues
4. **Cleanup**: Remove old backup files if needed

## Support & Maintenance

### Regular Maintenance
- **Update Dependencies**: Keep Python packages updated
- **Review Logs**: Regular log file review and cleanup
- **Test Configuration**: Periodic testing of deployment flow
- **Backup Management**: Clean up old backup files

### Monitoring
- **Service Status**: Monitor deployed services
- **Network Health**: Check network connectivity
- **Performance**: Monitor deployment cycle times
- **Error Rates**: Track and address recurring errors

## Manual Configuration Commands

### Forward Configuration (Manual)
```bash
# Connect to device
ssh admin@192.168.1.1

# Configure WAN for DHCP on eth1
sudo uci set network.wan.proto='dhcp'
sudo uci set network.wan.ifname='eth1'
sudo uci set network.wan.mtu=1500

# Configure LAN for static on eth0
sudo uci set network.lan.proto='static'
sudo uci set network.lan.ifname='eth0'
sudo uci set network.lan.ipaddr='192.168.1.1'
sudo uci set network.lan.netmask='255.255.255.0'

# Apply changes with enhanced process
sudo uci commit network
# Clean up empty routes
ip route show | grep 'default via $' | while read route; do ip route del $route; done
# Use advanced reload if available
/usr/sbin/network_config || /etc/init.d/network restart
# Final route cleanup and default route addition
ip route show | grep 'default via $' | while read route; do ip route del $route; done
wan_gateway=$(uci -q get network.wan.gateway)
wan_ifname=$(uci -q get network.wan.ifname)
if [ -n "$wan_gateway" ] && [ -n "$wan_ifname" ]; then
    ip route add default via "$wan_gateway" dev "$wan_ifname"
fi
```

### Reverse Configuration (Manual)
```bash
# Connect to device
ssh admin@192.168.1.1

# Configure WAN for LTE on USB device
sudo uci set network.wan.proto='lte'
sudo uci set network.wan.ifname='enx0250f4000000'
sudo uci set network.wan.mtu=1500

# Configure LAN for static on eth0
sudo uci set network.lan.proto='static'
sudo uci set network.lan.ifname='eth0'
sudo uci set network.lan.ipaddr='192.168.1.1'
sudo uci set network.lan.netmask='255.255.255.0'

# Apply changes with enhanced process
sudo uci commit network
# Clean up empty routes
ip route show | grep 'default via $' | while read route; do ip route del $route; done
# Use advanced reload if available
/usr/sbin/network_config || /etc/init.d/network restart
# Final route cleanup and default route addition
ip route show | grep 'default via $' | while read route; do ip route del $route; done
wan_gateway=$(uci -q get network.wan.gateway)
wan_ifname=$(uci -q get network.wan.ifname)
if [ -n "$wan_gateway" ] && [ -n "$wan_ifname" ]; then
    ip route add default via "$wan_gateway" dev "$wan_ifname"
fi
```

## Conclusion

The Unified Bivicom Configuration Bot with Enhanced WAN Config provides a robust, efficient, and reliable solution for deploying Bivicom infrastructure. The enhanced WAN configuration process significantly improves network reliability while maintaining all the functionality of the original multi-script approach.

Key benefits:
- **Enhanced Network Management**: Advanced reload methods and route management
- **Clean Architecture**: Separation between configuration and restoration
- **Simplified Management**: Single script instead of multiple files
- **Faster Deployment**: No reboot delays with enhanced reliability
- **Better Reliability**: Multiple fallback options and comprehensive error handling
- **Enhanced Monitoring**: Real-time progress tracking with detailed logging
- **Comprehensive Logging**: Detailed operation logs for all network operations
- **Flexible Configuration**: Forward/Reverse mode selection
- **Error Resilience**: Robust error handling and recovery
- **Interface Flexibility**: Automatic detection of WAN interfaces
- **Route Management**: Automatic cleanup and default route management

For support or questions, refer to the log files and configuration documentation provided with the bot.
