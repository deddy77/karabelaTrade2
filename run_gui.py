"""GUI launcher for KarabelaTrade Bot"""
import os
import sys
import logging
from initialize import setup_directories, setup_logging
from version_check import check_version, print_version_info, verify_compatibility
from gui import main as gui_main

def check_environment():
    """Verify environment and dependencies"""
    try:
        # Check if running correct Python version
        if sys.version_info < (3, 8):
            print("Error: Python 3.8 or higher is required")
            return False
        
        # Verify system compatibility
        if not verify_compatibility():
            print("Error: System compatibility check failed")
            print("Please run the installer to set up required dependencies")
            return False
        
        # Check installed version
        is_match, message = check_version()
        if not is_match:
            print(f"Warning: {message}")
            print("Consider running the installer to update your installation")
            print("\nContinuing anyway in 5 seconds...")
            from time import sleep
            sleep(5)
            
        return True
        
    except Exception as e:
        print(f"Error checking environment: {str(e)}")
        return False

def setup():
    """Initialize environment and setup logging"""
    try:
        # Setup directory structure
        setup_directories()
        
        # Configure logging
        setup_logging()
        
        logging.info("Bot startup initiated")
        
    except Exception as e:
        print(f"Error during setup: {str(e)}")
        sys.exit(1)

def main():
    """Main entry point"""
    try:
        # Print version info
        print_version_info()
        
        # Check environment
        if not check_environment():
            sys.exit(1)
        
        # Run initialization
        setup()
        
        # Start GUI
        logging.info("Starting GUI...")
        gui_main()
        
    except Exception as e:
        logging.error(f"Critical error: {str(e)}")
        print(f"\nError: {str(e)}")
        print("Check logs for details.")
        sys.exit(1)
    finally:
        logging.info("Bot shutdown complete")

if __name__ == "__main__":
    main()
