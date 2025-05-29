"""Test environment and components for KarabelaTrade Bot"""
import os
import sys
import logging
from datetime import datetime
import MetaTrader5 as mt5

from initialize import setup_directories, check_requirements
from logging_config import setup_logging
from error_handling import (
    handle_trading_error, retry_on_error, 
    ConnectionError, MarketError
)
from mt5_helper import connect, get_historical_data
from technical_analysis import run_technical_analysis
from discord_notify import test_discord_notification
from config import SYMBOL, TIMEFRAME

logger = logging.getLogger(__name__)

@handle_trading_error(ConnectionError, fallback_value=False)
def test_mt5_connection():
    """Test MetaTrader 5 connection"""
    logger.info("Testing MT5 connection...")
    
    if not connect():
        raise ConnectionError("Failed to connect to MetaTrader 5")
    
    account_info = mt5.account_info()
    if not account_info:
        raise ConnectionError("Failed to get account info")
        
    logger.info(f"Connected to account: {account_info.login} ({account_info.server})")
    logger.info(f"Balance: ${account_info.balance:.2f}, Equity: ${account_info.equity:.2f}")
    return True

@retry_on_error(max_attempts=3, retry_exceptions=MarketError)
def test_data_retrieval():
    """Test market data retrieval"""
    logger.info(f"Testing data retrieval for {SYMBOL}...")
    
    df = get_historical_data(SYMBOL, TIMEFRAME, bars_count=100)
    if df is None or len(df) == 0:
        raise MarketError(f"Failed to get historical data for {SYMBOL}")
        
    logger.info(f"Successfully retrieved {len(df)} bars of data")
    return True

def test_technical_analysis():
    """Test technical analysis functionality"""
    logger.info("Testing technical analysis...")
    
    df = get_historical_data(SYMBOL, TIMEFRAME, bars_count=100)
    if df is None:
        logger.error("Failed to get data for technical analysis")
        return False
        
    try:
        analysis = run_technical_analysis(df)
        if not analysis:
            logger.error("Technical analysis failed")
            return False
            
        logger.info("Technical analysis completed successfully")
        return True
    except Exception as e:
        logger.error(f"Error during technical analysis: {str(e)}")
        return False

def test_discord_notifications():
    """Test Discord notifications"""
    logger.info("Testing Discord notifications...")
    
    if test_discord_notification():
        logger.info("Discord notification test successful")
        return True
    else:
        logger.warning("Discord notification test failed")
        return False

def test_logging():
    """Test logging system"""
    logger.info("Testing logging system...")
    
    try:
        # Test different log levels
        logger.debug("Debug test message")
        logger.info("Info test message")
        logger.warning("Warning test message")
        logger.error("Error test message")
        
        # Test component loggers
        trades_logger = logging.getLogger('trades')
        analysis_logger = logging.getLogger('analysis')
        diagnostics_logger = logging.getLogger('diagnostics')
        
        trades_logger.info("Trade logger test")
        analysis_logger.info("Analysis logger test")
        diagnostics_logger.info("Diagnostics logger test")
        
        return True
    except Exception as e:
        print(f"Error testing logging system: {str(e)}")
        return False

def main():
    """Run all environment tests"""
    print("Starting environment tests...")
    
    # Initialize environment
    try:
        setup_directories()
        setup_logging()
    except Exception as e:
        print(f"Failed to initialize environment: {str(e)}")
        return False
    
    # Run tests
    tests = {
        "Requirements Check": check_requirements,
        "MT5 Connection": test_mt5_connection,
        "Data Retrieval": test_data_retrieval,
        "Technical Analysis": test_technical_analysis,
        "Discord Notifications": test_discord_notifications,
        "Logging System": test_logging
    }
    
    results = {}
    for test_name, test_func in tests.items():
        print(f"\nRunning test: {test_name}")
        try:
            result = test_func()
            results[test_name] = result
            print(f"{'✓' if result else '✗'} {test_name}: {'PASS' if result else 'FAIL'}")
        except Exception as e:
            results[test_name] = False
            print(f"✗ {test_name}: FAIL - {str(e)}")
    
    # Print summary
    print("\nTest Summary:")
    print("-" * 40)
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{test_name}: {status}")
    
    print("-" * 40)
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {total - passed}")
    
    return all(results.values())

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
