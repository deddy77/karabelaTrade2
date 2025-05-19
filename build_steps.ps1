# Step 1: Create the executable
Write-Host "Step 1: Creating executable with PyInstaller..." -ForegroundColor Yellow
python build_executable.py

# Check if executable was created
if (Test-Path "dist/KarabelaTrade.exe") {
    Write-Host "✅ Executable created successfully!" -ForegroundColor Green
    
    # Step 2: Create installer
    Write-Host "`nStep 2: Creating installer with Inno Setup..." -ForegroundColor Yellow
    
    # Create installer directory if it doesn't exist
    if (-not (Test-Path "installer")) {
        New-Item -ItemType Directory -Path "installer"
    }
    
    # Run Inno Setup Compiler
    & "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe" "installer_script.iss"
    
    # Check if installer was created
    if (Test-Path "installer/KarabelaTrade_Setup.exe") {
        Write-Host "✅ Installer created successfully!" -ForegroundColor Green
        Write-Host "`nYou can find the installer at: installer/KarabelaTrade_Setup.exe" -ForegroundColor Green
    } else {
        Write-Host "❌ Failed to create installer" -ForegroundColor Red
    }
} else {
    Write-Host "❌ Failed to create executable" -ForegroundColor Red
    Write-Host "Check the output above for any error messages" -ForegroundColor Yellow
}

# Pause to see the output
Write-Host "`nPress any key to exit..."
$null = $Host.UI.RawUI.ReadKey('NoEcho,IncludeKeyDown')
