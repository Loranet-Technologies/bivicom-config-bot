# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

The Bivicom Configuration Bot is a network automation toolkit for configuring and deploying infrastructure on Bivicom IoT devices. It combines device discovery, SSH automation, UCI network configuration, and infrastructure deployment into a unified workflow that operates **without requiring device reboots**.

### Core Architecture

**Primary Scripts:**
- **`master.py`**: Network bot that continuously scans for devices and runs automated configuration
- **`network_config.sh`**: Comprehensive bash script for network configuration and Docker service deployment
- **`gui.py`**: Cross-platform GUI interface using tkinter for user-friendly operation (legacy)

**Key Components:**
- `NetworkBot`: Main bot class that handles continuous scanning and 8-step deployment sequence
- `network_config.sh`: Bash script with 20+ commands for complete device configuration
- Configuration management via `.env` file with SSH credentials and Tailscale settings

### Network Configuration Architecture

The bot operates with two primary network configuration modes:

**Forward Mode (Deployment)**: 
- WAN: `eth1` interface with DHCP protocol (temporary for deployment)
- LAN: `eth0` interface with static IP (192.168.1.1)
- Used during infrastructure deployment phase

**Reverse Mode (Final State)**:
- WAN: `enx0250f4000000` interface with LTE protocol (final production config)
- LAN: `eth0` + `wlan0` interfaces with user-configurable static IP
- Applied after successful deployment and infrastructure setup

## Common Development Commands

### Environment Setup
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### Running the Bot

#### Command Line (Main Script)
```bash
# Run in forever mode (continuous operation)
python3 master.py

# Run single cycle (exit after completion)
python3 master.py --single
```

#### GUI Version
```bash
# Launch GUI application
python3 gui.py
```

### Building Executables
```bash
# Build for current platform (macOS)
./build.sh

# Manual build with PyInstaller
pip install pyinstaller
pyinstaller --onefile --windowed \
    --name="Bivicom Configurator V1" \
    --add-data=".env:." \
    gui.py
```

### Testing and Validation
```bash
# Check target device connectivity
ping 192.168.1.1

# Test SSH connection manually
ssh admin@192.168.1.1

# Validate UCI configuration on target
ssh admin@192.168.1.1 "sudo uci show network"

# Check deployed services
ssh admin@192.168.1.1 "docker --version && node-red --version && tailscale version"
```

## Configuration Management

### Primary Configuration (`.env` file)

**Critical Parameters:**
- `DEFAULT_USERNAME`/`DEFAULT_PASSWORD`: SSH credentials for device access (default: admin/admin)
- `TAILSCALE_AUTH_KEY`: Tailscale VPN authentication key (90-day validity)
- `SSH_TIMEOUT`: Connection timeout in seconds (default: 10)
- `TARGET_IP`: Target device IP address (fixed: 192.168.1.1)
- `FINAL_IP`: Final LAN IP after deployment reversal (user-configurable)

**Timing Controls:**
- `CONFIG_WAIT_TIME`: Network configuration settling time (default: 5s)
- `CURL_INSTALL_WAIT`: Wait time after curl installation (default: 5s) 
- `CYCLE_RESTART_DELAY`: Delay between bot cycles in forever mode (default: 30s)
- Various other delay parameters for fine-tuning deployment timing

**Network Configuration:**
- `TAILSCALE_ADVERTISE_ROUTES`: Subnet routes to advertise via Tailscale
- `TAILSCALE_ADVERTISE_TAGS`: Device tags for Tailscale identification

## High-Level Architecture

### Deployment Workflow (10-Step Process)

1. **Network Discovery & SSH Connection**: Establishes connection to target device (192.168.1.1)
2. **Forward Network Configuration**: Configures temporary DHCP WAN (eth1) for deployment
3. **Connectivity Verification**: Tests internet access via WAN interface
4. **Curl Installation**: Ensures curl is available for script downloads
5. **Infrastructure Deployment**: Downloads and executes bivicom-radar installation script
6. **Installation Verification**: Validates Docker, Node-RED, and Tailscale installations
7. **Docker User Group Configuration**: Configures proper Docker permissions
8. **Network Configuration Reversal**: Restores original LTE WAN configuration
9. **Tailscale Setup**: Configures VPN with route advertising and device tagging
10. **Master Bot Orchestration**: Completes cycle and prepares for next iteration

### Advanced Network Configuration Process

**Enhanced WAN Configuration** (`apply_wan_config()`):
- UCI configuration commitment with error handling
- Empty route cleanup to prevent routing conflicts  
- Advanced network reload using multiple fallback methods:
  - Primary: `sudo /etc/init.d/network restart`
  - Enhanced hostname resolution fixes
  - Automatic default route management

**Route Management Features**:
- Automatic cleanup of invalid/empty default routes
- Proper gateway detection and default route addition
- Multiple fallback mechanisms for network service reload

### SSH and Device Management

