#!/bin/bash

# Make script executable
chmod +x "$(dirname "$0")/manage_bot.sh"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not available"
    echo "Please install Python 3 and try again"
    read -p "Press enter to continue..."
    exit 1
fi

# Parse arguments
action="$1"
if [ -z "$action" ]; then
    echo "Available commands:"
    echo "  start    - Start the bot container"
    echo "  stop     - Stop the bot container"
    echo "  restart  - Restart the bot container"
    echo "  status   - Show container status"
    echo "  logs     - Show container logs"
    echo "  stats    - Show resource usage"
    echo "  rebuild  - Rebuild and restart container"
    echo "  monitor  - Monitor container status"
    echo
    echo "Example: $(basename "$0") start"
    read -p "Press enter to continue..."
    exit 1
fi

# Run management script
python3 docker_manage.py "$@"
if [ $? -ne 0 ]; then
    echo "Command failed"
    read -p "Press enter to continue..."
    exit 1
fi
