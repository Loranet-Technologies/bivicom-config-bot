# Bivicom Radar Bot - Complete Documentation

A comprehensive automation system for deploying and configuring Bivicom Radar devices. This project provides both command-line and GUI interfaces for automated device setup, network configuration, and infrastructure deployment.

## 📋 Table of Contents

1. [Overview](#-overview)
2. [Architecture](#️-architecture)
3. [Quick Start](#-quick-start)
4. [GUI Application](#-gui-application)
5. [Configuration](#-configuration)
6. [Deployment Process](#-deployment-process)
7. [Security Features](#️-security-features)
8. [Technical Requirements](#-technical-requirements)
9. [Network Configuration](#-network-configuration)
10. [Logging System](#-logging-system)
11. [Troubleshooting](#-troubleshooting)
12. [Advanced Usage](#-advanced-usage)
13. [Distribution Packages](#-distribution-packages)
14. [Support](#-support)

## 🎯 Overview

The Bivicom Radar Bot is designed to automate the complete setup process for Bivicom Radar devices, including:

- **Network Configuration**: Automatic WAN/LAN interface setup
- **Connectivity Verification**: Internet connectivity testing and validation
- **Infrastructure Deployment**: Automated installation of Loranet infrastructure
- **Device Discovery**: Network scanning and MAC address validation
- **Real-time Monitoring**: Live logging and progress tracking
- **Cross-Platform Support**: Windows, macOS, and Linux compatibility

## 🏗️ Architecture

The system consists of several interconnected components:

### Core Components

1. **Master Bot** (`master_bot.py`) - Main orchestration engine
2. **Script No. 1** (`script_no1.py`) - Network configuration and device reboot
3. **Script No. 2** (`script_no2.py`) - WAN internet connectivity verification
4. **Script No. 3** (`script_no3.py`) - Loranet infrastructure deployment bot
5. **GUI Application** (`radar_bot_gui.py`) - User-friendly interface

### Configuration

- **`bot_config.json`** - Main configuration file with network settings, credentials, and deployment parameters
- **`requirements.txt`** - Core Python dependencies
- **`requirements_gui.txt`** - GUI-specific dependencies

### Deployment Flow

```
Network Check → SSH Test → MAC Detection → Log Creation → 
Network Config → Connectivity Test → Infrastructure Deploy → Completion
```

## 🚀 Quick Start

### Prerequisites

- Python 3.7 or higher
- Network access to target devices (192.168.1.1)
- SSH access with admin/admin credentials
- Internet connectivity for infrastructure deployment

### Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Loranet-Technologies/bivicom-config-bot.git
   cd bivicom-config-bot
   ```

2. **Create virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **For GUI support**:
   ```bash
   pip install -r requirements_gui.txt
   ```

### Running the Application

#### Command Line Interface

**Run the complete automation cycle**:
```bash
python3 master_bot.py
```

**Run individual scripts**:
```bash
# Network configuration only
python3 script_no1.py

# Connectivity verification only
python3 script_no2.py

# Infrastructure deployment only
python3 script_no3.py
```

#### GUI Interface

**Launch the GUI application**:
```bash
python3 radar_bot_gui.py
```

## 🖥️ GUI Application

### Features

- **Intuitive GUI**: Easy-to-use interface for device setup
- **Real-time Progress**: Live monitoring of deployment progress
- **One-Click Setup**: Simple "Start Bot" button to begin automation
- **Status Indicators**: Visual feedback for each deployment stage
- **Log Display**: Real-time log output in the application window
- **Cross-Platform**: Works on Windows, macOS, and Linux

### Installation

#### Windows
1. Download `bivicom-radar-bot-windows-v1.0.zip`
2. Extract the archive
3. Double-click `INSTALL.bat`
4. Follow the installation prompts

#### macOS
1. Download `bivicom-radar-bot-macos-v1.0.zip`
2. Extract the archive
3. Run `./INSTALL.sh` in Terminal
4. Follow the installation prompts

#### Linux
1. Download `bivicom-radar-bot-linux-v1.0.zip`
2. Extract the archive
3. Run `./INSTALL.sh`
4. Follow the installation prompts

### Usage

#### Launching the Application

**Windows:**
- Double-click the desktop shortcut "Bivicom Radar Bot"
- Or run: `python radar_bot_gui.py`

**macOS:**
- Double-click the desktop shortcut
- Or open Applications folder and click "Bivicom Radar Bot"
- Or use Spotlight: Cmd+Space, type "Bivicom"

**Linux:**
- Double-click the desktop shortcut
- Or run: `python3 radar_bot_gui.py`

#### Using the GUI

1. **Launch the Application**: Start the GUI application
2. **Check Prerequisites**: Ensure your network and device are ready
3. **Click "Start Bot"**: Begin the automated deployment process
4. **Monitor Progress**: Watch real-time updates in the log window
5. **Wait for Completion**: The bot will notify you when finished

#### GUI Components

- **Start Bot Button**: Initiates the deployment process
- **Progress Bar**: Shows overall completion status
- **Log Window**: Displays real-time deployment logs
- **Status Labels**: Shows current operation status
- **Stop Button**: Allows you to cancel the operation (if needed)

## 📋 Configuration

### Network Settings

Edit `bot_config.json` to customize:

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

### Key Configuration Options

- **`network_range`**: IP range to scan for devices
- **`target_mac_prefixes`**: Authorized MAC address prefixes
- **`deployment_mode`**: "auto", "interactive", or "manual"
- **`ssh_timeout`**: SSH connection timeout in seconds
- **`max_threads`**: Maximum concurrent scanning threads
- **`strict_mac_validation`**: Enable/disable MAC address validation

## 🔄 Deployment Process

### Master Bot Cycle

The Master Bot orchestrates a complete automation cycle:

1. **IP Availability Check** - Verify target device (192.168.1.1) is reachable
2. **SSH Authentication** - Test login with admin/admin credentials
3. **Log File Creation** - Create timestamped log file with device MAC
4. **Script No. 1** - Network configuration and device reboot
5. **Script No. 2** - WAN internet connectivity verification (with retry logic)
6. **Script No. 3** - Loranet infrastructure deployment

### Script No. 1: Network Configuration

- Configures WAN interface (eth0) for DHCP internet access
- Configures LAN interface (eth1) for local network
- Applies network configuration using UCI commands
- Executes WAN configuration script
- Tests internet connectivity
- Reboots device to apply changes

### Script No. 2: Connectivity Verification

- Checks WAN interface status and IP assignment
- Verifies network routing table
- Tests network services (DHCP, interfaces)
- Performs internet connectivity tests:
  - DNS resolution
  - Ping to Google DNS (8.8.8.8)
  - HTTP connectivity tests
- Provides comprehensive connectivity report

### Script No. 3: Infrastructure Deployment

- Scans network for active devices
- Validates MAC addresses against authorized prefixes
- Tests SSH connectivity to discovered devices
- Deploys Loranet infrastructure via curl script
- Monitors deployment progress
- Verifies successful installation

### GUI Deployment Process

The GUI automates the following steps:

1. **Network Check**: Verifies connectivity to 192.168.1.1
2. **SSH Test**: Tests SSH connection with admin credentials
3. **MAC Detection**: Retrieves device MAC address
4. **Log Creation**: Creates timestamped log file
5. **Network Configuration**: Configures WAN/LAN interfaces
6. **Connectivity Verification**: Tests internet connectivity
7. **Infrastructure Deployment**: Installs Bivicom Radar system
8. **Completion Notification**: Notifies when deployment is complete

## 🛡️ Security Features

### MAC Address Validation

The system includes comprehensive MAC address validation:

- **Authorized OUIs**: Pre-configured Bivicom manufacturer prefixes
- **Custom Prefixes**: Configurable target MAC prefixes
- **Security Logging**: Audit trail for unauthorized devices
- **Strict Validation**: Optional enforcement of MAC address requirements

### SSH Security

- **Default Credentials**: admin/admin (change in production)
- **Connection Timeout**: 10 seconds
- **Key Exchange**: RSA/DSA key authentication
- **Cipher**: AES-256 encryption

### Security Audit Logging

All security events are logged to `security_audit.log`:
- Invalid MAC addresses
- Unauthorized device attempts
- SSH connection failures
- Configuration changes

### Network Security

- **Trusted Network**: Bot must run on trusted network
- **Device Validation**: Only authorized devices are configured
- **Audit Logging**: Complete operation logging
- **Error Handling**: Secure error reporting

## 🔧 Technical Requirements

### System Requirements

- **Python**: 3.7 or higher
- **Operating System**: Windows 10+, macOS 10.13+, Linux (Ubuntu 18.04+)
- **Network**: Access to target device network (192.168.1.1)
- **SSH**: Admin access with default credentials (admin/admin)

### Python Dependencies

```txt
paramiko>=2.7.0      # SSH client library
scp>=0.14.0          # SCP file transfer
psutil>=5.8.0        # System utilities
requests>=2.25.0     # HTTP requests
tkinter              # GUI framework (built-in)
```

### Target Device Requirements

- **Device Type**: Bivicom-compatible OpenWrt device
- **Network Interface**: eth0 (WAN), eth1 (LAN)
- **SSH Access**: Enabled with admin/admin credentials
- **UCI System**: OpenWrt configuration system available

## 🌐 Network Configuration

### Network Topology

```
Internet
    |
[WAN Router]
    |
[Target Device - 192.168.1.1]
    |
[Local Network - 192.168.1.0/24]
```

### Interface Configuration

**WAN Interface (eth0):**
- Protocol: DHCP
- Interface: eth0
- Purpose: Internet connectivity

**LAN Interface (eth1):**
- Protocol: DHCP
- Interface: eth1
- IP: 192.168.1.1
- Netmask: 255.255.255.0
- Purpose: Local network management

### UCI Commands Used

```bash
# WAN Configuration
uci set network.wan.proto=dhcp
uci set network.wan.ifname=eth0

# LAN Configuration
uci set network.lan.proto=dhcp
uci set network.lan.ifname=eth1
uci set network.lan.ipaddr=192.168.1.1
uci set network.lan.netmask=255.255.255.0

# Apply Configuration
uci commit network
/etc/init.d/network reload
```

### Deployment Process Details

#### Stage 1: Network Check
```python
# Ping target device
subprocess.run(['ping', '-c', '1', '192.168.1.1'])
```

#### Stage 2: SSH Test
```python
# Test SSH connection
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.1.1', username='admin', password='admin')
```

#### Stage 3: MAC Detection
```python
# Get MAC from ARP table
arp_output = subprocess.check_output(['arp', '-n', '192.168.1.1'])
mac_address = extract_mac_from_arp(arp_output)
```

#### Stage 4: Network Configuration
```python
# Configure network interfaces
commands = [
    'uci set network.wan.proto=dhcp',
    'uci set network.wan.ifname=eth0',
    'uci set network.lan.proto=dhcp',
    'uci set network.lan.ifname=eth1',
    'uci commit network',
    '/etc/init.d/network reload'
]
```

#### Stage 5: Connectivity Verification
```python
# Test internet connectivity
ssh.exec_command('ping -c 3 8.8.8.8')
```

#### Stage 6: Infrastructure Deployment
```python
# Deploy Bivicom Radar
deploy_command = 'curl -sSL https://raw.githubusercontent.com/Loranet-Technologies/bivicom-radar/main/install.sh | bash -s -- --auto'
ssh.exec_command(deploy_command)
```

## 📊 Logging System

### Log Files

- **Main Log**: `{MAC_ADDRESS}_{TIMESTAMP}.log` - Complete cycle log
- **Security Log**: `security_audit.log` - Security events
- **Deployment Reports**: `deployment_report_{TIMESTAMP}.txt` - Deployment summaries

### Log File Naming
```
{MAC_ADDRESS}_{YYYYMMDD}_{HHMMSS}.log
Example: a019b2d27af9_20250909_001637.log
```

### Log Format
```
[2025-09-09 00:16:37] [INFO] ================================================
[2025-09-09 00:16:37] [INFO] MASTER BOT EXECUTION STARTED
[2025-09-09 00:16:37] [INFO] Target IP: 192.168.1.1
[2025-09-09 00:16:37] [INFO] Device MAC: a019b2d27af9
[2025-09-09 00:16:37] [INFO] ================================================
```

### Log Levels

- **DEBUG**: Detailed debugging information
- **INFO**: General information messages
- **WARNING**: Warning messages
- **ERROR**: Error messages
- **CRITICAL**: Critical error messages

### GUI Monitoring

The GUI provides real-time monitoring with:
- Color-coded log messages
- Progress indicators
- Statistics tracking (cycles, devices, uptime)
- System notifications on completion

## 🐛 Troubleshooting

### Common Issues

1. **SSH Connection Failed**
   - Verify device is reachable: `ping 192.168.1.1`
   - Check credentials in `bot_config.json`
   - Ensure SSH service is running on target device

2. **MAC Address Not Found**
   - Check ARP table: `arp -a`
   - Verify network connectivity
   - Consider disabling strict MAC validation

3. **Internet Connectivity Issues**
   - Verify WAN interface configuration
   - Check DHCP client status
   - Test manual internet access

4. **GUI Not Displaying**
   - Install tkinter: `brew install python-tk` (macOS)
   - Check virtual environment activation
   - Verify GUI dependencies installation

5. **Device Not Found**
   - Verify device is at 192.168.1.1
   - Check network configuration
   - Ensure device is powered on

6. **MAC Address Validation Failed**
   - Check authorized OUI list
   - Verify device manufacturer
   - Disable strict validation if needed

7. **Network Configuration Failed**
   - Check UCI system availability
   - Verify interface names
   - Check permissions

### Debug Mode

Enable detailed logging:
```json
{
  "log_level": "DEBUG"
}
```

### Manual Verification

Test individual components:
```bash
# Test SSH connection
ssh admin@192.168.1.1

# Test network configuration
uci show network

# Test internet connectivity
ping 8.8.8.8

# Test SSH connection programmatically
python3 -c "from script_no3 import LoranetDeploymentBot; bot = LoranetDeploymentBot(); print(bot.test_ssh_connection('192.168.1.1', 'admin', 'admin'))"

# Test network scan
python3 -c "from script_no3 import LoranetDeploymentBot; bot = LoranetDeploymentBot(); print(bot.scan_network('192.168.1.0/24'))"
```

## 🔧 Advanced Usage

### Custom Deployment Modes

**Auto Mode** (default):
```bash
python3 script_no3.py
```

**Interactive Mode**:
```json
{
  "deployment_mode": "interactive"
}
```

**Manual Mode**:
```json
{
  "deployment_mode": "manual"
}
```

### Network Configuration Testing

Test network configuration commands without execution:
```bash
python3 -c "from script_no3 import LoranetDeploymentBot; bot = LoranetDeploymentBot(); bot.test_network_configuration_commands()"
```

### Server-Only Deployment

Deploy to specific server without network discovery:
```bash
python3 -c "from script_no3 import LoranetDeploymentBot; bot = LoranetDeploymentBot(); bot.deploy_to_server_only()"
```

### Command Line Alternative

If you prefer command-line usage:
```bash
python3 master_bot.py
```

### Individual Scripts

Run specific deployment stages:
```bash
python3 script_no1.py  # Network configuration
python3 script_no2.py  # Connectivity verification
python3 script_no3.py  # Infrastructure deployment
```

### Performance Optimization

#### Threading Configuration
```json
{
  "max_threads": 50,
  "scan_timeout": 5,
  "ssh_timeout": 10
}
```

#### Network Optimization
- Use wired connections for stability
- Ensure adequate bandwidth
- Minimize network latency

#### System Resources
- Monitor CPU usage during deployment
- Ensure sufficient memory
- Check disk space for logs

## 📦 Distribution Packages

The project includes platform-specific distribution packages:

- **Windows 11**: `BivicomRadarBot_Windows11.zip`
- **Ubuntu 20+**: `BivicomRadarBot_Ubuntu20+.zip`
- **macOS**: `BivicomRadarBot_macOS.zip`

Each package includes:
- Complete application with dependencies
- Platform-specific installation scripts
- Desktop shortcuts and app bundles
- Comprehensive documentation

### Multi-Platform Packages

Available in the releases directory:
- **Windows Package** (`bivicom-radar-bot-windows-v1.0.zip` - 37KB)
- **macOS Package** (`bivicom-radar-bot-macos-v1.0.zip` - 38KB)
- **Linux Package** (`bivicom-radar-bot-linux-v1.0.zip` - 38KB)

## 🔄 Maintenance

### Regular Tasks
- Review log files for errors
- Update authorized OUI list
- Test deployment process
- Backup configuration files

### Updates
- Monitor for security updates
- Update Python dependencies
- Test with new device models
- Update documentation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Check the troubleshooting section
- Review log files for error details
- Create an issue with detailed information
- Include system information and configuration

For technical support:
- Check log files for detailed error information
- Review this deployment guide
- Contact the development team
- Submit issues on GitHub

## 🔄 Version History

- **v1.0** - Initial release with core automation functionality
- **v1.1** - Added GUI interface and cross-platform support
- **v1.2** - Enhanced security features and MAC validation
- **v1.3** - Improved error handling and retry logic

---

**Author**: Aqmar  
**Organization**: Loranet Technologies  
**Date**: 2025-01-09  
**Version**: 1.3  
**Repository**: https://github.com/Loranet-Technologies/bivicom-config-bot
