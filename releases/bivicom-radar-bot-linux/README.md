# Bivicom Radar Bot

A comprehensive automation system for deploying and configuring Bivicom Radar devices. This project provides both command-line and GUI interfaces for automated device setup, network configuration, and infrastructure deployment.

## 🎯 Overview

The Bivicom Radar Bot is designed to automate the complete setup process for Bivicom Radar devices, including:

- **Network Configuration**: Automatic WAN/LAN interface setup
- **Connectivity Verification**: Internet connectivity testing and validation
- **Infrastructure Deployment**: Automated installation of Loranet infrastructure
- **Device Discovery**: Network scanning and MAC address validation
- **Real-time Monitoring**: Live logging and progress tracking

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

## 🚀 Quick Start

### Prerequisites

- Python 3.7 or higher
- Network access to target devices (192.168.1.1)
- SSH access with admin/admin credentials
- Internet connectivity for infrastructure deployment

### Installation

1. **Clone the repository**:
   ```bash
   git clone <repository-url>
   cd bivicom-radar-bot
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

The GUI provides:
- Real-time log display with color-coded messages
- Progress indicators and statistics
- Start/Stop/Pause controls
- System notifications on completion
- Cross-platform compatibility

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
  "network_configuration": {
    "enable_network_config": true,
    "wan_interface": "eth0",
    "lan_interface": "eth1",
    "lan_ip": "192.168.1.1",
    "wan_protocol": "dhcp",
    "lan_protocol": "dhcp"
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

## 🔄 Workflow

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

## 🛡️ Security Features

### MAC Address Validation

The system includes comprehensive MAC address validation:

- **Authorized OUIs**: Pre-configured Bivicom manufacturer prefixes
- **Custom Prefixes**: Configurable target MAC prefixes
- **Security Logging**: Audit trail for unauthorized devices
- **Strict Validation**: Optional enforcement of MAC address requirements

### Security Audit Logging

All security events are logged to `security_audit.log`:
- Invalid MAC addresses
- Unauthorized device attempts
- SSH connection failures
- Configuration changes

## 📊 Monitoring and Logging

### Log Files

- **Main Log**: `{MAC_ADDRESS}_{TIMESTAMP}.log` - Complete cycle log
- **Security Log**: `security_audit.log` - Security events
- **Deployment Reports**: `deployment_report_{TIMESTAMP}.txt` - Deployment summaries

### Log Levels

- **INFO**: General information and progress updates
- **SUCCESS**: Successful operations and completions
- **WARNING**: Non-critical issues and retries
- **ERROR**: Failures and critical issues
- **DEBUG**: Detailed debugging information

### GUI Monitoring

The GUI provides real-time monitoring with:
- Color-coded log messages
- Progress indicators
- Statistics tracking (cycles, devices, uptime)
- System notifications on completion

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
python3 -c "from script_no3 import LoranetDeploymentBot; bot = LoranetDeploymentBot(); print(bot.test_ssh_connection('192.168.1.1', 'admin', 'admin'))"

# Test network scan
python3 -c "from script_no3 import LoranetDeploymentBot; bot = LoranetDeploymentBot(); print(bot.scan_network('192.168.1.0/24'))"
```

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

## 🔄 Version History

- **v1.0** - Initial release with core automation functionality
- **v1.1** - Added GUI interface and cross-platform support
- **v1.2** - Enhanced security features and MAC validation
- **v1.3** - Improved error handling and retry logic

---

**Author**: Aqmar  
**Date**: 2025-01-09  
**Version**: 1.3