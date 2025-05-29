#!/usr/bin/env python3
"""Check Docker compatibility and requirements"""
import os
import sys
import platform
import subprocess
from typing import List, Dict, Tuple

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

def check_docker_installed() -> bool:
    """Check if Docker is installed"""
    code, _, _ = run_command(["docker", "--version"])
    return code == 0

def check_docker_compose_installed() -> bool:
    """Check if Docker Compose is installed"""
    code, _, _ = run_command(["docker-compose", "--version"])
    return code == 0

def check_docker_running() -> bool:
    """Check if Docker daemon is running"""
    code, _, _ = run_command(["docker", "info"])
    return code == 0

def check_system_requirements() -> Dict[str, bool]:
    """Check system requirements for Docker"""
    system = platform.system().lower()
    requirements = {
        "os_supported": system in ["linux", "windows", "darwin"],
        "64bit": platform.machine().endswith('64'),
        "memory_sufficient": False,
        "disk_space_sufficient": False
    }
    
    # Check memory (need at least 4GB)
    try:
        import psutil
        total_memory = psutil.virtual_memory().total
        requirements["memory_sufficient"] = total_memory >= 4 * 1024 * 1024 * 1024
    except ImportError:
        print("Warning: psutil not installed, skipping memory check")
        requirements["memory_sufficient"] = True
    
    # Check disk space (need at least 20GB)
    try:
        disk = psutil.disk_usage(os.path.dirname(os.path.abspath(__file__)))
        requirements["disk_space_sufficient"] = disk.free >= 20 * 1024 * 1024 * 1024
    except:
        print("Warning: Could not check disk space")
        requirements["disk_space_sufficient"] = True
    
    return requirements

def check_permissions() -> bool:
    """Check if user has necessary permissions"""
    if platform.system().lower() == "windows":
        # On Windows, check if running as administrator
        try:
            return os.getuid() == 0
        except AttributeError:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
    else:
        # On Unix-like systems, check if user is in docker group
        try:
            groups = subprocess.check_output(["groups"]).decode().split()
            return "docker" in groups
        except:
            return False

def check_networking() -> bool:
    """Check if required ports are available"""
    import socket
    
    ports = [8080]  # Add other required ports here
    available = True
    
    for port in ports:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        result = sock.connect_ex(('127.0.0.1', port))
        if result == 0:
            print(f"Warning: Port {port} is already in use")
            available = False
        sock.close()
    
    return available

def main():
    """Main entry point"""
    print("Checking Docker compatibility...\n")
    
    # Check Docker installation
    if not check_docker_installed():
        print("❌ Docker is not installed")
        print("Please install Docker from https://docs.docker.com/get-docker/")
        sys.exit(1)
    print("✓ Docker is installed")
    
    # Check Docker Compose
    if not check_docker_compose_installed():
        print("❌ Docker Compose is not installed")
        print("Please install Docker Compose from https://docs.docker.com/compose/install/")
        sys.exit(1)
    print("✓ Docker Compose is installed")
    
    # Check if Docker is running
    if not check_docker_running():
        print("❌ Docker daemon is not running")
        print("Please start the Docker service")
        sys.exit(1)
    print("✓ Docker daemon is running")
    
    # Check system requirements
    requirements = check_system_requirements()
    if not all(requirements.values()):
        print("\nSystem requirements not met:")
        if not requirements["os_supported"]:
            print("❌ Unsupported operating system")
        if not requirements["64bit"]:
            print("❌ 64-bit system required")
        if not requirements["memory_sufficient"]:
            print("❌ Insufficient memory (4GB minimum required)")
        if not requirements["disk_space_sufficient"]:
            print("❌ Insufficient disk space (20GB minimum required)")
        sys.exit(1)
    print("✓ System requirements met")
    
    # Check permissions
    if not check_permissions():
        print("\n❌ Insufficient permissions")
        if platform.system().lower() == "windows":
            print("Please run as administrator")
        else:
            print("Please add your user to the docker group:")
            print("sudo usermod -aG docker $USER")
        sys.exit(1)
    print("✓ Permissions OK")
    
    # Check networking
    if not check_networking():
        print("\n⚠️ Some required ports are not available")
        print("Please ensure port 8080 is free")
    else:
        print("✓ Network ports available")
    
    print("\n✓ All checks passed - system is ready for Docker deployment")
    
if __name__ == "__main__":
    main()
