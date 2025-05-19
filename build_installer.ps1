# Check if running as administrator
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$isAdmin = $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "Please run this script as Administrator" -ForegroundColor Red
    exit
}

# Function to check if a command exists
function Test-Command($cmdname) {
    return [bool](Get-Command -Name $cmdname -ErrorAction SilentlyContinue)
}

# Install Chocolatey if not installed
if (-not (Test-Command choco)) {
    Write-Host "Installing Chocolatey..." -ForegroundColor Yellow
    Set-ExecutionPolicy Bypass -Scope Process -Force
    [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
    iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))
}

# Install Python if not installed
if (-not (Test-Command python)) {
    Write-Host "Installing Python..." -ForegroundColor Yellow
    choco install python -y
    refreshenv
}

# Install Inno Setup if not installed
if (-not (Test-Path "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe")) {
    Write-Host "Installing Inno Setup..." -ForegroundColor Yellow
    choco install innosetup -y
}

# Install required Python packages
Write-Host "Installing Python dependencies..." -ForegroundColor Yellow
python -m pip install --upgrade pip
python -m pip install pyinstaller
python -m pip install -r requirements.txt

# Create executable using PyInstaller
Write-Host "Creating executable..." -ForegroundColor Yellow
python build_executable.py

# Create installer using Inno Setup
Write-Host "Creating installer..." -ForegroundColor Yellow
& "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe" "installer_script.iss"

Write-Host "`nBuild process completed!" -ForegroundColor Green
Write-Host "You can find the installer in the 'installer' directory." -ForegroundColor Green
Write-Host "The installer file is named 'KarabelaTrade_Setup.exe'" -ForegroundColor Green

# Pause to see the output
Write-Host "`nPress any key to exit..."
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
