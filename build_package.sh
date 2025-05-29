#!/bin/bash
echo "Building KarabelaTrade Bot package..."

# Clean up old builds
echo "Cleaning up old builds..."
rm -rf dist build karabelatrade.egg-info

# Create python virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip and install build tools
echo "Installing build tools..."
python -m pip install --upgrade pip
pip install wheel build twine

# Build package
echo "Building package..."
python -m build

# Install locally in development mode
echo "Installing package in development mode..."
pip install -e .

# Run tests
echo "Running environment tests..."
python test_environment.py

echo
echo "Build complete. Package installed in development mode."
echo "You can now run:"
echo "  karabelatrade  - Launch the trading bot"
echo "  kbt-test      - Run environment tests"
echo "  kbt-version   - Show version information"
echo

# Keep virtual environment active
echo "Virtual environment is now active."
echo "Use 'deactivate' to exit virtual environment."
exec $SHELL
