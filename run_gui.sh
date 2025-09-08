#!/bin/bash

# Bivicom Radar Bot GUI Launcher
# This script runs the GUI from source code (more reliable than standalone)

echo "Starting Bivicom Radar Bot GUI..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
else
    echo "Virtual environment not found. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
    pip install paramiko
fi

# Check if tkinter is available
python3 -c "import tkinter" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Error: tkinter is not available."
    echo "On macOS, tkinter should be included with Python."
    echo "If you're using Homebrew Python, try: brew install python-tk"
    exit 1
fi

# Run the GUI
echo "Launching GUI..."
python3 radar_bot_gui.py
