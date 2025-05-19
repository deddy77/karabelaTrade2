import time
import pytz
import os
from datetime import datetime
import MetaTrader5 as mt5
import pandas as pd
from discord_notify import send_discord_notification
from mt5_connection_manager import MT5ConnectionManager
from network_error_handler import with_network_error_handling, is_network_error, log_network_error
from input_validator import (
    validate_symbol, validate_timeframe, validate_bars_count, 
    validate_lot_size, validate_pips, validate_risk_percent,
    validate_price, validate_order_request, validate_and_fix_input,
    safe_float, safe_int
)
from config import (
    SYMBOL, TIMEFRAME, MAGIC_NUMBER, SLIPPAGE, LOG_FILE, SYMBOL_SETTINGS,
    MARKET_OPEN_DAY, MARKET_CLOSE_DAY, MARKET_OPEN_HOUR,
    DEFAULT_TP_MULTIPLIER, DEFAULT_TP_PIPS
)

# Create a global instance of the connection manager
connection_manager = MT5ConnectionManager(check_interval=300)  # Check every 5 minutes

# Map string timeframe to MT5 timeframe
TIMEFRAME_MAP = {
    "M1": mt5.TIMEFRAME_M1,
    "M5": mt5.TIMEFRAME_M5,
    "M15": mt5.TIMEFRAME_M15,
    "M30": mt5.TIMEFRAME_M30,
    "H1": mt5.TIMEFRAME_H1,
    "H4": mt5.TIMEFRAME_H4,
    "D1": mt5.TIMEFRAME_D1,
}

def connect():
    """Connect to MetaTrader 5 and enable auto-trading with robust error handling"""
    try:
        # Use the connection manager to check and establish connection
        if not connection_manager.check_connection(force=True):
            error_msg = "Failed to connect to MT5 using connection manager"
            print(error_msg)
            log_trade(error_msg)
            send_discord_notification(f"⚠️ {error_msg}")
            return False

        # Attempt to initialize terminal info
        terminal = mt5.terminal_info()
        if terminal is None:
            error_msg = "Failed to get terminal info"
            print(error_msg)
            log_trade(error_msg)
            send_discord_notification(f"⚠️ {error_msg}")
            return False

        # Enable auto-trading if not already enabled
        if not terminal.trade_allowed:
            print("Auto-trading is disabled - attempting to enable...")
            try:
                mt5.terminal_info().trade_allowed = True
                if not mt5.terminal_info().trade_allowed:
                    error_msg = "Failed to enable auto-trading - please enable manually in MT5 terminal"
                    print(error_msg)
                    log_trade(error_msg)
                    send_discord_notification(f"⚠️ {error_msg}")
                    return False
            except Exception as e:
                error_msg = f"Error enabling auto-trading: {str(e)}"
                print(error_msg)
                log_trade(error_msg)
                send_discord_notification(f"⚠️ {error_msg}")
                return False

        # Get account info
        account_info = mt5.account_info()
        if account_info is None:
            error_msg = "Failed to get account info"
            print(error_msg)
            log_trade(error_msg)
            send_discord_notification(f"⚠️ {error_msg}")
            return False

        print(f"Connected to MT5 account: {account_info.login} ({account_info.server})")
        print(f"Balance: {account_info.balance}, Equity: {account_info.equity}")
        
        try:
            os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
        except Exception as e:
            print(f"Warning: Could not create log directory: {str(e)}")
        
        success_msg = f"Successfully connected to MT5 account {account_info.login}"
        log_trade(success_msg)
        send_discord_notification(f"✅ {success_msg}")
        return True
        
    except Exception as e:
        error_msg = f"Error connecting to MT5: {str(e)}"
        print(error_msg)
        log_trade(error_msg)
        send_discord_notification(f"❌ {error_msg}")
        return False

def check_connection():
    """Check if MT5 is connected and reconnect if necessary with enhanced error handling"""
    try:
        connection_status = connection_manager.check_connection()
        if not connection_status:
            error_msg = "MT5 connection lost - attempting to reconnect"
            print(error_msg)
            log_trade(error_msg)
            send_discord_notification(f"⚠️ {error_msg}")
            # Try to reconnect immediately
            for attempt in range(3):
                if connect():
                    success_msg = "Successfully reconnected to MT5"
                    print(success_msg)
                    log_trade(success_msg)
                    send_discord_notification(f"✅ {success_msg}")
                    return True
                time.sleep(2 ** attempt)  # Exponential backoff
        return connection_status
    except Exception as e:
        error_msg = f"Error checking MT5 connection: {str(e)}"
        print(error_msg)
        log_trade(error_msg)
        send_discord_notification(f"❌ {error_msg}")
        return False

