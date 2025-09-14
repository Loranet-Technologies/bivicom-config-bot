# Bivicom Configuration Bot

A comprehensive network automation toolkit for configuring and deploying infrastructure on Bivicom IoT devices. This project combines device discovery, SSH automation, UCI network configuration, and infrastructure deployment into a unified workflow.

## ⚡ **Quick Install & Use**

```bash
# Install from PyPI
pip install bivicom-config-bot

# Run the network bot
bivicom-bot --help

# Run the GUI application
bivicom-gui
```

**That's it!** Your Bivicom Configuration Bot is ready to use. See the [Installation](#installation) section below for more options.

## 🆕 Recent Updates

### v1.0.3 - PyPI Package Distribution
- **📦 PyPI Package**: Available on PyPI as `bivicom-config-bot`
- **🚀 Easy Installation**: One-command install with `pip install bivicom-config-bot`
- **🔧 Global Commands**: `bivicom-bot` and `bivicom-gui` available globally after installation
- **📋 Optional Dependencies**: Support for GUI, build tools, and development dependencies
- **🎯 Professional Packaging**: Complete Python package structure with proper metadata
- **📚 Enhanced Documentation**: Updated README with PyPI installation and usage instructions
- **🌐 Cross-Platform**: Works on Windows, macOS, and Linux via pip

### v1.0.1 - Test Build Documentation & Script
- **📋 Test Build Documentation**: Comprehensive `TEST_BUILD.md` with build system overview
- **🧪 Test Build Script**: Automated `test_build.sh` script for testing build processes
- **🔧 Build System Testing**: Complete testing framework for standalone application builds
- **📊 Build Validation**: Automated validation of PyInstaller builds across platforms
- **🚀 Cross-Platform Support**: Testing for Windows, macOS, and Linux builds
- **📝 Build Documentation**: Detailed instructions for manual and automated builds

### v2.5 - Comprehensive Testing & Production Validation
- **🧪 Complete Function Testing**: All 20+ network_config.sh functions tested and validated
- **✅ Production Ready**: Comprehensive testing confirms all functions working correctly
- **🔍 Enhanced Verification**: New `verify-network` command with auto-detection of FORWARD/REVERSE modes
- **🛠️ Improved Check Mechanisms**: Fixed interface name handling (enx0250f4000000 vs usb0 for LTE)
- **📊 Test Results Documentation**: Complete test coverage documentation with results summary
- **🚀 Performance Validation**: All functions tested for reliability, error handling, and performance
- **🔧 SSH Automation**: Fully automated SSH operations with password and key authentication
- **📝 Comprehensive Logging**: Enhanced logging and status reporting across all functions

### v2.4 - File Upload Feature with Smart Source Logic
- **📁 File Upload Support**: Upload custom flows.json and package.json files directly from GUI
- **✅ Node-RED Structure Validation**: Comprehensive validation of Node-RED file structures
- **🔍 flows.json Validation**: Validates array format, required fields (id, type), and Node-RED flow structure
- **📦 package.json Validation**: Validates object format, required fields (name, version), and dependency structure
- **🎯 Smart Upload Logic**: Uses uploaded files when both are available, falls back to user selection
- **📦 Package Source Selection**: Independent package.json source selection (auto, local, github, uploaded)
- **🔄 Uploaded Files Integration**: Seamless integration with existing flows source options
- **🗑️ File Management**: Clear uploaded files functionality with status indicators
- **📂 Upload Directory**: Automatic creation of uploaded_files directory for file storage
- **⚠️ Detailed Error Messages**: Clear validation error messages for invalid file structures
- **🧹 Simplified Interface**: Removed GitHub URL field for cleaner, more focused GUI

### v2.3 - Enhanced GUI with Visual Progress Indicators
- **✅ Visual Step Indicators**: Real-time checkmarks and completion status for each process
- **📊 Scrollable Progress Display**: Visual tracking of all 12 configuration steps
- **🔄 Real-time Output Streaming**: Script output displayed in both GUI and Python terminal
- **🎯 Step Highlighting**: Current step highlighted in blue, completed steps show green checkmarks
- **❌ Error Visualization**: Failed steps clearly marked with red X indicators
- **🔧 Improved Threading**: Fixed cross-thread GUI access issues
- **📱 Enhanced User Experience**: Better visual feedback and progress tracking

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

