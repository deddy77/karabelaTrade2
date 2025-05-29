#!/usr/bin/env python3
"""Docker image update and maintenance script for KarabelaTrade Bot"""
import os
import sys
import json
import argparse
import subprocess
from typing import List, Tuple, Dict
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
    """Log maintenance actions"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def backup_data() -> bool:
    """Backup data before update"""
    log_action("Creating data backup...")
    try:
        backup_dir = f"backups/docker_update_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(backup_dir, exist_ok=True)
        
        # Backup config and data
        for item in ["config.py", "data", "logs"]:
            if os.path.exists(item):
                if os.path.isdir(item):
                    run_command(["tar", "-czf", f"{backup_dir}/{item}.tar.gz", item])
                else:
                    run_command(["cp", item, backup_dir])
        
        log_action(f"Backup created in {backup_dir}")
        return True
    except Exception as e:
        log_action(f"Backup failed: {str(e)}")
        return False

def pull_updates() -> bool:
    """Pull latest Docker images"""
    log_action("Pulling latest images...")
    code, _, stderr = run_command(["docker-compose", "pull"])
    if code != 0:
        log_action(f"Failed to pull updates: {stderr}")
        return False
    return True

def rebuild_images() -> bool:
    """Rebuild Docker images"""
    log_action("Rebuilding images...")
    code, _, stderr = run_command(["docker-compose", "build", "--no-cache"])
    if code != 0:
        log_action(f"Failed to rebuild images: {stderr}")
        return False
    return True

def update_containers() -> bool:
    """Update running containers"""
    log_action("Updating containers...")
    
    # Stop containers
    code, _, stderr = run_command(["docker-compose", "down"])
    if code != 0:
        log_action(f"Failed to stop containers: {stderr}")
        return False
    
    # Start updated containers
    code, _, stderr = run_command(["docker-compose", "up", "-d"])
    if code != 0:
        log_action(f"Failed to start containers: {stderr}")
        return False
    
    return True

def check_health() -> bool:
    """Check container health after update"""
    log_action("Checking container health...")
    
    code, stdout, _ = run_command([
        "docker", "inspect",
        "--format", "{{.State.Health.Status}}",
        "kbt2_bot"
    ])
    
    if code != 0 or stdout.strip() != "healthy":
        log_action("Container health check failed")
        return False
    
    return True

def cleanup_old_images() -> None:
    """Clean up old and unused images"""
    log_action("Cleaning up old images...")
    run_command(["docker", "image", "prune", "-f"])

def verify_version() -> bool:
    """Verify bot version after update"""
    log_action("Verifying bot version...")
    
    code, stdout, _ = run_command([
        "docker", "exec", "kbt2_bot",
        "python", "-c", "from version_check import VERSION; print(VERSION)"
    ])
    
    if code != 0:
        log_action("Failed to verify version")
        return False
    
    log_action(f"Running version: {stdout.strip()}")
    return True

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Docker update utility")
    parser.add_argument("--no-backup", action="store_true",
                       help="Skip data backup")
    parser.add_argument("--force-rebuild", action="store_true",
                       help="Force rebuild of all images")
    args = parser.parse_args()
    
    try:
        # Create backup
        if not args.no_backup and not backup_data():
            print("Update cancelled: Backup failed")
            sys.exit(1)
        
        # Pull updates
        if not pull_updates():
            print("Update failed: Could not pull updates")
            sys.exit(1)
        
        # Rebuild if requested
        if args.force_rebuild and not rebuild_images():
            print("Update failed: Could not rebuild images")
            sys.exit(1)
        
        # Update containers
        if not update_containers():
            print("Update failed: Could not update containers")
            sys.exit(1)
        
        # Check health
        if not check_health():
            print("Update warning: Container health check failed")
        
        # Verify version
        if not verify_version():
            print("Update warning: Version verification failed")
        
        # Cleanup
        cleanup_old_images()
        
        print("\nUpdate completed successfully!")
        
    except KeyboardInterrupt:
        print("\nUpdate cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUpdate failed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
