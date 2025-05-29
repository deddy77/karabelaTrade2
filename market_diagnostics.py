"""Market diagnostics and health check utilities"""
import MetaTrader5 as mt5
from datetime import datetime
import pytz
from config import (
    SYMBOL, TIMEFRAME, RISK_PER_TRADE, 
    MARKET_OPEN_DAY, MARKET_CLOSE_DAY, MARKET_OPEN_HOUR,
    MAX_SPREAD, SYMBOL_SETTINGS
)

def check_market_health(symbol=SYMBOL):
    """Check overall market health and conditions"""
    results = {
        "is_healthy": True,
        "messages": [],
        "data": {}
    }
    
    # Check market hours
    now = datetime.now()
    est_tz = pytz.timezone('US/Eastern')
    est_time = est_tz.localize(now)
    
    # Market hours check
    if est_time.weekday() == MARKET_CLOSE_DAY and est_time.hour >= MARKET_OPEN_HOUR:
        results["is_healthy"] = False
        results["messages"].append("Markets closed (Friday after 5PM EST)")
    elif est_time.weekday() == 5:  # Saturday
        results["is_healthy"] = False
        results["messages"].append("Markets closed (Saturday)")
    elif est_time.weekday() == MARKET_OPEN_DAY and est_time.hour < MARKET_OPEN_HOUR:
        results["is_healthy"] = False
        results["messages"].append("Markets closed (Sunday before 5PM EST)")
    
    # Symbol info check
    symbol_info = mt5.symbol_info(symbol)
    if not symbol_info:
        results["is_healthy"] = False
        results["messages"].append(f"Failed to get {symbol} info")
        return results
    
    # Store symbol data
    results["data"]["spread"] = symbol_info.spread
    results["data"]["trade_mode"] = symbol_info.trade_mode
    results["data"]["volume_min"] = symbol_info.volume_min
    results["data"]["volume_max"] = symbol_info.volume_max
    results["data"]["point"] = symbol_info.point
    
    # Check spread
    max_spread = SYMBOL_SETTINGS[symbol].get("MAX_SPREAD", MAX_SPREAD)
    if symbol_info.spread > max_spread:
        results["is_healthy"] = False
        results["messages"].append(f"Spread too wide: {symbol_info.spread} points")
    
    # Check trade mode
    if symbol_info.trade_mode != mt5.SYMBOL_TRADE_MODE_FULL:
        results["is_healthy"] = False
        results["messages"].append("Market not open for trading")
    
    return results

def get_account_diagnostics():
    """Get account health and status information"""
    results = {
        "is_healthy": True,
        "messages": [],
        "data": {}
    }
    
    account_info = mt5.account_info()
    if not account_info:
        results["is_healthy"] = False
        results["messages"].append("Failed to get account info")
        return results
    
    # Store account data
    results["data"]["balance"] = account_info.balance
    results["data"]["equity"] = account_info.equity
    results["data"]["margin"] = account_info.margin
    results["data"]["margin_free"] = account_info.margin_free
    results["data"]["margin_level"] = account_info.margin_level
    
    # Check margin level
    if account_info.margin_level is not None and account_info.margin_level < 200:
        results["is_healthy"] = False
        results["messages"].append(f"Low margin level: {account_info.margin_level}%")
    
    # Check if enough free margin
    if account_info.margin_free < account_info.balance * 0.1:
        results["is_healthy"] = False
        results["messages"].append("Low free margin")
    
    return results

def get_trading_diagnostics(symbol=SYMBOL):
    """Get trading-related diagnostics"""
    results = {
        "is_healthy": True,
        "messages": [],
        "data": {}
    }
    
    # Get current position info
    positions = mt5.positions_get(symbol=symbol)
    results["data"]["open_positions"] = len(positions) if positions else 0
    
    # Get symbol tick info
    tick = mt5.symbol_info_tick(symbol)
    if tick:
        results["data"]["last_price"] = tick.last
        results["data"]["volume"] = tick.volume
        results["data"]["time"] = datetime.fromtimestamp(tick.time)
    else:
        results["is_healthy"] = False
        results["messages"].append("Failed to get market tick data")
    
    # Trading parameters
    results["data"]["symbol"] = symbol
    results["data"]["timeframe"] = TIMEFRAME
    results["data"]["risk_per_trade"] = RISK_PER_TRADE
    
    return results

def run_full_diagnostics(symbol=SYMBOL):
    """Run all diagnostics and return combined results"""
    market = check_market_health(symbol)
    account = get_account_diagnostics()
    trading = get_trading_diagnostics(symbol)
    
    return {
        "market": market,
        "account": account,
        "trading": trading,
        "is_healthy": all([
            market["is_healthy"],
            account["is_healthy"],
            trading["is_healthy"]
        ])
    }