#### 🚀 **PyPI Package (Recommended)**
The easiest way to install and use the Bivicom Configuration Bot:

```bash
# Install from PyPI
pip install bivicom-config-bot

# Install with GUI support
pip install bivicom-config-bot[gui]

# Install with build tools
pip install bivicom-config-bot[build]

# Install with all optional dependencies
pip install bivicom-config-bot[gui,build,dev]
```

**After installation, you can use the commands globally:**
```bash
# Network bot
bivicom-bot --help
bivicom-bot --ip 192.168.1.1 --verbose

# GUI application
bivicom-gui
```

#### 📦 **From Source (Development)**
For development or if you want the latest features:

```bash
# Clone the repository
git clone https://github.com/Loranet-Technologies/bivicom-config-bot.git
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

#### 🚀 **PyPI Package Commands (Recommended)**
After installing from PyPI, use these global commands:

```bash
# Network bot - automatically scans for 192.168.1.1
bivicom-bot

# Custom IP and scan interval
bivicom-bot --ip 192.168.1.100 --interval 5

# Verbose mode - shows full output from all commands
bivicom-bot --verbose

# Custom IP with verbose logging
bivicom-bot --ip 192.168.1.100 --verbose

# Help
bivicom-bot --help

# GUI application
bivicom-gui
```

#### 📦 **Source Code Usage (Development)**
If running from source code:

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

# Start the GUI application
python3 gui_enhanced.py

# Features:
# - Real-time log display with color-coded messages
# - Visual step indicators with checkmarks and completion status
# - Scrollable progress display for all 12 configuration steps
# - Real-time script output streaming to both GUI and terminal
# - Username/password configuration fields with show/hide toggle
# - File upload support for custom flows.json and package.json files
# - Node-RED structure validation for uploaded files with detailed error messages
# - Smart upload logic that uses uploaded files when both are available
# - Independent package.json source selection (auto, local, github, uploaded)
# - Status indicators showing validation results and file upload status
# - Sound notifications for success/error events
# - System notifications for completion
# - Reset device functionality
# - Cross-platform compatibility (Windows, macOS, Linux)
```

## 📦 **PyPI Package Features**

### **Easy Installation**
```bash
# One-command installation
pip install bivicom-config-bot

# Global command availability
bivicom-bot --help
bivicom-gui
```

### **Command-Line Tools**
- **`bivicom-bot`**: Network automation bot with comprehensive logging
- **`bivicom-gui`**: User-friendly GUI application with visual progress indicators

### **Optional Dependencies**
```bash
# GUI support (notifications, sound alerts)
pip install bivicom-config-bot[gui]

# Build tools (PyInstaller, standalone executables)
pip install bivicom-config-bot[build]

# Development tools (testing, linting, formatting)
pip install bivicom-config-bot[dev]

# All optional features
pip install bivicom-config-bot[gui,build,dev]
```

### **Package Information**
- **Package Name**: `bivicom-config-bot`
- **Version**: 1.0.2+
- **Python Support**: 3.7+
- **Platforms**: Windows, macOS, Linux
- **License**: MIT
- **PyPI URL**: https://pypi.org/project/bivicom-config-bot/

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
- **12-Step Configuration**: Complete automated deployment sequence (cleanup-disk removed)
- **Comprehensive Logging**: Full command output saved to timestamped log files
- **Verbose Mode**: Real-time detailed output with `--verbose` flag
- **Error Handling**: Graceful failure recovery and retry logic
- **Real-time Logging**: Timestamped progress tracking with emojis
- **Ping Verification**: Connectivity checks before SSH operations
- **Robust Error Handling**: UCI availability checks and graceful failures

