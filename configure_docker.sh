#!/bin/bash

echo "Configuring Docker environment..."

# Make script executable
chmod +x "$(dirname "$0")/configure_docker.sh"

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not available"
    echo "Please install Python 3 and try again"
    read -p "Press enter to continue..."
    exit 1
fi

# Check if pyyaml is installed
python3 -c "import yaml" &> /dev/null
if [ $? -ne 0 ]; then
    echo "Installing pyyaml for configuration file generation..."
    pip3 install pyyaml
    if [ $? -ne 0 ]; then
        echo "Failed to install pyyaml"
        echo "Please run: pip3 install pyyaml"
        read -p "Press enter to continue..."
        exit 1
    fi
fi

# Run configuration script
python3 configure_docker.py
if [ $? -ne 0 ]; then
    echo "Configuration failed"
    read -p "Press enter to continue..."
    exit 1
fi

# Remind about deployment
echo
echo "To deploy with new configuration:"
echo "1. Review the generated .env file"
echo "2. Run ./docker_deploy.sh to apply changes"
echo

read -p "Press enter to continue..."
