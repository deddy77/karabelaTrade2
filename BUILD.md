# Building KarabelaTrade Installer

This document explains how to build the KarabelaTrade installer.

## Prerequisites

1. Python 3.11 or higher
2. Inno Setup 6.x installed
3. All requirements from requirements.txt installed

## Build Process

There are two ways to build the installer:

### Method 1: Using the automated build script (Recommended)

1. Open PowerShell as Administrator
2. Navigate to the project directory:
   ```powershell
   cd path/to/KBT2
   ```
3. Run the build script:
   ```powershell
   .\build_steps.ps1
   ```
4. The script will:
   - Create the executable using PyInstaller
   - Create the installer using Inno Setup
   - Show progress and results of each step

The final installer will be created at `installer/KarabelaTrade_Setup.exe`

### Method 2: Manual build process

If the automated script fails, you can try the manual process:

1. Create the executable:
   ```powershell
   python build_executable.py
   ```
2. Wait for the executable to be created in the `dist` folder
3. Create the installer:
   ```powershell
   & "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe" "installer_script.iss"
   ```

## Troubleshooting

1. If you get PyInstaller errors:
   - Make sure all dependencies are installed: `pip install -r requirements.txt`
   - Try running PyInstaller without administrator privileges

2. If you get Inno Setup errors:
   - Make sure the executable was created in the `dist` folder
   - Check if Inno Setup is properly installed

3. Network Issues:
   - Ensure you have a stable internet connection for downloading dependencies
   - If connection fails, try running the build process again

## Installation

After building, you can find the installer at `installer/KarabelaTrade_Setup.exe`. Run it to install the application.

The installer will:
- Install the application to the Program Files directory
- Create desktop and start menu shortcuts
- Add necessary registry entries
- Copy MQL5 files to the appropriate location
