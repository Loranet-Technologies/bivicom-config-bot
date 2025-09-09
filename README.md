# Bivicom Configurator V1

A comprehensive network automation toolkit for configuring and deploying infrastructure on Bivicom devices. This unified solution combines device discovery, SSH automation, UCI network configuration, and infrastructure deployment into a streamlined workflow.

## 🚀 Introduction & Process Flow

The Bivicom Configurator V1 automates the complete setup process for Bivicom devices with LTE WAN connectivity. Here's how it works:

### 📊 **Process Flow Overview**

```
┌─────────────────────────────────────────────────────────────────┐
│                    BIVICOM CONFIGURATOR V1                     │
│                      Process Flow (1-10)                       │
└─────────────────────────────────────────────────────────────────┘

1️⃣  NETWORK DISCOVERY & CONNECTION
    ├── Target IP: 192.168.1.1 (hardcoded)
    ├── SSH Authentication: admin/admin (configurable)
    └── Connection Timeout: 10s (configurable)

2️⃣  UCI BACKUP CREATION
    ├── Backup Location: /home/$USER (configurable)
    ├── Backup Name: uci_backup_YYYYMMDD_HHMMSS
    └── Backup Contents: Complete UCI configuration

3️⃣  NETWORK CONFIGURATION (LTE WAN)
    ├── WAN Interface: enx0250f4000000 (USB LTE device)
    ├── WAN Protocol: LTE (hardcoded)
    ├── LAN Interface: eth0 (hardcoded)
    ├── LAN IP: 192.168.1.1 (hardcoded)
    ├── LAN Protocol: Static (hardcoded)
    └── No Reboot Required (configuration applied live)

4️⃣  CONNECTIVITY VERIFICATION
    ├── WAN Route Check
    ├── Internet Connectivity Test
    └── Network Service Status

5️⃣  CURL INSTALLATION
    ├── Check if curl is installed
    ├── Install curl if missing
    └── Verify installation

6️⃣  INFRASTRUCTURE DEPLOYMENT
    ├── Docker Installation
    ├── Docker User Group Configuration
    ├── System Package Updates
    └── Service Configuration

7️⃣  INSTALLATION VERIFICATION
    ├── Docker Status Check
    ├── User Group Verification
    ├── Service Health Check
    └── System Status Validation

8️⃣  TAILSCALE SETUP
    ├── Tailscale Installation Check
    ├── Authentication Key Application
    ├── Network Join Process
    └── Connection Verification

9️⃣  UCI CONFIGURATION RESTORE
    ├── Restore from Backup (if needed)
    ├── Configuration Validation
    └── Service Restart (if required)

🔟  MASTER BOT ORCHESTRATION
    ├── Complete Cycle Validation
    ├── Success/Failure Reporting
    ├── Log Generation
    └── Next Cycle Preparation (if in forever mode)
```

### ⚙️ **Operation Modes**

#### **Single Cycle Mode**
- Runs steps 1-10 once
- Stops after completion
- Shows success/failure status

#### **Forever Mode**
- Continuously runs steps 1-10
- Retries on failure
- Runs until manually stopped
- Shows "stopped by user" when interrupted

### 🎯 **Key Benefits**

- **🔄 Automated**: Complete hands-off device setup
- **⚡ Fast**: No reboots required during configuration
- **🛡️ Safe**: Creates backups before making changes
- **📊 Monitored**: Real-time logging and status updates
- **🔧 Configurable**: All timing and credentials configurable via .env
- **🖥️ GUI**: User-friendly interface with progress tracking

### 📋 **Prerequisites**

- Bivicom device with default IP: 192.168.1.1
- SSH access with admin/admin credentials
- USB LTE device connected (enx0250f4000000)
- Network connectivity for package installation

## 📋 Table of Contents

