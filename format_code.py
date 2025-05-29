"""Code formatting and linting script"""
import os
import sys
import subprocess
from pathlib import Path
import logging
from typing import List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

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

def format_with_black(files: List[str]) -> bool:
    """Format Python files using black"""
    logger.info("Running black formatter...")
    returncode, stdout, stderr = run_command(["black"] + files)
    
    if returncode != 0:
        logger.error("Black formatting failed:")
        logger.error(stderr)
        return False
        
    logger.info("Black formatting complete")
    return True

def sort_imports(files: List[str]) -> bool:
    """Sort imports using isort"""
    logger.info("Sorting imports with isort...")
    returncode, stdout, stderr = run_command(["isort"] + files)
    
    if returncode != 0:
        logger.error("Import sorting failed:")
        logger.error(stderr)
        return False
        
    logger.info("Import sorting complete")
    return True

def run_pylint(files: List[str]) -> bool:
    """Run pylint for code analysis"""
    logger.info("Running pylint...")
    returncode, stdout, stderr = run_command(["pylint"] + files)
    
    if stdout:
        logger.info("Pylint output:")
        print(stdout)
        
    if returncode != 0:
        logger.warning("Pylint found issues")
        return False
        
    logger.info("Pylint check complete")
    return True

def run_mypy(files: List[str]) -> bool:
    """Run mypy for type checking"""
    logger.info("Running mypy type checker...")
    returncode, stdout, stderr = run_command(["mypy"] + files)
    
    if stdout:
        logger.info("Mypy output:")
        print(stdout)
        
    if returncode != 0:
        logger.warning("Mypy found type issues")
        return False
        
    logger.info("Type checking complete")
    return True

def get_python_files() -> List[str]:
    """Get all Python files in the project"""
    python_files = []
    exclude_dirs = {
        "venv", "__pycache__", "build", "dist", 
        "egg-info", ".git", ".pytest_cache"
    }
    
    for root, dirs, files in os.walk("."):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
                
    return python_files

def main():
    """Main entry point"""
    # Get all Python files
    files = get_python_files()
    if not files:
        logger.error("No Python files found")
        return 1
        
    logger.info(f"Found {len(files)} Python files")
    
    # Track success
    success = True
    
    # Format code
    if not format_with_black(files):
        success = False
    
    # Sort imports
    if not sort_imports(files):
        success = False
    
    # Run linting
    if not run_pylint(files):
        success = False
    
    # Run type checking
    if not run_mypy(files):
        success = False
    
    if success:
        logger.info("All checks passed successfully!")
        return 0
    else:
        logger.warning("Some checks failed. Please review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
