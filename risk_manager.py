# ai-trading-bot/risk_manager.py
import MetaTrader5 as mt5
from config import (
    MIN_LOT, MAX_LOT, DEFAULT_RISK_PERCENT,
    EVALUATION_MIN_DAYS, LEVERAGE_LIMIT, ACCOUNT_SIZE
)

def calculate_max_lot_size(symbol):
    """Calculate maximum allowed lot size based on leverage limit"""
    try:
        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info:
            print(f"⚠️ Failed to get symbol info for {symbol}")
            return MIN_LOT
            
        # Log symbol details
        print(f"\nCalculating max lot size for {symbol}:")
        print(f"Contract Size: {symbol_info.trade_contract_size}")
        print(f"Current Price: {symbol_info.ask}")
            
        contract_size = symbol_info.trade_contract_size
        current_price = symbol_info.ask
        
        if contract_size <= 0 or current_price <= 0:
            print("⚠️ Invalid contract size or price")
            return MIN_LOT

        # Calculate maximum position value based on leverage limit
        max_position_value = ACCOUNT_SIZE * LEVERAGE_LIMIT
        
        # Calculate maximum lot size
        max_lot = max_position_value / (contract_size * current_price)
        
        # Round down to 2 decimal places and respect MIN/MAX_LOT
        max_lot = round(min(max_lot, MAX_LOT), 2)
        max_lot = max(max_lot, MIN_LOT)
        
        # Log detailed calculations
        print(f"\nLeverage Calculations:")
        print(f"Max Position Value: ${max_position_value:.2f}")
        print(f"Account Size: ${ACCOUNT_SIZE:.2f}")
        print(f"Leverage Limit: {LEVERAGE_LIMIT}:1")
        print(f"Contract Size: {contract_size}")
        print(f"Current Price: {current_price:.5f}")
        print(f"Maximum Lot Size: {max_lot}")
        
        return max_lot
    except Exception as e:
        print(f"Error calculating max lot size: {e}")
        return MIN_LOT

def get_current_leverage_usage():
    """Calculate current leverage usage from existing positions"""
    try:
        positions = mt5.positions_get()
        if positions is None:
            return 0.0
            
        total_position_value = 0.0
        for pos in positions:
            symbol_info = mt5.symbol_info(pos.symbol)
            if symbol_info:
                position_value = pos.volume * symbol_info.trade_contract_size * pos.price_current
                total_position_value += position_value
                
        return total_position_value / ACCOUNT_SIZE
    except Exception as e:
        print(f"Error calculating current leverage: {e}")
        return 0.0

def check_leverage(symbol, lot_size):
    """Check if trade stays within leverage limits and adjust if needed, considering existing positions"""
    try:
        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info:
            return MIN_LOT
            
        contract_size = symbol_info.trade_contract_size
        current_price = symbol_info.ask
        position_value = lot_size * contract_size * current_price
        
        # Calculate total leverage including existing positions
        current_leverage = get_current_leverage_usage()
        new_leverage = position_value / ACCOUNT_SIZE
        total_leverage = current_leverage + new_leverage
        
        print(f"\nLeverage Analysis:")
        print(f"Current Portfolio Leverage: {current_leverage:.1f}:1")
        print(f"New Position Leverage: {new_leverage:.1f}:1")
        print(f"Total Combined Leverage: {total_leverage:.1f}:1")
        
        if total_leverage > LEVERAGE_LIMIT:
            print(f"⚠️ Total leverage {total_leverage:.1f}:1 would exceed limit {LEVERAGE_LIMIT}:1")
            
            # Calculate and log maximum allowed lot size
            max_lot = calculate_max_lot_size(symbol)
            print(f"\nLeverage Adjustment Required:")
            print(f"Current Portfolio Leverage: {current_leverage:.1f}:1")
            print(f"Position Value: ${position_value:.2f}")
            print(f"Account Size: ${ACCOUNT_SIZE:.2f}")
            print(f"Max Leverage: {LEVERAGE_LIMIT}:1")
            print(f"Adjusting lot size from {lot_size} to {max_lot}")
            return max_lot
            
        print(f"Leverage check passed: {total_leverage:.1f}:1")
        return lot_size
    except Exception as e:
        print(f"Leverage check error: {e}")
        return False

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
        
        # Round to 2 decimal places before applying constraints
        lot_size = round(lot_size, 2)
        
        # Apply broker constraints
        lot_size = max(MIN_LOT, min(lot_size, MAX_LOT))
        return lot_size
    except Exception as e:
        print(f"Lot calculation error: {e}. Using MIN_LOT")
        return MIN_LOT

def determine_lot(symbol, df, is_buy_signal, risk_percent=None):
    """
    Enhanced version with improved leverage handling and evaluation period scaling
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

        # Get current price and symbol info
        symbol_info = mt5.symbol_info(symbol)
        if not symbol_info:
            raise RuntimeError(f"Failed to get {symbol} info")

        # Check evaluation period
        from profit_manager import ProfitManager
        pm = ProfitManager()
        in_evaluation = pm.trading_days <= EVALUATION_MIN_DAYS
        
        # Apply evaluation period risk reduction
        if in_evaluation:
            risk_percent *= 0.75  # 25% risk reduction
            print(f"Evaluation Period: Reducing risk to {risk_percent:.2f}%")
        
        # Calculate initial lot size based on risk
        lot_size = calculate_lot_size(balance, risk_percent, stop_loss_pips, pip_value)
        print(f"\nRisk Parameters for {symbol}:")
        print(f"Balance: ${balance:.2f} | Risk: {risk_percent}%")
        print(f"SL: {stop_loss_pips} pips | Pip Value: ${pip_value:.2f}")
        print(f"Initial Lot Size: {lot_size}")
        
        # Get maximum allowed lot size based on leverage limit
        max_lot = calculate_max_lot_size(symbol)
        
        # Ensure lot size complies with leverage limit
        if lot_size > max_lot:
            print(f"\nLeverage Compliance:")
            print(f"Maximum allowed lot size: {max_lot}")
            print(f"Initial lot size ({lot_size}) exceeds maximum")
            print(f"Reducing lot size to {max_lot} to comply with 1:{LEVERAGE_LIMIT} leverage limit")
            lot_size = max_lot
            
        print(f"Final Lot Size: {lot_size}")
        
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
