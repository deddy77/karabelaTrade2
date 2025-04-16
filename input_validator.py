"""
Input validation utilities for the trading bot.
Provides functions to validate different types of inputs and parameters.
"""

import re
from typing import Any, List, Dict, Union, Optional, Tuple

def validate_symbol(symbol: str) -> Tuple[bool, str]:
    """
    Validate a trading symbol.
    
    Args:
        symbol: The symbol to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(symbol, str):
        return False, f"Symbol must be a string, got {type(symbol)}"
    
    # Most forex symbols are 6 characters (e.g., EURUSD)
    # But some can be longer (e.g., EURUSD.m)
    if not re.match(r'^[A-Z]{6}(\.[a-z]+)?$', symbol):
        return False, f"Invalid symbol format: {symbol}. Expected format like 'EURUSD'"
    
    return True, ""

def validate_timeframe(timeframe: str) -> Tuple[bool, str]:
    """
    Validate a timeframe string.
    
    Args:
        timeframe: The timeframe to validate (e.g., "M1", "H1", "D1")
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(timeframe, str):
        return False, f"Timeframe must be a string, got {type(timeframe)}"
    
    valid_timeframes = ["M1", "M5", "M15", "M30", "H1", "H4", "D1"]
    if timeframe not in valid_timeframes:
        return False, f"Invalid timeframe: {timeframe}. Must be one of {valid_timeframes}"
    
    return True, ""

def validate_lot_size(lot_size: float, min_lot: float = 0.01, max_lot: float = 10.0) -> Tuple[bool, str]:
    """
    Validate a lot size.
    
    Args:
        lot_size: The lot size to validate
        min_lot: Minimum allowed lot size
        max_lot: Maximum allowed lot size
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(lot_size, (int, float)):
        return False, f"Lot size must be a number, got {type(lot_size)}"
    
    if lot_size < min_lot:
        return False, f"Lot size {lot_size} is below minimum {min_lot}"
    
    if lot_size > max_lot:
        return False, f"Lot size {lot_size} is above maximum {max_lot}"
    
    # Check if lot size is a valid multiple of 0.01
    if round(lot_size * 100) != lot_size * 100:
        return False, f"Lot size {lot_size} is not a valid multiple of 0.01"
    
    return True, ""

def validate_pips(pips: int, min_pips: int = 1, max_pips: int = 1000) -> Tuple[bool, str]:
    """
    Validate a pip value.
    
    Args:
        pips: The pip value to validate
        min_pips: Minimum allowed pips
        max_pips: Maximum allowed pips
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(pips, (int, float)):
        return False, f"Pips must be a number, got {type(pips)}"
    
    if pips < min_pips:
        return False, f"Pips {pips} is below minimum {min_pips}"
    
    if pips > max_pips:
        return False, f"Pips {pips} is above maximum {max_pips}"
    
    return True, ""

def validate_risk_percent(risk_percent: float, min_risk: float = 0.1, max_risk: float = 5.0) -> Tuple[bool, str]:
    """
    Validate a risk percentage.
    
    Args:
        risk_percent: The risk percentage to validate
        min_risk: Minimum allowed risk percentage
        max_risk: Maximum allowed risk percentage
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(risk_percent, (int, float)):
        return False, f"Risk percentage must be a number, got {type(risk_percent)}"
    
    if risk_percent < min_risk:
        return False, f"Risk percentage {risk_percent} is below minimum {min_risk}"
    
    if risk_percent > max_risk:
        return False, f"Risk percentage {risk_percent} is above maximum {max_risk}"
    
    return True, ""

def validate_bars_count(bars_count: int, min_bars: int = 10, max_bars: int = 10000) -> Tuple[bool, str]:
    """
    Validate a bars count.
    
    Args:
        bars_count: The bars count to validate
        min_bars: Minimum allowed bars
        max_bars: Maximum allowed bars
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(bars_count, int):
        return False, f"Bars count must be an integer, got {type(bars_count)}"
    
    if bars_count < min_bars:
        return False, f"Bars count {bars_count} is below minimum {min_bars}"
    
    if bars_count > max_bars:
        return False, f"Bars count {bars_count} is above maximum {max_bars}"
    
    return True, ""

def validate_price(price: float, min_price: float = 0.00001) -> Tuple[bool, str]:
    """
    Validate a price.
    
    Args:
        price: The price to validate
        min_price: Minimum allowed price
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(price, (int, float)):
        return False, f"Price must be a number, got {type(price)}"
    
    if price < min_price:
        return False, f"Price {price} is below minimum {min_price}"
    
    return True, ""

def validate_magic_number(magic_number: int) -> Tuple[bool, str]:
    """
    Validate a magic number.
    
    Args:
        magic_number: The magic number to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(magic_number, int):
        return False, f"Magic number must be an integer, got {type(magic_number)}"
    
    if magic_number < 1 or magic_number > 2147483647:
        return False, f"Magic number {magic_number} is out of range (1-2147483647)"
    
    return True, ""

def validate_slippage(slippage: int, max_slippage: int = 1000) -> Tuple[bool, str]:
    """
    Validate a slippage value.
    
    Args:
        slippage: The slippage to validate
        max_slippage: Maximum allowed slippage
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(slippage, int):
        return False, f"Slippage must be an integer, got {type(slippage)}"
    
    if slippage < 0:
        return False, f"Slippage {slippage} cannot be negative"
    
    if slippage > max_slippage:
        return False, f"Slippage {slippage} is above maximum {max_slippage}"
    
    return True, ""

def validate_order_request(request: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate an order request.
    
    Args:
        request: The order request to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    required_fields = ["action", "symbol", "volume", "type", "price"]
    for field in required_fields:
        if field not in request:
            return False, f"Missing required field: {field}"
    
    # Validate symbol
    is_valid, error_msg = validate_symbol(request["symbol"])
    if not is_valid:
        return False, error_msg
    
    # Validate volume (lot size)
    is_valid, error_msg = validate_lot_size(request["volume"])
    if not is_valid:
        return False, error_msg
    
    # Validate price
    is_valid, error_msg = validate_price(request["price"])
    if not is_valid:
        return False, error_msg
    
    return True, ""

def safe_float(value: Any, default: float = 0.0) -> float:
    """
    Safely convert a value to float.
    
    Args:
        value: The value to convert
        default: Default value if conversion fails
        
    Returns:
        The converted float value or default
    """
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_int(value: Any, default: int = 0) -> int:
    """
    Safely convert a value to int.
    
    Args:
        value: The value to convert
        default: Default value if conversion fails
        
    Returns:
        The converted int value or default
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def validate_and_fix_input(value: Any, validator_func, default_value: Any) -> Tuple[Any, bool, str]:
    """
    Validate an input and fix it if invalid.
    
    Args:
        value: The value to validate
        validator_func: The validation function to use
        default_value: Default value to use if validation fails
        
    Returns:
        Tuple of (fixed_value, was_valid, error_message)
    """
    is_valid, error_msg = validator_func(value)
    if is_valid:
        return value, True, ""
    else:
        return default_value, False, error_msg
