# Bivicom Radar Bot - GUI Application

A user-friendly graphical interface for the Bivicom Radar Bot that automates device setup and infrastructure deployment.

## 🚀 Features

- **Intuitive GUI**: Easy-to-use interface for device setup
- **Real-time Progress**: Live monitoring of deployment progress
- **One-Click Setup**: Simple "Start Bot" button to begin automation
- **Status Indicators**: Visual feedback for each deployment stage
- **Log Display**: Real-time log output in the application window
- **Cross-Platform**: Works on Windows, macOS, and Linux

## 📋 Requirements

- Python 3.7 or higher
- tkinter (usually included with Python)
- Network access to target device (192.168.1.1)
- SSH access with admin/admin credentials

## 🛠️ Installation

### Windows
1. Download `bivicom-radar-bot-windows-v1.0.zip`
2. Extract the archive
3. Double-click `INSTALL.bat`
4. Follow the installation prompts

### macOS
1. Download `bivicom-radar-bot-macos-v1.0.zip`
2. Extract the archive
3. Run `./INSTALL.sh` in Terminal
4. Follow the installation prompts

### Linux
1. Download `bivicom-radar-bot-linux-v1.0.zip`
2. Extract the archive
3. Run `./INSTALL.sh`
4. Follow the installation prompts

## 🎯 Usage

### Launching the Application

**Windows:**
- Double-click the desktop shortcut "Bivicom Radar Bot"
- Or run: `python radar_bot_gui.py`

**macOS:**
- Double-click the desktop shortcut
- Or open Applications folder and click "Bivicom Radar Bot"
- Or use Spotlight: Cmd+Space, type "Bivicom"

**Linux:**
- Double-click the desktop shortcut
- Or run: `python3 radar_bot_gui.py`

### Using the GUI

1. **Launch the Application**: Start the GUI application
2. **Check Prerequisites**: Ensure your network and device are ready
3. **Click "Start Bot"**: Begin the automated deployment process
4. **Monitor Progress**: Watch real-time updates in the log window
5. **Wait for Completion**: The bot will notify you when finished

### GUI Components

- **Start Bot Button**: Initiates the deployment process
- **Progress Bar**: Shows overall completion status
- **Log Window**: Displays real-time deployment logs
- **Status Labels**: Shows current operation status
- **Stop Button**: Allows you to cancel the operation (if needed)

## 🔧 Configuration

The GUI uses the same configuration as the command-line version. Edit `bot_config.json` to customize:

- Network range to scan
- SSH credentials
- Target device settings
- Deployment options
- Timeout values

## 📊 Deployment Process

The GUI automates the following steps:

1. **Network Check**: Verifies connectivity to 192.168.1.1
2. **SSH Test**: Tests SSH connection with admin credentials
3. **MAC Detection**: Retrieves device MAC address
4. **Log Creation**: Creates timestamped log file
5. **Network Configuration**: Configures WAN/LAN interfaces
6. **Connectivity Verification**: Tests internet connectivity
7. **Infrastructure Deployment**: Installs Bivicom Radar system
8. **Completion Notification**: Notifies when deployment is complete

## 🛡️ Security Features

- **MAC Address Validation**: Only deploys to authorized Bivicom devices
- **SSH Security**: Uses secure SSH connections
- **Audit Trail**: Complete logging of all operations
- **Error Handling**: Robust error recovery and reporting

## 🐛 Troubleshooting

### Common Issues

1. **"Python not found"**: Install Python 3.7+ from python.org
2. **"tkinter not available"**: Install tkinter for your system
3. **"SSH connection failed"**: Check network and credentials
4. **"Device not found"**: Verify device is at 192.168.1.1

### Debug Mode

Enable debug logging by editing `bot_config.json`:
```json
{
  "log_level": "DEBUG"
}
```

### Log Files

All operations are logged to files named with MAC address and timestamp:
```
a019b2d27af9_20250909_001637.log
```

## 📖 Advanced Usage

### Command Line Alternative

If you prefer command-line usage:
```bash
python3 master_bot.py
```

### Individual Scripts

Run specific deployment stages:
```bash
python3 script_no1.py  # Network configuration
python3 script_no2.py  # Connectivity verification
python3 script_no3.py  # Infrastructure deployment
```

## 🤝 Support

- Check log files for detailed error information
- All operations are logged with timestamps
- Contact the developer for technical support
- Review DEPLOYMENT_GUIDE.md for technical details

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 👨‍💻 Author

**Aqmar** - *Initial work* - [Loranet Technologies](https://github.com/Loranet-Technologies)