def shutdown():
    """Shutdown connection to MetaTrader 5"""
    mt5.shutdown()
    connection_manager.connection_state = False
    print("MT5 connection closed.")

@with_network_error_handling(max_retries=3, initial_backoff=1, backoff_factor=2)
def get_historical_data(symbol=SYMBOL, timeframe=TIMEFRAME, bars_count=100):
    """Get historical price data with automatic retry on network errors"""
    # Validate inputs
    symbol_valid, symbol_error = validate_symbol(symbol)
    if not symbol_valid:
        print(f"⚠️ Invalid symbol: {symbol_error}. Using default symbol: {SYMBOL}")
        symbol = SYMBOL
        
    timeframe_valid, timeframe_error = validate_timeframe(timeframe)
    if not timeframe_valid:
        print(f"⚠️ Invalid timeframe: {timeframe_error}. Using default timeframe: {TIMEFRAME}")
        timeframe = TIMEFRAME
        
    bars_count, bars_valid, bars_error = validate_and_fix_input(
        bars_count, 
        lambda x: validate_bars_count(x, min_bars=10, max_bars=5000),
        100
    )
    if not bars_valid:
        print(f"⚠️ Invalid bars count: {bars_error}. Using default: 100")
    
    # Check connection before attempting to get data
    if not check_connection():
        print(f"⚠️ MT5 not connected! Attempting to reconnect before getting data for {symbol}")
        if not connect():
            print(f"❌ Failed to reconnect to MT5. Cannot get historical data for {symbol}")
            return None
    
    # Timeframe fallback hierarchy:
    # 1. First try the explicitly provided timeframe
    # 2. Then fall back to TIMEFRAME from config.py
    # 3. Finally use M5 as last resort
    mt5_timeframe = TIMEFRAME_MAP.get(timeframe, TIMEFRAME_MAP.get(TIMEFRAME, mt5.TIMEFRAME_M5))
    if mt5_timeframe == mt5.TIMEFRAME_M5 and timeframe != TIMEFRAME:
        print(f"⚠️ Using M5 as fallback timeframe (provided: {timeframe}, config: {TIMEFRAME})")
    
    # Get current time and fetch data relative to now
    current_time = datetime.now()
    rates = mt5.copy_rates_from(symbol, mt5_timeframe, current_time, bars_count)
    if rates is None or len(rates) == 0:
        print(f"Failed to get historical data for {symbol}")
        return None
    
    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    
    utc_tz = pytz.timezone('UTC')
    est_tz = pytz.timezone('US/Eastern')
    df['time'] = df['time'].dt.tz_localize(utc_tz).dt.tz_convert(est_tz)
    df['time'] = df['time'].dt.tz_localize(None)
    return df

def check_market_conditions(symbol=SYMBOL):
    """Check if market is suitable for trading"""
    # Validate symbol
    symbol_valid, symbol_error = validate_symbol(symbol)
    if not symbol_valid:
        print(f"⚠️ Invalid symbol: {symbol_error}. Using default symbol: {SYMBOL}")
        symbol = SYMBOL
        
    if not check_connection():
        print("⚠️ MT5 not connected!")
        return False
    
    # Check market hours (Sunday 5PM to Friday 5PM EST)
    now = datetime.now()
    est_tz = pytz.timezone('US/Eastern')
    est_time = est_tz.localize(now)
    
    # Friday after 5PM
    if est_time.weekday() == MARKET_CLOSE_DAY and est_time.hour >= MARKET_OPEN_HOUR:
        print("⚠️ Markets closed (Friday after 5PM EST)")
        return False
    # Saturday
    elif est_time.weekday() == 5:
        print("⚠️ Markets closed (Saturday)")
        return False
    # Sunday before 5PM
    elif est_time.weekday() == MARKET_OPEN_DAY and est_time.hour < MARKET_OPEN_HOUR:
        print("⚠️ Markets closed (Sunday before 5PM EST)")
        return False
    
    symbol_info = mt5.symbol_info(symbol)
    print(f"Current spread for {symbol}: {symbol_info.spread} points")
    if not symbol_info:
        print(f"⚠️ Failed to get {symbol} info")
        return False
    
    # Get symbol-specific spread limit
    max_spread = SYMBOL_SETTINGS[symbol].get("MAX_SPREAD", 20)  # Default to 20 if not specified
    
    if symbol_info.spread > max_spread:
        print(f"⚠️ Spread too wide for {symbol}: {symbol_info.spread} points")
        return False
    
    if not symbol_info.trade_mode == mt5.SYMBOL_TRADE_MODE_FULL:
        print(f"⚠️ Market not open for trading {symbol}")
        return False
    
    return True