### 🖥️ GUI Application (`gui.py`)
- **Real-time Logging**: Color-coded log messages with timestamps
- **Visual Step Indicators**: Real-time checkmarks (✓), failures (✗), and current step highlighting (●)
- **Scrollable Progress Display**: Visual tracking of all 12 configuration steps
- **Real-time Output Streaming**: Script output displayed in both GUI and Python terminal
- **User Configuration**: Username/password input fields with show/hide toggle
- **File Upload Support**: Upload custom flows.json and package.json files with validation
- **Node-RED Structure Validation**: Comprehensive validation of Node-RED file structures
- **flows.json Validation**: Validates array format, required fields (id, type), and Node-RED flow structure
- **package.json Validation**: Validates object format, required fields (name, version), and dependency structure
- **Smart Upload Logic**: Uses uploaded files when both are available, falls back to user selection
- **Package Source Selection**: Independent package.json source selection (auto, local, github, uploaded)
- **File Management**: Clear uploaded files functionality with status indicators
- **Smart Source Selection**: Automatic flows source switching when files are uploaded
- **Sound Notifications**: Audio feedback for success/error events (cross-platform)
- **System Notifications**: Desktop notifications for completion/errors
- **Reset Functionality**: Complete device reset to default state
- **Thread-safe**: Non-blocking UI with background operations
- **Cross-platform**: Works on Windows, macOS, and Linux

### 🔧 Configuration Script (`network_config.sh`)
- **Network Configuration**: FORWARD and REVERSE modes
- **Docker Services**: Node-RED, Portainer, Restreamer with hardware privileges
- **Node-RED Integration**: Custom nodes, flow import, and enhanced settings
- **Tailscale VPN**: Secure mesh networking
- **Remote Execution**: SSH-based remote device management
- **Ping Verification**: Connectivity checks before SSH operations
- **Docker Image Retry**: Robust image pulling with retry logic
- **Non-interactive Installation**: Debconf configuration for automated setup
- **Safe Disk Cleanup**: Preserves Docker images while freeing space
- **Device Reset**: Complete factory reset functionality

### 🧪 Test Build System (`test_build.sh` & `TEST_BUILD.md`)
- **Automated Build Testing**: Complete testing framework for standalone application builds
- **Cross-Platform Validation**: Automated testing for Windows, macOS, and Linux builds
- **PyInstaller Integration**: Comprehensive testing of PyInstaller build processes
- **Build Documentation**: Detailed `TEST_BUILD.md` with build system overview and instructions
- **Build Validation**: Automated validation of executable creation and functionality
- **Environment Testing**: Virtual environment setup and dependency validation
- **Build Artifacts Management**: Automated cleanup and organization of build outputs
- **Error Detection**: Comprehensive error checking and reporting for build failures

### 🎯 12-Step Automated Sequence

When a device is detected, the bot automatically runs:

1. **Configure Network FORWARD** - Set up temporary DHCP WAN for deployment
2. **Check DNS Connectivity** - Verify internet access
3. **Fix DNS Configuration** - Ensure proper DNS resolution
4. **Install curl** - Install curl package for GitHub downloads
5. **Install Docker** - Set up container runtime
6. **Install All Docker Services** - Deploy Node-RED, Portainer, Restreamer
7. **Install Node-RED Nodes** - Add custom nodes (ffmpeg, queue-gate, sqlite, serialport)
8. **Import Node-RED Flows** - Load your radar and automation flows
9. **Update Node-RED Authentication** - Set secure password (L@ranet2025)
10. **Install Tailscale VPN Router** - Set up secure mesh networking
11. **Configure Network REVERSE** - Switch to final LTE WAN configuration
12. **Change Device Password** - Set secure device password (L@ranet2025)

> **Note**: The cleanup-disk step has been removed from the automated sequence to preserve Docker images during deployment.

### 📁 File Upload Feature

The GUI now supports uploading custom `flows.json` and `package.json` files for Node-RED configuration:

#### How to Use File Upload:
1. **Start the GUI**: Run `python3 gui_enhanced.py`
2. **Configure Sources**: 
   - Set "Flows Source" to your preferred option (auto, local, github, uploaded)
   - Set "Package Source" to your preferred option (auto, local, github, uploaded)