**All network operations require `sudo` privileges** on target Bivicom devices:
- UCI (Unified Configuration Interface) commands: `sudo uci set/commit/show`
- Network service management: `sudo /etc/init.d/network restart`
- Package installation: `sudo apt update && sudo apt install -y`
- Docker operations: `sudo docker`, `sudo usermod -aG docker`
- Tailscale configuration: `sudo tailscale up --auth-key=<key>`

**Device Discovery Process:**
- Ping-based reachability testing to 192.168.1.1
- SSH credential validation with configurable timeout
- MAC address extraction for log file naming
- Connection persistence throughout deployment cycle

## Key Implementation Details

### Threading and Concurrency
- Single-threaded deployment process for reliability
- GUI runs deployment in separate thread to maintain UI responsiveness
- Graceful shutdown handling via signal handlers (SIGINT, SIGTERM)
- Thread-safe logging between bot operations and GUI display

### Error Handling Strategy
- Comprehensive error logging with multiple severity levels (INFO, SUCCESS, WARNING, ERROR)
- Graceful degradation with fallback mechanisms for network operations
- Non-blocking warnings for non-critical failures
- Automatic retry logic for infrastructure deployment (up to 2 retries)
- Clean resource cleanup on errors or interruption

### Infrastructure Deployment
**Target Script**: `https://raw.githubusercontent.com/Loranet-Technologies/bivicom-radar/main/install.sh`
**Deployment Command**: 
```bash
DEBIAN_FRONTEND=noninteractive curl -sSL --connect-timeout 30 --max-time 300 \
  https://raw.githubusercontent.com/Loranet-Technologies/bivicom-radar/main/install.sh \
  | bash -s -- --auto
```

**Services Deployed:**
- Docker container runtime with user group configuration
- Node-RED flow-based development tool
- Tailscale mesh VPN with route advertising

### Security Considerations

**Device Authentication:**
- Default admin/admin credentials (configurable via environment)
- SSH timeout enforcement to prevent hanging connections
- Automatic credential validation before deployment

**Network Safety:**
- No device reboots required - maintains SSH connectivity throughout
- UCI configuration backup before network changes
- Network connectivity preservation during configuration changes
- Error handling to maintain SSH access in failure scenarios

**Tailscale Integration:**
- 90-day authentication key rotation requirement
- Device tagging for network identification and access control
- Subnet route advertising based on final LAN IP configuration
- Full mesh connectivity with route acceptance from other devices

## Build System

The project includes a comprehensive build system for creating cross-platform executables:

**Build Script**: `build.sh` (macOS-specific)
- Creates virtual environment and installs dependencies
- Builds standalone executable using PyInstaller
- Includes configuration files and assets
- Generates windowed application bundle for GUI version

**Distribution Formats:**
- macOS: `.app` bundle and DMG installer
- Windows: `.exe` executable and installer
- Linux: AppImage and DEB packages

## Troubleshooting Guidelines

### Common Network Issues
```bash
# Check UCI network configuration
ssh admin@192.168.1.1 "sudo uci show network"

# Verify interface status
ssh admin@192.168.1.1 "ip addr show eth0; ip addr show eth1; ip addr show enx0250f4000000"

# Check routing table
ssh admin@192.168.1.1 "ip route show"

# Test connectivity
ssh admin@192.168.1.1 "ping -c 3 8.8.8.8"
```

### Service Verification
```bash
# Check deployed services
ssh admin@192.168.1.1 "docker --version && node-red --version && tailscale version"

# Network service status  
ssh admin@192.168.1.1 "sudo /etc/init.d/network status"

# Docker service status
ssh admin@192.168.1.1 "sudo systemctl status docker"
```

### Log Analysis
- Log files are named with format: `{MAC_ADDRESS}_{TIMESTAMP}.log`
- Real-time progress tracking with timestamped entries
- Color-coded log levels in GUI: INFO (gray), SUCCESS (green), WARNING (orange), ERROR (red)
- Detailed command execution logging with exit status codes

## Development Patterns

### Configuration Pattern
- Environment-based configuration with comprehensive defaults
- Runtime configuration merging and validation  
- Extensive timing and behavior customization options
- Secure credential management through environment variables

### Network Configuration Best Practices
- Always commit UCI changes before network reload: `sudo uci commit network`
- Clean up empty routes before and after network configuration changes
- Use multiple fallback methods for network service reload
- Verify connectivity after network changes before proceeding

### SSH Command Execution
- All system-level commands on target devices must use `sudo`
- Proper exit status checking and error output capture
- Command timeout handling for long-running operations
- Graceful connection cleanup and resource management

This architecture provides a robust, reliable, and user-friendly solution for automating Bivicom device deployment while maintaining network connectivity and operational safety throughout the process.

<citations>
<document>
<document_type>WARP_DOCUMENTATION</document_type>
<document_id>getting-started/quickstart-guide/coding-in-warp</document_id>
</document>
</citations>