# Bivicom Radar Bot

An automated deployment bot for Bivicom Radar infrastructure that performs network discovery, device configuration, and infrastructure deployment via SSH.

## 🚀 Features

- **Network Discovery**: Automatically scans network ranges for active devices
- **MAC Address Validation**: Validates devices against authorized Bivicom manufacturer prefixes
- **Network Configuration**: Configures WAN/LAN interfaces on OpenWrt devices
- **SSH Automation**: Connects to devices using default credentials (admin/admin)
- **Automated Deployment**: Runs the Bivicom Radar infrastructure setup script remotely
- **Progress Monitoring**: Real-time monitoring with comprehensive logging
- **Delay System**: Configurable delays for controlled execution
- **Single Log File**: Dynamic log files with MAC address and timestamp naming

## 📋 Prerequisites

- Python 3.6 or higher
- Network access to target devices
- SSH access with admin/admin credentials
- Target devices must be on the same network

## 🛠️ Installation

### Quick Install
```bash
# Download and install the bot
curl -sSL https://raw.githubusercontent.com/Loranet-Technologies/bivicom-radar-bot/main/install_bot.sh | bash
```

### Manual Install
```bash
# Clone the repository
git clone https://github.com/Loranet-Technologies/bivicom-radar-bot.git
cd bivicom-radar-bot

# Install Python dependencies
pip3 install -r requirements.txt

# Make scripts executable
chmod +x *.py
```

## ⚙️ Configuration

Edit `bot_config.json` to customize the bot behavior:

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
    "wan_interface": "eth0",
    "lan_interface": "eth1",
    "lan_ip": "192.168.1.1",
    "lan_netmask": "255.255.255.0",
    "wan_protocol": "dhcp",
    "lan_protocol": "dhcp",
    "reboot_timeout": 300,
    "ssh_ready_delay": 30
  },
  "server_targets": {
    "192.168.1.1": {
      "priority": 1,
      "description": "Main server requiring network configuration",
      "requires_network_config": true,
      "requires_reboot": true
    }
  }
}
```

### Configuration Options

- **network_range**: Network range to scan (CIDR notation)
- **default_credentials**: SSH username and password for target devices
- **target_mac_prefixes**: MAC address prefixes to identify target devices
- **deployment_mode**: "auto", "interactive", or "manual"
- **ssh_timeout**: SSH connection timeout in seconds
- **scan_timeout**: Network scan timeout per host
- **max_threads**: Maximum concurrent threads for scanning
- **strict_mac_validation**: Enable/disable MAC address validation
- **network_configuration**: Network interface configuration settings
- **server_targets**: Specific server configurations

## 🎯 Usage

### Master Bot (Recommended)

The master bot orchestrates the entire deployment process:

```bash
# Run the complete deployment process
python3 master_bot.py
```

The master bot will:
1. Check if `192.168.1.1` is reachable
2. Test SSH login with admin/admin
3. Create a log file with MAC address and timestamp
4. Run Script No. 1 (Network Configuration)
5. Run Script No. 2 (Connectivity Verification)
6. Run Script No. 3 (Infrastructure Deployment)
7. Skip stages if already completed

### Individual Scripts

#### Script No. 1 - Network Configuration
```bash
# Configure network settings and reboot
python3 script_no1.py
```

#### Script No. 2 - Connectivity Verification
```bash
# Verify WAN internet connectivity
python3 script_no2.py
```

#### Script No. 3 - Infrastructure Deployment
```bash
# Deploy Bivicom Radar infrastructure
python3 script_no3.py
```

### Legacy Bot (script_no3.py)

The legacy bot can still be used for direct deployment:

```bash
# Deploy to all discovered devices (auto mode)
python3 script_no3.py

# Deploy to specific server only
python3 script_no3.py --server-only

# Network configuration only
python3 script_no3.py --network-config-only
```

## 🔍 How It Works

### Master Bot Process

1. **IP Availability Check**: Pings `192.168.1.1` to verify reachability
2. **SSH Login Test**: Tests SSH connection with admin/admin credentials
3. **MAC Address Detection**: Retrieves device MAC from ARP table
4. **Log File Creation**: Creates timestamped log file with MAC address
5. **Sequential Script Execution**: Runs scripts in order with delays
6. **Stage Skipping**: Checks completion status to avoid re-running completed stages
7. **Comprehensive Logging**: All output logged to single file

### Network Configuration Process

For servers requiring network configuration:

1. **SSH Connection**: Connects to server with admin credentials
2. **Network Configuration**: Configures WAN (eth0) and LAN (eth1) interfaces
3. **UCI Commands**: Uses `sudo uci set` commands for OpenWrt configuration
4. **Interface Setup**: 
   - WAN: eth0 with DHCP protocol
   - LAN: eth1 with DHCP protocol
   - Bridge: Preserved intact
5. **Configuration Apply**: Commits and reloads network configuration
6. **Device Reboot**: Reboots device to apply changes
7. **Wait for Online**: Waits for device to come back online

### Infrastructure Deployment Process

1. **Curl Installation**: Ensures curl is available (apt/opkg fallback)
2. **Deployment Command**: Executes Bivicom Radar installation
3. **Auto Mode**: Always uses `--auto` flag for unattended installation
4. **Progress Monitoring**: Real-time monitoring of deployment progress
5. **Verification**: Verifies successful deployment

## 📊 Delay System

The master bot includes a comprehensive delay system for controlled execution:

```python
delays = {
    "ip_check": 2,           # Delay after IP check
    "ssh_test": 3,           # Delay after SSH test
    "log_creation": 1,       # Delay after log creation
    "between_scripts": 5,    # Delay between scripts
    "script_completion": 2,  # Delay after script completion
    "final_success": 3       # Delay before final success message
}
```

## 📝 Logging

### Log File Naming
Log files are named with the device's MAC address and timestamp:
```
a019b2d27af9_20250909_001637.log
```

### Log Structure
```
[2025-09-09 00:16:37] [INFO] ================================================
[2025-09-09 00:16:37] [INFO] MASTER BOT EXECUTION STARTED
[2025-09-09 00:16:37] [INFO] Target IP: 192.168.1.1
[2025-09-09 00:16:37] [INFO] Device MAC: a019b2d27af9
[2025-09-09 00:16:37] [INFO] ================================================
```

## 🛡️ Security Considerations

- **MAC Address Validation**: Only deploys to authorized Bivicom devices (configurable)
- **SSH Security**: Uses admin/admin credentials (change in production)
- **Network Trust**: Ensure the bot runs on a trusted network
- **Audit Trail**: Complete logging of all operations

## 🐛 Troubleshooting

### Common Issues

1. **No devices found**: Check network range and MAC prefixes
2. **SSH connection failed**: Verify credentials and network connectivity
3. **Deployment timeout**: Increase timeout values in configuration
4. **Permission denied**: Ensure the bot has necessary permissions

### Debug Mode

Enable debug logging by setting log level in configuration:

```json
{
  "log_level": "DEBUG"
}
```

## 📋 Deployment Command

The bot uses the following command for Bivicom Radar deployment:

```bash
curl -sSL https://raw.githubusercontent.com/Loranet-Technologies/bivicom-radar/main/install.sh | bash -s -- --auto
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👨‍💻 Author

**Aqmar** - *Initial work* - [Loranet Technologies](https://github.com/Loranet-Technologies)

## 🙏 Acknowledgments

- OpenWrt community for UCI configuration system
- Node-RED team for the excellent platform
- Docker team for containerization
- Tailscale for VPN solution