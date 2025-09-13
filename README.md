# Bivicom Configuration Bot

A comprehensive network automation toolkit for configuring and deploying infrastructure on Bivicom IoT devices. This project combines device discovery, SSH automation, UCI network configuration, and infrastructure deployment into a unified workflow.

## 🆕 Recent Updates

### v2.2 - Enhanced Logging & Safe Cleanup
- **📝 Comprehensive Logging**: Full command output logging to timestamped files
- **🔍 Verbose Mode**: Real-time detailed output with `--verbose` flag
- **🛡️ Safe Disk Cleanup**: New `safe-cleanup` command that preserves Docker images
- **⚡ Optimized Sequence**: Removed cleanup-disk from automated Python bot sequence
- **📊 Enhanced Node-RED**: Updated settings with custom theme and static file serving
- **🔧 Improved Error Handling**: Better bcrypt hash generation and error reporting
- **📁 Log Management**: Automatic log file creation in `logs/` directory

### v2.1 - Enhanced Reliability & User Experience
- **🔊 Sound Notifications**: Audio feedback for success/error events across all platforms
- **🔗 Ping Verification**: Connectivity checks before SSH operations to prevent timeouts
- **🔄 Docker Retry Logic**: Robust image pulling with 3-attempt retry mechanism
- **⚙️ Non-interactive Installation**: Fixed debconf issues for automated package installation
- **🖥️ Enhanced GUI**: Username/password fields, progress tracking, and reset functionality
- **🛠️ Device Reset**: Complete factory reset with Docker cleanup and network restoration
- **🐛 Bug Fixes**: Fixed command parsing, remote execution, and error handling

### v2.0 - GUI Application & Automation
- **🖥️ GUI Application**: User-friendly interface with real-time logging
- **📊 Progress Tracking**: Visual 8-step configuration progress
- **🔐 User Configuration**: Username/password input with show/hide toggle
- **🔔 System Notifications**: Cross-platform desktop notifications
- **🔄 Reset Functionality**: Complete device reset to default state

## 🚀 Quick Start

### Prerequisites
- Python 3.7+
- SSH access to target Bivicom devices
- Network connectivity to target subnet (192.168.1.0/24)
- `sshpass` utility for password-based SSH authentication

### Installation
```bash
# Clone the repository
git clone <repository-url>
cd bivicom-config-bot

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt
```

### Basic Usage

#### Network Bot (Recommended)
```bash
# Start the network bot - automatically scans for 192.168.1.1
python3 master.py

# Custom IP and scan interval
python3 master.py --ip 192.168.1.100 --interval 5

# Verbose mode - shows full output from all commands
python3 master.py --verbose

# Custom IP with verbose logging
python3 master.py --ip 192.168.1.100 --verbose

# Help
python3 master.py --help
```

#### GUI Application (User-Friendly)
```bash
# Start the GUI application
python3 gui.py

# Features:
# - Real-time log display with color-coded messages
# - Step-by-step progress tracking (8-step configuration)
# - Username/password configuration fields
# - Sound notifications for success/error events
# - System notifications for completion
# - Reset device functionality
```

#### Manual Configuration Script
```bash
# Configure network FORWARD
./network_config.sh --remote 192.168.1.1 admin admin forward

# Safe disk cleanup (preserves Docker images)
./network_config.sh --remote 192.168.1.1 admin admin safe-cleanup

# Aggressive disk cleanup (removes all Docker images)
./network_config.sh --remote 192.168.1.1 admin admin cleanup-disk

# Install all Docker services
./network_config.sh --remote 192.168.1.1 admin admin install-services

# Install Tailscale VPN router
./network_config.sh --remote 192.168.1.1 admin admin install-tailscale

# See all available commands
./network_config.sh --help
```

## 📋 Features

### 🤖 Network Bot (`master.py`)
- **Continuous Scanning**: Automatically detects Bivicom devices at 192.168.1.1
- **10-Step Configuration**: Complete automated deployment sequence (cleanup-disk removed)
- **Comprehensive Logging**: Full command output saved to timestamped log files
- **Verbose Mode**: Real-time detailed output with `--verbose` flag
- **Error Handling**: Graceful failure recovery and retry logic
- **Real-time Logging**: Timestamped progress tracking with emojis
- **Ping Verification**: Connectivity checks before SSH operations
- **Robust Error Handling**: UCI availability checks and graceful failures

### 🖥️ GUI Application (`gui.py`)
- **Real-time Logging**: Color-coded log messages with timestamps
- **Progress Tracking**: Visual 8-step configuration progress with checkboxes
- **User Configuration**: Username/password input fields with show/hide toggle
- **Sound Notifications**: Audio feedback for success/error events (cross-platform)
- **System Notifications**: Desktop notifications for completion/errors
- **Reset Functionality**: Complete device reset to default state
- **Thread-safe**: Non-blocking UI with background operations

