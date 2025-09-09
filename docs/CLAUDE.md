# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the Bivicom Configuration Bot repository - a network automation toolkit for configuring and deploying infrastructure on Bivicom devices. The project combines device discovery, SSH automation, UCI network configuration, and infrastructure deployment into a unified workflow.

**⚠️ IMPORTANT**: All network configuration, package management, and system service commands on target Bivicom devices require `sudo` privileges. The scripts automatically execute commands with elevated permissions on remote devices via SSH.

## Core Architecture

### Primary Scripts
- **`unified_bivicom_bot_with_wan_config.py`**: Main unified bot with enhanced WAN configuration supporting forward/reverse modes
- **`master_bot.py`**: Legacy master coordination script  
- **`script_no1.py`, `script_no2.py`, `script_no3.py`**: Modular components (device discovery, network config, infrastructure deployment)
- **`radar_bot_gui.py`**: GUI interface using tkinter

### Key Class: UnifiedBivicomBot

The main `UnifiedBivicomBot` class orchestrates the entire deployment workflow:

**Core Methods:**
- `configure_network_settings_forward()`: WAN=eth1 (DHCP), LAN=eth0 (Static)
- `configure_network_settings_reverse()`: WAN=enx0250f4000000 (LTE), LAN=eth0 (Static) 
- `apply_wan_config()`: Enhanced network configuration with route cleanup
- `deploy_infrastructure()`: Downloads and executes deployment scripts
- `check_wan_connectivity()`: Verifies network connectivity post-configuration
- `create_uci_backup()/restore_uci_backup_simple()`: Configuration backup/restore

### Configuration Architecture

**Forward Mode (Default)**: Ethernet-based setup
- WAN: eth1 interface with DHCP protocol
- LAN: eth0 interface with static IP (192.168.1.1)
- Manual setup: `sudo uci set network.wan.ifname='eth1'`

**Reverse Mode**: LTE modem setup  
- WAN: enx0250f4000000 interface with LTE protocol
- LAN: eth0 interface with static IP (192.168.1.1)
- Manual setup: `sudo uci set network.wan.ifname='enx0250f4000000'`

## Common Commands

### Development Setup
```bash
# Virtual environment setup
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# GUI dependencies (optional)
pip install -r requirements_gui.txt
```

### Running the Bot

#### Unified Bot (Recommended)
```bash
# Forward mode - continuous operation
python3 unified_bivicom_bot_with_wan_config.py

# Forward mode - single cycle
python3 unified_bivicom_bot_with_wan_config.py --single

# Reverse mode - continuous operation  
python3 unified_bivicom_bot_with_wan_config.py --reverse

# Reverse mode - single cycle
python3 unified_bivicom_bot_with_wan_config.py --single --reverse
```

#### GUI Version
```bash
python3 radar_bot_gui.py
```

#### Legacy Modular Scripts
```bash
python3 script_no1.py  # Device discovery
python3 script_no2.py  # Network configuration  
python3 script_no3.py  # Infrastructure deployment
```

### Build and Distribution
```bash
# Create multi-platform packages
./create_multi_platform_packages.sh

# Build standalone executable
pip install pyinstaller
pyinstaller --onefile unified_bivicom_bot_with_wan_config.py
```

## Configuration Management

### Primary Config: `config.json`

**Key Configuration Sections:**
- `network_range`: Target subnet for device scanning (default: "192.168.1.0/24")
- `default_credentials`: SSH authentication credentials
- `target_mac_prefixes`: Bivicom device MAC identification patterns
- `network_configuration`: Forward mode interface settings
- `reverse_configuration`: LTE mode interface settings  
- `tailscale`: VPN authentication configuration
- `delays`: Timing controls for each deployment phase

**Critical Parameters:**
```json
{
  "network_configuration": {
    "wan_interface": "eth1",           // Forward: ethernet WAN
    "lan_interface": "eth0", 
    "wan_protocol": "dhcp",
    "lan_protocol": "static"
  },
  "reverse_configuration": {
    "wan_interface": "enx0250f4000000", // Reverse: USB LTE WAN  
    "wan_protocol": "lte"
  }
}
```

## Enhanced WAN Configuration Process

### Network Configuration Flow
1. **UCI Backup**: `sudo uci backup folder /home/$USER`
2. **Interface Configuration**: Set WAN/LAN interfaces and protocols via UCI
3. **Enhanced Application**: `apply_wan_config()` with advanced reload methods
4. **Route Management**: `cleanup_empty_routes()` removes invalid routes
5. **Connectivity Verification**: Test WAN connectivity and internet access
6. **Infrastructure Deployment**: Execute installation scripts
7. **Configuration Restore**: `restore_uci_backup_simple()` reverts to original config

