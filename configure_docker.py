#!/usr/bin/env python3
"""Docker environment configuration utility for KarabelaTrade Bot"""
import os
import sys
import json
from typing import Dict, Optional
from pathlib import Path

def load_config() -> Dict[str, str]:
    """Load existing configuration from .env file"""
    config = {}
    env_file = Path(".env")
    
    if env_file.exists():
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    key, value = line.split("=", 1)
                    config[key.strip()] = value.strip().strip('"\'')
    
    return config

def save_config(config: Dict[str, str]) -> None:
    """Save configuration to .env file"""
    with open(".env", "w") as f:
        f.write("# KarabelaTrade Bot Docker Environment Configuration\n\n")
        for key, value in sorted(config.items()):
            f.write(f"{key}={value}\n")

def get_input(prompt: str, default: str = "") -> str:
    """Get user input with default value"""
    if default:
        response = input(f"{prompt} [{default}]: ").strip()
        return response if response else default
    return input(f"{prompt}: ").strip()

def configure_mt5() -> Dict[str, str]:
    """Configure MetaTrader 5 settings"""
    config = {}
    print("\nMetaTrader 5 Configuration")
    print("-" * 40)
    
    config["MT5_LOGIN"] = get_input("MT5 Login")
    config["MT5_PASSWORD"] = get_input("MT5 Password")
    config["MT5_SERVER"] = get_input("MT5 Server")
    
    return config

def configure_display() -> Dict[str, str]:
    """Configure display settings for GUI"""
    config = {}
    print("\nDisplay Configuration")
    print("-" * 40)
    
    if sys.platform.startswith("linux"):
        config["DISPLAY"] = get_input("X11 Display", ":0")
    
    return config

def configure_resources() -> Dict[str, str]:
    """Configure container resource limits"""
    config = {}
    print("\nResource Configuration")
    print("-" * 40)
    
    memory = get_input("Memory Limit (in GB)", "4")
    cpus = get_input("CPU Cores", "2")
    
    config["MEMORY_LIMIT"] = f"{memory}g"
    config["CPU_LIMIT"] = cpus
    
    return config

def configure_network() -> Dict[str, str]:
    """Configure network settings"""
    config = {}
    print("\nNetwork Configuration")
    print("-" * 40)
    
    port = get_input("Web Interface Port", "8080")
    config["WEB_PORT"] = port
    
    return config

def save_settings(config: Dict[str, str]) -> None:
    """Save settings to multiple config files"""
    # Save .env file
    save_config(config)
    
    # Save docker-compose override
    compose_override = {
        "version": "3.8",
        "services": {
            "tradingbot": {
                "environment": [
                    f"{k}={v}" for k, v in config.items()
                ],
                "mem_limit": config.get("MEMORY_LIMIT", "4g"),
                "cpus": float(config.get("CPU_LIMIT", "2")),
                "ports": [
                    f"{config.get('WEB_PORT', '8080')}:8080"
                ]
            }
        }
    }
    
    with open("docker-compose.override.yml", "w") as f:
        try:
            import yaml
            yaml.dump(compose_override, f, default_flow_style=False)
        except ImportError:
            import json
            json.dump(compose_override, f, indent=2)

def main():
    """Main entry point"""
    print("KarabelaTrade Bot Docker Configuration\n")
    
    # Load existing config
    config = load_config()
    
    # Get configurations
    config.update(configure_mt5())
    config.update(configure_display())
    config.update(configure_resources())
    config.update(configure_network())
    
    # Show summary
    print("\nConfiguration Summary:")
    print("-" * 40)
    for key, value in sorted(config.items()):
        if "PASSWORD" in key:
            value = "*" * len(value)
        print(f"{key}: {value}")
    
    # Confirm and save
    if input("\nSave configuration? (y/n): ").lower().startswith('y'):
        save_settings(config)
        print("\nConfiguration saved.")
        print("You can now run: ./docker_deploy.sh")
    else:
        print("\nConfiguration cancelled.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nConfiguration cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"\nError: {str(e)}")
        sys.exit(1)