def prepare_order_request(symbol, order_type, lot_size, price, sl=None, tp=None):
    """Prepare the order request with enhanced validation and error handling"""
    from config import USE_FIXED_SLTP, FIXED_SL_POINTS, FIXED_TP_POINTS
    # Validate symbol
    # Get fixed SL/TP prices if enabled
    if USE_FIXED_SLTP:
        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info:
            print(f"Failed to get symbol info for {symbol}")
            return None
            
        point = symbol_info.point
        if order_type == mt5.ORDER_TYPE_BUY:
            sl = price - (FIXED_SL_POINTS * point)
            tp = price + (FIXED_TP_POINTS * point)
        else:  # SELL
            sl = price + (FIXED_SL_POINTS * point)
            tp = price - (FIXED_TP_POINTS * point)
    
    symbol_valid, symbol_error = validate_symbol(symbol)
    if not symbol_valid:
        print(f"⚠️ Invalid symbol: {symbol_error}. Using default symbol: {SYMBOL}")
        symbol = SYMBOL
    
    # Validate lot size and ensure 2 decimal places
    lot_size = round(float(lot_size), 2)  # Round to 2 decimal places first
    lot_size, lot_valid, lot_error = validate_and_fix_input(
        lot_size,
        lambda x: validate_lot_size(x, min_lot=0.01, max_lot=10.0),
        0.01
    )
    if not lot_valid:
        print(f"⚠️ Invalid lot size: {lot_error}. Using minimum: 0.01")
    
    # Validate price
    price, price_valid, price_error = validate_and_fix_input(
        price,
        lambda x: validate_price(x, min_price=0.00001),
        None
    )
    if not price_valid:
        print(f"⚠️ Invalid price: {price_error}")
        return None
    
    symbol_info = mt5.symbol_info(symbol)
    if not symbol_info:
        print(f"Failed to get symbol info for {symbol}")
        return None
        
    print(f"Symbol info for {symbol} - Digits: {symbol_info.digits}, Point: {symbol_info.point}")
    print(f"Trade modes - Filling: {symbol_info.filling_mode}, Execution: {symbol_info.trade_mode}")
    
    # Convert SL/TP - keep 0.0 only if no pips were provided
    sl = safe_float(sl, 0.0)
    tp = safe_float(tp, 0.0)
    
    # Validate order type
    valid_order_types = [mt5.ORDER_TYPE_BUY, mt5.ORDER_TYPE_SELL]
    if order_type not in valid_order_types:
        error_msg = f"Invalid order type: {order_type}"
        print(error_msg)
        log_trade(error_msg)
        return None

    # Get market info for additional validation
    market_info = mt5.symbol_info(symbol)
    if not market_info:
        error_msg = f"Cannot get market info for {symbol}"
        print(error_msg)
        log_trade(error_msg)
        return None

    # Enhanced price validation
    current_tick = mt5.symbol_info_tick(symbol)
    if not current_tick:
        error_msg = f"Cannot get current price for {symbol}"
        print(error_msg)
        log_trade(error_msg)
        return None

    # Validate price is within reasonable range
    if order_type == mt5.ORDER_TYPE_BUY:
        if abs(price - current_tick.ask) > market_info.point * 100:
            error_msg = f"Price deviation too large for {symbol} buy order"
            print(error_msg)
            log_trade(error_msg)
            return None
    else:
        if abs(price - current_tick.bid) > market_info.point * 100:
            error_msg = f"Price deviation too large for {symbol} sell order"
            print(error_msg)
            log_trade(error_msg)
            return None

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": float(lot_size),
        "type": order_type,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": SLIPPAGE,
        "magic": MAGIC_NUMBER,
        "comment": "python-bot",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC,
    }
    
    print(f"Order request details for {symbol}:")
    print(f"Price: {price}, SL: {sl}, TP: {tp}")
    print(f"Volume: {lot_size}, Type: {order_type}")
    
    return request

