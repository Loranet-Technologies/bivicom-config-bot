# Unified Bivicom Configuration Bot Documentation

## Overview
The Unified Bivicom Configuration Bot is a comprehensive deployment script that combines all functionality from the original Script No. 1, 2, 3, and Master Bot into a single, streamlined solution. This version operates **WITHOUT REBOOTS** for faster and more reliable deployment and includes **FORWARD/REVERSE** network configuration modes.

## Key Features

### ✅ **No Reboot Operation**
- All network configuration changes applied without device restart
- Faster deployment cycles
- More reliable operation
- Continuous SSH connection maintained

### ✅ **Forward/Reverse Configuration Modes**
- **FORWARD Mode**: WAN=eth1 (DHCP), LAN=eth0 (Static)
- **REVERSE Mode**: WAN=enx0250f4000000 (LTE), LAN=eth0 (Static)
- Command-line mode selection
- Automatic interface detection

### ✅ **Complete Flow Implementation**
1. **SSH Connection & UCI Backup**
2. **Network Configuration (Forward/Reverse)**
3. **Connectivity Verification**
4. **Curl Installation**
5. **Infrastructure Deployment**
6. **Installation Verification**
7. **Tailscale Setup**
8. **UCI Configuration Restore**

### ✅ **Enhanced Error Handling**
- Comprehensive error logging
- Graceful failure handling
- Detailed progress tracking
- Real-time monitoring

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
python3 unified_bivicom_bot_with_reverse.py

# Run single cycle with forward configuration
python3 unified_bivicom_bot_with_reverse.py --single

# Explicit forward mode
python3 unified_bivicom_bot_with_reverse.py --forward
```

### Reverse Mode
```bash
# Run in forever mode with reverse configuration
python3 unified_bivicom_bot_with_reverse.py --reverse

# Run single cycle with reverse configuration
python3 unified_bivicom_bot_with_reverse.py --single --reverse
```

### Command Line Options
- `--forward`: Use forward configuration (WAN=eth1 DHCP, LAN=eth0 Static)
- `--reverse`: Use reverse configuration (WAN=enx0250f4000000 LTE, LAN=eth0 Static)
- `--single`: Run single cycle instead of forever mode

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

# Apply Configuration
sudo uci commit network
sudo /etc/init.d/network reload
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

# Apply Configuration
sudo uci commit network
sudo /etc/init.d/network reload
```

## Deployment Flow

### Step-by-Step Process

#### 1. **SSH Connection & UCI Backup**
- Establishes SSH connection to target device (192.168.1.1)
- Creates UCI configuration backup using `sudo uci backup folder /home/$USER`
- Backup stored for later restoration

#### 2. **Network Configuration (Forward/Reverse)**
- **Forward Mode**: Configures WAN=eth1 (DHCP), LAN=eth0 (Static)
- **Reverse Mode**: Configures WAN=enx0250f4000000 (LTE), LAN=eth0 (Static)
- **Apply Configuration**: `sudo uci commit network`
- **Reload Services**: `sudo /etc/init.d/network reload` (NO REBOOT)
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

#### 8. **UCI Configuration Restore**
- Restores original UCI configuration from backup
- Commands:
  ```bash
  sudo uci restore /home/$USER/uci-backup-<timestamp>
  sudo uci commit
  sudo /etc/init.d/network reload
  ```

## UCI Configuration Analysis

### Before Configuration (Original)
```bash
network.lan.ifname='eth0'                    # LAN on eth0
network.wan.ifname='enx0250f4000000'         # WAN on USB LTE device
network.wan.proto='lte'                      # WAN using LTE
```

### After Configuration (Forward Mode)
```bash
network.lan.ifname='eth0'                    # LAN on eth0
network.wan.ifname='eth1'                    # WAN on eth1
network.wan.proto='dhcp'                     # WAN using DHCP
```

### Reverse Configuration (Back to Original)
```bash
network.lan.ifname='eth0'                    # LAN on eth0
network.wan.ifname='enx0250f4000000'         # WAN back to USB LTE device
network.wan.proto='lte'                      # WAN back to LTE
```

## Logging & Monitoring

### Log Files
- **Format**: `{MAC_ADDRESS}_{TIMESTAMP}.log`
- **Example**: `a019b2d27afa_20250109_143709.log`
- **Location**: Current working directory
- **Content**: Complete deployment cycle output

### Log Levels
- **INFO**: General information and progress
- **SUCCESS**: Successful operations
- **WARNING**: Non-critical issues
- **ERROR**: Critical failures
- **DEBUG**: Detailed debugging information

### Real-time Monitoring
- All operations logged with timestamps
- Real-time progress indication
- Detailed error messages for troubleshooting
- Step-by-step completion tracking

## Error Handling

### Network Configuration Errors
- **UCI Command Failures**: Logged as warnings, operation continues
- **Service Reload Failures**: Attempted with fallback methods
- **IP Assignment Failures**: Logged but deployment continues
- **Interface Detection Failures**: Checks multiple interfaces

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

## Performance Benefits

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

### Timing Parameters
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

# Apply changes
sudo uci commit network
sudo /etc/init.d/network reload
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

# Apply changes
sudo uci commit network
sudo /etc/init.d/network reload
```

## Conclusion

The Unified Bivicom Configuration Bot with reverse functionality provides a robust, efficient, and reliable solution for deploying Bivicom infrastructure. The no-reboot approach significantly improves deployment speed and reliability while maintaining all the functionality of the original multi-script approach.

Key benefits:
- **Simplified Management**: Single script instead of multiple files
- **Faster Deployment**: No reboot delays
- **Better Reliability**: Continuous operation without restart risks
- **Enhanced Monitoring**: Real-time progress tracking
- **Comprehensive Logging**: Detailed operation logs
- **Flexible Configuration**: Forward/Reverse mode selection
- **Error Resilience**: Robust error handling and recovery
- **Interface Flexibility**: Automatic detection of WAN interfaces

For support or questions, refer to the log files and configuration documentation provided with the bot.