3. **Upload Files**: 
   - Click "Choose File" next to "Upload flows.json" to select your custom flows file
   - Click "Choose File" next to "Upload package.json" to select your custom package file
4. **Automatic Validation**: Files are automatically validated for Node-RED structure
5. **Status Indicators**: Green checkmarks (✓) show successfully uploaded and validated files
6. **Smart Logic**: System automatically uses uploaded files when both are available
7. **Clear Files**: Use "Clear Uploaded Files" button to remove uploaded files

#### File Requirements and Validation:

**flows.json Requirements:**
- Must be a JSON array (not an object)
- Each item must be a JSON object with `id` and `type` fields
- Must contain at least one tab or node
- Tab items must have a `label` field
- Supports standard Node-RED node types (inject, debug, function, switch, etc.)
- Supports custom node types and groups

**package.json Requirements:**
- Must be a JSON object (not an array)
- Must have `name` and `version` fields (non-empty strings)
- Optional `dependencies` object with package names and versions
- Optional `node-red` object for Node-RED specific configuration
- All dependency names and versions must be non-empty strings

**Validation Process:**
- Files are validated for proper JSON format first
- Then validated for Node-RED specific structure requirements
- Detailed error messages are shown for validation failures
- Files are copied to `uploaded_files/` directory only after successful validation

#### Smart Upload Logic:
The system uses intelligent logic to determine which files to use:

**When both flows.json and package.json are uploaded:**
- Both flows source and package source are automatically set to "uploaded"
- The bot uses your uploaded files for both flows and package installation

**When only flows.json is uploaded:**
- Flows source is automatically set to "uploaded"
- Package source uses your manual selection (auto, local, github)

**When only package.json is uploaded:**
- Package source is automatically set to "uploaded"
- Flows source uses your manual selection (auto, local, github)

**When no files are uploaded:**
- Both sources use your manual selection
- System falls back to auto-detection, local files, or GitHub as configured

#### Integration with Configuration:
- Uploaded files take precedence over manual source selection
- Files are passed to the network configuration script for deployment
- The bot logs which sources are being used for transparency

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
- **Features**: VPN router
- **Auth Key**: Configured via environment variables

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
  reverse [LAN_IP]    Configure network REVERSE (WAN=enx0250f4000000 LTE, LAN=eth0 static with optional custom IP)
  verify-network      Verify current network configuration (auto-detects FORWARD/REVERSE mode)
  install-docker      Install Docker container engine
  install-docker-compose Install standalone docker-compose binary
  install-services    Install all Docker services (Node-RED, Portainer, Restreamer)
  install-nodered-nodes [SOURCE] Install Node-RED nodes (auto|local|github|uploaded)
  import-nodered-flows [SOURCE] Import Node-RED flows (auto|local|github|uploaded)
  update-nodered-auth [PASSWORD] Update Node-RED authentication with custom password
  install-tailscale   Install Tailscale VPN router
  check-dns           Check internet connectivity and DNS
  fix-dns             Fix DNS configuration by adding Google DNS (8.8.8.8)
  safe-cleanup        Perform safe disk cleanup (preserves Docker images)
  cleanup-disk        Perform aggressive disk cleanup (removes all Docker images)
  add-user-to-docker  Add user to docker group
  install-curl        Install curl package
  set-password-admin  Change password back to admin
  set-password PASSWORD Change password to custom value
  forward-and-docker  Configure network FORWARD and install Docker
  reset-device        Reset device to default state (remove all Docker, reset network, restore defaults)

Options:
  --remote HOST [USER] [PASS|SSH_KEY]  Execute commands on remote host via SSH
                        If 4th parameter is a file path, it's treated as SSH key
                        Otherwise, it's treated as password
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
- **Access**: Secure mesh networking between devices

## 🛠️ Development

### Project Structure
```
bivicom-config-bot/
├── master.py              # Network bot with comprehensive logging (312 lines)
├── network_config.sh      # Configuration script (2508 lines)
├── gui_enhanced.py        # Enhanced GUI with visual progress indicators (3000+ lines)
├── test_build.sh          # Automated test build script (executable)
├── TEST_BUILD.md          # Test build documentation and instructions
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

### Test Build System
```bash
# Run automated test build
./test_build.sh

