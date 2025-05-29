@echo off
echo Checking Docker compatibility...

REM Check Python installation
where python >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not available
    echo Please install Python and try again
    pause
    exit /b 1
)

REM Run compatibility check
python check_docker.py
if errorlevel 1 (
    echo Docker compatibility check failed
    echo Please resolve the issues and try again
    pause
    exit /b 1
)

REM Check if psutil is installed (needed for system checks)
python -c "import psutil" >nul 2>&1
if errorlevel 1 (
    echo Installing psutil for system checks...
    pip install psutil
    if errorlevel 1 (
        echo Failed to install psutil
        echo Please run: pip install psutil
        pause
        exit /b 1
    )
)

REM Build and deploy
echo Building and deploying KarabelaTrade Bot using Docker...

REM Build Docker containers
echo Building Docker containers...
docker-compose build --no-cache

if errorlevel 1 (
    echo Error: Docker build failed
    pause
    exit /b 1
)

echo Starting containers...
docker-compose up -d

if errorlevel 1 (
    echo Error: Failed to start containers
    pause
    exit /b 1
)

echo.
echo Deployment complete!
echo.
echo You can:
echo - View logs with: docker-compose logs -f
echo - Stop bot with: docker-compose down
echo - Check status with: docker-compose ps
echo - Monitor with: manage_bot.bat monitor
echo.
pause
