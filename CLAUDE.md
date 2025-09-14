# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the Bivicom Configuration Bot - a network automation toolkit for configuring and deploying infrastructure on Bivicom IoT devices. The project combines device discovery, SSH automation, UCI network configuration, and infrastructure deployment into a unified workflow that operates without requiring device reboots.

## Architecture

### Core Scripts
- **`master.py`**: Primary network bot with continuous device scanning and automated 12-step configuration
- **`network_config.sh`**: Comprehensive bash script (2500+ lines) for network configuration and Docker service deployment  
- **`gui.py`**: Cross-platform tkinter GUI with real-time progress tracking, file upload support, and sound notifications
- **`master_backup.py`**: Legacy backup version of the main bot

### Key Classes

**NetworkBot (`master.py`):**
- Main automation class with continuous device scanning
- `scan_and_configure()`: Primary method for device detection and configuration
- `run_network_config()`: Executes 12-step automated deployment sequence
- `ping_host()`: Network connectivity testing
- Comprehensive logging with timestamped file output

**GUIBotWrapper (`gui.py`):**
- GUI-optimized wrapper around NetworkBot
- `log_message()`: Thread-safe logging with sound notifications
- Extends NetworkBot with GUI-specific features and callbacks

**NetworkBotGUI (`gui.py`):**
- Main GUI application class with tkinter interface
- Real-time log display with color-coded messages
- File upload support with Node-RED structure validation
- Visual progress indicators for all 12 configuration steps
- Cross-platform system notifications

### Network Configuration Modes

**Forward Mode (Deployment Phase):**
- WAN: `eth1` interface with DHCP protocol (temporary for infrastructure deployment)
- LAN: `eth0` interface with static IP (192.168.1.1)
- Used during Docker service installation and setup

**Reverse Mode (Production State):**
- WAN: `enx0250f4000000` interface with LTE protocol (final production configuration)
- LAN: `eth0` interface with static IP (192.168.1.1)
- Applied after successful deployment completion

## Common Commands

### Development Setup
```bash
# Virtual environment setup
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### Running the Bot
```bash
# Network bot - continuous scanning
python3 master.py

# Network bot - verbose mode with full command output
python3 master.py --verbose

# Network bot - custom IP and scan interval
python3 master.py --ip 192.168.1.100 --interval 5

# GUI application
python3 gui.py
```

### Manual Network Configuration
```bash
# Configure forward mode (deployment)
./network_config.sh --remote 192.168.1.1 admin admin forward

# Configure reverse mode (production)
./network_config.sh --remote 192.168.1.1 admin admin reverse

# Verify network configuration (auto-detects mode)
./network_config.sh --remote 192.168.1.1 admin admin verify-network

# Install all Docker services
./network_config.sh --remote 192.168.1.1 admin admin install-services

# Safe disk cleanup (preserves Docker images)
./network_config.sh --remote 192.168.1.1 admin admin safe-cleanup

# Reset device to factory defaults
./network_config.sh --remote 192.168.1.1 admin admin reset-device
```

### Comprehensive Testing (v2.5)
```bash
# Test all network configuration functions
./network_config.sh --remote 192.168.1.1 admin admin verify-network
./network_config.sh --remote 192.168.1.1 admin admin forward
./network_config.sh --remote 192.168.1.1 admin admin reverse

# Test password management
./network_config.sh --remote 192.168.1.1 admin admin set-password-admin
./network_config.sh --remote 192.168.1.1 admin admin set-password testpass123

# Test Docker functions
./network_config.sh --remote 192.168.1.1 admin admin install-docker
./network_config.sh --remote 192.168.1.1 admin admin install-docker-compose
./network_config.sh --remote 192.168.1.1 admin admin add-user-to-docker

# Test service installation
./network_config.sh --remote 192.168.1.1 admin admin install-nodered
./network_config.sh --remote 192.168.1.1 admin admin install-portainer
./network_config.sh --remote 192.168.1.1 admin admin install-restreamer

# Test utility functions
./network_config.sh --remote 192.168.1.1 admin admin check-dns
./network_config.sh --remote 192.168.1.1 admin admin fix-dns
./network_config.sh --remote 192.168.1.1 admin admin install-curl
./network_config.sh --remote 192.168.1.1 admin admin cleanup-disk

# Test Node-RED functions
./network_config.sh --remote 192.168.1.1 admin admin install-nodered-nodes
./network_config.sh --remote 192.168.1.1 admin admin import-nodered-flows
./network_config.sh --remote 192.168.1.1 admin admin update-nodered-auth newpass123

# Test advanced functions
./network_config.sh --remote 192.168.1.1 admin admin install-tailscale
./network_config.sh --remote 192.168.1.1 admin admin forward-and-docker
./network_config.sh --remote 192.168.1.1 admin admin install-services
```

### Testing and Diagnostics
```bash
# Test network connectivity
ping 192.168.1.1

# Test SSH connection
ssh admin@192.168.1.1

