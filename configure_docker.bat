@echo off
echo Configuring Docker environment...

REM Check Python installation
where python >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not available
    echo Please install Python and try again
    pause
    exit /b 1
)

REM Check if pyyaml is installed
python -c "import yaml" >nul 2>&1
if errorlevel 1 (
    echo Installing pyyaml for configuration file generation...
    pip install pyyaml
    if errorlevel 1 (
        echo Failed to install pyyaml
        echo Please run: pip install pyyaml
        pause
        exit /b 1
    )
)

REM Run configuration script
python configure_docker.py
if errorlevel 1 (
    echo Configuration failed
    pause
    exit /b 1
)

REM Remind about deployment
echo.
echo To deploy with new configuration:
echo 1. Review the generated .env file
echo 2. Run docker_deploy.bat to apply changes
echo.
pause