- [Introduction & Process Flow](#-introduction--process-flow)
- [Overview](#overview)
- [Quick Start](#quick-start)
- [Key Features](#key-features)
- [Installation & Setup](#installation--setup)
- [Configuration](#configuration)
- [Usage](#usage)
- [Network Configuration Modes](#network-configuration-modes)
- [Deployment Flow](#deployment-flow)
- [Enhanced WAN Configuration](#enhanced-wan-configuration)
- [Build System](#build-system)
- [GUI Application](#gui-application)
- [Troubleshooting](#troubleshooting)
- [Security Considerations](#security-considerations)
- [Development Guide](#development-guide)
- [Support & Maintenance](#support--maintenance)

## Overview

The Bivicom Configuration Bot is a unified deployment script that combines all functionality from the original Script No. 1, 2, 3, and Master Bot into a single, streamlined solution. This version operates **WITHOUT REBOOTS** for faster and more reliable deployment and includes **FORWARD/REVERSE** network configuration modes.

### Core Architecture

**Primary Scripts:**
- **`unified_bivicom_bot_with_wan_config.py`**: Main unified bot with enhanced WAN configuration supporting forward/reverse modes
- **`master_bot.py`**: Legacy master coordination script  
- **`script_no1.py`, `script_no2.py`, `script_no3.py`**: Modular components (device discovery, network config, infrastructure deployment)
- **`radar_bot_gui.py`**: GUI interface using tkinter

**Key Class: UnifiedBivicomBot**

The main `UnifiedBivicomBot` class orchestrates the entire deployment workflow:

**Core Methods:**
- `configure_network_settings_forward()`: WAN=eth1 (DHCP), LAN=eth0 (Static)
- `configure_network_settings_reverse()`: WAN=enx0250f4000000 (LTE), LAN=eth0 (Static) 
- `apply_wan_config()`: Enhanced network configuration with route cleanup
- `deploy_infrastructure()`: Downloads and executes deployment scripts
- `check_wan_connectivity()`: Verifies network connectivity post-configuration
- `create_uci_backup()/restore_uci_backup_simple()`: Configuration backup/restore

## Quick Start

### Prerequisites
```bash
# Install required Python packages
pip install paramiko ipaddress plyer

# Or use virtual environment
python3 -m venv venv
source venv/bin/activate
pip install paramiko ipaddress plyer
```

### Running the Bot

#### Master Bot (Recommended)
```bash
# Standard configuration - continuous operation
python3 master.py

# Standard configuration - single cycle
python3 master.py --single
```

#### GUI Version
```bash
python3 gui.py
```

## Key Features

### ✅ **No Reboot Operation**
- All network configuration changes applied without device restart
- Faster deployment cycles
- More reliable operation
- Continuous SSH connection maintained

### ✅ **Standard Configuration Mode**
- **WAN**: enx0250f4000000 (USB LTE device)
- **LAN**: eth0 (Static IP 192.168.1.1)
- Simplified single configuration
- No mode selection required

### ✅ **Enhanced WAN Configuration Process**
- **Advanced Network Reload**: Uses `/usr/sbin/network_config` and `luci-reload` when available
- **Route Management**: Automatic cleanup of empty/invalid routes
- **Default Route Management**: Adds proper default routes when WAN is configured
- **Fallback Mechanisms**: Multiple fallback options for network reload
- **Comprehensive Error Handling**: Robust error handling with detailed logging

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

### Development Setup
```bash
# Virtual environment setup
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### Build and Distribution
```bash
# Build standalone executable (macOS)
./build.sh

# Or build manually
python3 -m venv venv
source venv/bin/activate
pip install paramiko ipaddress plyer pyinstaller
pyinstaller --onefile --windowed --name="Bivicom Configurator V1" gui.py
```

## Configuration

### Primary Config: `.env`

**Key Configuration Variables:**
- `DEFAULT_USERNAME` / `DEFAULT_PASSWORD`: SSH authentication credentials
- `SSH_TIMEOUT`: SSH connection timeout in seconds
- `TAILSCALE_AUTH_KEY`: Tailscale authentication key
- `CONFIG_WAIT_TIME`: Network configuration wait time
- `CURL_INSTALL_WAIT`: Curl installation wait time
- `VERIFICATION_WAIT`: Verification wait time
- `TAILSCALE_AUTH_WAIT`: Tailscale setup wait time
- `IP_CHECK_DELAY`: IP availability check delay
- `SSH_TEST_DELAY`: SSH test delay
- `CYCLE_RESTART_DELAY`: Delay between bot cycles

**Environment File Format:**
```bash
# SSH Authentication
DEFAULT_USERNAME=admin
DEFAULT_PASSWORD=admin
SSH_TIMEOUT=10

# Network Configuration Timing
CONFIG_WAIT_TIME=5
CURL_INSTALL_WAIT=5
VERIFICATION_WAIT=5
TAILSCALE_AUTH_WAIT=5

# Delay Settings
IP_CHECK_DELAY=2
SSH_TEST_DELAY=3
CYCLE_RESTART_DELAY=30

# Tailscale
TAILSCALE_AUTH_KEY=YOUR_TAILSCALE_AUTH_KEY_HERE
```

**All Available Parameters:**
```bash
# SSH Authentication
DEFAULT_USERNAME=admin
DEFAULT_PASSWORD=admin
SSH_TIMEOUT=10

# Network Configuration Timing
CONFIG_WAIT_TIME=5
CURL_INSTALL_WAIT=5
VERIFICATION_WAIT=5
TAILSCALE_AUTH_WAIT=5

# Delay Settings
IP_CHECK_DELAY=2
SSH_TEST_DELAY=3
LOG_CREATION_DELAY=1
BETWEEN_SCRIPTS_DELAY=5
SCRIPT_COMPLETION_DELAY=2
FINAL_SUCCESS_DELAY=3
CYCLE_RESTART_DELAY=30

# Tailscale Configuration
TAILSCALE_AUTH_KEY=YOUR_TAILSCALE_AUTH_KEY_HERE
```

**Critical Parameters:**
- `DEFAULT_USERNAME` / `DEFAULT_PASSWORD`: Required for SSH access
- `TAILSCALE_AUTH_KEY`: Required for Tailscale setup
- `SSH_TIMEOUT`: Controls connection timeout
- `CYCLE_RESTART_DELAY`: Controls how often the bot retries

## Usage

### Command Line Options
- `--single`: Run single cycle instead of forever mode

### Standard Configuration
```bash
# Run in forever mode with standard configuration
python3 master.py

# Run single cycle with standard configuration
python3 master.py --single
```

### Legacy Modular Scripts
```bash
# Note: These scripts are no longer available in the simplified version
# Use master.py for all functionality
```

## Network Configuration

### Standard Configuration
**Target**: WAN=enx0250f4000000 (USB LTE), LAN=eth0 (Static)

```bash
# WAN Configuration (USB LTE Device)
sudo uci set network.wan.proto='lte'
sudo uci set network.wan.ifname='enx0250f4000000'
sudo uci set network.wan.mtu=1500
sudo uci set network.wan.disabled='0'
sudo uci set network.wan.service='AUTO'
sudo uci set network.wan.auth_type='none'
sudo uci set network.wan.use_wifi_client='0'

# LAN Configuration (Static)
sudo uci set network.lan.proto='static'
sudo uci set network.lan.ifname='eth0'
sudo uci set network.lan.ipaddr='192.168.1.1'
sudo uci set network.lan.netmask='255.255.255.0'
sudo uci set network.lan.type='bridge'

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

#### 2. **Network Configuration (Enhanced LTE Setup)**
- **WAN Configuration**: Configures enx0250f4000000 (USB LTE device)
- **LAN Configuration**: Configures eth0 (Static IP 192.168.1.1)
- **Enhanced Process**: `apply_wan_config()` with route cleanup and advanced reload
- **Wait**: 5 seconds for configuration to settle

#### 3. **WAN Connectivity Check**
- Verifies WAN interface received IP (checks enx0250f4000000)
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

## Enhanced WAN Configuration

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

## Build System

### Multi-Platform Distribution
The build system creates distribution packages for:
- Windows (with INSTALL.bat)
- Linux (with INSTALL.sh)  
- macOS (with INSTALL.sh)

Each package includes all necessary scripts, configuration files, and platform-specific installation instructions.

### 🚀 Quick Start

#### Build for Current Platform
```bash
./build_all.sh
```

#### Build for Specific Platform
```bash
# macOS
./build_macos.sh

# Windows (on Windows)
build_windows.bat

# Ubuntu/Linux
./build_ubuntu.sh
```

### 📁 Files Overview

#### Core Files
- `radar_bot_gui.py` - Main GUI application
- `requirements_gui.txt` - Python dependencies for GUI builds
- `.env` - Environment configuration file

#### Build Scripts
- `build_all.sh` - Universal build script (detects platform)
- `build_macos.sh` - macOS-specific build script
- `build_windows.bat` - Windows-specific build script
- `build_ubuntu.sh` - Ubuntu/Linux-specific build script

#### Generated Outputs
- `dist/` - Distribution files directory
- `build/` - Temporary build files (cleaned after build)

### 🛠️ Prerequisites

#### All Platforms
- Python 3.8 or later
- pip (Python package installer)

#### macOS
- Xcode Command Line Tools
- macOS 10.15 (Catalina) or later

#### Windows
- Visual Studio Build Tools (optional, for some packages)
- Windows 10 or later

#### Ubuntu/Linux
- Build essentials: `sudo apt-get install build-essential`
- Python development headers: `sudo apt-get install python3-dev`
- Tkinter: `sudo apt-get install python3-tk`

### 📦 Generated Packages

#### macOS
- **App Bundle**: `BivicomRadarBot.app` - Native macOS application
- **DMG Installer**: `BivicomRadarBot-YYYYMMDD.dmg` - Disk image for distribution

#### Windows
- **Executable**: `BivicomRadarBot.exe` - Standalone Windows executable
- **Installer**: `BivicomRadarBot-Installer.exe` - NSIS installer (if NSIS available)
- **ZIP Package**: `BivicomRadarBot-Windows-YYYYMMDD.zip` - Portable package

#### Ubuntu/Linux
- **Executable**: `BivicomRadarBot` - Standalone Linux executable
- **AppImage**: `BivicomRadarBot-YYYYMMDD.AppImage` - Portable Linux application
- **DEB Package**: `BivicomRadarBot-YYYYMMDD.deb` - Debian package
- **Tarball**: `BivicomRadarBot-Ubuntu-YYYYMMDD.tar.gz` - Portable archive

### 🎯 Build System Features
- ✅ Automated dependency management
- ✅ Virtual environment isolation
- ✅ Platform-specific optimizations
- ✅ Multiple distribution formats
- ✅ Icon support (when available)
- ✅ Code signing ready (macOS)
- ✅ Installer generation (Windows/Linux)

### 🔧 Customization

#### Adding Icons
Place icon files in the project root:
- `icon.ico` - Windows icon
- `icon.icns` - macOS icon
- `icon.png` - Linux icon

#### Modifying Dependencies
Edit `requirements_gui.txt` to add or remove dependencies.

#### Custom Build Options
Modify the build scripts to:
- Change application name
- Add additional data files
- Modify PyInstaller options
- Customize installers

### PyInstaller Integration
```bash
# Create standalone executable
pyinstaller --onefile --add-data ".env:." master.py
```

## GUI Application

### 🎉 GUI Build System Complete!

#### ✅ What's Been Created

##### 1. **Main GUI Application** (`radar_bot_gui.py`)
- Cross-platform Tkinter-based GUI
- Real-time log display with color coding
- Progress indicators and status updates
- Forward/Reverse mode selection
- System notifications
- Graceful shutdown handling

##### 2. **Build Scripts**
- `build_all.sh` - Universal build script (auto-detects platform)
- `build_macos.sh` - macOS-specific build (creates .app bundle + DMG)
- `build_windows.bat` - Windows-specific build (creates .exe + installer)
- `build_ubuntu.sh` - Ubuntu/Linux-specific build (creates AppImage + DEB)

##### 3. **Updated Requirements** (`requirements_gui.txt`)
- Platform-specific dependencies
- PyInstaller for executable creation
- Cross-platform notification support

### 🎯 Key Features

#### GUI Features
- ✅ **Cross-platform**: Works on macOS, Windows, Ubuntu 20+
- ✅ **Real-time logs**: Color-coded log display (INFO, SUCCESS, WARNING, ERROR)
- ✅ **Progress tracking**: Visual progress indicators
- ✅ **Mode selection**: Forward/Reverse network configuration
- ✅ **System notifications**: Platform-specific notifications
- ✅ **Graceful shutdown**: Proper cleanup on exit
- ✅ **No console**: Pure GUI application (no terminal window)

#### Build System Features
- ✅ **Automated builds**: One-command builds for all platforms
- ✅ **Virtual environments**: Isolated dependency management
- ✅ **Multiple formats**: App bundles, installers, portable packages
- ✅ **Icon support**: Platform-specific icon integration
- ✅ **Code signing ready**: Prepared for macOS code signing
- ✅ **Clean builds**: Automatic cleanup of temporary files

### 📋 Next Steps

1. **Test the GUI**: Run `python3 radar_bot_gui.py` to test locally
2. **Build for your platform**: Run `./build_all.sh`
3. **Test the executable**: Run the generated executable
4. **Distribute**: Share the appropriate package for each platform

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

### Platform-Specific Issues

#### macOS
- **Code signing**: Add certificate for distribution
- **Gatekeeper**: May need to allow unsigned apps
- **Architecture**: Build for Intel/Apple Silicon as needed

#### Windows
- **Antivirus**: May flag PyInstaller executables
- **DLL issues**: Ensure Visual C++ redistributables installed
- **Path issues**: Use forward slashes in build scripts

#### Linux
- **Library dependencies**: Install system packages
- **AppImage**: May need FUSE for older systems
- **Desktop integration**: Check desktop file permissions

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

## Development Guide

### Commands Requiring Sudo Access

**IMPORTANT**: All commands executed on target Bivicom devices via SSH require `sudo` privileges. The scripts automatically prepend `sudo` to all UCI and system commands.

#### UCI Configuration Commands (All require sudo)
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

#### Network Service Commands (All require sudo)
```bash
# Network service control
sudo /etc/init.d/network reload
sudo /etc/init.d/network restart

# Advanced network configuration tools
sudo /usr/sbin/network_config
sudo /usr/sbin/luci-reload network
```

#### Package Management (Requires sudo)
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

#### Node.js and Node-RED Installation (Requires sudo)
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

#### System Configuration (Requires sudo)
```bash
# Host file modifications
echo '127.0.0.1 localhost.localdomain' | sudo tee -a /etc/hosts

# Package management fixes
DEBIAN_FRONTEND=noninteractive sudo apt-get update
sudo apt-get install -f -y
sudo dpkg --configure -a
```

#### Shell Script Operations (wan_config_simple.sh)
All operations in `wan_config_simple.sh` require sudo:
```bash
sudo /home/admin/wan_config_simple.sh apply      # Apply WAN configuration
sudo /home/admin/wan_config_simple.sh backup     # Backup configuration
sudo /home/admin/wan_config_simple.sh configure  # Interactive configuration
sudo /home/admin/wan_config_simple.sh fix-lan    # Fix LAN issues
```

#### OpenWrt System Commands (All require sudo)
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

#### Tailscale Operations (Require sudo)
```bash
# Tailscale service management
sudo tailscale up --authkey=<AUTH_KEY>
sudo tailscale down
tailscale status  # Status check doesn't require sudo
sudo tailscale status  # May require sudo on some systems
sudo systemctl enable tailscaled
sudo systemctl start tailscaled
```

#### Sudo Privilege Requirements
- The target Bivicom devices must have the `admin` user configured with sudo privileges
- Default credentials (admin/admin) must have passwordless sudo access for network operations
- All UCI (Unified Configuration Interface) commands require root privileges
- Network service restarts and configuration changes require elevated permissions
- Package installation and system service management require root access

### Development Patterns

#### Error Handling Strategy
- Graceful degradation with multiple fallback mechanisms
- Non-blocking error logging for non-critical failures
- Automatic retry logic for network operations
- Clean resource cleanup on errors or interruption

#### Threading Model
- Multi-threaded device discovery using `ThreadPoolExecutor`
- Thread-safe logging and state management  
- Configurable concurrency limits (default: 50 threads)
- Proper signal handling for graceful shutdown

#### Configuration Pattern
- JSON-based configuration with comprehensive defaults
- Runtime configuration merging and validation
- Environment-specific parameter overrides
- Extensive timing and behavior customization options

### Testing and Debugging

#### Network Diagnostics
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

#### Service Verification
```bash
# Check deployed services
ssh admin@192.168.1.1 "docker --version && node-red --version && tailscale version"

# Network service status
ssh admin@192.168.1.1 "sudo /etc/init.d/network status"
```

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

### Logging & Monitoring

#### Log Files
- **Format**: `{MAC_ADDRESS}_{TIMESTAMP}.log`
- **Example**: `a019b2d27afa_20250109_143709.log`
- **Location**: Current working directory
- **Content**: Complete deployment cycle output with enhanced WAN config details

#### Log Levels
- **INFO**: General information and progress
- **SUCCESS**: Successful operations
- **WARNING**: Non-critical issues
- **ERROR**: Critical failures
- **DEBUG**: Detailed debugging information

#### Enhanced Logging Features
- **Route Cleanup Logging**: Detailed route management operations
- **Network Reload Logging**: Advanced reload method selection and results
- **Fallback Logging**: Fallback method usage and results
- **Command Detection Logging**: Available command detection results

#### Real-time Monitoring
- All operations logged with timestamps
- Real-time progress indication
- Detailed error messages for troubleshooting
- Step-by-step completion tracking

### Performance Benefits

#### Enhanced WAN Config Advantages
- ⚡ **Faster Execution**: Advanced reload methods are more efficient
- 🔄 **Better Reliability**: Multiple fallback options ensure success
- 🛡️ **Route Management**: Automatic cleanup prevents routing issues
- 📊 **Better Monitoring**: Enhanced logging for all network operations
- 🐛 **Easier Debugging**: Detailed logging of all network operations

#### No Reboot Advantages
- ⚡ **Faster Execution**: No waiting for device restart
- 🔄 **Continuous Operation**: No interruption in SSH connection
- 🛡️ **More Reliable**: No risk of device not coming back online
- 📊 **Better Monitoring**: Can monitor all steps in real-time
- 🐛 **Easier Debugging**: No need to reconnect after reboot

#### Timing Optimizations
- **Configurable Delays**: All wait times configurable in .env file
- **Smart Timing**: Delays only where necessary for stability
- **Parallel Operations**: Where possible, operations run in parallel

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

The Bivicom Configuration Bot provides a robust, efficient, and reliable solution for deploying Bivicom infrastructure. The enhanced WAN configuration process significantly improves network reliability while maintaining all the functionality of the original multi-script approach.

### Key Benefits:
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

---

**🎉 Ready to Use!**

The Bivicom Configuration Bot is now complete and ready for creating standalone applications. The build scripts will handle all the complexity of creating cross-platform executables with proper packaging and distribution formats.

**Happy building! 🚀**
