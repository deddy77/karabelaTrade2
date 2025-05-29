"""Initialize the bot environment"""
import os
import sys
import logging
from datetime import datetime
from logging_config import setup_logging
from version_check import write_version_info, verify_compatibility

def setup_directories():
    """Create necessary directories"""
    directories = [
        "logs",
        "logs/trades",
        "logs/analysis",
        "logs/diagnostics",
        "data",
        "data/charts"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Created directory: {directory}")

def main():
    """Run initialization"""
    print("Initializing KarabelaTrade Bot environment...")
    
    try:
        # Verify system compatibility
        if not verify_compatibility():
            print("System compatibility check failed")
            print("Please check requirements and try again")
            sys.exit(1)
        
        # Create directory structure
        setup_directories()
        
        # Setup logging
        setup_logging()
        logger = logging.getLogger(__name__)
        logger.info("Logging system initialized")
        
        # Write version information
        write_version_info()
        
        print("\nInitialization complete. Environment is ready.")
        logger.info("Environment initialization completed successfully")
        
    except Exception as e:
        print(f"Error during initialization: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
