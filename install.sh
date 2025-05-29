#!/bin/bash
echo "Installing KarabelaTrade Bot dependencies..."
python3 -m pip install --upgrade pip
pip3 install -r requirements.txt

echo
echo "Initializing environment..."
python3 initialize.py

echo
echo "Running environment tests..."
python3 test_environment.py

echo
if [ $? -eq 0 ]; then
    echo "All tests passed successfully!"
else
    echo "Some tests failed. Please check the logs for details."
fi

echo
echo "Installation and testing complete."
echo "Please update config.py with your settings before running the bot."
echo
echo "To start the bot, run: python3 run_gui.py"
read -p "Press enter to continue..."