### Advanced Network Reload Methods
- **Primary**: `sudo /usr/sbin/network_config` (OpenWrt native tool)
- **Secondary**: `sudo luci-reload network` (LuCI web interface reload)
- **Fallback**: `sudo /etc/init.d/network restart` (standard init script)

### Route Management Features  
- Automatic cleanup of empty gateway routes
- Default route management based on WAN configuration
- Multiple fallback mechanisms for network reload operations

## SSH and Device Management

### Device Discovery Process
- Network scanning using `ipaddress` library across configured subnet
- Multi-threaded device discovery with configurable thread pool
- MAC address validation against authorized OUI patterns
- SSH connectivity testing with credential validation

### SSH Connection Management  
- Automatic SSH connection establishment and cleanup
- Connection timeout handling and retry logic
- Secure credential management through configuration file
- Session persistence throughout deployment workflow

## Infrastructure Deployment

### Deployment Workflow
1. **Curl Installation**: Verify/install curl via `sudo opkg update && sudo opkg install curl`
2. **Script Download**: Fetch from `https://raw.githubusercontent.com/Loranet-Technologies/bivicom-radar/main/install.sh`  
3. **Automated Execution**: Run with `--auto` flag for non-interactive deployment
4. **Service Verification**: Check Docker, Node-RED, and Tailscale installations
5. **Tailscale Authentication**: Set up VPN using configured auth key

### Monitoring and Logging
- Real-time deployment progress tracking
- Comprehensive error logging with timestamps
- Log files named: `{MAC_ADDRESS}_{TIMESTAMP}.log`
- Configurable log levels: DEBUG, INFO, WARNING, ERROR

## Testing and Debugging

### Network Diagnostics
```bash
# Verify UCI configuration
ssh admin@192.168.1.1 "sudo uci show network"

# Check interface status
ssh admin@192.168.1.1 "ip addr show eth0; ip addr show eth1; ip addr show enx0250f4000000"

# Verify routing table  
ssh admin@192.168.1.1 "ip route show"  # Read-only, no sudo needed

# Test connectivity
ssh admin@192.168.1.1 "ping -c 3 8.8.8.8"
```

### Service Verification
```bash
# Check deployed services
ssh admin@192.168.1.1 "docker --version && node-red --version && tailscale version"

# Network service status
ssh admin@192.168.1.1 "sudo /etc/init.d/network status"
```

## Commands Requiring Sudo Access

**IMPORTANT**: All commands executed on target Bivicom devices via SSH require `sudo` privileges. The scripts automatically prepend `sudo` to all UCI and system commands.

### UCI Configuration Commands (All require sudo)
```bash
# WAN configuration
sudo uci set network.wan.proto='dhcp'  # or 'lte' for reverse mode
sudo uci set network.wan.ifname='eth1'  # or 'enx0250f4000000' for LTE
sudo uci set network.wan.mtu=1500

# LAN configuration
sudo uci set network.lan.proto='static'
sudo uci set network.lan.ifname='eth0'
sudo uci set network.lan.ipaddr='192.168.1.1'
sudo uci set network.lan.netmask='255.255.255.0'

# Commit changes
sudo uci commit network

# Import/export configuration
sudo uci export > /backup/file
sudo uci import < /backup/file

# Show network configuration
sudo uci show network
```

### Network Service Commands (All require sudo)
```bash
# Network service control
sudo /etc/init.d/network reload
sudo /etc/init.d/network restart

# Advanced network configuration tools
sudo /usr/sbin/network_config
sudo /usr/sbin/luci-reload network
```

### Package Management (Requires sudo)
```bash
# OpenWrt package management
sudo opkg update
sudo opkg install curl
sudo opkg list-installed

# Debian/Ubuntu package management
sudo apt update && sudo apt install -y curl

# System maintenance
sudo usermod -aG docker $USER
sudo systemctl start docker
sudo service docker start
sudo /etc/init.d/docker start
```

### Node.js and Node-RED Installation (Requires sudo)
```bash
# Node.js installation
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs

# Node-RED installation
sudo npm install -g --unsafe-perm node-red

# Service management
sudo systemctl start node-red
sudo service node-red start
```

### System Configuration (Requires sudo)
```bash
# Host file modifications
echo '127.0.0.1 localhost.localdomain' | sudo tee -a /etc/hosts

# Package management fixes
DEBIAN_FRONTEND=noninteractive sudo apt-get update
sudo apt-get install -f -y
sudo dpkg --configure -a
```

### Shell Script Operations (wan_config_simple.sh)
All operations in `wan_config_simple.sh` require sudo:
```bash
sudo /home/admin/wan_config_simple.sh apply      # Apply WAN configuration
sudo /home/admin/wan_config_simple.sh backup     # Backup configuration
sudo /home/admin/wan_config_simple.sh configure  # Interactive configuration
sudo /home/admin/wan_config_simple.sh fix-lan    # Fix LAN issues
```

