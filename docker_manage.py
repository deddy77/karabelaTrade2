#!/usr/bin/env python3
"""Docker management script for KarabelaTrade Bot"""
import os
import sys
import time
import argparse
import subprocess
from typing import List, Tuple, Optional

def run_command(command: List[str]) -> Tuple[int, str, str]:
    """Run a shell command and return exit code, stdout, and stderr"""
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

def check_docker() -> bool:
    """Check if Docker is running"""
    code, _, _ = run_command(["docker", "info"])
    return code == 0

def get_container_status() -> Optional[str]:
    """Get bot container status"""
    code, stdout, _ = run_command(["docker-compose", "ps", "-q", "tradingbot"])
    if code != 0 or not stdout.strip():
        return None
    
    code, stdout, _ = run_command(["docker", "inspect", "-f", "{{.State.Status}}", stdout.strip()])
    return stdout.strip() if code == 0 else None

def show_logs(tail: int = 100) -> None:
    """Show container logs"""
    run_command(["docker-compose", "logs", "-f", "--tail", str(tail)])

def start_bot() -> bool:
    """Start the bot container"""
    print("Starting bot container...")
    code, _, stderr = run_command(["docker-compose", "up", "-d"])
    if code != 0:
        print(f"Error starting container: {stderr}")
        return False
    return True

def stop_bot() -> bool:
    """Stop the bot container"""
    print("Stopping bot container...")
    code, _, stderr = run_command(["docker-compose", "down"])
    if code != 0:
        print(f"Error stopping container: {stderr}")
        return False
    return True

def restart_bot() -> bool:
    """Restart the bot container"""
    return stop_bot() and start_bot()

def show_stats() -> None:
    """Show container resource usage"""
    run_command(["docker", "stats", "--no-stream", "kbt2_bot"])

def rebuild() -> bool:
    """Rebuild and restart the container"""
    print("Rebuilding container...")
    code, _, stderr = run_command(["docker-compose", "build", "--no-cache"])
    if code != 0:
        print(f"Error building container: {stderr}")
        return False
        
    return restart_bot()

def monitor(interval: int = 60) -> None:
    """Monitor container status and resources"""
    try:
        while True:
            os.system('cls' if os.name == 'nt' else 'clear')
            print("\nContainer Status:")
            status = get_container_status()
            print(f"Status: {status or 'Not running'}")
            
            print("\nResource Usage:")
            show_stats()
            
            print(f"\nMonitoring... (Ctrl+C to stop)")
            time.sleep(interval)
            
    except KeyboardInterrupt:
        print("\nMonitoring stopped")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Docker management for KarabelaTrade Bot")
    parser.add_argument("action", choices=[
        "start", "stop", "restart", "status", 
        "logs", "stats", "rebuild", "monitor"
    ])
    parser.add_argument("--tail", type=int, default=100, help="Number of log lines to show")
    parser.add_argument("--interval", type=int, default=60, help="Monitoring interval in seconds")
    
    args = parser.parse_args()
    
    # Check Docker
    if not check_docker():
        print("Error: Docker is not running")
        sys.exit(1)
    
    # Execute requested action
    if args.action == "start":
        sys.exit(0 if start_bot() else 1)
    elif args.action == "stop":
        sys.exit(0 if stop_bot() else 1)
    elif args.action == "restart":
        sys.exit(0 if restart_bot() else 1)
    elif args.action == "status":
        status = get_container_status()
        print(f"Container status: {status or 'Not running'}")
    elif args.action == "logs":
        show_logs(args.tail)
    elif args.action == "stats":
        show_stats()
    elif args.action == "rebuild":
        sys.exit(0 if rebuild() else 1)
    elif args.action == "monitor":
        monitor(args.interval)

if __name__ == "__main__":
    main()
