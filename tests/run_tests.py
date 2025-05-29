"""Test runner for KarabelaTrade Bot tests"""
import os
import sys
import unittest
import logging
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Import test modules
from test_template import TestTemplate
# Import other test modules as they are created

def setup_test_logging():
    """Configure logging for tests"""
    log_dir = os.path.join(project_root, "logs", "tests")
    os.makedirs(log_dir, exist_ok=True)
    
    log_file = os.path.join(
        log_dir,
        f"test_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    )
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return log_file

def create_test_suite():
    """Create test suite with all tests"""
    suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestTemplate,
        # Add other test classes as they are created
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    return suite

def run_test_suite(suite, log_file):
    """Run test suite and return results"""
    logger = logging.getLogger(__name__)
    logger.info("Starting test run")
    
    # Create test runner
    runner = unittest.TextTestRunner(verbosity=2)
    
    # Run tests
    start_time = datetime.now()
    result = runner.run(suite)
    end_time = datetime.now()
    duration = end_time - start_time
    
    # Log results
    logger.info("\nTest Run Complete")
    logger.info("-" * 60)
    logger.info(f"Run Duration: {duration}")
    logger.info(f"Tests Run: {result.testsRun}")
    logger.info(f"Failures: {len(result.failures)}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Skipped: {len(result.skipped)}")
    logger.info(f"Log File: {log_file}")
    
    if result.failures:
        logger.error("\nFailures:")
        for failure in result.failures:
            logger.error(f"\n{failure[0]}\n{failure[1]}")
            
    if result.errors:
        logger.error("\nErrors:")
        for error in result.errors:
            logger.error(f"\n{error[0]}\n{error[1]}")
    
    return result.wasSuccessful()

def main():
    """Main test runner entry point"""
    # Setup logging
    log_file = setup_test_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Print header
        logger.info("=" * 60)
        logger.info("KarabelaTrade Bot Test Runner")
        logger.info("=" * 60)
        
        # Create and run test suite
        suite = create_test_suite()
        success = run_test_suite(suite, log_file)
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except Exception as e:
        logger.error(f"Error running tests: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