# Test build with verbose output
./test_build.sh --verbose

# Test specific build components
./test_build.sh --test-env
./test_build.sh --test-deps
./test_build.sh --test-build

# Clean test environment
./test_build.sh --clean
```

The test build system provides comprehensive validation of the build process:
- **Environment Testing**: Validates Python virtual environment setup
- **Dependency Testing**: Checks all required packages and versions
- **Build Testing**: Tests PyInstaller executable creation
- **Cross-Platform Support**: Automated testing for multiple platforms
- **Documentation**: Complete build system documentation in `TEST_BUILD.md`

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

## 🧪 Testing & Validation

### Comprehensive Function Testing (v2.5)

All network_config.sh functions have been thoroughly tested and validated:

| **Function Category** | **Status** | **Functions Tested** | **Results** |
|----------------------|------------|---------------------|-------------|
| **Network Configuration** | ✅ **PASSED** | `forward`, `reverse`, `verify-network` | All working perfectly with proper check mechanisms |
| **Password Management** | ✅ **PASSED** | `set-password-admin`, `set-password` | Both functions working correctly |
| **Docker Installation** | ✅ **PASSED** | `install-docker`, `install-docker-compose`, `add-user-to-docker` | All Docker functions working properly |
| **Service Installation** | ✅ **PASSED** | `install-nodered`, `install-portainer`, `install-restreamer` | All services installed and running |
| **Utility Functions** | ✅ **PASSED** | `check-dns`, `fix-dns`, `install-curl`, `cleanup-disk` | All utility functions working correctly |
| **Node-RED Functions** | ✅ **PASSED** | `install-nodered-nodes`, `import-nodered-flows`, `update-nodered-auth` | All Node-RED functions working properly |
| **Advanced Functions** | ✅ **PASSED** | `install-tailscale`, `forward-and-docker`, `install-services` | All advanced functions working correctly |

### Key Testing Results:
- **✅ All 20+ Functions Working**: Every function tested and validated
- **✅ Check Mechanisms Fixed**: Interface name handling (enx0250f4000000 vs usb0) resolved
- **✅ SSH Automation Complete**: Password and key authentication working
- **✅ Error Handling Robust**: Graceful fallbacks and retry logic validated
- **✅ Performance Validated**: All functions tested for reliability and speed

### Testing Commands:
```bash
# Test network configuration
./network_config.sh --remote 192.168.1.1 admin admin verify-network

# Test all functions systematically
./network_config.sh --remote 192.168.1.1 admin admin [COMMAND]

# Verify specific configurations
./network_config.sh --remote 192.168.1.1 admin admin check-dns
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

#### Network Configuration Issues
```bash
# Verify current network configuration
./network_config.sh --remote 192.168.1.1 admin admin verify-network

# Check interface status
ssh admin@192.168.1.1 "ip addr show"

# Check routing table
ssh admin@192.168.1.1 "ip route"
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

### Visual Progress Indicators (GUI)

The GUI application provides real-time visual feedback for each configuration step:

#### Step Status Indicators
- **○ Gray Circle**: Step not started (default state)
- **● Blue Circle**: Step currently running (highlighted)
- **✓ Green Checkmark**: Step completed successfully
- **✗ Red X**: Step failed

#### Real-time Output Streaming
- **GUI Log Window**: Color-coded messages with timestamps
- **Python Terminal**: Script output with `[SCRIPT OUTPUT]` prefix
- **Dual Display**: See progress in both GUI and terminal simultaneously

#### Progress Tracking
- **Scrollable Display**: All 12 steps visible in a scrollable panel
- **Current Step Highlighting**: Active step highlighted in blue
- **Completion Status**: Immediate visual feedback when steps complete
- **Error Visualization**: Failed steps clearly marked with red X

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
- **Device Tagging**: Network identification and access control

## 📚 Documentation

- **[TEST_BUILD.md](TEST_BUILD.md)** - Test build system documentation and instructions
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
