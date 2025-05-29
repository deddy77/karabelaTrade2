#!/bin/bash

# Make script executable
chmod +x "$(dirname "$0")/cleanup_docker.sh"

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not available"
    echo "Please install Python 3 and try again"
    read -p "Press enter to continue..."
    exit 1
fi

# Parse arguments
action="$1"
if [ -z "$action" ]; then
    echo "Available options:"
    echo "  safe       - Remove unused resources (default)"
    echo "  full      - Remove all Docker resources (WARNING: Removes everything!)"
    echo "  space     - Show Docker space usage"
    echo
    echo "Example: $(basename "$0") safe"
    read -p "Choose an option: " action
fi

# Run cleanup script with appropriate options
case "$action" in
    "full")
        python3 docker_cleanup.py --full
        ;;
    "space")
        python3 docker_cleanup.py --show-space
        ;;
    *)
        python3 docker_cleanup.py
        ;;
esac

if [ $? -ne 0 ]; then
    echo "Cleanup failed"
    read -p "Press enter to continue..."
    exit 1
fi