@with_network_error_handling(max_retries=3, initial_backoff=1, backoff_factor=2)
def open_buy_order(symbol=SYMBOL, lot=None, stop_loss_pips=None, take_profit_pips=None, max_retries=3):
    """Open a buy position with proper error handling and dynamic risk management"""
    # Validate symbol
    symbol_valid, symbol_error = validate_symbol(symbol)
    if not symbol_valid:
        print(f"⚠️ Invalid symbol: {symbol_error}. Using default symbol: {SYMBOL}")
        symbol = SYMBOL
    
    # Validate lot size and ensure 2 decimal places
    if lot is None:
        print("⚠️ No lot size provided! Using minimum 0.01")
        lot = 0.01
    else:
        # Round to 2 decimal places first
        lot = round(float(lot), 2)
        lot, lot_valid, lot_error = validate_and_fix_input(
            lot,
            lambda x: validate_lot_size(x, min_lot=0.01, max_lot=10.0),
            0.01
        )
        if not lot_valid:
            print(f"⚠️ Invalid lot size: {lot_error}. Using minimum: 0.01")
    
    # Validate stop loss pips
    if stop_loss_pips is None:
        print("⚠️ No stop-loss provided! Using 20 pips default")
        stop_loss_pips = 20
    else:
        stop_loss_pips, sl_valid, sl_error = validate_and_fix_input(
            stop_loss_pips,
            lambda x: validate_pips(x, min_pips=5, max_pips=500),
            20
        )
        if not sl_valid:
            print(f"⚠️ Invalid stop loss pips: {sl_error}. Using default: 20")
    
    # Validate take profit pips
    if take_profit_pips is not None:
        take_profit_pips, tp_valid, tp_error = validate_and_fix_input(
            take_profit_pips,
            lambda x: validate_pips(x, min_pips=5, max_pips=1000),
            stop_loss_pips * 2
        )
        if not tp_valid:
            print(f"⚠️ Invalid take profit pips: {tp_error}. Using default: {stop_loss_pips * 2}")
    
    # Validate max retries
    max_retries, retries_valid, retries_error = validate_and_fix_input(
        max_retries,
        lambda x: validate_bars_count(x, min_bars=1, max_bars=10),
        3
    )
    if not retries_valid:
        print(f"⚠️ Invalid max retries: {retries_error}. Using default: 3")
    
    if not check_market_conditions(symbol):
        print(f"❌ Buy order aborted for {symbol} - bad market conditions")
        return False

    symbol_info = mt5.symbol_info(symbol)
    if not symbol_info:
        print(f"Failed to get symbol info for {symbol}")
        return False

    if not symbol_info.select:
        if not mt5.symbol_select(symbol, True):
            print(f"Failed to select {symbol}")
            return False

    point = symbol_info.point
    digits = symbol_info.digits
    
    # First check if we already have a buy position - avoid duplicate orders
    if has_buy_position(symbol):
        print(f"✅ BUY position already exists for {symbol}, skipping new order")
        return True
    
    for attempt in range(max_retries):
        try:
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                print(f"Failed to get current price for {symbol}")
                time.sleep(1)
                continue

            price = tick.ask
            pip_value = point * (10 if not symbol.endswith("JPY") else 1)  # Adjust for JPY pairs
            
            # Calculate SL/TP prices - ensure we don't pass 0.0 if pips are provided
            take_profit = round(price + (take_profit_pips * pip_value), digits) if take_profit_pips is not None else 0.0
            stop_loss = round(price - (stop_loss_pips * pip_value), digits) if stop_loss_pips is not None else 0.0
            
            # Verify SL/TP prices are valid
            if take_profit_pips is not None and take_profit == 0.0:
                print(f"❌ TP calculation failed for {symbol} - {take_profit_pips} pips resulted in 0.0")
                time.sleep(1)
                continue
                
            if stop_loss_pips is not None and stop_loss == 0.0:
                print(f"❌ SL calculation failed for {symbol} - {stop_loss_pips} pips resulted in 0.0")
                time.sleep(1)
                continue

            request = prepare_order_request(
                symbol=symbol,
                order_type=mt5.ORDER_TYPE_BUY,
                lot_size=lot,
                price=price,
                sl=stop_loss,
                tp=take_profit
            )
            
            # Rest of the function remains the same...
            # [Keep all the existing order check and execution logic]
            
            if request is None:
                print(f"Failed to prepare order request for {symbol}")
                continue

            check = mt5.order_check(request)
            print(f"\nOrder check results for {symbol}:")
            print(f"Retcode: {check.retcode}")
            print(f"Balance: {check.balance}")
            print(f"Equity: {check.equity}")
            print(f"Margin: {check.margin}")
            print(f"Margin Free: {check.margin_free}")
            
            if check.retcode == 0:  # TRADE_RETCODE_DONE (success)
                result = mt5.order_send(request)
                print(f"\nOrder send results for {symbol}:")
                print(f"Retcode: {result.retcode}")
                print(f"Description: {result.comment}")
                
                # Wait a moment for the order to process
                time.sleep(0.5)
                
                # Check if the position was actually opened, regardless of the return code
                if has_buy_position(symbol):
                    print(f"✅ BUY order executed for {symbol} at {price} ({TIMEFRAME}) (SL: {stop_loss}, TP: {take_profit})")
                    log_trade(f"OPENED BUY: {lot} lot(s) of {symbol} at {price} ({TIMEFRAME})")
                    send_discord_notification(f"🟢 BUY SIGNAL: {symbol} ({TIMEFRAME}) - {lot} lot(s) at {price}")
                    return True
                else:
                    # Only retry if we don't have a position and the return code indicated failure
                    if result.retcode != 0:
                        print(f"Order send failed for {symbol} with code: {result.retcode}")
                        print(f"Message: {result.comment}")
                    else:
                        # This is unexpected - success code but no position
                        print(f"Warning: Order returned success code but no position was detected for {symbol}")
            else:
                print(f"Order check failed for {symbol} with code: {check.retcode}")
                print(f"Message: {check.comment}")
            
            # Check again before retrying - position might have been opened despite errors
            if has_buy_position(symbol):
                print(f"✅ BUY position detected for {symbol} after attempted order, no need to retry")
                log_trade(f"OPENED BUY: {lot} lot(s) of {symbol} at {price}")
                return True
                
            time.sleep(1)

        except Exception as e:
            print(f"Error during buy order for {symbol}: {str(e)}")
            # Check if position was opened despite the exception
            if has_buy_position(symbol):
                print(f"✅ BUY position detected for {symbol} despite error, no need to retry")
                return True
            time.sleep(1)
    
    # Final check in case position was opened in the last attempt
    if has_buy_position(symbol):
        print(f"✅ BUY position detected for {symbol} after all attempts")
        return True
        
    print(f"❌ All buy order attempts failed for {symbol}")
    return False

