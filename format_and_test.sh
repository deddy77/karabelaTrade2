#!/bin/bash
echo "Running code formatting and tests..."

# Activate virtual environment if it exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "Virtual environment not found. Please run install.sh first."
    exit 1
fi

# Format and lint code
echo
echo "Running code formatting and linting..."
python3 format_code.py
if [ $? -ne 0 ]; then
    echo "Code formatting or linting failed"
    read -p "Press enter to continue..."
    exit 1
fi

# Run tests
echo
echo "Running tests..."
python3 -m pytest
if [ $? -ne 0 ]; then
    echo "Tests failed"
    read -p "Press enter to continue..."
    exit 1
fi

echo
echo "All checks and tests passed successfully!"
read -p "Press enter to continue..."
