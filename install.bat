@echo off
echo Installing KarabelaTrade Bot dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo Initializing environment...
python initialize.py

echo.
echo Running environment tests...
python test_environment.py

echo.
if %ERRORLEVEL% EQU 0 (
    echo All tests passed successfully!
) else (
    echo Some tests failed. Please check the logs for details.
)

echo.
echo Installation and testing complete.
echo Please update config.py with your settings before running the bot.
echo.
echo To start the bot, run: python run_gui.py
pause