@with_network_error_handling(max_retries=3, initial_backoff=1, backoff_factor=2)
def open_sell_order(symbol=SYMBOL, lot=None, stop_loss_pips=None, take_profit_pips=None, max_retries=3):
    """Open a sell position with proper error handling and dynamic risk management"""
    # Validate symbol
    symbol_valid, symbol_error = validate_symbol(symbol)
    if not symbol_valid:
        print(f"⚠️ Invalid symbol: {symbol_error}. Using default symbol: {SYMBOL}")
        symbol = SYMBOL
    
    # Validate lot size and ensure 2 decimal places
    if lot is None:
        print("⚠️ No lot size provided! Using minimum 0.01")
        lot = 0.01
    else:
        # Round to 2 decimal places first
        lot = round(float(lot), 2)
        lot, lot_valid, lot_error = validate_and_fix_input(
            lot,
            lambda x: validate_lot_size(x, min_lot=0.01, max_lot=10.0),
            0.01
        )
        if not lot_valid:
            print(f"⚠️ Invalid lot size: {lot_error}. Using minimum: 0.01")
    
    # Validate stop loss pips
    if stop_loss_pips is None:
        print("⚠️ No stop-loss provided! Using 20 pips default")
        stop_loss_pips = 20
    else:
        stop_loss_pips, sl_valid, sl_error = validate_and_fix_input(
            stop_loss_pips,
            lambda x: validate_pips(x, min_pips=5, max_pips=500),
            20
        )
        if not sl_valid:
            print(f"⚠️ Invalid stop loss pips: {sl_error}. Using default: 20")
    
    # Validate take profit pips
    if take_profit_pips is not None:
        take_profit_pips, tp_valid, tp_error = validate_and_fix_input(
            take_profit_pips,
            lambda x: validate_pips(x, min_pips=5, max_pips=1000),
            stop_loss_pips * 2
        )
        if not tp_valid:
            print(f"⚠️ Invalid take profit pips: {tp_error}. Using default: {stop_loss_pips * 2}")
    
    # Validate max retries
    max_retries, retries_valid, retries_error = validate_and_fix_input(
        max_retries,
        lambda x: validate_bars_count(x, min_bars=1, max_bars=10),
        3
    )
    if not retries_valid:
        print(f"⚠️ Invalid max retries: {retries_error}. Using default: 3")
    
    if not check_market_conditions(symbol):
        print(f"❌ Sell order aborted for {symbol} - bad market conditions")
        return False

    symbol_info = mt5.symbol_info(symbol)
    if not symbol_info:
        print(f"Failed to get symbol info for {symbol}")
        return False

    if not symbol_info.select:
        if not mt5.symbol_select(symbol, True):
            print(f"Failed to select {symbol}")
            return False

    point = symbol_info.point
    digits = symbol_info.digits
    
    # First check if we already have a sell position - avoid duplicate orders
    if has_sell_position(symbol):
        print(f"✅ SELL position already exists for {symbol}, skipping new order")
        return True
    
    for attempt in range(max_retries):
        try:
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                print(f"Failed to get current price for {symbol}")
                time.sleep(1)
                continue

            price = tick.bid
            pip_value = point * (10 if not symbol.endswith("JPY") else 1)  # Adjust for JPY pairs
            
            # Calculate SL/TP prices - ensure we don't pass 0.0 if pips are provided
            take_profit = round(price - (take_profit_pips * pip_value), digits) if take_profit_pips is not None else 0.0
            stop_loss = round(price + (stop_loss_pips * pip_value), digits) if stop_loss_pips is not None else 0.0
            
            # Verify SL/TP prices are valid
            if take_profit_pips is not None and take_profit == 0.0:
                print(f"❌ TP calculation failed for {symbol} - {take_profit_pips} pips resulted in 0.0")
                time.sleep(1)
                continue
                
            if stop_loss_pips is not None and stop_loss == 0.0:
                print(f"❌ SL calculation failed for {symbol} - {stop_loss_pips} pips resulted in 0.0")
                time.sleep(1)
                continue

            print(f"Calculated TP price: {take_profit} (from {take_profit_pips} pips)")
            print(f"Calculated SL price: {stop_loss} (from {stop_loss_pips} pips)")
            
            request = prepare_order_request(
                symbol=symbol,
                order_type=mt5.ORDER_TYPE_SELL,
                lot_size=lot,
                price=price,
                sl=stop_loss,
                tp=take_profit
            )
            
            # Rest of the function remains the same...
            # [Keep all the existing order check and execution logic]
            
            if request is None:
                print(f"Failed to prepare order request for {symbol}")
                continue

            check = mt5.order_check(request)
            print(f"\nOrder check results for {symbol}:")
            print(f"Retcode: {check.retcode}")
            print(f"Balance: {check.balance}")
            print(f"Equity: {check.equity}")
            print(f"Margin: {check.margin}")
            print(f"Margin Free: {check.margin_free}")
            
            if check.retcode == 0:  # TRADE_RETCODE_DONE (success)
                result = mt5.order_send(request)
                print(f"\nOrder send results for {symbol}:")
                print(f"Retcode: {result.retcode}")
                print(f"Description: {result.comment}")
                
                # Wait a moment for the order to process
                time.sleep(0.5)
                
                # Check if the position was actually opened, regardless of the return code
                if has_sell_position(symbol):
                    print(f"✅ SELL order executed for {symbol} at {price} ({TIMEFRAME}) (SL: {stop_loss}, TP: {take_profit})")
                    log_trade(f"OPENED SELL: {lot} lot(s) of {symbol} at {price} ({TIMEFRAME})")
                    send_discord_notification(f"🔴 SELL SIGNAL: {symbol} ({TIMEFRAME}) - {lot} lot(s) at {price}")
                    return True
                else:
                    # Only retry if we don't have a position and the return code indicated failure
                    if result.retcode != 0:
                        print(f"Order send failed for {symbol} with code: {result.retcode}")
                        print(f"Message: {result.comment}")
                    else:
                        # This is unexpected - success code but no position
                        print(f"Warning: Order returned success code but no position was detected for {symbol}")
            else:
                print(f"Order check failed for {symbol} with code: {check.retcode}")
                print(f"Message: {check.comment}")
            
            # Check again before retrying - position might have been opened despite errors
            if has_sell_position(symbol):
                print(f"✅ SELL position detected for {symbol} after attempted order, no need to retry")
                log_trade(f"OPENED SELL: {lot} lot(s) of {symbol} at {price}")
                return True
                
            time.sleep(1)

        except Exception as e:
            print(f"Error during sell order for {symbol}: {str(e)}")
            # Check if position was opened despite the exception
            if has_sell_position(symbol):
                print(f"✅ SELL position detected for {symbol} despite error, no need to retry")
                return True
            time.sleep(1)
    
    # Final check in case position was opened in the last attempt
    if has_sell_position(symbol):
        print(f"✅ SELL position detected for {symbol} after all attempts")
        return True
        
    print(f"❌ All sell order attempts failed for {symbol}")
    return False

