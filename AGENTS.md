# Agent Guidelines for bivicom-config-bot

## Build/Lint/Test Commands

### Build Commands
- **Standalone build (current platform)**: `./build_standalone.sh`
- **Cross-platform build**: `./build_cross_platform.sh`
- **Windows build**: `build_windows.bat`
- **Manual PyInstaller**: `pyinstaller --onefile --windowed --name="Bivicom-Configurator" --add-data="network_config.sh:." --add-data="requirements.txt:." --hidden-import="tkinter" --hidden-import="paramiko" --hidden-import="plyer" gui_enhanced.py`

### Test Commands
- **Build system test**: `./test_build.sh`
- **Run all tests**: `python -m pytest` (pytest configured but no test files exist)
- **Run single test**: No specific single test command (no test files present)

### Lint/Type Check Commands
- **Format code**: `black .`
- **Lint code**: `flake8 bivicom_config_bot/`
- **Type check**: `mypy bivicom_config_bot/`
- **Full quality check**: `black . && flake8 bivicom_config_bot/ && mypy bivicom_config_bot/`

## Code Style Guidelines

### Python Version & Imports
- **Python version**: 3.7+ required
- **Import order**: Standard library → Third-party → Local modules
- **Type hints**: Use typing module for function parameters and return types
- **Import examples**:
  ```python
  import os
  import sys
  from typing import Optional, Dict, Any, List
  from datetime import datetime
  import paramiko
  import tkinter as tk
  ```

### Formatting (Black)
- **Line length**: 88 characters
- **Target Python versions**: 3.7, 3.8, 3.9, 3.10, 3.11, 3.12
- **Excluded directories**: .eggs, .git, .hg, .mypy_cache, .tox, build, dist

### Naming Conventions
- **Classes**: PascalCase (e.g., `NetworkBot`, `EnhancedGUI`)
- **Functions/methods**: snake_case (e.g., `setup_logging`, `run_ping_test`)
- **Variables**: snake_case (e.g., `target_ip`, `scan_interval`)
- **Constants**: UPPER_CASE (e.g., `DEFAULT_TIMEOUT`)
- **Modules**: snake_case (e.g., `master.py`, `gui_enhanced.py`)

### Documentation
- **Module docstrings**: Required with description, author, date
- **Function docstrings**: Required for public functions/methods
- **Inline comments**: Minimal, only when code logic isn't obvious

### Error Handling
- **Use try/except blocks**: Catch specific exceptions, not bare `except:`
- **Logging**: Use logging module for errors and important events
- **Graceful degradation**: Handle failures without crashing
- **User feedback**: Provide clear error messages in GUI/logs

### Code Structure
- **Class-based**: Prefer classes over functions for complex functionality
- **Separation of concerns**: GUI logic separate from business logic
- **Threading**: Use threading for long-running operations in GUI
- **Signal handlers**: Implement SIGINT/SIGTERM handlers for graceful shutdown

### Security
- **No secrets in code**: Never commit passwords, keys, or sensitive data
- **Environment variables**: Use python-dotenv for configuration
- **Input validation**: Validate all user inputs and file contents
- **SSH security**: Use key-based auth when possible, secure password handling