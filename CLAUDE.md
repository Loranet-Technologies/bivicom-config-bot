# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Bivicom Configuration Bot is a comprehensive network automation toolkit for configuring and deploying infrastructure on Bivicom IoT devices. The project combines device discovery, SSH automation, UCI network configuration, and infrastructure deployment into a unified workflow.

## Core Architecture

### Main Components

- **master.py**: Network bot with continuous scanning and 12-step automated configuration sequence
- **network_config.sh**: Core bash script (2500+ lines) handling all device configuration operations
- **gui_enhanced.py**: Professional GUI application with visual progress indicators and real-time logging
- **setup.py**: Python package configuration for PyPI distribution

### Network Configuration Modes

The system operates in two distinct network modes:

1. **Forward Mode (Deployment)**: WAN=eth1 (DHCP), LAN=eth0 (Static 192.168.1.1)
2. **Reverse Mode (Production)**: WAN=enx0250f4000000 (LTE), LAN=eth0 (Static)

## Development Commands

### PyPI Package Installation (Recommended)
```bash
# Install from PyPI
pip install bivicom-config-bot

# Install with optional dependencies
pip install bivicom-config-bot[gui,build,dev]

# Use global commands
bivicom-bot --help
bivicom-gui
```

### Development from Source
```bash
# Install dependencies
pip install -r requirements.txt

# Run network bot
python3 master.py [--ip IP] [--interval SEC] [--verbose]

# Run GUI application
python3 gui_enhanced.py

# Test build system
./test_build.sh [--verbose] [--clean]

# Manual network configuration
./network_config.sh --remote 192.168.1.1 admin admin [COMMAND]
```

### Building Executables
```bash
# Automated build testing
./test_build.sh

# Manual build with PyInstaller
pip install pyinstaller
pyinstaller --onefile --windowed master.py
```

## Key Implementation Details

### Network Bot (master.py)
- Uses socket-based ping detection (port 22) for device discovery
- Implements 12-step sequential configuration with timeout handling
- Comprehensive logging to `logs/` directory with timestamps
- Graceful signal handling for SIGINT/SIGTERM
- Supports verbose mode for real-time detailed output

### Configuration Script (network_config.sh)
- SSH-based remote execution with password/key authentication
- UCI network configuration with backup/restore capabilities
- Docker service deployment (Node-RED, Portainer, Restreamer)
- Tailscale VPN router integration
- Node-RED flows import with custom node installation
- File upload support for custom flows/package.json

### GUI Application (gui_enhanced.py)
- Multi-threaded design with queue-based message passing
- Visual step indicators (○, ●, ✓, ✗) for progress tracking
- Real-time output streaming from configuration scripts
- File validation for Node-RED structure compliance
- Cross-platform sound notifications and system alerts

## Testing

The project includes comprehensive test coverage:
- All 20+ network_config.sh functions tested and validated
- Test build system for cross-platform executable creation
- Network connectivity and SSH connection testing
- Docker service deployment validation

## Configuration Files

- **requirements.txt**: Core dependencies (paramiko, python-dotenv, plyer, pyinstaller)
- **.env**: SSH credentials and Tailscale configuration
- **logs/**: Automatic timestamped log file creation
- **uploaded_files/**: Temporary storage for user-uploaded Node-RED files

## Package Structure

The project is distributed as a PyPI package with proper entry points:
- `bivicom-bot` command for network automation
- `bivicom-gui` command for GUI application

## Important Notes

- The system requires `sshpass` utility for password-based SSH authentication
- Default device credentials are admin/admin (configurable)
- All operations maintain SSH connectivity without device reboots
- Configuration backup is performed before making network changes
- Docker image retry logic is implemented for robust deployment

## Development Workflow

1. Use PyPI package for production deployments
2. Use source installation for development
3. Test changes with comprehensive validation system
4. Build executables using test_build.sh framework
5. Validate all functions before release deployment

## Cursor Configuration

The project includes `.cursorignore` to exclude common development artifacts:
- Python cache files and virtual environments
- Build directories and distribution packages
- IDE/editor files and OS-generated files
- Log files and temporary test scripts
- Configuration files that may contain sensitive data