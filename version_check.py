"""Version checking and update management for KarabelaTrade Bot"""
import os
import sys
import logging
import json
from datetime import datetime
from typing import Dict, Tuple

logger = logging.getLogger(__name__)

# Current version info
VERSION = "2.0.0"
RELEASE_DATE = "2025-05-19"
BUILD_NUMBER = "200"

def get_version_info() -> Dict:
    """Get current version information"""
    return {
        "version": VERSION,
        "release_date": RELEASE_DATE,
        "build": BUILD_NUMBER,
        "python_version": sys.version.split()[0],
        "platform": sys.platform
    }

def write_version_info():
    """Write version info to file"""
    version_file = "data/version_info.json"
    os.makedirs("data", exist_ok=True)
    
    info = get_version_info()
    info["install_date"] = datetime.now().strftime("%Y-%m-%d")
    
    try:
        with open(version_file, 'w') as f:
            json.dump(info, f, indent=4)
        logger.info(f"Version info written to {version_file}")
    except Exception as e:
        logger.error(f"Failed to write version info: {str(e)}")

def check_version() -> Tuple[bool, str]:
    """
    Check if current version matches installed version
    Returns: (is_match, message)
    """
    version_file = "data/version_info.json"
    
    try:
        if not os.path.exists(version_file):
            return False, "Version info not found. Please run installer."
            
        with open(version_file, 'r') as f:
            installed = json.load(f)
            
        current = get_version_info()
        
        if installed["version"] != current["version"]:
            return False, f"Version mismatch: Installed {installed['version']}, Current {current['version']}"
            
        if installed["build"] != current["build"]:
            return False, f"Build mismatch: Installed {installed['build']}, Current {current['build']}"
            
        return True, "Version check passed"
        
    except Exception as e:
        logger.error(f"Error checking version: {str(e)}")
        return False, f"Version check failed: {str(e)}"

def print_version_info():
    """Print version information"""
    info = get_version_info()
    
    print("\nKarabelaTrade Bot Version Information")
    print("-" * 40)
    print(f"Version: {info['version']}")
    print(f"Release Date: {info['release_date']}")
    print(f"Build: {info['build']}")
    print(f"Python Version: {info['python_version']}")
    print(f"Platform: {info['platform']}")
    
    # Check installed version
    is_match, message = check_version()
    print(f"\nVersion Check: {'✓' if is_match else '✗'}")
    print(f"Status: {message}")

def verify_compatibility() -> bool:
    """Verify system compatibility"""
    try:
        # Check Python version
        py_version = tuple(map(int, sys.version.split()[0].split('.')))
        if py_version < (3, 8):
            logger.error(f"Python version {py_version} not supported. Required: 3.8+")
            return False
        
        # Check required packages
        import MetaTrader5
        import pandas
        import numpy
        import matplotlib
        import mplfinance
        
        logger.info("All required packages verified")
        return True
        
    except ImportError as e:
        logger.error(f"Missing required package: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Compatibility check failed: {str(e)}")
        return False

if __name__ == "__main__":
    # Setup basic logging
    logging.basicConfig(level=logging.INFO)
    
    # Print version info
    print_version_info()
    
    # Check compatibility
    if verify_compatibility():
        print("\nSystem compatibility check passed")
    else:
        print("\nSystem compatibility check failed")
        print("Please check the logs for details")
