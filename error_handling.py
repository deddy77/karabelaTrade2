"""Error handling and logging utilities for KarabelaTrade Bot"""
import sys
import logging
import traceback
from functools import wraps
from typing import Callable, Any, Type, Union, Tuple

# Configure module logger
logger = logging.getLogger(__name__)

class TradingError(Exception):
    """Base class for trading-related errors"""
    pass

class MarketError(TradingError):
    """Errors related to market conditions"""
    pass

class ConnectionError(TradingError):
    """Errors related to MT5 connection"""
    pass

class OrderError(TradingError):
    """Errors related to order operations"""
    pass

class ValidationError(TradingError):
    """Errors related to data validation"""
    pass

def log_exception(e: Exception, context: str = "") -> None:
    """Log exception with full traceback and context"""
    logger.error(
        f"Error in {context if context else 'application'}: {str(e)}\n"
        f"Traceback:\n{''.join(traceback.format_tb(e.__traceback__))}"
    )

def handle_trading_error(
    error_type: Type[Exception],
    fallback_value: Any = None,
    log_level: str = "error"
) -> Callable:
    """
    Decorator for handling trading-related errors
    
    Args:
        error_type: Type of error to catch
        fallback_value: Value to return if error occurs
        log_level: Logging level to use ("error", "warning", "info")
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except error_type as e:
                # Get log method based on level
                log_method = getattr(logger, log_level)
                
                # Log the error with context
                log_method(
                    f"Error in {func.__name__}: {str(e)}\n"
                    f"Args: {args}, Kwargs: {kwargs}\n"
                    f"Traceback:\n{''.join(traceback.format_tb(e.__traceback__))}"
                )
                
                return fallback_value
        return wrapper
    return decorator

def retry_on_error(
    max_attempts: int = 3,
    retry_exceptions: Union[Type[Exception], Tuple[Type[Exception], ...]] = Exception,
    delay_seconds: float = 1.0
) -> Callable:
    """
    Decorator to retry function on error
    
    Args:
        max_attempts: Maximum number of retry attempts
        retry_exceptions: Exception types to retry on
        delay_seconds: Delay between retries in seconds
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            import time
            
            attempts = 0
            last_exception = None
            
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except retry_exceptions as e:
                    attempts += 1
                    last_exception = e
                    
                    if attempts < max_attempts:
                        logger.warning(
                            f"Attempt {attempts}/{max_attempts} failed for {func.__name__}: {str(e)}\n"
                            f"Retrying in {delay_seconds} seconds..."
                        )
                        time.sleep(delay_seconds)
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}\n"
                            f"Last error: {str(e)}\n"
                            f"Traceback:\n{''.join(traceback.format_tb(e.__traceback__))}"
                        )
            
            raise last_exception
        return wrapper
    return decorator

def safe_execute(
    operation: str,
    error_msg: str = "",
    fallback: Any = None
) -> Callable:
    """
    Decorator for safely executing operations with proper error handling and logging
    
    Args:
        operation: Description of the operation
        error_msg: Custom error message
        fallback: Fallback value if operation fails
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            try:
                return func(*args, **kwargs)
            except Exception as e:
                msg = error_msg or f"Error during {operation}"
                logger.error(
                    f"{msg}: {str(e)}\n"
                    f"Function: {func.__name__}\n"
                    f"Args: {args}, Kwargs: {kwargs}\n"
                    f"Traceback:\n{''.join(traceback.format_tb(e.__traceback__))}"
                )
                return fallback
        return wrapper
    return decorator

# Example usage:
"""
@handle_trading_error(ConnectionError, fallback_value=None)
def connect_to_broker():
    # Connection logic here
    pass

@retry_on_error(max_attempts=3, retry_exceptions=(ConnectionError, TimeoutError))
def get_market_data():
    # Data fetching logic here
    pass

@safe_execute("order placement", "Failed to place order", fallback=False)
def place_order():
    # Order placement logic here
    pass
"""
