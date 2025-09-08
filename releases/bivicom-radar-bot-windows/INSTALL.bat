@echo off
echo 🎉 Installing Bivicom Radar Bot for Windows...

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed. Please install Python 3.7 or higher.
    echo Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python found

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install dependencies
echo Installing dependencies...
pip install -r requirements_gui.txt

REM Create desktop shortcut
echo Creating desktop shortcut...
powershell -Command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\Bivicom Radar Bot.lnk'); $Shortcut.TargetPath = 'python'; $Shortcut.Arguments = 'radar_bot_gui.py'; $Shortcut.WorkingDirectory = '%CD%'; $Shortcut.IconLocation = 'python.exe,0'; $Shortcut.Save()"

echo.
echo 🎉 Installation completed successfully!
echo.
echo 🖥️  Desktop shortcut created: Bivicom Radar Bot
echo.
echo 🚀 How to launch:
echo 1. Double-click the desktop shortcut
echo 2. Or run: python radar_bot_gui.py
echo.
echo 📖 Read COMPLETE_DOCUMENTATION.md for detailed instructions
echo.
echo ✅ Ready to use!
pause
