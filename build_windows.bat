@echo off
REM Windows build script for standalone executable

echo 🔨 Building Windows standalone executable...

REM Create build directory
if not exist "dist\windows" mkdir "dist\windows"
if not exist "build_assets" mkdir "build_assets"

REM Copy required files
copy "network_config.sh" "build_assets\"
copy "requirements.txt" "build_assets\"
copy "LICENSE" "build_assets\"
xcopy "uploaded_files" "build_assets\uploaded_files\" /E /I

echo 📦 Building executable with PyInstaller...

REM Build the executable
pyinstaller --onefile --windowed ^
    --name="Bivicom-Configurator" ^
    --add-data="build_assets\network_config.sh;." ^
    --add-data="build_assets\requirements.txt;." ^
    --add-data="build_assets\LICENSE;." ^
    --add-data="build_assets\uploaded_files;uploaded_files" ^
    --hidden-import="tkinter" ^
    --hidden-import="paramiko" ^
    --hidden-import="plyer" ^
    --hidden-import="threading" ^
    --hidden-import="queue" ^
    --hidden-import="subprocess" ^
    --hidden-import="json" ^
    --hidden-import="os" ^
    --hidden-import="sys" ^
    --hidden-import="time" ^
    --hidden-import="datetime" ^
    --hidden-import="platform" ^
    --hidden-import="socket" ^
    --hidden-import="ipaddress" ^
    --distpath="dist\windows" ^
    gui_enhanced.py

REM Create package directory
set PACKAGE_DIR=dist\Bivicom-Configurator-windows
if not exist "%PACKAGE_DIR%" mkdir "%PACKAGE_DIR%"

REM Copy files to package
copy "dist\windows\Bivicom-Configurator.exe" "%PACKAGE_DIR%\"
copy "build_assets\network_config.sh" "%PACKAGE_DIR%\"
copy "build_assets\requirements.txt" "%PACKAGE_DIR%\"
copy "build_assets\LICENSE" "%PACKAGE_DIR%\"
xcopy "build_assets\uploaded_files" "%PACKAGE_DIR%\uploaded_files\" /E /I

REM Create README
echo Bivicom Configuration Manager - Standalone Application > "%PACKAGE_DIR%\README.txt"
echo ==================================================== >> "%PACKAGE_DIR%\README.txt"
echo. >> "%PACKAGE_DIR%\README.txt"
echo This is a standalone application that doesn't require Python installation. >> "%PACKAGE_DIR%\README.txt"
echo. >> "%PACKAGE_DIR%\README.txt"
echo Files included: >> "%PACKAGE_DIR%\README.txt"
echo - Bivicom-Configurator.exe: Main application executable >> "%PACKAGE_DIR%\README.txt"
echo - network_config.sh: Configuration script >> "%PACKAGE_DIR%\README.txt"
echo - requirements.txt: Dependencies list (for reference) >> "%PACKAGE_DIR%\README.txt"
echo - LICENSE: License file >> "%PACKAGE_DIR%\README.txt"
echo - uploaded_files/: Directory for file uploads >> "%PACKAGE_DIR%\README.txt"
echo. >> "%PACKAGE_DIR%\README.txt"
echo Usage: >> "%PACKAGE_DIR%\README.txt"
echo 1. Double-click Bivicom-Configurator.exe to run >> "%PACKAGE_DIR%\README.txt"
echo 2. Configure your network settings in the GUI >> "%PACKAGE_DIR%\README.txt"
echo 3. Use the network_config.sh script for advanced operations >> "%PACKAGE_DIR%\README.txt"

echo ✅ Windows build completed!
echo 📁 Output: dist\Bivicom-Configurator-windows\
echo 🚀 Ready for distribution!

REM Cleanup
rmdir /S /Q build_assets
rmdir /S /Q build

pause
