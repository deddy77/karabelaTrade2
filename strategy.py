# ================================
# ai-trading-bot/strategy.py
# ================================

import MetaTrader5 as mt5
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from config import (SYMBOL, TIMEFRAME, MA_MEDIUM, MA_LONG, 
                   USE_ADAPTIVE_MA, AMA_FAST_EMA, AMA_SLOW_EMA, SYMBOL_SETTINGS,
                   DEFAULT_TP_PIPS)
from mt5_helper import (get_historical_data, open_buy_order, open_sell_order, 
                       close_all_positions, has_buy_position, has_sell_position,
                       check_market_conditions, get_positions)
from risk_manager import determine_lot

def write_diagnostic_log(symbol, message, include_separator=False):
    """Write diagnostic messages to a log file"""
    os.makedirs("logs", exist_ok=True)
    log_file = f"logs/{symbol}_diagnostics.log"
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    with open(log_file, "a") as f:
        if include_separator:
            f.write("\n" + "="*50 + "\n")
        f.write(f"{timestamp} - {message}\n")

def write_ama_diagnostics(symbol, timeframe, latest, prev):
    """Write AMA indicator diagnostics"""
    msg = (
        f"AMA Analysis on {timeframe}:\n"
        f"Current Price: {latest['close']:.5f}\n"
        f"AMA50: {latest['ma_medium']:.5f}\n"
        f"AMA200: {latest['ma_long']:.5f}\n"
        f"Previous AMA50: {prev['ma_medium']:.5f}\n"
        f"Previous AMA200: {prev['ma_long']:.5f}\n"
        f"AMA50 > AMA200: {latest['ma_medium'] > latest['ma_long']}\n"
    )
    write_diagnostic_log(symbol, msg, include_separator=True)

def calculate_ama(df, period, fast_ema=2, slow_ema=30):
    """Calculate Adaptive Moving Average"""
    direction = abs(df['close'] - df['close'].shift(period))
    volatility = df['close'].diff().abs().rolling(window=period).sum()
    
    er = (direction / volatility).fillna(0)
    
    fast_sc = 2 / (fast_ema + 1)
    slow_sc = 2 / (slow_ema + 1)
    
    sc = ((er * (fast_sc - slow_sc)) + slow_sc).pow(2)
    
    ama = pd.Series(index=df.index, dtype='float64')
    
    start_index = period + 50
    ama.iloc[start_index] = df['close'].iloc[start_index]
    
    for i in range(start_index + 1, len(df)):
        ama.iloc[i] = ama.iloc[i-1] + sc.iloc[i] * (df['close'].iloc[i] - ama.iloc[i-1])
    
    return ama