@with_network_error_handling(max_retries=3, initial_backoff=1, backoff_factor=2)
def close_positions_by_type(symbol=SYMBOL, position_type=None):
    """Close positions of specific type (buy/sell) for the given symbol"""
    # Validate symbol
    symbol_valid, symbol_error = validate_symbol(symbol)
    if not symbol_valid:
        print(f"⚠️ Invalid symbol: {symbol_error}. Using default symbol: {SYMBOL}")
        symbol = SYMBOL
        
    # Validate position type
    if position_type not in [mt5.ORDER_TYPE_BUY, mt5.ORDER_TYPE_SELL]:
        print(f"⚠️ Invalid position type specified: {position_type}")
        return False
        
    positions = mt5.positions_get(symbol=symbol)
    
    if positions is None or len(positions) == 0:
        return True
    
    for position in positions:
        if position.magic != MAGIC_NUMBER or position.type != position_type:
            continue
            
        close_type = mt5.ORDER_TYPE_SELL if position.type == mt5.ORDER_TYPE_BUY else mt5.ORDER_TYPE_BUY
        price = mt5.symbol_info_tick(symbol).bid if position.type == mt5.ORDER_TYPE_BUY else mt5.symbol_info_tick(symbol).ask
        
        request = prepare_order_request(
            symbol=symbol,
            order_type=close_type,
            lot_size=position.volume,
            price=price,
            sl=0,  # No SL/TP for closing orders
            tp=0
        )
        
        if request is None:
            continue

        request["position"] = position.ticket
        result = mt5.order_send(request)
        
        if result.retcode != 0:
            error_msg = f"Close position failed for {symbol}. Error code: {result.retcode}"
            print(error_msg)
            log_trade(f"ERROR: {error_msg}")
            return False
        
        type_str = "BUY" if position.type == mt5.ORDER_TYPE_BUY else "SELL"
        success_msg = f"Closed {type_str} position: {position.volume} lot(s) of {symbol} at {price}"
        print(success_msg)
        log_trade(f"CLOSED {type_str}: {success_msg}")
        send_discord_notification(f"🟠 CLOSED {type_str}: {position.volume} lot(s) of {symbol} at {price}")
    
    return True

