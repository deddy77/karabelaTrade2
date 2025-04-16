# ai-trading-bot/risk_manager.py
import MetaTrader5 as mt5

MIN_LOT = 0.01  # Smallest allowed lot size
MAX_LOT = 10.0  # Largest allowed lot size
DEFAULT_RISK_PERCENT = 1.0  # 1% of account balance per trade

def get_pip_value(symbol):
    """Calculate exact pip value using MT5 data with fallback"""
    try:
        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info:
            raise Exception("Symbol info unavailable")
            
        point = symbol_info.point
        contract_size = symbol_info.trade_contract_size
        pip_value = point * 10 * contract_size  # Standard pairs
        return pip_value / 100 if symbol.endswith("JPY") else pip_value
    except Exception as e:
        print(f"⚠️ Pip calc error for {symbol}: {e}. Using estimates")
        return 10.0  # Fallback for majors

def calculate_lot_size(balance, risk_percent, stop_loss_pips, pip_value):
    """
    Safer lot size calculation with constraints
    """
    try:
        risk_amount = balance * (risk_percent / 100)
        lot_size = risk_amount / (stop_loss_pips * pip_value)
        
        # Apply broker constraints
        lot_size = max(MIN_LOT, min(lot_size, MAX_LOT))
        return round(lot_size, 2)
    except Exception as e:
        print(f"Lot calculation error: {e}. Using MIN_LOT")
        return MIN_LOT

def determine_lot(symbol, df, is_buy_signal, risk_percent=None):
    """
    Enhanced version with better error handling and logging
    """
    if risk_percent is None:
        risk_percent = DEFAULT_RISK_PERCENT
        
    try:
        account_info = mt5.account_info()
        if not account_info:
            raise RuntimeError("No MT5 account info")
            
        balance = account_info.balance
        pip_value = get_pip_value(symbol)
        stop_loss_pips = calculate_stop_loss(symbol, df, is_buy_signal)
        
        print(f"Risk Parameters for {symbol}:")
        print(f"Balance: ${balance:.2f} | Risk: {risk_percent}%")
        print(f"SL: {stop_loss_pips} pips | Pip Value: ${pip_value:.2f}")
        
        lot_size = calculate_lot_size(balance, risk_percent, stop_loss_pips, pip_value)
        print(f"Calculated Lot Size: {lot_size}")
        
        return lot_size, stop_loss_pips
        
    except Exception as e:
        print(f"Risk Manager Error: {e}. Using fallback values")
        return MIN_LOT, 20  # Fallback SL of 20 pips


def calculate_stop_loss(symbol, df, is_buy_signal):
    if len(df) < 15:  # Minimum data check
        print(f"⚠️ Not enough data ({len(df)} bars). Using fixed SL")
        return 20  # Default 20 pips
    
    """
    Calculate dynamic stop loss based on recent volatility.
    Returns stop loss in pips.
    """
    atr_period = 14
    atr = df['high'].rolling(atr_period).max() - df['low'].rolling(atr_period).min()
    recent_atr = atr.iloc[-1]
    
    # For JPY pairs, multiply by 100 since 1 pip = 0.01
    multiplier = 100 if symbol.endswith("JPY") else 10000
    
    # Convert ATR to pips
    atr_pips = recent_atr * multiplier
    
    # Use 1.5x ATR for stop loss
    stop_loss_pips = round(atr_pips * 1.5)
    
    # Ensure stop loss is within reasonable bounds
    min_sl = 10  # 10 pips minimum
    max_sl = 100  # 100 pips maximum
    
    # For buy signals, place stop below recent low
    if is_buy_signal:
        recent_low = df['low'].rolling(5).min().iloc[-1]
        price = df['close'].iloc[-1]
        sl_price_distance = (price - recent_low) * multiplier
        stop_loss_pips = max(min_sl, min(max_sl, sl_price_distance, stop_loss_pips))
    # For sell signals, place stop above recent high
    else:
        recent_high = df['high'].rolling(5).max().iloc[-1]
        price = df['close'].iloc[-1]
        sl_price_distance = (recent_high - price) * multiplier
        stop_loss_pips = max(min_sl, min(max_sl, sl_price_distance, stop_loss_pips))
    
    return stop_loss_pips