# Check deployed services
curl http://192.168.1.1:1880  # Node-RED
curl http://192.168.1.1:9000  # Portainer
curl http://192.168.1.1:8080  # Restreamer
```

### Build System
```bash
# Build standalone executable
./build.sh

# Manual PyInstaller build
pip install pyinstaller
pyinstaller --onefile --windowed --name="Bivicom Configurator V1" gui.py
```

## 12-Step Automated Deployment Sequence

When a device is detected at 192.168.1.1, the bot automatically executes:

1. **Configure Network FORWARD** - Set up temporary DHCP WAN for deployment
2. **Check DNS Connectivity** - Verify internet access
3. **Fix DNS Configuration** - Ensure proper DNS resolution
4. **Install curl** - Install curl package for GitHub downloads
5. **Install Docker** - Set up container runtime
6. **Install All Docker Services** - Deploy Node-RED, Portainer, Restreamer
7. **Install Node-RED Nodes** - Add custom nodes (ffmpeg, queue-gate, sqlite, serialport)
8. **Import Node-RED Flows** - Load radar and automation flows
9. **Update Node-RED Authentication** - Set secure password (L@ranet2025)
10. **Install Tailscale VPN Router** - Set up secure mesh networking
11. **Configure Network REVERSE** - Switch to final LTE WAN configuration
12. **Change Device Password** - Set secure device password (L@ranet2025)

## Configuration

### Environment Variables (`.env`)
```bash
# SSH Credentials
DEFAULT_USERNAME=admin
DEFAULT_PASSWORD=admin

# Tailscale Configuration
TAILSCALE_AUTH_KEY=tskey-auth-...

# Network Settings
TARGET_IP=192.168.1.1
SSH_TIMEOUT=10
```

### Docker Services Deployed

**Node-RED** (`nodered/node-red:latest`):
- Port: 1880 (HTTP)
- Features: Hardware privileges, serial port access, custom nodes
- Data: Persistent storage in `/data/nodered/`

**Portainer** (`portainer/portainer-ce:latest`):
- Ports: 9000 (HTTP), 9443 (HTTPS)
- Features: Docker container management UI
- Data: Persistent storage in `/data/portainer/`

**Restreamer** (`datarhei/restreamer:latest`):
- Port: 8080 (HTTP)
- Features: Video streaming with hardware access
- Credentials: admin/L@ranet2025

**Tailscale** (`tailscale/tailscale:latest`):
- Features: Mesh VPN router with device tagging
- Auth: Configured via environment variables

## File Upload Feature (GUI)

The GUI supports uploading custom Node-RED configuration files:

### Supported Files
- **`flows.json`**: Node-RED flow definitions (must be JSON array with id/type fields)
- **`package.json`**: Node-RED package dependencies (must be JSON object with name/version)

### Validation Requirements
- `flows.json`: Array format, each item must have `id` and `type` fields, tab items need `label`
- `package.json`: Object format, must have `name` and `version` fields, optional `dependencies`

### Smart Upload Logic
- When both files uploaded: Both sources automatically set to "uploaded"
- When only one file uploaded: That source set to "uploaded", other uses manual selection
- Files validated for Node-RED structure before acceptance
- Uploaded files stored in `uploaded_files/` directory after validation

## Security Considerations

### Device Authentication
- Default credentials: admin/admin (configurable via `.env`)
- SSH timeout enforcement (default: 10 seconds)
- Connection validation before deployment

### Network Safety
- No device reboots required - maintains SSH connectivity throughout
- UCI configuration backup before network changes
- Error handling to preserve SSH access during failures

### Tailscale Security
- 90-day authentication key rotation
- Device tagging for network identification
- Mesh connectivity with route acceptance

## Development Patterns

### Logging Strategy
- Timestamped log files in `logs/` directory: `bivicom_bot_YYYYMMDD_HHMMSS.log`
- Real-time console output with emoji indicators
- Verbose mode available with `--verbose` flag
- GUI logging with color-coded messages and sound notifications

### Error Handling
- Graceful degradation with fallback mechanisms
- Non-blocking warnings for non-critical failures
- Automatic retry logic for infrastructure deployment
- Clean resource cleanup on errors or interruption

### Threading Model
- Single-threaded deployment for reliability
- GUI operations run in separate thread
- Thread-safe logging between bot and GUI
- Graceful shutdown via signal handlers (SIGINT, SIGTERM)

### SSH Command Requirements
All system commands on target Bivicom devices require `sudo` privileges:
- UCI configuration: `sudo uci set/commit/show network`
- Network services: `sudo /etc/init.d/network restart`
- Package management: `sudo opkg update && sudo opkg install`
- Docker operations: `sudo docker`, `sudo usermod -aG docker`
- Tailscale setup: `sudo tailscale up --auth-key=<key>`

## Infrastructure Deployment

The bot deploys infrastructure by downloading and executing:
```bash
curl -sSL https://raw.githubusercontent.com/Loranet-Technologies/bivicom-radar/main/install.sh | bash -s -- --auto
```

This script installs Docker, Node-RED, Portainer, Restreamer, and Tailscale with proper configuration and security settings.