def close_all_positions(symbol=SYMBOL):
    """Close all positions for the given symbol"""
    # Validate symbol
    symbol_valid, symbol_error = validate_symbol(symbol)
    if not symbol_valid:
        print(f"⚠️ Invalid symbol: {symbol_error}. Using default symbol: {SYMBOL}")
        symbol = SYMBOL
        
    # Close buy positions first
    if not close_positions_by_type(symbol, mt5.ORDER_TYPE_BUY):
        return False
    # Then close sell positions
    return close_positions_by_type(symbol, mt5.ORDER_TYPE_SELL)

def get_positions(symbol=SYMBOL):
    """Get all open positions for the given symbol"""
    # Validate symbol
    symbol_valid, symbol_error = validate_symbol(symbol)
    if not symbol_valid:
        print(f"⚠️ Invalid symbol: {symbol_error}. Using default symbol: {SYMBOL}")
        symbol = SYMBOL
        
    positions = mt5.positions_get(symbol=symbol)
    return [] if positions is None else [pos for pos in positions if pos.magic == MAGIC_NUMBER]

def get_open_positions(symbol=SYMBOL):
    """Get all open positions for the given symbol (alias for get_positions)"""
    return get_positions(symbol)

def has_buy_position(symbol=SYMBOL):
    """Check if there is an open buy position"""
    # Validate symbol
    symbol_valid, symbol_error = validate_symbol(symbol)
    if not symbol_valid:
        print(f"⚠️ Invalid symbol: {symbol_error}. Using default symbol: {SYMBOL}")
        symbol = SYMBOL
        
    positions = get_open_positions(symbol)
    return any(pos.type == mt5.ORDER_TYPE_BUY for pos in positions)

