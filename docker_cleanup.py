#!/usr/bin/env python3
"""Docker cleanup script for KarabelaTrade Bot"""
import os
import sys
import argparse
import subprocess
from typing import List, Tuple, Optional
from datetime import datetime

def run_command(command: List[str]) -> Tuple[int, str, str]:
    """Run a command and return exit code, stdout, and stderr"""
    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        stdout, stderr = process.communicate()
        return process.returncode, stdout, stderr
    except Exception as e:
        return 1, "", str(e)

def log_action(message: str) -> None:
    """Log cleanup actions"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def stop_containers() -> None:
    """Stop running containers"""
    log_action("Stopping containers...")
    run_command(["docker-compose", "down"])

def remove_containers() -> None:
    """Remove all containers"""
    log_action("Removing containers...")
    run_command(["docker", "rm", "-f", "$(docker ps -aq)"])

def remove_images(all_images: bool = False) -> None:
    """Remove Docker images"""
    if all_images:
        log_action("Removing all Docker images...")
        run_command(["docker", "rmi", "-f", "$(docker images -q)"])
    else:
        log_action("Removing dangling images...")
        run_command(["docker", "image", "prune", "-f"])

def remove_volumes(all_volumes: bool = False) -> None:
    """Remove Docker volumes"""
    if all_volumes:
        log_action("Removing all volumes...")
        run_command(["docker", "volume", "rm", "-f", "$(docker volume ls -q)"])
    else:
        log_action("Removing dangling volumes...")
        run_command(["docker", "volume", "prune", "-f"])

def remove_networks() -> None:
    """Remove unused networks"""
    log_action("Removing unused networks...")
    run_command(["docker", "network", "prune", "-f"])

def clean_build_cache() -> None:
    """Clean Docker build cache"""
    log_action("Cleaning build cache...")
    run_command(["docker", "builder", "prune", "-f"])

def show_space_usage() -> None:
    """Show Docker disk space usage"""
    print("\nDocker Space Usage:")
    print("-" * 40)
    code, stdout, _ = run_command(["docker", "system", "df"])
    if code == 0:
        print(stdout)
    else:
        print("Error getting space usage information")

def full_cleanup() -> None:
    """Perform full system cleanup"""
    log_action("Starting full system cleanup...")
    
    # Stop and remove containers
    stop_containers()
    remove_containers()
    
    # Remove images and volumes
    remove_images(True)
    remove_volumes(True)
    
    # Clean other resources
    remove_networks()
    clean_build_cache()
    
    log_action("Full cleanup complete")

def safe_cleanup() -> None:
    """Perform safe cleanup (preserve important data)"""
    log_action("Starting safe cleanup...")
    
    # Only remove stopped containers
    log_action("Removing stopped containers...")
    run_command(["docker", "container", "prune", "-f"])
    
    # Remove dangling resources
    remove_images(False)
    remove_volumes(False)
    remove_networks()
    clean_build_cache()
    
    log_action("Safe cleanup complete")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Docker cleanup utility")
    parser.add_argument("--full", action="store_true", 
                       help="Perform full cleanup (WARNING: Removes all Docker resources)")
    parser.add_argument("--show-space", action="store_true",
                       help="Show Docker space usage")
    args = parser.parse_args()
    
    # Show initial space usage
    if args.show_space:
        show_space_usage()
        return
    
    # Confirm full cleanup
    if args.full:
        print("WARNING: Full cleanup will remove ALL Docker resources!")
        print("This includes:")
        print("- All containers (running and stopped)")
        print("- All images")
        print("- All volumes")
        print("- All networks")
        print("- Build cache")
        response = input("\nAre you sure you want to continue? (yes/no): ")
        if response.lower() != "yes":
            print("Cleanup cancelled")
            return
        full_cleanup()
    else:
        safe_cleanup()
    
    # Show final space usage
    print("\nFinal space usage:")
    show_space_usage()

if __name__ == "__main__":
    main()