### 🔧 Configuration Script (`network_config.sh`)
- **Network Configuration**: FORWARD and REVERSE modes
- **Docker Services**: Node-RED, Portainer, Restreamer with hardware privileges
- **Node-RED Integration**: Custom nodes, flow import, and enhanced settings
- **Tailscale VPN**: Secure mesh networking with route advertising
- **Remote Execution**: SSH-based remote device management
- **Ping Verification**: Connectivity checks before SSH operations
- **Docker Image Retry**: Robust image pulling with retry logic
- **Non-interactive Installation**: Debconf configuration for automated setup
- **Safe Disk Cleanup**: Preserves Docker images while freeing space
- **Device Reset**: Complete factory reset functionality

### 🎯 10-Step Automated Sequence

When a device is detected, the bot automatically runs:

1. **Configure Network FORWARD** - Set up temporary DHCP WAN for deployment
2. **Check DNS Connectivity** - Verify internet access
3. **Fix DNS Configuration** - Ensure proper DNS resolution
4. **Install Docker** - Set up container runtime
5. **Install All Docker Services** - Deploy Node-RED, Portainer, Restreamer
6. **Install Node-RED Nodes** - Add custom nodes (ffmpeg, queue-gate, sqlite, serialport)
7. **Import Node-RED Flows** - Load your radar and automation flows
8. **Update Node-RED Authentication** - Set secure password (L@ranet2025)
9. **Install Tailscale VPN Router** - Set up secure mesh networking
10. **Configure Network REVERSE** - Switch to final LTE WAN configuration

> **Note**: The cleanup-disk step has been removed from the automated sequence to preserve Docker images during deployment.

## 🏗️ Architecture

### Network Configuration Modes

#### Forward Mode (Deployment)
- **WAN**: `eth1` interface with DHCP protocol
- **LAN**: `eth0` interface with static IP (192.168.1.1)
- **Purpose**: Temporary configuration for infrastructure deployment

#### Reverse Mode (Production)
- **WAN**: `enx0250f4000000` interface with LTE protocol
- **LAN**: `eth0` interface with static IP (192.168.1.1)
- **Purpose**: Final production configuration

### Docker Services

#### Node-RED
- **Image**: `nodered/node-red:latest`
- **Port**: 1880 (HTTP)
- **Features**: Hardware privileges, serial port access, custom nodes
- **Data**: Persistent storage in `/data/nodered/`

#### Portainer
- **Image**: `portainer/portainer-ce:latest`
- **Ports**: 9000 (HTTP), 9443 (HTTPS)
- **Features**: Docker container management
- **Data**: Persistent storage in `/data/portainer/`

#### Restreamer
- **Image**: `datarhei/restreamer:latest`
- **Port**: 8080 (HTTP)
- **Features**: Video streaming with hardware access
- **Credentials**: admin/L@ranet2025
- **Data**: Persistent storage in `/data/restreamer/`

#### Tailscale
- **Image**: `tailscale/tailscale:latest`
- **Features**: VPN router with route advertising
- **Auth Key**: Configured via environment variables
- **Routes**: Advertises 192.168.1.0/24 and 192.168.14.0/24

## ⚙️ Configuration

### Environment Variables (`.env`)
```bash
# SSH Credentials
DEFAULT_USERNAME=admin
DEFAULT_PASSWORD=admin

# Tailscale Configuration
TAILSCALE_AUTH_KEY=tskey-auth-kvwRxYc6o321CNTRL-6kggdogXnMdAdewR7Y7cMdNSp7yrJsSC

# Network Settings
TARGET_IP=192.168.1.1
SSH_TIMEOUT=10
```

### Network Bot Options
```bash
python3 master.py [OPTIONS]

Options:
  --ip IP              Target IP address to scan for (default: 192.168.1.1)
  --interval INTERVAL  Scan interval in seconds (default: 10)
  --verbose, -v        Show full output from all commands (default: show only summary)
  -h, --help          Show help message
```

### Configuration Script Commands
```bash
./network_config.sh [OPTIONS] [COMMAND]

Commands:
  forward             Configure network FORWARD (WAN=eth1 DHCP, LAN=eth0 static)
  reverse             Configure network REVERSE (WAN=enx0250f4000000 LTE, LAN=eth0 static)
  install-docker      Install Docker container engine
  install-services    Install all Docker services (Node-RED, Portainer, Restreamer)
  install-nodered-nodes Install Node-RED nodes (ffmpeg, queue-gate, sqlite, serialport)
  import-nodered-flows Import Node-RED flows from backup
  install-tailscale   Install Tailscale VPN router
  check-dns           Check internet connectivity and DNS
  fix-dns             Fix DNS configuration by adding Google DNS (8.8.8.8)
  safe-cleanup        Perform safe disk cleanup (preserves Docker images)
  cleanup-disk        Perform aggressive disk cleanup (removes all Docker images)
  add-user-to-docker  Add user to docker group
  install-curl        Install curl package
  set-password-admin  Change password back to admin
  reset-device        Reset device to default state (remove all Docker, reset network, restore defaults)

Options:
  --remote HOST [USER] [PASS]  Execute commands on remote host via SSH
  -h, --help                   Show help message
```

