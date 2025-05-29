@echo off
setlocal

REM Check Python installation
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
    echo Available options:
    echo   safe       - Remove unused resources ^(default^)
    echo   full      - Remove all Docker resources ^(WARNING: Removes everything!^)
    echo   space     - Show Docker space usage
    echo.
    echo Example: %~n0 safe
    set /p "action=Choose an option: "
)

REM Run cleanup script with appropriate options
if "%action%"=="full" (
    python docker_cleanup.py --full
) else if "%action%"=="space" (
    python docker_cleanup.py --show-space
) else (
    python docker_cleanup.py
)

if errorlevel 1 (
    echo Cleanup failed
    pause
    exit /b 1
)

endlocal
