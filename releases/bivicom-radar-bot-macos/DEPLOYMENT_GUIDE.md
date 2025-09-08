# Bivicom Radar Bot - Deployment Guide

Technical deployment guide for the Bivicom Radar Bot automation system.

## 🏗️ Architecture Overview

The Bivicom Radar Bot consists of several components working together to automate device setup and infrastructure deployment:

### Core Components

1. **Master Bot** (`master_bot.py`): Orchestrates the entire deployment process
2. **Network Configuration Script** (`script_no1.py`): Configures WAN/LAN interfaces
3. **Connectivity Verification Script** (`script_no2.py`): Tests internet connectivity
4. **Infrastructure Deployment Script** (`script_no3.py`): Installs Bivicom Radar system
5. **GUI Application** (`radar_bot_gui.py`): User-friendly interface

### Deployment Flow

```
Network Check → SSH Test → MAC Detection → Log Creation → 
Network Config → Connectivity Test → Infrastructure Deploy → Completion
```

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

## 🔐 Security Configuration

### SSH Security

- **Default Credentials**: admin/admin (change in production)
- **Connection Timeout**: 10 seconds
- **Key Exchange**: RSA/DSA key authentication
- **Cipher**: AES-256 encryption

### MAC Address Validation

Authorized Bivicom OUI prefixes:
```json
{
  "a4:7a:cf": "VIBICOM COMMUNICATIONS INC.",
  "00:06:2c": "Bivio Networks",
  "00:24:d9": "BICOM, Inc.",
  "00:52:24": "Bivicom (custom/private)",
  "02:52:24": "Bivicom (alternative)"
}
```

### Network Security

- **Trusted Network**: Bot must run on trusted network
- **Device Validation**: Only authorized devices are configured
- **Audit Logging**: Complete operation logging
- **Error Handling**: Secure error reporting

## 📊 Deployment Process Details

### Stage 1: Network Check
```python
# Ping target device
subprocess.run(['ping', '-c', '1', '192.168.1.1'])
```

### Stage 2: SSH Test
```python
# Test SSH connection
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.1.1', username='admin', password='admin')
```

### Stage 3: MAC Detection
```python
# Get MAC from ARP table
arp_output = subprocess.check_output(['arp', '-n', '192.168.1.1'])
mac_address = extract_mac_from_arp(arp_output)
```

### Stage 4: Network Configuration
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

### Stage 5: Connectivity Verification
```python
# Test internet connectivity
ssh.exec_command('ping -c 3 8.8.8.8')
```

### Stage 6: Infrastructure Deployment
```python
# Deploy Bivicom Radar
deploy_command = 'curl -sSL https://raw.githubusercontent.com/Loranet-Technologies/bivicom-radar/main/install.sh | bash -s -- --auto'
ssh.exec_command(deploy_command)
```

## 📝 Logging System

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

## 🔧 Configuration Management

### Configuration File: `bot_config.json`

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

## 🚀 Deployment Commands

### Master Bot Execution
```bash
python3 master_bot.py
```

### Individual Script Execution
```bash
# Network configuration only
python3 script_no1.py

# Connectivity verification only
python3 script_no2.py

# Infrastructure deployment only
python3 script_no3.py
```

### GUI Application
```bash
python3 radar_bot_gui.py
```

## 🛠️ Troubleshooting

### Common Issues

1. **SSH Connection Failed**
   - Check network connectivity
   - Verify SSH credentials
   - Ensure SSH service is running

2. **Device Not Found**
   - Verify device is at 192.168.1.1
   - Check network configuration
   - Ensure device is powered on

3. **MAC Address Validation Failed**
   - Check authorized OUI list
   - Verify device manufacturer
   - Disable strict validation if needed

4. **Network Configuration Failed**
   - Check UCI system availability
   - Verify interface names
   - Check permissions

### Debug Mode

Enable debug logging:
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
```

## 📈 Performance Optimization

### Threading Configuration
```json
{
  "max_threads": 50,
  "scan_timeout": 5,
  "ssh_timeout": 10
}
```

### Network Optimization
- Use wired connections for stability
- Ensure adequate bandwidth
- Minimize network latency

### System Resources
- Monitor CPU usage during deployment
- Ensure sufficient memory
- Check disk space for logs

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

## 📞 Support

For technical support:
- Check log files for detailed error information
- Review this deployment guide
- Contact the development team
- Submit issues on GitHub

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👨‍💻 Author

**Aqmar** - *Initial work* - [Loranet Technologies](https://github.com/Loranet-Technologies)