## 🔧 Advanced Usage

### Custom Node-RED Flows
1. Place your `flows.json` file in the project directory
2. Run: `./network_config.sh --remote 192.168.1.1 admin admin import-nodered-flows`

### Custom Node-RED Nodes
The script automatically installs these nodes:
- `node-red-contrib-ffmpeg@~0.1.1` - Video processing
- `node-red-contrib-queue-gate@~1.5.5` - Queue management
- `node-red-node-sqlite@~1.1.0` - SQLite database
- `node-red-node-serialport@2.0.3` - Serial communication

### Tailscale Configuration
- **Auth Key**: Set in `.env` file
- **Routes**: Automatically advertises device subnets
- **Access**: Secure mesh networking between devices

## 🛠️ Development

### Project Structure
```
bivicom-config-bot/
├── master.py              # Network bot with comprehensive logging (290+ lines)
├── network_config.sh      # Configuration script (2400+ lines)
├── gui.py                 # GUI interface (legacy)
├── requirements.txt       # Python dependencies
├── .env                   # Configuration file
├── logs/                  # Automatic log file directory
│   ├── bivicom_bot_20250109_143022.log
│   └── bivicom_bot_20250109_150315.log
├── docs/
│   └── CLAUDE.md         # Development documentation
├── WARP.md               # WARP IDE documentation
└── README.md             # This file
```

### Building Executables
```bash
# Build for current platform
./build.sh

# Manual build with PyInstaller
pip install pyinstaller
pyinstaller --onefile --windowed master.py
```

### Testing
```bash
# Test network connectivity
ping 192.168.1.1

# Test SSH connection
ssh admin@192.168.1.1

# Test Docker services
curl http://192.168.1.1:1880  # Node-RED
curl http://192.168.1.1:9000  # Portainer
curl http://192.168.1.1:8080  # Restreamer
```

## 🔍 Troubleshooting

### Common Issues

#### SSH Connection Failed
```bash
# Check device connectivity
ping 192.168.1.1

# Verify SSH service
ssh -v admin@192.168.1.1

# Check credentials in .env file
cat .env
```

#### Docker Installation Failed
```bash
# Check internet connectivity
./network_config.sh --remote 192.168.1.1 admin admin check-dns

# Verify network configuration
./network_config.sh --remote 192.168.1.1 admin admin forward
```

#### Node-RED Not Accessible
```bash
# Check container status
ssh admin@192.168.1.1 "sudo docker ps | grep nodered"

# Check logs
ssh admin@192.168.1.1 "sudo docker logs nodered"
```

### Log Files
- **Bot Logs**: Real-time console output with timestamps
- **Detailed Logs**: Full command output saved to `logs/bivicom_bot_YYYYMMDD_HHMMSS.log`
- **Verbose Mode**: Real-time detailed output with `--verbose` flag
- **Script Logs**: Detailed command execution logs
- **Container Logs**: Docker service logs via SSH

### Logging Features
```bash
# Normal mode - summary output, full logs saved to file
python3 master.py

# Verbose mode - real-time detailed output + file logging
python3 master.py --verbose

# Log files are automatically created in logs/ directory
ls logs/
# bivicom_bot_20250109_143022.log
# bivicom_bot_20250109_150315.log
```

## 🔒 Security

### Device Authentication
- **Default Credentials**: admin/admin (configurable)
- **SSH Security**: Timeout enforcement and connection validation
- **Sudo Privileges**: All system commands require elevated permissions

### Network Safety
- **No Reboots**: Maintains SSH connectivity throughout deployment
- **Configuration Backup**: Automatic UCI backup before changes
- **Error Recovery**: Graceful handling of network failures

### Tailscale Security
- **Auth Key Rotation**: 90-day key validity
- **Route Advertising**: Controlled subnet access
- **Device Tagging**: Network identification and access control

## 📚 Documentation

- **[WARP.md](WARP.md)** - WARP IDE development guide
- **[docs/CLAUDE.md](docs/CLAUDE.md)** - Claude AI development guide
- **[LICENSE](LICENSE)** - Project license

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the documentation files
3. Create an issue in the repository

---

**Bivicom Configuration Bot** - Automating IoT device deployment with confidence.
