# Bivicom Radar Bot - GUI Application

A standalone GUI application for the Bivicom Radar Bot that provides an easy-to-use interface for device setup and monitoring.

## Features

- **Real-time Log Display**: Color-coded log messages with timestamps
- **Progress Indicators**: Visual progress bars and status updates
- **System Notifications**: Desktop notifications when device setup completes
- **Cross-platform**: Works on Windows, macOS, and Linux
- **Graceful Exit**: Proper cleanup and shutdown handling
- **Statistics Tracking**: Monitor cycles completed and devices setup

## Screenshots

The GUI provides:
- Main window with log display
- Start/Stop/Pause controls
- Real-time statistics
- Color-coded log levels (INFO=green, SUCCESS=green bold, WARNING=yellow, ERROR=red)

## Installation

### Option 1: Run from Source

1. **Install Python 3.7+** (if not already installed)
2. **Install dependencies**:
   ```bash
   pip install -r requirements_gui.txt
   ```
3. **Run the launcher**:
   ```bash
   python launch_gui.py
   ```

### Option 2: Standalone Executable

1. **Build the executable**:
   ```bash
   python build_standalone.py --platform all
   ```
2. **Run the installer**:
   - Windows: `install_windows.bat` (run as administrator)
   - macOS: `./install_mac.sh`

## Usage

1. **Launch the application**
2. **Click "Start Bot"** to begin device setup
3. **Monitor progress** in the log window
4. **Receive notifications** when setup completes
5. **View statistics** in the bottom panel

## Requirements

- **Network Access**: Must be able to reach 192.168.1.1
- **SSH Credentials**: admin/admin (default)
- **Target Device**: Must be reachable and SSH-enabled

## Configuration

The application uses `bot_config.json` for configuration. Key settings:

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
  "deployment_mode": "auto"
}
```

## Troubleshooting

### Common Issues

1. **Application won't start**:
   - Check Python version (3.7+ required)
   - Install missing dependencies: `pip install -r requirements_gui.txt`
   - On Linux: Install tkinter: `sudo apt-get install python3-tk`

2. **Device not found**:
   - Verify network connectivity to 192.168.1.1
   - Check SSH credentials (admin/admin)
   - Ensure target device is powered on

3. **Build fails**:
   - Install PyInstaller: `pip install pyinstaller`
   - Check all required files are present
   - Run as administrator (Windows)

### Log Files

The application creates log files in the format:
- `{MAC_ADDRESS}_{TIMESTAMP}.log`

Example: `a019b2d27af9_20250109_143022.log`

## Development

### Building from Source

1. **Clone the repository**
2. **Install development dependencies**:
   ```bash
   pip install -r requirements_gui.txt
   ```
3. **Run tests**:
   ```bash
   python -m pytest tests/
   ```
4. **Build executable**:
   ```bash
   python build_standalone.py
   ```

### File Structure

```
bivicom-radar-bot/
├── radar_bot_gui.py          # Main GUI application
├── master_bot.py             # Core bot logic
├── script_no1.py             # Network configuration
├── script_no2.py             # Connectivity verification
├── script_no3.py             # Infrastructure deployment
├── bot_config.json           # Configuration file
├── build_standalone.py       # Build script
├── launch_gui.py             # Launcher script
├── requirements_gui.txt      # GUI dependencies
└── README_GUI.md             # This file
```

## API Reference

### RadarBotGUI Class

Main GUI application class with methods:

- `start_bot()`: Start the bot in background thread
- `stop_bot()`: Stop the bot gracefully
- `pause_bot()`: Pause bot execution
- `resume_bot()`: Resume bot execution
- `log_message(message, level)`: Add log message
- `show_completion_notification()`: Show system notification

### Log Levels

- `INFO`: General information (green)
- `SUCCESS`: Successful operations (green bold)
- `WARNING`: Warning messages (yellow)
- `ERROR`: Error messages (red bold)
- `DEBUG`: Debug information (gray)

## Security

- SSH connections use default credentials (admin/admin)
- MAC address validation for authorized devices
- Security events logged to `security_audit.log`
- Network scanning with configurable timeouts

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For technical support:
1. Check the troubleshooting section
2. Review log files for error details
3. Contact the development team

## Changelog

### Version 1.0 (2025-01-09)
- Initial GUI release
- Cross-platform support
- Real-time log display
- System notifications
- Standalone executable builds
