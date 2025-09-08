#!/bin/bash

# Bivicom Radar Bot Launcher
# Double-click this file to launch the application

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Activate virtual environment and run GUI
source venv/bin/activate
python3 radar_bot_gui.py