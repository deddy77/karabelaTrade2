@echo off
echo Building KarabelaTrade Bot package...

REM Clean up old builds
echo Cleaning up old builds...
if exist "dist" rd /s /q "dist"
if exist "build" rd /s /q "build"
if exist "karabelatrade.egg-info" rd /s /q "karabelatrade.egg-info"

REM Create python virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate

REM Upgrade pip and install build tools
echo Installing build tools...
python -m pip install --upgrade pip
pip install wheel build twine

REM Build package
echo Building package...
python -m build

REM Install locally in development mode
echo Installing package in development mode...
pip install -e .

REM Run tests
echo Running environment tests...
python test_environment.py

echo.
echo Build complete. Package installed in development mode.
echo You can now run:
echo   karabelatrade  - Launch the trading bot
echo   kbt-test      - Run environment tests
echo   kbt-version   - Show version information
echo.

REM Keep virtual environment active
echo Virtual environment is now active.
echo Use 'deactivate' to exit virtual environment.
cmd /k