### OpenWrt System Commands (All require sudo)
```bash
# UCI system operations
sudo uci add system system
sudo uci set system.@system[0].hostname='bivicom-device'
sudo uci commit system

# Network interface operations
sudo ifconfig eth0 up
sudo ifconfig eth0 down
sudo ifup wan
sudo ifdown wan
sudo ip link set eth0 up
sudo ip link set eth0 down

# Route management
sudo ip route add default via 192.168.1.1
sudo ip route del default
sudo route add default gw 192.168.1.1

# Service management
sudo /etc/init.d/network enable
sudo /etc/init.d/network disable
sudo /etc/init.d/firewall restart
sudo /etc/init.d/dnsmasq restart

# System configuration
sudo sysctl -w net.ipv4.ip_forward=1
sudo echo 'net.ipv4.ip_forward=1' | sudo tee -a /etc/sysctl.conf
```

### Tailscale Operations (Require sudo)
```bash
# Tailscale service management
sudo tailscale up --authkey=<AUTH_KEY>
sudo tailscale down
tailscale status  # Status check doesn't require sudo
sudo tailscale status  # May require sudo on some systems
sudo systemctl enable tailscaled
sudo systemctl start tailscaled
```

### Sudo Privilege Requirements
- The target Bivicom devices must have the `admin` user configured with sudo privileges
- Default credentials (admin/admin) must have passwordless sudo access for network operations
- All UCI (Unified Configuration Interface) commands require root privileges
- Network service restarts and configuration changes require elevated permissions
- Package installation and system service management require root access

## ✅ Code Updated: All Commands Now Include Proper Sudo

**Status: RESOLVED** - All commands in the Python scripts have been updated to include the required `sudo` prefix where needed.

### Fixed Commands in unified_bivicom_bot_with_wan_config.py:

**✅ Tailscale Authentication** (Line 781):
```python
tailscale_cmd = f"sudo tailscale up --authkey={auth_key}"
```

**✅ Network Service Restart** (Line 895):
```python
network_config_cmd = "sudo /etc/init.d/network restart"
```

**✅ Network Service Reload** (Line 954):
```python
ssh.exec_command("sudo /etc/init.d/network reload")
```

**✅ Route Cleanup Commands** (Lines 806-810):
```python
cleanup_commands = [
    "ip route show | grep 'default via $' | while read route; do sudo ip route del $route 2>/dev/null || true; done",
    "ip route show | grep 'default via  metric' | while read route; do sudo ip route del $route 2>/dev/null || true; done",
    "ip route show | grep 'default via.*dev $' | while read route; do sudo ip route del $route 2>/dev/null || true; done"
]
```

**✅ Route Addition** (Line 827):
```python
add_route_cmd = f"sudo ip route add default via \"{wan_gateway}\" dev \"{wan_ifname}\" 2>/dev/null || true"
```

### Benefits of These Fixes:
- **Tailscale Setup**: Now works correctly with proper privileges
- **Network Service Management**: Network restart/reload operations execute successfully
- **Route Management**: Route cleanup and default route addition work properly
- **System Configuration**: Complete deployments with all operations functioning correctly

### Debug Mode
Set `"log_level": "DEBUG"` in `config.json` for detailed operation logging.

## Security Considerations

### Device Authentication
- Default credentials: admin/admin (configurable)
- MAC address validation using authorized OUI database
- SSH timeout and connection security
- Automatic credential validation before deployment

### Configuration Safety
- Automatic UCI backup before any network changes
- Configuration restore capability to revert changes
- Network connectivity preservation throughout process
- Error handling to maintain SSH access

### Backup Management
- UCI backups stored in `/home/$USER/` on target device
- Timestamped backup files for traceability
- Automatic cleanup of deployment artifacts
- Secure credential storage in configuration file

## Build System

### Multi-Platform Distribution
The `create_multi_platform_packages.sh` script generates distribution packages for:
- Windows (with INSTALL.bat)
- Linux (with INSTALL.sh)  
- macOS (with INSTALL.sh)

Each package includes all necessary scripts, configuration files, and platform-specific installation instructions.

### PyInstaller Integration
```bash
# Create standalone executable
pyinstaller --onefile --add-data "config.json:." master.py
```

## Development Patterns

### Error Handling Strategy
- Graceful degradation with multiple fallback mechanisms
- Non-blocking error logging for non-critical failures
- Automatic retry logic for network operations
- Clean resource cleanup on errors or interruption

### Threading Model
- Multi-threaded device discovery using `ThreadPoolExecutor`
- Thread-safe logging and state management  
- Configurable concurrency limits (default: 50 threads)
- Proper signal handling for graceful shutdown

### Configuration Pattern
- JSON-based configuration with comprehensive defaults
- Runtime configuration merging and validation
- Environment-specific parameter overrides
- Extensive timing and behavior customization options