def has_sell_position(symbol=SYMBOL):
    """Check if there is an open sell position"""
    # Validate symbol
    symbol_valid, symbol_error = validate_symbol(symbol)
    if not symbol_valid:
        print(f"⚠️ Invalid symbol: {symbol_error}. Using default symbol: {SYMBOL}")
        symbol = SYMBOL
        
    positions = get_open_positions(symbol)
    return any(pos.type == mt5.ORDER_TYPE_SELL for pos in positions)

def log_trade(message):
    """Log trade information to file"""
    # Validate message
    if not isinstance(message, str):
        print(f"⚠️ Invalid log message: {message}. Converting to string.")
        message = str(message)
        
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as log_file:
        log_file.write(f"{timestamp} - {message}\n")

@with_network_error_handling(max_retries=3, initial_backoff=1, backoff_factor=2)
def check_and_add_sltp(symbol=SYMBOL):
    """Check existing positions and add SL/TP if missing"""
    # Validate symbol
    symbol_valid, symbol_error = validate_symbol(symbol)
    if not symbol_valid:
        print(f"⚠️ Invalid symbol: {symbol_error}. Using default symbol: {SYMBOL}")
        symbol = SYMBOL
        
    positions = get_open_positions(symbol)
    if not positions:
        return True
    
    for position in positions:
        # Skip if position already has SL/TP
        if position.sl != 0.0 and position.tp != 0.0:
            continue
            
        print(f"Found position {position.ticket} for {symbol} with missing SL/TP")
        
        # Get current price
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            print(f"Failed to get current price for {symbol}")
            continue
            
        price = tick.ask if position.type == mt5.ORDER_TYPE_BUY else tick.bid
        point = mt5.symbol_info(symbol).point
        digits = mt5.symbol_info(symbol).digits
        pip_value = point * (10 if not symbol.endswith("JPY") else 1)
        
        # Calculate SL/TP based on risk management settings
        sl_pips = 20  # Default SL pips
        
        # Get TP multiplier from symbol settings or use default
        tp_multiplier = SYMBOL_SETTINGS.get(symbol, {}).get("TP_MULTIPLIER", DEFAULT_TP_MULTIPLIER)
        
        # Use fixed TP pips if specified, otherwise calculate from multiplier
        if DEFAULT_TP_PIPS is not None:
            tp_pips = DEFAULT_TP_PIPS
        else:
            tp_pips = int(sl_pips * tp_multiplier)
        
        # Calculate SL/TP prices based on position type
        if position.type == mt5.ORDER_TYPE_BUY:
            sl_price = round(price - (sl_pips * pip_value), digits)
            tp_price = round(price + (tp_pips * pip_value), digits)
        else:
            sl_price = round(price + (sl_pips * pip_value), digits)
            tp_price = round(price - (tp_pips * pip_value), digits)
        
        # Prepare modification request
        request = {
            "action": mt5.TRADE_ACTION_SLTP,
            "position": position.ticket,
            "symbol": symbol,
            "sl": sl_price,
            "tp": tp_price,
            "magic": MAGIC_NUMBER,
            "comment": "python-bot-added-sltp"
        }
        
        # Send modification request
        result = mt5.order_send(request)
        if result.retcode == mt5.TRADE_RETCODE_DONE:
            print(f"✅ Added SL/TP to position {position.ticket}: SL={sl_price}, TP={tp_price}")
            log_trade(f"ADDED SL/TP: {symbol} position {position.ticket} - SL={sl_price}, TP={tp_price}")
        else:
            print(f"❌ Failed to add SL/TP to position {position.ticket}: {result.comment}")
            log_trade(f"FAILED SL/TP: {symbol} position {position.ticket} - {result.comment}")
    
    return True
