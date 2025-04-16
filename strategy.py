# ================================
# ai-trading-bot/strategy.py
# ================================

import MetaTrader5 as mt5
import os

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

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from ta.momentum import RSIIndicator
from ta import add_all_ta_features
import forex_factory_scrap
from config import (SYMBOL, TIMEFRAME, MA_MEDIUM, MA_LONG, 
                  USE_ADAPTIVE_MA, AMA_FAST_EMA, AMA_SLOW_EMA, SYMBOL_SETTINGS,
                  DEFAULT_TP_PIPS, RSI_PERIOD, RSI_OVERBOUGHT, RSI_OVERSOLD, USE_RSI_FILTER,
                  USE_PRICE_ACTION, MIN_PATTERN_BARS, SUPPORT_RESISTANCE_LOOKBACK,
                  ANALYSIS_TIMEFRAMES, MTF_WEIGHTS, MTF_AGREEMENT_THRESHOLD, MTF_INDICATORS,
                  TRADING_SESSIONS, SESSION_PARAMS)
from mt5_helper import (get_historical_data, open_buy_order, open_sell_order, close_all_positions, has_buy_position, has_sell_position)
from risk_manager import determine_lot

def calculate_ma(df, period):
    """Calculate Simple Moving Average"""
    return df['close'].rolling(window=period).mean()

def calculate_rsi(df, period=14):
    """Calculate RSI using ta package"""
    try:
        rsi_values = RSIIndicator(close=df['close'], window=period).rsi()
        return rsi_values
    except Exception as e:
        print(f"Error calculating RSI: {str(e)}")
        return pd.Series([np.nan] * len(df), index=df.index)

def detect_price_patterns(df, lookback=20):
    """Detect common price action patterns"""
    patterns = {
        'support': False,
        'resistance': False,
        'hammer': False,
        'engulfing': False,
        'pinbar': False
    }
    
    if len(df) < lookback:
        return patterns
    
    # Support/Resistance detection
    recent_lows = df['low'].rolling(window=3).min().tail(lookback)
    recent_highs = df['high'].rolling(window=3).max().tail(lookback)
    
    current_low = df['low'].iloc[-1]
    current_high = df['high'].iloc[-1]
    
    # Support - price bouncing off recent lows
    patterns['support'] = any(abs(current_low - low) < 0.0005 for low in recent_lows)
    
    # Resistance - price bouncing off recent highs
    patterns['resistance'] = any(abs(current_high - high) < 0.0005 for high in recent_highs)
    
    # Candlestick patterns (last 3 bars)
    if len(df) >= 3:
        prev2 = df.iloc[-3]
        prev1 = df.iloc[-2]
        curr = df.iloc[-1]
        
        # Hammer pattern
        body_size = abs(curr['open'] - curr['close'])
        lower_wick = min(curr['open'], curr['close']) - curr['low']
        upper_wick = curr['high'] - max(curr['open'], curr['close'])
        
        patterns['hammer'] = (
            lower_wick > 2 * body_size and 
            upper_wick < body_size * 0.5 and
            curr['close'] > curr['open']  # Bullish hammer
        )
        
        # Engulfing pattern
        patterns['engulfing'] = (
            (prev1['close'] < prev1['open'] and  # Previous bearish
             curr['close'] > curr['open'] and    # Current bullish
             curr['open'] < prev1['close'] and
             curr['close'] > prev1['open']) or
            (prev1['close'] > prev1['open'] and  # Previous bullish
             curr['close'] < curr['open'] and    # Current bearish
             curr['open'] > prev1['close'] and
             curr['close'] < prev1['open'])
        )
        
        # Pinbar pattern
        patterns['pinbar'] = (
            (upper_wick > 2 * body_size and 
             lower_wick < body_size * 0.5) or
            (lower_wick > 2 * body_size and
             upper_wick < body_size * 0.5)
        )
    
    return patterns

