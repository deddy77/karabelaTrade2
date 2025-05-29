@echo off
echo Running code formatting and tests...

REM Activate virtual environment if it exists
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate
) else (
    echo Virtual environment not found. Please run install.bat first.
    exit /b 1
)

REM Format and lint code
echo.
echo Running code formatting and linting...
python format_code.py
if errorlevel 1 (
    echo Code formatting or linting failed
    pause
    exit /b 1
)

REM Run tests
echo.
echo Running tests...
python -m pytest
if errorlevel 1 (
    echo Tests failed
    pause
    exit /b 1
)

echo.
echo All checks and tests passed successfully!
pause
