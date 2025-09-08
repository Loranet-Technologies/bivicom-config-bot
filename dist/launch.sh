#!/bin/bash

# Bivicom Radar Bot Launcher
echo "Starting Bivicom Radar Bot..."

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Run the executable
./BivicomRadarBot
