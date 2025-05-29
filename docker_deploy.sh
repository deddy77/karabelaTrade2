#!/bin/bash
echo "Checking Docker compatibility..."

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not available"
    echo "Please install Python 3 and try again"
    read -p "Press enter to continue..."
    exit 1
fi

# Make script executable
chmod +x "$(dirname "$0")/docker_deploy.sh"

# Run compatibility check
python3 check_docker.py
if [ $? -ne 0 ]; then
    echo "Docker compatibility check failed"
    echo "Please resolve the issues and try again"
    read -p "Press enter to continue..."
    exit 1
fi

# Check if psutil is installed (needed for system checks)
python3 -c "import psutil" &> /dev/null
if [ $? -ne 0 ]; then
    echo "Installing psutil for system checks..."
    pip3 install psutil
    if [ $? -ne 0 ]; then
        echo "Failed to install psutil"
        echo "Please run: pip3 install psutil"
        read -p "Press enter to continue..."
        exit 1
    fi
fi

# Build and deploy
echo "Building and deploying KarabelaTrade Bot using Docker..."

# Build Docker containers
echo "Building Docker containers..."
if ! docker-compose build --no-cache; then
    echo "Error: Docker build failed"
    read -p "Press enter to continue..."
    exit 1
fi

echo "Starting containers..."
if ! docker-compose up -d; then
    echo "Error: Failed to start containers"
    read -p "Press enter to continue..."
    exit 1
fi

echo
echo "Deployment complete!"
echo
echo "You can:"
echo "- View logs with: docker-compose logs -f"
echo "- Stop bot with: docker-compose down"
echo "- Check status with: docker-compose ps"
echo "- Monitor with: ./manage_bot.sh monitor"
echo

read -p "Press enter to continue..."
