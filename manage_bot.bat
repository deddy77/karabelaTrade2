@echo off
setlocal

REM Check if Python is available
where python >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not available
    echo Please install Python and try again
    pause
    exit /b 1
)

REM Parse arguments
set "action=%~1"
if "%action%"=="" (
    echo Available commands:
    echo   start    - Start the bot container
    echo   stop     - Stop the bot container
    echo   restart  - Restart the bot container
    echo   status   - Show container status
    echo   logs     - Show container logs
    echo   stats    - Show resource usage
    echo   rebuild  - Rebuild and restart container
    echo   monitor  - Monitor container status
    echo.
    echo Example: %~n0 start
    pause
    exit /b 1
)

REM Run management script
python docker_manage.py %*
if errorlevel 1 (
    echo Command failed
    pause
    exit /b 1
)

endlocal