def calculate_ama(df, period, fast_ema=2, slow_ema=30):
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
    """Check for recent AMA20/AMA50 crossovers"""
    df = get_historical_data(symbol, TIMEFRAME, bars_count=300)
    if df is None:
        print(f"Failed to get historical data for {symbol} recent crossover check")
        return
    
    df['ma_medium'] = calculate_ama(df, MA_MEDIUM)  # AMA50
    df['ma_long'] = calculate_ama(df, MA_LONG)      # AMA200
    
    df = df.dropna()
    
    # Automatically adapt to different timeframes
    if TIMEFRAME.startswith("M"):
        timeframe_minutes = int(TIMEFRAME[1:])
        # For M1: check 20 bars (20 mins)
        # For M5: check 4 bars (20 mins)
        # For M15: check 2 bars (30 mins)
        bars_to_check = max(2, 20 // timeframe_minutes)
    else:
        # For H1+ timeframes, check 20 bars
        bars_to_check = 20
    
    print(f"Timeframe: {TIMEFRAME}, checking {bars_to_check} bars")
    
    print(f"Checking last {bars_to_check} bars for recent crossovers...")
    
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
                    # Get symbol-specific lot size
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
                    # Get symbol-specific lot size
                    risk_df = get_historical_data(symbol, TIMEFRAME, bars_count=50)
                    if risk_df is not None:
                        lot_size, sl_pips = determine_lot(symbol, risk_df, is_buy_signal=False)
                        open_sell_order(symbol, lot_size, stop_loss_pips=sl_pips)
            else:
                print("Current price conditions do not confirm the bearish crossover")
    
    if not crossover_found:
        print(f"No recent crossovers detected in the past {minutes_to_check} minutes")



def analyze_ma_crossover(latest, prev, tf):
    """Analyze moving average crossover signals using AMA200/AMA50"""
    buy_score = 0
    sell_score = 0
    
    # Primary signal - AMA200 vs AMA50 position
    if MTF_INDICATORS.get("MA_CROSSOVER", True):
        # Debug print
        print(f"\nAMA Analysis for {tf}:")
        print(f"AMA50: {latest['ma_medium']:.5f}")
        print(f"AMA200: {latest['ma_long']:.5f}")
        print(f"Current Price: {latest['close']:.5f}")
        
        # Bullish setup: AMA50 > AMA200
        if latest['ma_medium'] > latest['ma_long']:
            buy_score += 2  # Higher weight for primary signal
            print(f"🟢 Bullish AMA setup on {tf} (AMA50 > AMA200)")
            if prev['ma_medium'] <= prev['ma_long']:
                buy_score += 1
                print(f"🟢 Fresh AMA50 cross above AMA200")
            if latest['close'] > latest['ma_medium']:
                buy_score += 0.5
                print(f"🟢 Price above AMA50 - Additional confirmation")
                
        # Bearish setup: AMA50 < AMA200
        elif latest['ma_medium'] < latest['ma_long']:
            sell_score += 2  # Higher weight for primary signal
            print(f"🔴 Bearish AMA setup on {tf} (AMA50 < AMA200)")
            if prev['ma_medium'] >= prev['ma_long']:
                sell_score += 1
                print(f"🔴 Fresh AMA50 cross below AMA200")
            if latest['close'] < latest['ma_medium']:
                sell_score += 0.5
                print(f"🔴 Price below AMA50 - Additional confirmation")
                
    return buy_score, sell_score

def analyze_rsi(latest, prev, tf):
    """Analyze RSI signals"""
    buy_score = 0
    sell_score = 0
    
    if USE_RSI_FILTER and MTF_INDICATORS.get("RSI", True) and 'rsi' in latest.index:
        rsi_value = latest['rsi']
        
        if rsi_value <= RSI_OVERSOLD:
            buy_score += 1
            print(f"RSI oversold ({rsi_value:.1f}) on {tf} - bullish")
        elif rsi_value >= RSI_OVERBOUGHT:
            sell_score += 1
            print(f"RSI overbought ({rsi_value:.1f}) on {tf} - bearish")
        elif rsi_value < 40 and rsi_value > RSI_OVERSOLD and rsi_value > prev.get('rsi', rsi_value):
            buy_score += 0.5
            print(f"RSI trending up from near oversold on {tf}")
        elif rsi_value > 60 and rsi_value < RSI_OVERBOUGHT and rsi_value < prev.get('rsi', rsi_value):
            sell_score += 0.5
            print(f"RSI trending down from near overbought on {tf}")
            
    return buy_score, sell_score

def analyze_price_patterns(df, latest, tf):
    """Analyze price action patterns"""
    buy_score = 0
    sell_score = 0
    
    if USE_PRICE_ACTION and MTF_INDICATORS.get("PRICE_ACTION", True):
        patterns = detect_price_patterns(df)
        
        # Bullish patterns
        if patterns.get('hammer', False):
            buy_score += 0.5
            print(f"Bullish hammer pattern on {tf}")
        if patterns.get('support', False):
            buy_score += 0.5
            print(f"Price at support level on {tf}")
        if patterns.get('engulfing', False) and latest['close'] > latest['open']:
            buy_score += 0.5
            print(f"Bullish engulfing pattern on {tf}")
            
        # Bearish patterns    
        if patterns.get('resistance', False):
            sell_score += 0.5
            print(f"Price at resistance level on {tf}")
        if patterns.get('pinbar', False) and latest['close'] < latest['open']:
            sell_score += 0.5
            print(f"Bearish pinbar pattern on {tf}")
        if patterns.get('engulfing', False) and latest['close'] < latest['open']:
            sell_score += 0.5
            print(f"Bearish engulfing pattern on {tf}")
            
    return buy_score, sell_score

def calculate_timeframe_signals(df, tf, weight):
    """Calculate signals for a specific timeframe"""
    if len(df) < 10:
        print(f"Not enough data points after calculating indicators for timeframe {tf}")
        return None
        
    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest
    
    buy_score = 0
    sell_score = 0
    
    # Analyze different indicators
    ma_buy, ma_sell = analyze_ma_crossover(latest, prev, tf)
    rsi_buy, rsi_sell = analyze_rsi(latest, prev, tf)
    pattern_buy, pattern_sell = analyze_price_patterns(df, latest, tf)
    
    # Combine scores
    buy_score = ma_buy + rsi_buy + pattern_buy
    sell_score = ma_sell + rsi_sell + pattern_sell
    
    # Determine signal
    signal = 'NEUTRAL'
    if buy_score > sell_score:
        signal = 'BUY'
    elif sell_score > buy_score:
        signal = 'SELL'
        
    return {
        'signal': signal,
        'buy_score': buy_score,
        'sell_score': sell_score,
        'weight': weight,
        'weighted_buy': buy_score * weight,
        'weighted_sell': sell_score * weight,
        'ma_medium': latest['ma_medium'],  # AMA50
        'ma_long': latest['ma_long'],      # AMA200
        'close': latest['close'],
        'rsi': latest.get('rsi', None)
    }

def prepare_timeframe_data(symbol, tf):
    """Prepare indicator data for a timeframe"""
    # Need more bars for AMA200
    df = get_historical_data(symbol, tf, bars_count=400)
    if df is None or len(df) == 0:
        print(f"No historical data available for {symbol} on {tf}")
        return None
        
    if len(df) < MA_LONG + 5:
        print(f"Not enough historical data for {symbol} on {tf}")
        return None
        
    # Calculate indicators
    df['ma_medium'] = calculate_ama(df, MA_MEDIUM, AMA_FAST_EMA, AMA_SLOW_EMA) if USE_ADAPTIVE_MA else calculate_ma(df, MA_MEDIUM)
    df['ma_long'] = calculate_ama(df, MA_LONG, AMA_FAST_EMA, AMA_SLOW_EMA) if USE_ADAPTIVE_MA else calculate_ma(df, MA_LONG)
    
    if USE_RSI_FILTER and MTF_INDICATORS.get("RSI", True):
        df['rsi'] = calculate_rsi(df, RSI_PERIOD)
        
    return df.dropna()

def analyze_multiple_timeframes_weighted(symbol, timeframes=ANALYSIS_TIMEFRAMES, weights=MTF_WEIGHTS):
    """Analyze M5 timeframe for AMA50/AMA200 crossover signals"""
    signals = initialize_signals()
    
    print(f"\n=== M5 AMA Analysis for {symbol} ===")
    
    # Get M5 data
    df = prepare_timeframe_data(symbol, "M5")
    if df is None or len(df) < 2:
        print("Not enough M5 data available")
        return signals
        
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    # Debug print current values
    print(f"Current Price: {latest['close']:.5f}")
    print(f"AMA50: {latest['ma_medium']:.5f}")
    print(f"AMA200: {latest['ma_long']:.5f}")
    
    # Check AMA crossover
    if latest['ma_medium'] > latest['ma_long']:
        # Bullish setup
        signals['weighted_buy_score'] = 100
        signals['overall_signal'] = 'BUY'
        signals['signal_strength'] = 100
        print("🟢 Bullish Setup: AMA50 > AMA200")
        if prev['ma_medium'] <= prev['ma_long']:
            print("🟢 Fresh Golden Cross Detected!")
            
    elif latest['ma_medium'] < latest['ma_long']:
        # Bearish setup
        signals['weighted_sell_score'] = 100
        signals['overall_signal'] = 'SELL'
        signals['signal_strength'] = 100
        print("🔴 Bearish Setup: AMA50 < AMA200")
        if prev['ma_medium'] >= prev['ma_long']:
            print("🔴 Fresh Death Cross Detected!")
            
    else:
        signals['overall_signal'] = 'NEUTRAL'
        signals['signal_strength'] = 0
        print("AMA lines equal - No clear trend")
        
    # Store M5 signals
    signals['timeframe_signals']["M5"] = {
        'signal': signals['overall_signal'],
        'ma_medium': latest['ma_medium'],
        'ma_long': latest['ma_long'],
        'close': latest['close']
    }
    
    print(f"\nFinal Signal: {signals['overall_signal']}")
    return signals

def get_current_session():
    """Determine current trading session based on time of day"""
    now = datetime.now()
    current_hour = now.hour
    
    for session, times in TRADING_SESSIONS.items():
        start = times['start_hour']
        end = times['end_hour']
        
        # Handle sessions that span midnight (like Asian session)
        if start > end:  # Session crosses midnight
            if current_hour >= start or current_hour < end:
                return session
        else:  # Normal session within same day
            if start <= current_hour < end:
                return session
    
    return None  # No active session found

def get_session_parameters(base_risk_percent):
    """Get session-specific trading parameters"""
    current_session = get_current_session()
    
    if current_session is None:
        print("No active trading session")
        return None, None, None
        
    # Get session parameters
    session_params = SESSION_PARAMS.get(current_session, {})
    
    # Calculate effective risk based on session risk multiplier
    risk_multiplier = session_params.get('risk_multiplier', 1.0)
    effective_risk = base_risk_percent * risk_multiplier
    
    # Get RSI filter setting for session
    use_rsi = session_params.get('use_rsi_filter', USE_RSI_FILTER)
    
    print(f"\nCurrent Session: {current_session}")
    print(f"Risk Multiplier: {risk_multiplier}")
    print(f"Effective Risk: {effective_risk}%")
    print(f"Using RSI Filter: {use_rsi}")
    
    return current_session, effective_risk, use_rsi

def has_upcoming_high_impact_news(symbol):
    """Check if there's upcoming high impact news for the symbol's currency"""
    print("\n=== Checking Forex Factory Calendar ===")
    events = forex_factory_scrap.fetch_forexfactory_calendar()
    now = datetime.now()
    
    if not events:
        print("No high-impact news events found today")
        return False
        
    print(f"Found {len(events)} high-impact events to check:")
    
    for event in events:
        print(f"\nChecking event: {event['event']} ({event['currency']}) at {event['time']}")
        
        # Check if event affects our symbol's currency (first 3 letters)
        if event['currency'] != symbol[:3]:
            print("-> Doesn't affect our symbol, skipping")
            continue
            
        # Parse event time (assuming format like "8:30am" or "2:00pm")
        try:
            time_str, period = event['time'].lower().replace('am', '').replace('pm', '').strip().split()
            hour, minute = map(int, time_str.split(':'))
            if 'pm' in event['time'].lower() and hour != 12:
                hour += 12
            event_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # Check if event is within our avoidance window
            time_before = event_time - timedelta(minutes=MINUTES_BEFORE_NEWS)
            time_after = event_time + timedelta(minutes=MINUTES_AFTER_NEWS)
            
            print(f"-> Event time: {event_time}")
            print(f"-> Avoidance window: {time_before} to {time_after}")
            
            if time_before <= now <= time_after:
                print(f"⚠️ HIGH IMPACT NEWS DETECTED: {event['event']} at {event['time']}")
                print("-> Avoiding trade due to news impact")
                return True
            else:
                print("-> Outside avoidance window, safe to trade")
                
        except Exception as e:
            print(f"Error parsing event time: {e}")
            continue
            
    print("\nNo upcoming high-impact news affecting our symbol")
    return False

# Add cooldown tracking
from datetime import datetime, timedelta
from typing import Dict

# Global dictionary to track last trade time per symbol
last_trade_times: Dict[str, datetime] = {}
TRADE_COOLDOWN_MINUTES = 5  # Wait at least 5 minutes between trades


def initialize_signals():
    """Initialize the signals dictionary for multi-timeframe analysis"""
    return {
        'weighted_buy_score': 0,
        'weighted_sell_score': 0, 
        'total_weight': 0,
        'timeframe_signals': {},
        'overall_signal': 'NEUTRAL'
    }

def validate_trading_conditions(symbol, risk_percent=1.0):
    """Validate all conditions before trading"""
    # Initialize diagnostic logging
    write_diagnostic_log(symbol, f"Starting trade analysis for {symbol}")
    
    # Check for upcoming high impact news
    if has_upcoming_high_impact_news(symbol):
        msg = f"Skipping trade due to upcoming high impact news"
        print(f"\n=== {symbol} NEWS CHECK ===")
        print(msg)
        write_diagnostic_log(symbol, msg)
        return False
    return True

def initialize_mt5_connection(symbol):
    """Initialize and verify MT5 connection"""
    try:
        if not mt5.initialize():
            error_msg = f"Failed to initialize MT5 connection for {symbol}. Error: {mt5.last_error()}"
            print(error_msg)
            write_diagnostic_log(symbol, error_msg)
            return False
        write_diagnostic_log(symbol, "MT5 initialized successfully")
        return True
    except Exception as e:
        error_msg = f"MT5 initialization exception for {symbol}: {str(e)}"
        print(error_msg)
        write_diagnostic_log(symbol, error_msg)
        return False

def check_cooldown(symbol, current_time):
    """Check if the symbol is in cooldown period"""
    if symbol in last_trade_times:
        time_since_last_trade = current_time - last_trade_times[symbol]
        if time_since_last_trade.total_seconds() < TRADE_COOLDOWN_MINUTES * 60:
            write_diagnostic_log(symbol, f"Skipping trade - cooldown period active ({TRADE_COOLDOWN_MINUTES} minutes)")
            return False
    return True

def handle_existing_positions(symbol, trade_signals, current_time):
    """Handle any existing positions for the symbol"""
    from mt5_helper import get_positions
    positions = get_positions(symbol)
    if positions:
        write_diagnostic_log(symbol, f"Found existing positions for {symbol}. Analyzing conflicts...")
        for pos in positions:
            if (pos.type == 0 and trade_signals['overall_signal'] == 'SELL') or \
               (pos.type == 1 and trade_signals['overall_signal'] == 'BUY'):
                write_diagnostic_log(symbol, "Closing conflicting position before new trade")
                close_all_positions(symbol)
                last_trade_times[symbol] = current_time
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
        
    # Calculate indicators
    df['ma_medium'] = calculate_ama(df, MA_MEDIUM)  # AMA50
    df['ma_long'] = calculate_ama(df, MA_LONG)      # AMA200
    if USE_RSI_FILTER:
        df['rsi'] = calculate_rsi(df, RSI_PERIOD)
    df = df.dropna()
    
    if len(df) < 10:
        print(f"Not enough data points after calculating indicators for {symbol}")
        return None
        
    return df

def check_signal_and_trade(symbol=SYMBOL, risk_percent=1.0):
    """Check for signals and execute trades based on M5 AMA crossovers"""
    from main import pm
    from mt5_helper import check_market_conditions
    
    # Initial validations
    if not validate_trading_conditions(symbol, risk_percent):
        return
        
    current_session, effective_risk, _ = get_session_parameters(risk_percent)
    if current_session is None:
        return
        
    print(f"\n=== Processing {symbol} on M5 timeframe ===")
    
    if not initialize_mt5_connection(symbol):
        return
        
    if pm.target_reached:
        print(f"Target already achieved - skipping trade for {symbol}")
        return
        
    market_open = check_market_conditions(symbol)
    print(f"Market status for {symbol}: {'OPEN' if market_open else 'CLOSED'}")
    write_diagnostic_log(symbol, f"Market {'OPEN' if market_open else 'CLOSED'}")
    
    # Get M5 data
    df = prepare_market_data(symbol)
    if df is None or len(df) < 2:
        write_diagnostic_log(symbol, "Not enough M5 data available")
        return
        
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    # Log AMA values
    write_ama_diagnostics(symbol, "M5", latest, prev)
    
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
    
    write_diagnostic_log(symbol, f"M5 AMA Signal: {signal}")
    
    # Check trading conditions
    current_time = datetime.now()
    if not check_cooldown(symbol, current_time):
        return
        
    # Process signals and execute trades if signal is not neutral
    if signal != 'NEUTRAL':
        is_buy = signal == 'BUY'
        
        # Check for existing positions that might conflict
        if not handle_existing_positions(symbol, {'overall_signal': signal}, current_time):
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