def check_recent_crossovers(minutes_to_check=5, symbol=SYMBOL):
    """Check for recent AMA50/AMA200 crossovers"""
    df = get_historical_data(symbol, TIMEFRAME, bars_count=300)
    if df is None:
        print(f"Failed to get historical data for {symbol} recent crossover check")
        return
        
    df['ma_medium'] = calculate_ama(df, MA_MEDIUM)  # AMA50
    df['ma_long'] = calculate_ama(df, MA_LONG)      # AMA200
    
    df = df.dropna()
    
    # Adapt to different timeframes
    if TIMEFRAME.startswith("M"):
        timeframe_minutes = int(TIMEFRAME[1:])
        bars_to_check = max(2, 20 // timeframe_minutes)
    else:
        bars_to_check = 20
    
    print(f"Timeframe: {TIMEFRAME}, checking {bars_to_check} bars")
    
    recent_df = df.iloc[-bars_to_check:]
    
    crossover_found = False
    
    for i in range(1, len(recent_df)):
        current = recent_df.iloc[i]
        previous = recent_df.iloc[i-1]
        
        # Golden Cross (AMA50 > AMA200)
        if current['ma_medium'] > current['ma_long'] and previous['ma_medium'] <= previous['ma_long']:
            print(f"\n*** GOLDEN CROSS DETECTED at {current['time']} ***")
            print(f"AMA50 crossed above AMA200 at price: {current['close']}")
            print(f"Previous bar: AMA50={previous['ma_medium']:.5f}, AMA200={previous['ma_long']:.5f}")
            print(f"Current bar: AMA50={current['ma_medium']:.5f}, AMA200={current['ma_long']:.5f}")
            crossover_found = True
            
            latest = df.iloc[-1]
            if latest['close'] > latest['ma_medium'] and latest['ma_medium'] > latest['ma_long']:
                print("Current price and AMA alignment is BULLISH")
                if not has_buy_position(symbol):
                    risk_df = get_historical_data(symbol, TIMEFRAME, bars_count=50)
                    if risk_df is not None:
                        lot_size, sl_pips = determine_lot(symbol, risk_df, is_buy_signal=True)
                        open_buy_order(symbol, lot_size, stop_loss_pips=sl_pips)
            else:
                print("Current price conditions do not confirm the bullish crossover")
        
        # Death Cross (AMA50 < AMA200)
        if current['ma_medium'] < current['ma_long'] and previous['ma_medium'] >= previous['ma_long']:
            print(f"\n*** DEATH CROSS DETECTED at {current['time']} ***")
            print(f"AMA50 crossed below AMA200 at price: {current['close']}")
            print(f"Previous bar: AMA50={previous['ma_medium']:.5f}, AMA200={previous['ma_long']:.5f}")
            print(f"Current bar: AMA50={current['ma_medium']:.5f}, AMA200={current['ma_long']:.5f}")
            crossover_found = True
            
            latest = df.iloc[-1]
            if latest['close'] < latest['ma_medium'] and latest['ma_medium'] < latest['ma_long']:
                print("Current price and AMA alignment is BEARISH")
                if not has_sell_position(symbol):
                    risk_df = get_historical_data(symbol, TIMEFRAME, bars_count=50)
                    if risk_df is not None:
                        lot_size, sl_pips = determine_lot(symbol, risk_df, is_buy_signal=False)
                        open_sell_order(symbol, lot_size, stop_loss_pips=sl_pips)
            else:
                print("Current price conditions do not confirm the bearish crossover")
    
    if not crossover_found:
        print(f"No recent crossovers detected in the past {minutes_to_check} minutes")

# Add cooldown tracking
last_trade_times = {}
TRADE_COOLDOWN_MINUTES = 5

def check_cooldown(symbol, current_time):
    """Check if the symbol is in cooldown period"""
    if symbol in last_trade_times:
        time_since_last_trade = current_time - last_trade_times[symbol]
        if time_since_last_trade.total_seconds() < TRADE_COOLDOWN_MINUTES * 60:
            write_diagnostic_log(symbol, f"Skipping trade - cooldown period active ({TRADE_COOLDOWN_MINUTES} minutes)")
            return False
    return True

def handle_existing_positions(symbol, signal):
    """Handle any existing positions for the symbol"""
    positions = get_positions(symbol)
    if positions:
        write_diagnostic_log(symbol, f"Found existing positions for {symbol}. Analyzing conflicts...")
        for pos in positions:
            if (pos.type == 0 and signal == 'SELL') or \
               (pos.type == 1 and signal == 'BUY'):
                write_diagnostic_log(symbol, "Closing conflicting position before new trade")
                close_all_positions(symbol)
                return False
    return True

def calculate_trade_parameters(symbol, is_buy, df):
    """Calculate trade parameters like lot size and pip values"""
    lot_size, sl_pips = determine_lot(
        symbol,
        df,
        is_buy_signal=is_buy,
        risk_percent=1.0
    )
    
    tp_pips = SYMBOL_SETTINGS.get(symbol, {}).get("TP_PIPS", DEFAULT_TP_PIPS)
    if tp_pips is None:
        tp_multiplier = SYMBOL_SETTINGS.get(symbol, {}).get("TP_MULTIPLIER", 2.0)
        tp_pips = int(sl_pips * tp_multiplier)
    
    return lot_size, sl_pips, tp_pips

def execute_trade(symbol, is_buy, lot_size, sl_pips, tp_pips):
    """Execute the trade with given parameters"""
    try:
        if is_buy:
            print(f"Attempting to open BUY position for {symbol}:")
            print(f"Lot Size: {lot_size}, SL: {sl_pips} pips, TP: {tp_pips} pips")
            open_buy_order(symbol, lot_size, stop_loss_pips=sl_pips, take_profit_pips=tp_pips)
        else:
            print(f"Attempting to open SELL position for {symbol}:")
            print(f"Lot Size: {lot_size}, SL: {sl_pips} pips, TP: {tp_pips} pips")
            open_sell_order(symbol, lot_size, stop_loss_pips=sl_pips, take_profit_pips=tp_pips)
    except Exception as e:
        error_msg = f"Error executing order: {str(e)}"
        print(error_msg)
        write_diagnostic_log(symbol, error_msg)

def prepare_market_data(symbol):
    """Prepare market data and calculate indicators"""
    df = get_historical_data(symbol, TIMEFRAME, bars_count=400)  # Increased for AMA200
    if df is None or len(df) == 0:
        print(f"No historical data available for {symbol}")
        return None
        
    if len(df) < MA_LONG + 5:
        print(f"Not enough historical data for {symbol} (need at least {MA_LONG + 5} bars)")
        return None
        
    # Calculate AMAs
    df['ma_medium'] = calculate_ama(df, MA_MEDIUM)  # AMA50
    df['ma_long'] = calculate_ama(df, MA_LONG)      # AMA200
    df = df.dropna()
    
    if len(df) < 10:
        print(f"Not enough data points after calculating indicators for {symbol}")
        return None
        
    return df

def check_signal_and_trade(symbol=SYMBOL, risk_percent=1.0):
    """Check for signals and execute trades based on AMA50/AMA200 crossovers"""
    print(f"\n=== Processing {symbol} on {TIMEFRAME} timeframe ===")
    
    # Initialize MT5
    if not mt5.initialize():
        error_msg = f"Failed to initialize MT5 connection for {symbol}. Error: {mt5.last_error()}"
        print(error_msg)
        write_diagnostic_log(symbol, error_msg)
        return
        
    write_diagnostic_log(symbol, "MT5 initialized successfully")
    
    # Check market conditions
    market_open = check_market_conditions(symbol)
    print(f"Market status for {symbol}: {'OPEN' if market_open else 'CLOSED'}")
    write_diagnostic_log(symbol, f"Market {'OPEN' if market_open else 'CLOSED'}")
    
    # Get market data
    df = prepare_market_data(symbol)
    if df is None or len(df) < 2:
        write_diagnostic_log(symbol, "Not enough data available")
        return
        
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    # Log AMA values
    write_ama_diagnostics(symbol, TIMEFRAME, latest, prev)
    
    # Determine signal based on AMA crossover
    signal = 'NEUTRAL'
    if latest['ma_medium'] > latest['ma_long']:
        signal = 'BUY'
        print("🟢 Bullish Setup: AMA50 > AMA200")
        if prev['ma_medium'] <= prev['ma_long']:
            print("🟢 Fresh Golden Cross Detected!")
    elif latest['ma_medium'] < latest['ma_long']:
        signal = 'SELL'
        print("🔴 Bearish Setup: AMA50 < AMA200")
        if prev['ma_medium'] >= prev['ma_long']:
            print("🔴 Fresh Death Cross Detected!")
    
    write_diagnostic_log(symbol, f"AMA Signal: {signal}")
    
    # Check trading conditions
    current_time = datetime.now()
    if not check_cooldown(symbol, current_time):
        return
        
    # Process signals and execute trades if signal is not neutral
    if signal != 'NEUTRAL':
        is_buy = signal == 'BUY'
        
        # Check for existing positions that might conflict
        if not handle_existing_positions(symbol, signal):
            return
            
        # Get fresh data for risk calculations
        risk_df = get_historical_data(symbol, TIMEFRAME, bars_count=50)
        if risk_df is None:
            print(f"No historical data available for {symbol}")
            return
            
        # Calculate and execute trade
        lot_size, sl_pips, tp_pips = calculate_trade_parameters(symbol, is_buy, risk_df)
        if market_open:
            last_trade_times[symbol] = current_time
            execute_trade(symbol, is_buy, lot_size, sl_pips, tp_pips)
