import time
import socket
import requests
import urllib.error
import http.client
from functools import wraps
import traceback
import logging
from datetime import datetime
import os
from discord_notify import send_discord_notification

# Configure logging
os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/network_errors.log",
    level=logging.ERROR,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("network_error_handler")

# Common network errors
NETWORK_ERRORS = (
    socket.error,
    socket.timeout,
    ConnectionError,
    ConnectionRefusedError,
    ConnectionResetError,
    ConnectionAbortedError,
    requests.exceptions.RequestException,
    requests.exceptions.ConnectionError,
    requests.exceptions.Timeout,
    urllib.error.URLError,
    http.client.HTTPException,
    TimeoutError,
    OSError
)

def with_network_error_handling(max_retries=3, initial_backoff=1, backoff_factor=2, notify_discord=True):
    """
    Decorator for functions that may encounter network errors.
    Retries the function with exponential backoff on network errors.
    
    Args:
        max_retries (int): Maximum number of retry attempts
        initial_backoff (float): Initial backoff time in seconds
        backoff_factor (float): Factor to multiply backoff time by after each attempt
        notify_discord (bool): Whether to send Discord notifications on errors
        
    Returns:
        The decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            backoff = initial_backoff
            
            while True:
                try:
                    return func(*args, **kwargs)
                except NETWORK_ERRORS as e:
                    retries += 1
                    
                    # Log the error
                    error_msg = f"Network error in {func.__name__}: {str(e)}"
                    logger.error(error_msg)
                    logger.error(traceback.format_exc())
                    
                    # Print to console
                    print(f"⚠️ Network error: {str(e)}")
                    
                    # Check if we've exceeded max retries
                    if retries > max_retries:
                        error_msg = f"Maximum retries ({max_retries}) exceeded for {func.__name__}"
                        logger.error(error_msg)
                        print(f"❌ {error_msg}")
                        
                        if notify_discord:
                            send_discord_notification(f"🔴 NETWORK ERROR: {error_msg}")
                        
                        # Re-raise the exception
                        raise
                    
                    # Calculate backoff time
                    wait_time = backoff * (backoff_factor ** (retries - 1))
                    
                    # Log retry attempt
                    retry_msg = f"Retrying {func.__name__} in {wait_time:.1f}s (attempt {retries}/{max_retries})"
                    logger.info(retry_msg)
                    print(f"🔄 {retry_msg}")
                    
                    # Wait before retrying
                    time.sleep(wait_time)
                except Exception as e:
                    # For non-network errors, log and re-raise
                    error_msg = f"Non-network error in {func.__name__}: {str(e)}"
                    logger.error(error_msg)
                    logger.error(traceback.format_exc())
                    
                    if notify_discord:
                        send_discord_notification(f"🔴 ERROR: {error_msg}")
                    
                    raise
        
        return wrapper
    
    return decorator

def is_network_error(exception):
    """
    Check if an exception is a known network error.
    
    Args:
        exception (Exception): The exception to check
        
    Returns:
        bool: True if the exception is a network error, False otherwise
    """
    return isinstance(exception, NETWORK_ERRORS)

def log_network_error(func_name, error, notify_discord=True):
    """
    Log a network error and optionally send a Discord notification.
    
    Args:
        func_name (str): Name of the function where the error occurred
        error (Exception): The error that occurred
        notify_discord (bool): Whether to send a Discord notification
    """
    error_msg = f"Network error in {func_name}: {str(error)}"
    logger.error(error_msg)
    logger.error(traceback.format_exc())
    
    if notify_discord:
        send_discord_notification(f"🔴 NETWORK ERROR: {error_msg}")
