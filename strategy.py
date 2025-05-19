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

def write_macd_diagnostics(symbol, tf, macd_line, signal_line, histogram, recent_hist):
    """Write MACD diagnostics to log"""
    msg = (
        f"MACD Analysis on {tf}:\n"
        f"MACD Line: {macd_line.iloc[-1]:.5f}\n"
        f"Signal Line: {signal_line.iloc[-1]:.5f}\n"
        f"Histogram: {histogram.iloc[-1]:.5f}\n"
        f"Last {len(recent_hist)} histogram values:\n"
    )
    for i, val in enumerate(recent_hist):
        msg += f"Bar {i+1}: {val:.5f}\n"
    
    msg += f"Growing bars detected: {all(recent_hist.iloc[i] > recent_hist.iloc[i-1] for i in range(1, len(recent_hist)))}\n"
    msg += f"Zero line cross: {(histogram.iloc[-len(recent_hist)-1] < 0) != (histogram.iloc[-1] < 0)}\n"
    
    write_diagnostic_log(symbol, msg, include_separator=True)

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from ta.momentum import RSIIndicator
from ta import add_all_ta_features
import forex_factory_scrap
from config import (SYMBOL, TIMEFRAME, MA_MEDIUM, MA_LONG, ATR_PERIOD, MAX_ATR_MULT, MIN_ATR_MULT,
                  KC_PERIOD, KC_ATR_MULT, KC_USE_EMA,
                  USE_ADAPTIVE_MA, AMA_FAST_EMA, AMA_SLOW_EMA, SYMBOL_SETTINGS,
                  DEFAULT_TP_PIPS, RSI_PERIOD, RSI_OVERBOUGHT, RSI_OVERSOLD, USE_RSI_FILTER,
                  USE_PRICE_ACTION, MIN_PATTERN_BARS, SUPPORT_RESISTANCE_LOOKBACK,
                  ANALYSIS_TIMEFRAMES, MTF_WEIGHTS, MTF_AGREEMENT_THRESHOLD, MTF_INDICATORS,
                  session_mgr, MIN_AMA_GAP_PERCENT,
                  USE_ADX_FILTER, ADX_PERIOD, ADX_THRESHOLD, ADX_EXTREME,
                  USE_MACD_FILTER, MACD_FAST, MACD_SLOW, MACD_SIGNAL,
                  MACD_CONSECUTIVE_BARS, MACD_GROWING_FACTOR, MACD_ZERO_CROSS_CONFIRM,
                  USE_BB_FILTER, BB_PERIOD, BB_STD_DEV, BB_EXTENSION_THRESHOLD, MIN_BB_BANDWIDTH,
                  MAX_PRICE_DEVIATION_PIPS)
from mt5_helper import (get_historical_data, open_buy_order, open_sell_order, close_all_positions, has_buy_position, has_sell_position)
from risk_manager import determine_lot

def calculate_ma(df, period, use_vwma=False):
    """Calculate Simple Moving Average or Volume-Weighted Moving Average"""
    if use_vwma:
        volume = df['tick_volume'] if 'tick_volume' in df.columns else None
        if volume is not None:
            # Calculate VWMA using tick volume
            return (df['close'] * volume).rolling(window=period).sum() / volume.rolling(window=period).sum()
    # Calculate regular SMA if no volume data or VWMA not requested
    return df['close'].rolling(window=period).mean()

def calculate_vwma(df, period):
    """Calculate Volume-Weighted Moving Average using tick volume"""
    try:
        # Use 'tick_volume' from MT5 data instead of 'volume'
        volume = df['tick_volume'] if 'tick_volume' in df.columns else None
        
        if volume is None:
            print("No volume data available, skipping VWMA calculation")
            return pd.Series([np.nan] * len(df), index=df.index)
            
        return (df['close'] * volume).rolling(window=period).sum() / volume.rolling(window=period).sum()
    except Exception as e:
        print(f"Error calculating VWMA: {str(e)}")
        return pd.Series([np.nan] * len(df), index=df.index)

def calculate_atr(df, period=14):
    """Calculate Average True Range"""
    try:
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift())
        low_close = abs(df['low'] - df['close'].shift())
        
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        atr = true_range.rolling(window=period).mean()
        return atr
    except Exception as e:
        print(f"Error calculating ATR: {str(e)}")
        return pd.Series([np.nan] * len(df), index=df.index)

def calculate_keltner_channels(df, period=20, atr_mult=2.0, use_ema=True):
    """Calculate Keltner Channels"""
    try:
        # Calculate middle line (EMA or SMA)
        if use_ema:
            middle_line = df['close'].ewm(span=period, adjust=False).mean()
        else:
            middle_line = df['close'].rolling(window=period).mean()
        
        # Calculate ATR for channel width
        atr = calculate_atr(df, period)
        
        # Calculate upper and lower channels
        upper_channel = middle_line + (atr * atr_mult)
        lower_channel = middle_line - (atr * atr_mult)
        
        # Calculate channel width as percentage of middle line
        channel_width = (upper_channel - lower_channel) / middle_line * 100
        
        return upper_channel, middle_line, lower_channel, channel_width
    except Exception as e:
        print(f"Error calculating Keltner Channels: {str(e)}")
        return None, None, None, None

def calculate_bollinger_bands(df, period=20, std_dev=2):
    """Calculate Bollinger Bands"""
    try:
        middle_band = df['close'].rolling(window=period).mean()
        std = df['close'].rolling(window=period).std()
        upper_band = middle_band + (std * std_dev)
        lower_band = middle_band - (std * std_dev)
        bandwidth = (upper_band - lower_band) / middle_band * 100
        return upper_band, middle_band, lower_band, bandwidth
    except Exception as e:
        print(f"Error calculating Bollinger Bands: {str(e)}")
        return None, None, None, None

def calculate_roc(df, period=14):
    """Calculate Rate of Change (ROC) indicator"""
    try:
        roc = ((df['close'] - df['close'].shift(period)) / df['close'].shift(period)) * 100
        return roc
    except Exception as e:
        print(f"Error calculating ROC: {str(e)}")
        return pd.Series([np.nan] * len(df), index=df.index)

def calculate_rsi(df, period=14):
    """Calculate RSI using ta package"""
    try:
        rsi_values = RSIIndicator(close=df['close'], window=period).rsi()
        return rsi_values
    except Exception as e:
        print(f"Error calculating RSI: {str(e)}")
        return pd.Series([np.nan] * len(df), index=df.index)

def analyze_volume_patterns(df):
    """Analyze volume patterns for price action confirmation using tick volume"""
    try:
        # Use tick_volume from MT5 data
        volume = df['tick_volume'] if 'tick_volume' in df.columns else None
        
        if volume is None:
            print("No volume data available for analysis")
            return None
            
        close = df['close']
        high = df['high']
        low = df['low']
        
        # Get recent data
        recent_volume = volume.tail(5)
        avg_volume = volume.rolling(window=20).mean().iloc[-1]
        
        # Volume analysis
        volume_increasing = recent_volume.is_monotonic_increasing
        volume_above_avg = recent_volume.iloc[-1] > avg_volume
        price_spread = high.iloc[-1] - low.iloc[-1]
        avg_spread = (high - low).rolling(window=20).mean().iloc[-1]
        wide_spread = price_spread > avg_spread * 1.2
        
        return {
            'volume_increasing': volume_increasing,
            'volume_above_avg': volume_above_avg,
            'wide_spread': wide_spread,
            'current_volume': recent_volume.iloc[-1],
            'avg_volume': avg_volume,
            'volume_ratio': recent_volume.iloc[-1] / avg_volume if avg_volume > 0 else 0
        }
    except Exception as e:
        print(f"Error analyzing volume patterns: {str(e)}")
        return None

def calculate_obv(df):
    """Calculate On-Balance Volume (OBV) indicator using tick volume"""
    try:
        obv = pd.Series(0.0, index=df.index)
        
        # Get volume data
        volume = df['tick_volume'] if 'tick_volume' in df.columns else None
        if volume is None:
            print("No volume data available for OBV calculation")
            return obv
        
        # Calculate OBV
        for i in range(1, len(df)):
            if df['close'].iloc[i] > df['close'].iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] + volume.iloc[i]
            elif df['close'].iloc[i] < df['close'].iloc[i-1]:
                obv.iloc[i] = obv.iloc[i-1] - volume.iloc[i]
            else:
                obv.iloc[i] = obv.iloc[i-1]
        
        return obv
    except Exception as e:
        print(f"Error calculating OBV: {str(e)}")
        return pd.Series([np.nan] * len(df), index=df.index)

def calculate_adx(df, period=14):
    """Calculate Average Directional Index (ADX) and DMI for trend strength"""
    try:
        # Calculate +DI and -DI
        high_diff = df['high'].diff()
        low_diff = -df['low'].diff()
        
        # True Range
        tr1 = df['high'] - df['low']
        tr2 = abs(df['high'] - df['close'].shift(1))
        tr3 = abs(df['low'] - df['close'].shift(1))
        tr = pd.DataFrame({'tr1': tr1, 'tr2': tr2, 'tr3': tr3}).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        # Directional Movement
        pos_dm = high_diff.copy()
        neg_dm = low_diff.copy()
        
        pos_dm[pos_dm < 0] = 0
        neg_dm[neg_dm < 0] = 0
        
        # When high_diff and low_diff are both positive, keep only the larger one
        for i in range(len(df)):
            if high_diff.iloc[i] > 0 and low_diff.iloc[i] > 0:
                if high_diff.iloc[i] > low_diff.iloc[i]:
                    neg_dm.iloc[i] = 0
                else:
                    pos_dm.iloc[i] = 0
        
        # Smoothed Directional Indicators
        pos_di = 100 * (pos_dm.rolling(window=period).mean() / atr)
        neg_di = 100 * (neg_dm.rolling(window=period).mean() / atr)
        
        # Directional Index
        dx = 100 * abs(pos_di - neg_di) / (pos_di + neg_di)
        
        # Average Directional Index
        adx = dx.rolling(window=period).mean()
        
        # Return ADX along with +DI and -DI for trend direction confirmation
        return adx, pos_di, neg_di
    except Exception as e:
        print(f"Error calculating ADX: {str(e)}")
        return pd.Series([np.nan] * len(df), index=df.index), pd.Series([np.nan] * len(df), index=df.index), pd.Series([np.nan] * len(df), index=df.index)

def detect_dynamic_sr_levels(df, lookback=50, min_touches=2, buffer_pips=3):
    """Identify dynamic support/resistance levels based on recent price action"""
    buffer = buffer_pips * 0.0001  # Convert pips to price level
    levels = {'supports': [], 'resistances': []}
    
    # Get recent price data
    recent_df = df.tail(lookback)
    
    # Find potential support levels (clusters of lows)
    low_clusters = []
    current_cluster = []
    
    for i in range(len(recent_df)):
        current_low = recent_df['low'].iloc[i]
        
        # Check if price is near any existing cluster
        found_cluster = False
        for cluster in low_clusters:
            if any(abs(current_low - x) <= buffer for x in cluster):
                cluster.append(current_low)
                found_cluster = True
                break
                
        if not found_cluster:
            # Check if price is near any price in current cluster
            if current_cluster and any(abs(current_low - x) <= buffer for x in current_cluster):
                current_cluster.append(current_low)
            else:
                if len(current_cluster) >= min_touches:
                    low_clusters.append(current_cluster)
                current_cluster = [current_low]
    
    # Add last cluster if valid
    if len(current_cluster) >= min_touches:
        low_clusters.append(current_cluster)
    
    # Calculate support levels as average of clusters
    for cluster in low_clusters:
        if len(cluster) >= min_touches:
            levels['supports'].append(sum(cluster)/len(cluster))
    
    # Repeat for resistance levels (clusters of highs)
    high_clusters = []
    current_cluster = []
    
    for i in range(len(recent_df)):
        current_high = recent_df['high'].iloc[i]
        
        # Check if price is near any existing cluster
        found_cluster = False
        for cluster in high_clusters:
            if any(abs(current_high - x) <= buffer for x in cluster):
                cluster.append(current_high)
                found_cluster = True
                break
                
        if not found_cluster:
            # Check if price is near any price in current cluster
            if current_cluster and any(abs(current_high - x) <= buffer for x in current_cluster):
                current_cluster.append(current_high)
            else:
                if len(current_cluster) >= min_touches:
                    high_clusters.append(current_cluster)
                current_cluster = [current_high]
    
    # Add last cluster if valid
    if len(current_cluster) >= min_touches:
        high_clusters.append(current_cluster)
    
    # Calculate resistance levels as average of clusters
    for cluster in high_clusters:
        if len(cluster) >= min_touches:
            levels['resistances'].append(sum(cluster)/len(cluster))
    
    return levels

def detect_swing_points(df, left_bars=3, right_bars=3):
    """Detect swing highs and lows in price data"""
    swings = {'highs': [], 'lows': []}
    
    for i in range(left_bars, len(df)-right_bars):
        # Check for swing high
        is_high = True
        for j in range(1, left_bars+1):
            if df['high'].iloc[i] < df['high'].iloc[i-j]:
                is_high = False
                break
        if is_high:
            for j in range(1, right_bars+1):
                if df['high'].iloc[i] < df['high'].iloc[i+j]:
                    is_high = False
                    break
        if is_high:
            swings['highs'].append((df.index[i], df['high'].iloc[i]))
            
        # Check for swing low
        is_low = True
        for j in range(1, left_bars+1):
            if df['low'].iloc[i] > df['low'].iloc[i-j]:
                is_low = False
                break
        if is_low:
            for j in range(1, right_bars+1):
                if df['low'].iloc[i] > df['low'].iloc[i+j]:
                    is_low = False
                    break
        if is_low:
            swings['lows'].append((df.index[i], df['low'].iloc[i]))
            
    return swings

def detect_harmonic_patterns(df, tolerance=0.05):
    """
    Detect harmonic price patterns (Gartley, Butterfly, Bat, Crab)
    tolerance: Allowable deviation from exact Fibonacci ratios (e.g., 0.05 = 5%)
    """
    patterns = {
        'gartley': {'bullish': False, 'bearish': False, 'points': None},
        'butterfly': {'bullish': False, 'bearish': False, 'points': None},
        'bat': {'bullish': False, 'bearish': False, 'points': None},
        'crab': {'bullish': False, 'bearish': False, 'points': None}
    }
    
    try:
        # Get recent swing points
        swings = detect_swing_points(df)
        highs = swings['highs']
        lows = swings['lows']
        
        if len(highs) < 2 or len(lows) < 2:
            return patterns
            
        # Get latest 5 swing points for pattern detection
        points = []
        all_swings = sorted(highs + lows, key=lambda x: x[0])  # Sort by time
        points = all_swings[-5:] if len(all_swings) >= 5 else []
        
        if len(points) < 5:
            return patterns
            
        # Extract XABCD points
        X = points[0][1]
        A = points[1][1]
        B = points[2][1]
        C = points[3][1]
        D = points[4][1]
        
        # Calculate retracement ratios
        AB = abs(B - A)
        BC = abs(C - B)
        CD = abs(D - C)
        XA = abs(A - X)
        
        # Gartley Pattern
        gartley_ratios = {
            'XB': 0.618,  # XA to AB retracement
            'BC': 0.382,  # AB to BC retracement
            'CD': 1.272,  # BC to CD extension
            'AD': 0.786   # XA to AD retracement
        }
        
        # Butterfly Pattern
        butterfly_ratios = {
            'XB': 0.786,
            'BC': 0.382,
            'CD': 1.618,
            'AD': 1.27
        }
        
        # Bat Pattern
        bat_ratios = {
            'XB': 0.382,
            'BC': 0.382,
            'CD': 2.618,
            'AD': 0.886
        }
        
        # Crab Pattern
        crab_ratios = {
            'XB': 0.382,
            'BC': 0.618,
            'CD': 3.618,
            'AD': 1.618
        }
        
        def is_within_tolerance(actual, expected, tolerance):
            return abs(actual - expected) <= tolerance
        
        # Check for bullish patterns
        if D < X:  # Potential bullish pattern
            # Gartley
            if (is_within_tolerance(abs(B - X) / XA, gartley_ratios['XB'], tolerance) and
                is_within_tolerance(BC / AB, gartley_ratios['BC'], tolerance) and
                is_within_tolerance(CD / BC, gartley_ratios['CD'], tolerance) and
                is_within_tolerance(abs(D - X) / XA, gartley_ratios['AD'], tolerance)):
                patterns['gartley']['bullish'] = True
                patterns['gartley']['points'] = [X, A, B, C, D]
            
            # Butterfly
            if (is_within_tolerance(abs(B - X) / XA, butterfly_ratios['XB'], tolerance) and
                is_within_tolerance(BC / AB, butterfly_ratios['BC'], tolerance) and
                is_within_tolerance(CD / BC, butterfly_ratios['CD'], tolerance) and
                is_within_tolerance(abs(D - X) / XA, butterfly_ratios['AD'], tolerance)):
                patterns['butterfly']['bullish'] = True
                patterns['butterfly']['points'] = [X, A, B, C, D]
            
            # Bat
            if (is_within_tolerance(abs(B - X) / XA, bat_ratios['XB'], tolerance) and
                is_within_tolerance(BC / AB, bat_ratios['BC'], tolerance) and
                is_within_tolerance(CD / BC, bat_ratios['CD'], tolerance) and
                is_within_tolerance(abs(D - X) / XA, bat_ratios['AD'], tolerance)):
                patterns['bat']['bullish'] = True
                patterns['bat']['points'] = [X, A, B, C, D]
            
            # Crab
            if (is_within_tolerance(abs(B - X) / XA, crab_ratios['XB'], tolerance) and
                is_within_tolerance(BC / AB, crab_ratios['BC'], tolerance) and
                is_within_tolerance(CD / BC, crab_ratios['CD'], tolerance) and
                is_within_tolerance(abs(D - X) / XA, crab_ratios['AD'], tolerance)):
                patterns['crab']['bullish'] = True
                patterns['crab']['points'] = [X, A, B, C, D]
        
        # Check for bearish patterns
        elif D > X:  # Potential bearish pattern
            # Gartley
            if (is_within_tolerance(abs(B - X) / XA, gartley_ratios['XB'], tolerance) and
                is_within_tolerance(BC / AB, gartley_ratios['BC'], tolerance) and
                is_within_tolerance(CD / BC, gartley_ratios['CD'], tolerance) and
                is_within_tolerance(abs(D - X) / XA, gartley_ratios['AD'], tolerance)):
                patterns['gartley']['bearish'] = True
                patterns['gartley']['points'] = [X, A, B, C, D]
            
            # Butterfly
            if (is_within_tolerance(abs(B - X) / XA, butterfly_ratios['XB'], tolerance) and
                is_within_tolerance(BC / AB, butterfly_ratios['BC'], tolerance) and
                is_within_tolerance(CD / BC, butterfly_ratios['CD'], tolerance) and
                is_within_tolerance(abs(D - X) / XA, butterfly_ratios['AD'], tolerance)):
                patterns['butterfly']['bearish'] = True
                patterns['butterfly']['points'] = [X, A, B, C, D]
            
            # Bat
            if (is_within_tolerance(abs(B - X) / XA, bat_ratios['XB'], tolerance) and
                is_within_tolerance(BC / AB, bat_ratios['BC'], tolerance) and
                is_within_tolerance(CD / BC, bat_ratios['CD'], tolerance) and
                is_within_tolerance(abs(D - X) / XA, bat_ratios['AD'], tolerance)):
                patterns['bat']['bearish'] = True
                patterns['bat']['points'] = [X, A, B, C, D]
            
            # Crab
            if (is_within_tolerance(abs(B - X) / XA, crab_ratios['XB'], tolerance) and
                is_within_tolerance(BC / AB, crab_ratios['BC'], tolerance) and
                is_within_tolerance(CD / BC, crab_ratios['CD'], tolerance) and
                is_within_tolerance(abs(D - X) / XA, crab_ratios['AD'], tolerance)):
                patterns['crab']['bearish'] = True
                patterns['crab']['points'] = [X, A, B, C, D]
        
        return patterns
        
    except Exception as e:
        print(f"Error detecting harmonic patterns: {str(e)}")
        return patterns

def detect_breakout(df, lookback=20, volume_confirm=True):
    """
    Detect and validate breakout patterns with price action confirmation
    Returns: dict with breakout details and confirmation levels
    """
    breakout = {
        'detected': False,
        'direction': None,  # 'UP' or 'DOWN'
        'price_level': None,
        'strength': 0,  # 0-100 score
        'volume_confirmed': False,
        'retested': False
    }
    
    try:
        # Need at least lookback + 5 bars for analysis
        if len(df) < lookback + 5:
            return breakout
            
        # Calculate recent highs and lows
        recent_highs = df['high'].rolling(window=3).max()
        recent_lows = df['low'].rolling(window=3).min()
        
        # Get current and previous prices
        current_price = df['close'].iloc[-1]
        prev_price = df['close'].iloc[-2]
        
        # Identify resistance and support levels
        resistance_level = recent_highs.iloc[-lookback:-1].max()
        support_level = recent_lows.iloc[-lookback:-1].min()
        
        # Check for resistance breakout
        if current_price > resistance_level and prev_price <= resistance_level:
            breakout['detected'] = True
            breakout['direction'] = 'UP'
            breakout['price_level'] = resistance_level
            
            # Volume confirmation
            if volume_confirm and 'tick_volume' in df.columns:
                avg_volume = df['tick_volume'].iloc[-lookback:-1].mean()
                current_volume = df['tick_volume'].iloc[-1]
                breakout['volume_confirmed'] = current_volume > avg_volume * 1.5
            
            # Calculate breakout strength
            price_distance = (current_price - resistance_level) / resistance_level * 100
            breakout['strength'] = min(100, int(price_distance * 20))  # Scale up to 100
            
            # Check for retest
            recent_min = df['low'].iloc[-3:].min()
            breakout['retested'] = resistance_level - recent_min < resistance_level * 0.001
            
        # Check for support breakout (breakdown)
        elif current_price < support_level and prev_price >= support_level:
            breakout['detected'] = True
            breakout['direction'] = 'DOWN'
            breakout['price_level'] = support_level
            
            # Volume confirmation
            if volume_confirm and 'tick_volume' in df.columns:
                avg_volume = df['tick_volume'].iloc[-lookback:-1].mean()
                current_volume = df['tick_volume'].iloc[-1]
                breakout['volume_confirmed'] = current_volume > avg_volume * 1.5
            
            # Calculate breakout strength
            price_distance = (support_level - current_price) / support_level * 100
            breakout['strength'] = min(100, int(price_distance * 20))
            
            # Check for retest
            recent_max = df['high'].iloc[-3:].max()
            breakout['retested'] = recent_max - support_level < support_level * 0.001
            
        return breakout
        
    except Exception as e:
        print(f"Error detecting breakout: {str(e)}")
        return breakout

def detect_price_patterns(df, lookback=20):
    """Detect common price action patterns and candlestick formations"""
    patterns = {
        'support': False,
        'resistance': False,
        'dynamic_support': None,
        'dynamic_resistance': None,
        'hammer': False,
        'shooting_star': False,
        'engulfing': False,
        'pinbar': False,
        'doji': False,
        'morning_star': False,
        'evening_star': False,
        'three_white_soldiers': False,
        'three_black_crows': False,
        'higher_high': False,
        'higher_low': False,
        'lower_high': False,
        'lower_low': False,
        'inside_bar': False,
        'outside_bar': False
    }
    
    if len(df) < lookback:
        return patterns
    
    # Dynamic S/R levels
    if USE_DYNAMIC_SR:
        dynamic_levels = detect_dynamic_sr_levels(
            df, 
            DYNAMIC_SR_LOOKBACK, 
            DYNAMIC_SR_MIN_TOUCHES, 
            DYNAMIC_SR_BUFFER_PIPS
        )
        
        current_price = df['close'].iloc[-1]
        buffer = DYNAMIC_SR_BUFFER_PIPS * 0.0001
        
        # Check dynamic supports
        for level in dynamic_levels['supports']:
            if abs(current_price - level) <= buffer:
                patterns['dynamic_support'] = level
                break
                
        # Check dynamic resistances
        for level in dynamic_levels['resistances']:
            if abs(current_price - level) <= buffer:
                patterns['dynamic_resistance'] = level
                break
    
    # Swing point analysis
    if USE_SWING_POINTS:
        swings = detect_swing_points(df, SWING_LEFT_BARS, SWING_RIGHT_BARS)
        if len(swings['highs']) >= 2 and len(swings['lows']) >= 2:
            # Check for higher highs/lower lows
            last_high = swings['highs'][-1][1]
            prev_high = swings['highs'][-2][1]
            last_low = swings['lows'][-1][1]
            prev_low = swings['lows'][-2][1]
            
            patterns['higher_high'] = last_high > prev_high
            patterns['lower_high'] = last_high < prev_high
            patterns['higher_low'] = last_low > prev_low
            patterns['lower_low'] = last_low < prev_low
    
    # Support/Resistance detection
    recent_lows = df['low'].rolling(window=3).min().tail(lookback)
    recent_highs = df['high'].rolling(window=3).max().tail(lookback)
    
    current_low = df['low'].iloc[-1]
    current_high = df['high'].iloc[-1]
    
    # Support - price bouncing off recent lows
    patterns['support'] = any(abs(current_low - low) < 0.0005 for low in recent_lows)
    
    # Resistance - price bouncing off recent highs
    patterns['resistance'] = any(abs(current_high - high) < 0.0005 for high in recent_highs)
    
    # Candlestick patterns
    if len(df) >= 3:
        prev2 = df.iloc[-3]
        prev1 = df.iloc[-2]
        curr = df.iloc[-1]
        
        # Calculate body and wick sizes
        body_size = abs(curr['close'] - curr['open'])
        lower_wick = min(curr['open'], curr['close']) - curr['low']
        upper_wick = curr['high'] - max(curr['open'], curr['close'])
        
        # Doji pattern (very small body)
        avg_body = df['close'].rolling(window=20).apply(lambda x: abs(x - x.shift(1))).mean()
        patterns['doji'] = body_size < (avg_body * 0.1) and (upper_wick + lower_wick) > (3 * body_size)
        
        # Hammer pattern (bullish)
        patterns['hammer'] = (
            lower_wick > 2 * body_size and 
            upper_wick < body_size * 0.5 and
            curr['close'] > curr['open'] and  # Bullish hammer
            curr['close'] > prev1['close']    # Confirming upward movement
        )
        
        # Shooting Star pattern (bearish)
        patterns['shooting_star'] = (
            upper_wick > 2 * body_size and
            lower_wick < body_size * 0.5 and
            curr['close'] < curr['open'] and  # Bearish
            curr['close'] < prev1['close']    # Confirming downward movement
        )
        
        # Engulfing patterns with volume confirmation
        if 'tick_volume' in df.columns:
            vol_increase = curr['tick_volume'] > prev1['tick_volume'] * 1.2  # 20% volume increase
            patterns['engulfing'] = (
                # Bullish engulfing
                (prev1['close'] < prev1['open'] and    # Previous bearish
                 curr['close'] > curr['open'] and      # Current bullish
                 curr['open'] < prev1['close'] and     # Opens below
                 curr['close'] > prev1['open'] and     # Closes above
                 vol_increase) or                      # Higher volume
                # Bearish engulfing
                (prev1['close'] > prev1['open'] and    # Previous bullish
                 curr['close'] < curr['open'] and      # Current bearish
                 curr['open'] > prev1['close'] and     # Opens above
                 curr['close'] < prev1['open'] and     # Closes below
                 vol_increase)                         # Higher volume
            )
        
        # Morning Star pattern (bullish reversal)
        if len(df) >= 4:
            patterns['morning_star'] = (
                prev2['close'] < prev2['open'] and     # First bar bearish
                abs(prev1['close'] - prev1['open']) < avg_body * 0.5 and  # Small middle bar
                curr['close'] > curr['open'] and       # Third bar bullish
                curr['close'] > (prev2['open'] + prev2['close']) / 2      # Closes above midpoint of first bar
            )
        
        # Evening Star pattern (bearish reversal)
        if len(df) >= 4:
            patterns['evening_star'] = (
                prev2['close'] > prev2['open'] and     # First bar bullish
                abs(prev1['close'] - prev1['open']) < avg_body * 0.5 and  # Small middle bar
                curr['close'] < curr['open'] and       # Third bar bearish
                curr['close'] < (prev2['open'] + prev2['close']) / 2      # Closes below midpoint of first bar
            )
        
        # Three White Soldiers (bullish continuation)
        if len(df) >= 4:
            patterns['three_white_soldiers'] = all(
                df.iloc[i]['close'] > df.iloc[i]['open'] and              # All bullish
                df.iloc[i]['close'] > df.iloc[i-1]['close'] and          # Each closes higher
                df.iloc[i]['open'] > df.iloc[i-1]['open']                # Each opens higher
                for i in range(-3, 0)
            )
        
        # Three Black Crows (bearish continuation)
        if len(df) >= 4:
            patterns['three_black_crows'] = all(
                df.iloc[i]['close'] < df.iloc[i]['open'] and              # All bearish
                df.iloc[i]['close'] < df.iloc[i-1]['close'] and          # Each closes lower
                df.iloc[i]['open'] < df.iloc[i-1]['open']                # Each opens lower
                for i in range(-3, 0)
            )
        
        # Inside Bar pattern
        patterns['inside_bar'] = (
            curr['high'] < prev1['high'] and
            curr['low'] > prev1['low']
        )
        
        # Outside Bar pattern
        patterns['outside_bar'] = (
            curr['high'] > prev1['high'] and
            curr['low'] < prev1['low']
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
    
    # More flexible initialization
    start_index = period
    if len(df) <= start_index:
        return pd.Series([np.nan] * len(df), index=df.index)
        
    # Initialize first value
    ama.iloc[start_index] = df['close'].iloc[start_index]
    
    # Calculate AMA values
    for i in range(start_index + 1, len(df)):
        ama.iloc[i] = ama.iloc[i-1] + sc.iloc[i] * (df['close'].iloc[i] - ama.iloc[i-1])
    
    # Fill initial values with NaN
    ama.iloc[:start_index] = np.nan
    
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
    min_gap_percent = MIN_AMA_GAP_PERCENT  # Minimum gap between AMAs from config
    
    for i in range(1, len(recent_df)):
        current = recent_df.iloc[i]
        previous = recent_df.iloc[i-1]
        
        # Calculate the gap between AMA50 and AMA200 as a percentage
        ama_gap_percent = abs(current['ma_medium'] - current['ma_long']) / current['ma_long'] * 100
        sufficient_gap = ama_gap_percent >= min_gap_percent
        
        # Golden Cross (AMA50 > AMA200)
        if current['ma_medium'] > current['ma_long'] and previous['ma_medium'] <= previous['ma_long']:
            print(f"\n*** GOLDEN CROSS DETECTED at {current['time']} ***")
            print(f"AMA50 crossed above AMA200 at price: {current['close']}")
            print(f"Previous bar: AMA50={previous['ma_medium']:.5f}, AMA200={previous['ma_long']:.5f}")
            print(f"Current bar: AMA50={current['ma_medium']:.5f}, AMA200={current['ma_long']:.5f}")
            print(f"AMA Gap: {ama_gap_percent:.2f}% (minimum: {min_gap_percent:.2f}%)")
            crossover_found = True
            
            latest = df.iloc[-1]
            # Check if price is above AMA50 to confirm bullish trend
            price_confirms_trend = latest['close'] > latest['ma_medium']
            
            # Calculate the latest gap
            latest_gap_percent = abs(latest['ma_medium'] - latest['ma_long']) / latest['ma_long'] * 100
            latest_sufficient_gap = latest_gap_percent >= min_gap_percent
            
            if price_confirms_trend and latest_sufficient_gap:
                print("Current price and AMA alignment is BULLISH")
                print(f"Price confirmation: Price ({latest['close']:.5f}) > AMA50 ({latest['ma_medium']:.5f})")
                print(f"AMA Gap: {latest_gap_percent:.2f}% (minimum: {min_gap_percent:.2f}%)")
                
                if not has_buy_position(symbol):
                    # Get symbol-specific lot size
                    risk_df = get_historical_data(symbol, TIMEFRAME, bars_count=50)
                    if risk_df is not None:
                        lot_size, sl_pips = determine_lot(symbol, risk_df, is_buy_signal=True)
                        open_buy_order(symbol, lot_size, stop_loss_pips=sl_pips)
            else:
                if not price_confirms_trend:
                    print(f"⚠️ Price ({latest['close']:.5f}) below AMA50 ({latest['ma_medium']:.5f}) - trend not confirmed")
                if not latest_sufficient_gap:
                    print(f"⚠️ Insufficient gap between AMAs: {latest_gap_percent:.2f}% (minimum: {min_gap_percent:.2f}%)")
                print("Current price conditions do not confirm the bullish crossover")
        
        # Death Cross (AMA50 < AMA200)
        if current['ma_medium'] < current['ma_long'] and previous['ma_medium'] >= previous['ma_long']:
            print(f"\n*** DEATH CROSS DETECTED at {current['time']} ***")
            print(f"AMA50 crossed below AMA200 at price: {current['close']}")
            print(f"Previous bar: AMA50={previous['ma_medium']:.5f}, AMA200={previous['ma_long']:.5f}")
            print(f"Current bar: AMA50={current['ma_medium']:.5f}, AMA200={current['ma_long']:.5f}")
            print(f"AMA Gap: {ama_gap_percent:.2f}% (minimum: {min_gap_percent:.2f}%)")
            crossover_found = True
            
            latest = df.iloc[-1]
            # Check if price is below AMA50 to confirm bearish trend
            price_confirms_trend = latest['close'] < latest['ma_medium']
            
            # Calculate the latest gap
            latest_gap_percent = abs(latest['ma_medium'] - latest['ma_long']) / latest['ma_long'] * 100
            latest_sufficient_gap = latest_gap_percent >= min_gap_percent
            
            if price_confirms_trend and latest_sufficient_gap:
                print("Current price and AMA alignment is BEARISH")
                print(f"Price confirmation: Price ({latest['close']:.5f}) < AMA50 ({latest['ma_medium']:.5f})")
                print(f"AMA Gap: {latest_gap_percent:.2f}% (minimum: {min_gap_percent:.2f}%)")
                
                if not has_sell_position(symbol):
                    # Get symbol-specific lot size
                    risk_df = get_historical_data(symbol, TIMEFRAME, bars_count=50)
                    if risk_df is not None:
                        lot_size, sl_pips = determine_lot(symbol, risk_df, is_buy_signal=False)
                        open_sell_order(symbol, lot_size, stop_loss_pips=sl_pips)
            else:
                if not price_confirms_trend:
                    print(f"⚠️ Price ({latest['close']:.5f}) above AMA50 ({latest['ma_medium']:.5f}) - trend not confirmed")
                if not latest_sufficient_gap:
                    print(f"⚠️ Insufficient gap between AMAs: {latest_gap_percent:.2f}% (minimum: {min_gap_percent:.2f}%)")
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
        
        # Calculate the gap between AMA50 and AMA200 as a percentage
        ama_gap_percent = abs(latest['ma_medium'] - latest['ma_long']) / latest['ma_long'] * 100
        sufficient_gap = ama_gap_percent >= MIN_AMA_GAP_PERCENT
        
        # Bullish setup: AMA50 > AMA200
        if latest['ma_medium'] > latest['ma_long']:
            # Check if there's a sufficient gap between AMAs
            if sufficient_gap:
                buy_score += 2  # Higher weight for primary signal
                print(f"🟢 Bullish AMA setup on {tf} (AMA50 > AMA200)")
                print(f"🟢 AMA Gap: {ama_gap_percent:.2f}% (minimum: {MIN_AMA_GAP_PERCENT:.2f}%)")
                
                if prev['ma_medium'] <= prev['ma_long']:
                    buy_score += 1
                    print(f"🟢 Fresh AMA50 cross above AMA200")
                
                # Check if price is above AMA50 to confirm bullish trend
                if latest['close'] > latest['ma_medium']:
                    buy_score += 0.5
                    print(f"🟢 Price above AMA50 - Additional confirmation")
            else:
                print(f"⚠️ Insufficient gap between AMAs: {ama_gap_percent:.2f}% (minimum: {MIN_AMA_GAP_PERCENT:.2f}%)")
                
        # Bearish setup: AMA50 < AMA200
        elif latest['ma_medium'] < latest['ma_long']:
            # Check if there's a sufficient gap between AMAs
            if sufficient_gap:
                sell_score += 2  # Higher weight for primary signal
                print(f"🔴 Bearish AMA setup on {tf} (AMA50 < AMA200)")
                print(f"🔴 AMA Gap: {ama_gap_percent:.2f}% (minimum: {MIN_AMA_GAP_PERCENT:.2f}%)")
                
                if prev['ma_medium'] >= prev['ma_long']:
                    sell_score += 1
                    print(f"🔴 Fresh AMA50 cross below AMA200")
                
                # Check if price is below AMA50 to confirm bearish trend
                if latest['close'] < latest['ma_medium']:
                    sell_score += 0.5
                    print(f"🔴 Price below AMA50 - Additional confirmation")
            else:
                print(f"⚠️ Insufficient gap between AMAs: {ama_gap_percent:.2f}% (minimum: {MIN_AMA_GAP_PERCENT:.2f}%)")
                
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
    """Analyze price action patterns including harmonic patterns and breakouts"""
    buy_score = 0
    sell_score = 0
    
    if USE_PRICE_ACTION and MTF_INDICATORS.get("PRICE_ACTION", True):
        # Detect regular price patterns
        patterns = detect_price_patterns(df)
        
        # Detect harmonic patterns
        harmonic_patterns = detect_harmonic_patterns(df)
        
        # Detect breakouts
        breakout = detect_breakout(df)
        if breakout['detected']:
            if breakout['direction'] == 'UP':
                buy_score += 2.0  # Strong weight for confirmed breakouts
                print(f"🚀 Bullish breakout detected on {tf}")
                print(f"Breakout level: {breakout['price_level']:.5f}")
                print(f"Strength: {breakout['strength']}%")
                if breakout['volume_confirmed']:
                    buy_score += 0.5
                    print("Volume confirms breakout")
                if breakout['retested']:
                    buy_score += 0.5
                    print("Breakout level retested - bullish confirmation")
            else:  # 'DOWN'
                sell_score += 2.0
                print(f"💥 Bearish breakdown detected on {tf}")
                print(f"Breakdown level: {breakout['price_level']:.5f}")
                print(f"Strength: {breakout['strength']}%")
                if breakout['volume_confirmed']:
                    sell_score += 0.5
                    print("Volume confirms breakdown")
                if breakout['retested']:
                    sell_score += 0.5
                    print("Breakdown level retested - bearish confirmation")
        
        # Check for bullish harmonic patterns
        for pattern_name, pattern_data in harmonic_patterns.items():
            if pattern_data['bullish']:
                buy_score += 1.5  # Higher weight for harmonic patterns
                print(f"🟢 Bullish {pattern_name.capitalize()} pattern detected on {tf}")
            elif pattern_data['bearish']:
                sell_score += 1.5  # Higher weight for harmonic patterns
                print(f"🔴 Bearish {pattern_name.capitalize()} pattern detected on {tf}")
        
        # Dynamic S/R scoring
        if USE_DYNAMIC_SR:
            if patterns.get('dynamic_support') is not None:
                buy_score += 1.0
                print(f"🟢 Price at dynamic support: {patterns['dynamic_support']:.5f} on {tf}")
            if patterns.get('dynamic_resistance') is not None:
                sell_score += 1.0
                print(f"🔴 Price at dynamic resistance: {patterns['dynamic_resistance']:.5f} on {tf}")
        
        # Swing point analysis scoring
        if USE_SWING_POINTS:
            if patterns.get('higher_high', False) and patterns.get('higher_low', False):
                buy_score += 1.5  # Strong uptrend confirmation
                print(f"🟢 Uptrend confirmed (higher high + higher low) on {tf}")
            elif patterns.get('lower_high', False) and patterns.get('lower_low', False):
                sell_score += 1.5  # Strong downtrend confirmation
                print(f"🔴 Downtrend confirmed (lower high + lower low) on {tf}")
            elif patterns.get('higher_high', False):
                buy_score += 0.5  # Potential uptrend
                print(f"🟢 Higher high detected on {tf}")
            elif patterns.get('higher_low', False):
                buy_score += 0.5  # Potential uptrend continuation
                print(f"🟢 Higher low detected on {tf}")
            elif patterns.get('lower_high', False):
                sell_score += 0.5  # Potential downtrend
                print(f"🔴 Lower high detected on {tf}")
            elif patterns.get('lower_low', False):
                sell_score += 0.5  # Potential downtrend continuation
                print(f"🔴 Lower low detected on {tf}")
        
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

def calculate_pivot_points(df, pivot_type="STANDARD"):
    """Calculate pivot points using daily data
    Supported types: STANDARD, FIBONACCI, WOODIE, CAMARILLA, DEMARK"""
    if len(df) < 1:
        return None
        
    # Get high, low, close for previous day
    high = df['high'].iloc[-1]
    low = df['low'].iloc[-1]
    close = df['close'].iloc[-1]
    open_price = df['open'].iloc[-1] if 'open' in df else close
    
    # Common calculations
    pivot = (high + low + close) / 3
    pp_range = high - low
    
    if pivot_type == "STANDARD":
        # Standard pivot points
        return {
            'P': pivot,
            'R1': (2 * pivot) - low,
            'R2': pivot + pp_range,
            'R3': high + 2 * (pivot - low),
            'S1': (2 * pivot) - high,
            'S2': pivot - pp_range,
            'S3': low - 2 * (high - pivot)
        }
    elif pivot_type == "FIBONACCI":
        # Fibonacci pivot points
        return {
            'P': pivot,
            'R1': pivot + pp_range * 0.382,
            'R2': pivot + pp_range * 0.618,
            'R3': pivot + pp_range * 1.000,
            'S1': pivot - pp_range * 0.382,
            'S2': pivot - pp_range * 0.618,
            'S3': pivot - pp_range * 1.000
        }
    elif pivot_type == "WOODIE":
        # Woodie pivot points
        pivot = (high + low + 2 * close) / 4
        return {
            'P': pivot,
            'R1': (2 * pivot) - low,
            'R2': pivot + (high - low),
            'R3': high + 2 * (pivot - low),
            'S1': (2 * pivot) - high,
            'S2': pivot - (high - low),
            'S3': low - 2 * (high - pivot)
        }
    elif pivot_type == "CAMARILLA":
        # Camarilla pivot points
        return {
            'P': pivot,
            'R1': close + pp_range * 1.1 / 12,
            'R2': close + pp_range * 1.1 / 6,
            'R3': close + pp_range * 1.1 / 4,
            'R4': close + pp_range * 1.1 / 2,
            'S1': close - pp_range * 1.1 / 12,
            'S2': close - pp_range * 1.1 / 6,
            'S3': close - pp_range * 1.1 / 4,
            'S4': close - pp_range * 1.1 / 2
        }
    elif pivot_type == "DEMARK":
        # DeMark pivot points
        x = high + 2 * low + close if close < open_price else 2 * high + low + close
        x = x / 4 if close == open_price else x / 4
        return {
            'P': x,
            'R1': x * 2 - low,
            'S1': x * 2 - high
        }
    else:
        return None

def check_pivot_levels(current_price, pivot_levels, buffer_pips, symbol=SYMBOL):
    """Check if price is near any pivot levels with enhanced detection"""
    if pivot_levels is None:
        return None
        
    buffer = buffer_pips * 0.0001  # Convert pips to price level for 4-digit pairs
    closest_level = None
    min_distance = float('inf')
    
    for level_name, level_price in pivot_levels.items():
        distance = abs(current_price - level_price)
        
        # Check if within buffer zone
        if distance <= buffer:
            # Log pivot level interaction
            msg = f"Price {current_price:.5f} near {level_name} at {level_price:.5f} (distance: {distance:.5f})"
            print(msg)
            write_diagnostic_log(symbol, msg)
            
            # Track closest level within buffer
            if distance < min_distance:
                min_distance = distance
                closest_level = {
                    'level': level_name,
                    'price': level_price,
                    'distance': current_price - level_price,
                    'percent_distance': (distance / level_price) * 100,
                    'is_support': 'S' in level_name,
                    'is_resistance': 'R' in level_name
                }
    
    # Additional check for price between pivot levels
    if closest_level is None and len(pivot_levels) >= 2:
        sorted_levels = sorted([(k, v) for k, v in pivot_levels.items()], key=lambda x: x[1])
        for i in range(len(sorted_levels)-1):
            lower = sorted_levels[i][1]
            upper = sorted_levels[i+1][1]
            if lower < current_price < upper:
                msg = f"Price {current_price:.5f} between {sorted_levels[i][0]} ({lower:.5f}) and {sorted_levels[i+1][0]} ({upper:.5f})"
                print(msg)
                write_diagnostic_log(symbol, msg)
                return {
                    'between': True,
                    'lower_level': sorted_levels[i][0],
                    'lower_price': lower,
                    'upper_level': sorted_levels[i+1][0],
                    'upper_price': upper,
                    'distance_to_lower': current_price - lower,
                    'distance_to_upper': upper - current_price
                }
    
    return closest_level

def calculate_macd(df):
    """Calculate MACD indicator and histogram"""
    from config import MACD_FAST, MACD_SLOW, MACD_SIGNAL
    
    # Calculate exponential moving averages
    ema_fast = df['close'].ewm(span=MACD_FAST, adjust=False).mean()
    ema_slow = df['close'].ewm(span=MACD_SLOW, adjust=False).mean()
    
    # Calculate MACD line
    macd_line = ema_fast - ema_slow
    
    # Calculate Signal line
    signal_line = macd_line.ewm(span=MACD_SIGNAL, adjust=False).mean()
    
    # Calculate Histogram
    histogram = macd_line - signal_line
    
    return macd_line, signal_line, histogram

def analyze_macd_momentum(df, latest, prev, tf, symbol=SYMBOL):
    """Analyze MACD histogram for momentum confirmation"""
    from config import MACD_CONSECUTIVE_BARS, MACD_GROWING_FACTOR, MACD_ZERO_CROSS_CONFIRM, USE_MACD_FILTER
    
    buy_score = 0
    sell_score = 0
    
    if not USE_MACD_FILTER:
        return buy_score, sell_score
    
    # Calculate MACD components
    macd_line, signal_line, histogram = calculate_macd(df)
    
    if len(histogram) < MACD_CONSECUTIVE_BARS + 1:
        return buy_score, sell_score
    
    # Get last few histogram values
    recent_hist = histogram.tail(MACD_CONSECUTIVE_BARS + 1)
    
    # Log MACD diagnostics
    write_macd_diagnostics(symbol, tf, macd_line, signal_line, histogram, recent_hist)
    
    # Check for consecutive growing positive histogram bars (bullish momentum)
    if all(recent_hist.iloc[i] > 0 for i in range(-MACD_CONSECUTIVE_BARS, 0)):
        growing = True
        for i in range(-MACD_CONSECUTIVE_BARS, 0):
            if recent_hist.iloc[i] < recent_hist.iloc[i-1] * MACD_GROWING_FACTOR:
                growing = False
                break
        if growing:
            buy_score += 1
            print(f"🟢 Bullish momentum: {MACD_CONSECUTIVE_BARS} consecutive growing histogram bars on {tf}")
            
            # Additional point if just crossed zero line
            if MACD_ZERO_CROSS_CONFIRM and histogram.iloc[-MACD_CONSECUTIVE_BARS-1] < 0:
                buy_score += 0.5
                print(f"🟢 Bullish zero-line crossover confirmed on {tf}")
    
    # Check for consecutive growing negative histogram bars (bearish momentum)
    if all(recent_hist.iloc[i] < 0 for i in range(-MACD_CONSECUTIVE_BARS, 0)):
        growing = True
        for i in range(-MACD_CONSECUTIVE_BARS, 0):
            if abs(recent_hist.iloc[i]) < abs(recent_hist.iloc[i-1]) * MACD_GROWING_FACTOR:
                growing = False
                break
        if growing:
            sell_score += 1
            print(f"🔴 Bearish momentum: {MACD_CONSECUTIVE_BARS} consecutive growing histogram bars on {tf}")
            
            # Additional point if just crossed zero line
            if MACD_ZERO_CROSS_CONFIRM and histogram.iloc[-MACD_CONSECUTIVE_BARS-1] > 0:
                sell_score += 0.5
                print(f"🔴 Bearish zero-line crossover confirmed on {tf}")
    
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
    macd_buy, macd_sell = analyze_macd_momentum(df, latest, prev, tf, symbol)
    
    # Combine scores
    buy_score = ma_buy + rsi_buy + pattern_buy + macd_buy
    sell_score = ma_sell + rsi_sell + pattern_sell + macd_sell
    
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

def validate_signal_conditions(df, latest, signal_type):
    """Validate signal conditions just before execution"""
    if len(df) < 2:
        return False, "Not enough data for validation"
        
    # Verify AMA alignment
    price = latest['close']
    ama50 = latest['ma_medium']
    ama200 = latest['ma_long']
    
    # Calculate gap percentage
    ama_gap_percent = abs(ama50 - ama200) / ama200 * 100
    sufficient_gap = ama_gap_percent >= MIN_AMA_GAP_PERCENT
    
    if not sufficient_gap:
        return False, f"Insufficient AMA gap: {ama_gap_percent:.2f}% < {MIN_AMA_GAP_PERCENT}%"
    
    if signal_type == 'BUY':
        # For BUY: AMA50 > AMA200 AND Price > AMA50
        if not (ama50 > ama200 and price > ama50):
            return False, "AMA conditions not met for BUY signal"
    else:  # SELL
        # For SELL: AMA50 < AMA200 AND Price < AMA50
        if not (ama50 < ama200 and price < ama50):
            return False, "AMA conditions not met for SELL signal"
            
    return True, "Signal conditions valid"

def analyze_multiple_timeframes_weighted(symbol, timeframes=ANALYSIS_TIMEFRAMES, weights=MTF_WEIGHTS):
    """Analyze timeframe for AMA50/AMA200 crossover signals with enhanced validation"""
    signals = initialize_signals()
    
    print(f"\n=== {TIMEFRAME} AMA Analysis for {symbol} ===")
    
    # Get data for current timeframe
    df = prepare_timeframe_data(symbol, TIMEFRAME)
    if df is None or len(df) < 2:
        print("Not enough M5 data available")
        return signals
        
    latest = df.iloc[-1]
    prev = df.iloc[-2]
    
    # Debug print current values
    print(f"Current Price: {latest['close']:.5f}")
    print(f"AMA50: {latest['ma_medium']:.5f}")
    print(f"AMA200: {latest['ma_long']:.5f}")
    
    # Calculate the gap between AMA50 and AMA200 as a percentage
    ama_gap_percent = abs(latest['ma_medium'] - latest['ma_long']) / latest['ma_long'] * 100
    sufficient_gap = ama_gap_percent >= MIN_AMA_GAP_PERCENT
    
    # Check AMA crossover
    if latest['ma_medium'] > latest['ma_long']:
        # For BUY signals, price MUST be above AMA50
        if latest['close'] > latest['ma_medium']:
            if sufficient_gap:
                # Bullish setup
                signals['weighted_buy_score'] = 100
                signals['overall_signal'] = 'BUY'
                signals['signal_strength'] = 100
                print("🟢 Bullish Setup: AMA50 > AMA200")
                print(f"🟢 AMA Gap: {ama_gap_percent:.2f}% (minimum: {MIN_AMA_GAP_PERCENT:.2f}%)")
                print(f"🟢 Price confirmation: Price ({latest['close']:.5f}) > AMA50 ({latest['ma_medium']:.5f})")
                
                if prev['ma_medium'] <= prev['ma_long']:
                    print("🟢 Fresh Golden Cross Detected!")
            else:
                signals['overall_signal'] = 'NEUTRAL'
                signals['signal_strength'] = 0
                print(f"⚠️ Insufficient gap between AMAs: {ama_gap_percent:.2f}% (minimum: {MIN_AMA_GAP_PERCENT:.2f}%)")
        else:
            signals['overall_signal'] = 'NEUTRAL'
            signals['signal_strength'] = 0
            print(f"⚠️ Price ({latest['close']:.5f}) below AMA50 ({latest['ma_medium']:.5f}) - trend not confirmed")
            
    elif latest['ma_medium'] < latest['ma_long']:
        # For SELL signals, price MUST be below AMA50
        if latest['close'] < latest['ma_medium']:
            if sufficient_gap:
                # Bearish setup
                signals['weighted_sell_score'] = 100
                signals['overall_signal'] = 'SELL'
                signals['signal_strength'] = 100
                print("🔴 Bearish Setup: AMA50 < AMA200")
                print(f"🔴 AMA Gap: {ama_gap_percent:.2f}% (minimum: {MIN_AMA_GAP_PERCENT:.2f}%)")
                print(f"🔴 Price confirmation: Price ({latest['close']:.5f}) < AMA50 ({latest['ma_medium']:.5f})")
                
                if prev['ma_medium'] >= prev['ma_long']:
                    print("🔴 Fresh Death Cross Detected!")
            else:
                signals['overall_signal'] = 'NEUTRAL'
                signals['signal_strength'] = 0
                print(f"⚠️ Insufficient gap between AMAs: {ama_gap_percent:.2f}% (minimum: {MIN_AMA_GAP_PERCENT:.2f}%)")
        else:
            signals['overall_signal'] = 'NEUTRAL'
            signals['signal_strength'] = 0
            print(f"⚠️ Price ({latest['close']:.5f}) above AMA50 ({latest['ma_medium']:.5f}) - trend not confirmed")
            
    else:
        signals['overall_signal'] = 'NEUTRAL'
        signals['signal_strength'] = 0
        print("AMA lines equal - No clear trend")
        
    # Store signals for current timeframe
    signals['timeframe_signals'][TIMEFRAME] = {
        'signal': signals['overall_signal'],
        'ma_medium': latest['ma_medium'],
        'ma_long': latest['ma_long'],
        'close': latest['close']
    }
    
    print(f"\nFinal Signal: {signals['overall_signal']}")
    return signals

def get_session_parameters(symbol, base_risk_percent=1.0):
    """Get session-specific trading parameters"""
    from config import session_mgr, DEFAULT_RISK_PERCENT
    params = session_mgr.get_session_parameters(symbol, base_risk_percent)
    
    if not params["should_trade"]:
        print(f"Trading not recommended for {symbol} in current session")
        return None, None, None
        
    # Get session status information
    status = params["status"]
    print(f"\nSession Status for {symbol}:")
    print(f"Priority: {status['priority']}")
    print(f"Active Sessions: {', '.join(status['active_sessions'])}")
    if status["is_overlap"]:
        print("🔥 High-liquidity overlap period")
        
    # Use effective risk from session parameters
    effective_risk = params["effective_risk_percent"]
    timeframe = params["timeframe"]
    
    print(f"Risk Multiplier: {params['risk_multiplier']}")
    print(f"Base Risk: {params['base_risk_percent']}%")
    print(f"Effective Risk: {effective_risk}%")
    print(f"Using Timeframe: {timeframe}")
    
    return status["priority"], effective_risk, timeframe

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
TRADE_COOLDOWN_MINUTES = 1  # Wait at least 1 minutes between trades


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
    from config import session_mgr
    
    # Initialize diagnostic logging
    write_diagnostic_log(symbol, f"Starting trade analysis for {symbol}")
    
    # Check if we should trade this pair in current session
    if not session_mgr.should_trade_pair(symbol):
        msg = f"Skipping {symbol} - Not active in current session"
        print(msg)
        write_diagnostic_log(symbol, msg)
        return False
        
    # Check for upcoming high impact news
    if has_upcoming_high_impact_news(symbol):
        msg = f"Skipping trade due to upcoming high impact news"
        print(f"\n=== {symbol} NEWS CHECK ===")
        print(msg)
        write_diagnostic_log(symbol, msg)
        return False
        
    # Get session parameters with risk percent
    session_params = session_mgr.get_session_parameters(symbol, risk_percent)
    
    if session_params is None:
        msg = "Failed to get session parameters"
        print(msg)
        write_diagnostic_log(symbol, msg)
        return False

    # Check spread against session requirements
    current_spread = mt5.symbol_info(symbol).spread * mt5.symbol_info(symbol).point
    if current_spread > session_params["min_spread"]:
        msg = f"Spread too high for current session: {current_spread} > {session_params['min_spread']}"
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

def calculate_trade_parameters(symbol, is_buy, df, effective_risk=1.0):
    """Calculate trade parameters like lot size and pip values"""
    lot_size, sl_pips = determine_lot(
        symbol,
        df,
        is_buy_signal=is_buy,
        risk_percent=effective_risk
    )
    
    tp_pips = SYMBOL_SETTINGS.get(symbol, {}).get("TP_PIPS", DEFAULT_TP_PIPS)
    if tp_pips is None:
        tp_multiplier = SYMBOL_SETTINGS.get(symbol, {}).get("TP_MULTIPLIER", 2.0)
        tp_pips = int(sl_pips * tp_multiplier)
    
    return lot_size, sl_pips, tp_pips

def execute_trade(symbol, is_buy, lot_size, sl_pips, tp_pips):
    """Execute the trade with given parameters and log trade details"""
    try:
        from trade_logger import log_trade_entry
        entry_price = mt5.symbol_info_tick(symbol).ask if is_buy else mt5.symbol_info_tick(symbol).bid
        
        if is_buy:
            print(f"Attempting to open BUY position for {symbol}:")
            print(f"Lot Size: {lot_size}, SL: {sl_pips} pips, TP: {tp_pips} pips")
            result = open_buy_order(symbol, lot_size, stop_loss_pips=sl_pips, take_profit_pips=tp_pips)
        else:
            print(f"Attempting to open SELL position for {symbol}:")
            print(f"Lot Size: {lot_size}, SL: {sl_pips} pips, TP: {tp_pips} pips")
            result = open_sell_order(symbol, lot_size, stop_loss_pips=sl_pips, take_profit_pips=tp_pips)
            
        if result:
            log_trade_entry(
                symbol=symbol,
                direction='BUY' if is_buy else 'SELL',
                entry_price=entry_price,
                size=lot_size,
                sl_pips=sl_pips,
                tp_pips=tp_pips,
                strategy='AMA_CROSS'
            )
    except Exception as e:
        error_msg = f"Error executing order: {str(e)}"
        print(error_msg)
        write_diagnostic_log(symbol, error_msg)

def prepare_market_data(symbol):
    """Prepare market data and calculate indicators"""
    # Dynamically adjust bars_count based on timeframe
    # For lower timeframes like M1, we need more bars; for higher timeframes like H4, we need fewer
    from config import TIMEFRAME_MULTIPLIERS
    
    # Base number of bars needed for M5 timeframe
    base_bars = 400
    
    # Get multiplier for current timeframe (default to 1 if not found)
    tf_multiplier = TIMEFRAME_MULTIPLIERS.get(TIMEFRAME, 1)
    
    # Calculate adjusted bars count - for lower timeframes we need more bars
    # For M1, we'll request 5x more bars than M5; for H4, we'll request 1/12 of M5 bars
    if tf_multiplier < 5:  # For timeframes lower than M5 (like M1)
        adjusted_bars = int(base_bars * (5 / tf_multiplier))
    else:  # For timeframes higher than M5 (like H1, H4)
        adjusted_bars = int(base_bars * (5 / tf_multiplier)) + 50  # Add buffer
    
    # Ensure we have at least 400 bars
    bars_count = max(400, adjusted_bars)
    
    print(f"Requesting {bars_count} bars for {symbol} on {TIMEFRAME} timeframe")
    df = get_historical_data(symbol, TIMEFRAME, bars_count=bars_count)
    
    if df is None or len(df) == 0:
        print(f"No historical data available for {symbol}")
        return None
        
    if len(df) < MA_LONG + 5:
        print(f"Not enough historical data for {symbol} (need at least {MA_LONG + 5} bars)")
        return None
        
    # Calculate indicators
    df['ma_medium'] = calculate_ama(df, MA_MEDIUM)  # AMA50
    df['ma_long'] = calculate_ama(df, MA_LONG)      # AMA200
    
    # Add VWMA for additional confirmation
    df['vwma_medium'] = calculate_vwma(df, MA_MEDIUM)  # VWMA50
    df['vwma_long'] = calculate_vwma(df, MA_LONG)      # VWMA200
    
    if USE_RSI_FILTER:
        df['rsi'] = calculate_rsi(df, RSI_PERIOD)
    df = df.dropna()
    
    if len(df) < 10:
        print(f"Not enough data points after calculating indicators for {symbol}")
        return None
        
    return df

def validate_execution_conditions(symbol, analysis_price, signal_type, timeframe):
    """
    Validate conditions just before trade execution
    Returns: (bool, str) - (is_valid, message)
    """
    # Get fresh tick data
    tick = mt5.symbol_info_tick(symbol)
    if not tick:
        return False, "Failed to get current price"
        
    current_price = tick.ask if signal_type == 'BUY' else tick.bid
    
    # Calculate price deviation in pips
    pip_value = 0.0001 if not symbol.endswith('JPY') else 0.01
    price_deviation_pips = abs(current_price - analysis_price) / pip_value
    
    if price_deviation_pips > MAX_PRICE_DEVIATION_PIPS:
        return False, f"Price deviation too large: {price_deviation_pips:.1f} pips"
    
    # Get fresh data for signal validation
    df = prepare_market_data(symbol)
    if df is None or len(df) < 2:
        return False, "Failed to get fresh market data"
    
    latest = df.iloc[-1]
    is_valid, message = validate_signal_conditions(df, latest, signal_type)
    
    return is_valid, message

def check_signal_and_trade(symbol=SYMBOL, risk_percent=1.0):
    """Check for signals and execute trades based on AMA crossovers with enhanced validation"""
    from main import pm
    from mt5_helper import check_market_conditions
    
    # Initial validations
    if not validate_trading_conditions(symbol, risk_percent):
        return
        
    # Get session parameters with updated risk handling
    current_session, effective_risk, timeframe = get_session_parameters(symbol, risk_percent)
    if current_session is None:
        return
        
    # Update global timeframe if needed
    global TIMEFRAME
    TIMEFRAME = timeframe
        
    print(f"\n=== Processing {symbol} on {TIMEFRAME} timeframe ===")
    
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
    
    # Calculate and display ADX and MACD values
    # Initialize filter flags
    adx_value = None
    adx_filter_passed = False
    macd_filter_passed = True  # Default to True since it's optional
    roc_filter_passed = True   # Default to True
    bb_filter_passed = True    # Default to True
    atr_filter_passed = False
    obv_confirms_trend = False

    if USE_ADX_FILTER:
        adx, pos_di, neg_di = calculate_adx(df, ADX_PERIOD)
        if not adx.isna().iloc[-1]:
            adx_value = adx.iloc[-1]
            adx_filter_passed = adx_value >= ADX_THRESHOLD
            adx_value = adx.iloc[-1]
            pos_di_value = pos_di.iloc[-1]
            neg_di_value = neg_di.iloc[-1]
            
            # Calculate ROC
            roc = calculate_roc(df, period=14)
            roc_value = roc.iloc[-1]
            
            print(f"\nMomentum Analysis:")
            print(f"ROC(14): {roc_value:.2f}%")
            if roc_value > 0:
                print(f"🟢 Bullish momentum (Price rising at {roc_value:.2f}% rate)")
            else:
                print(f"🔴 Bearish momentum (Price falling at {abs(roc_value):.2f}% rate)")

            print(f"\nADX/DMI Analysis:")
            print(f"ADX: {adx_value:.1f} (Threshold: {ADX_THRESHOLD})")
            print(f"+DI{ADX_PERIOD}: {pos_di_value:.1f}")
            print(f"-DI{ADX_PERIOD}: {neg_di_value:.1f}")
            
            # DMI Trend Direction
            if pos_di_value > neg_di_value:
                print(f"🟢 Bullish trend (+DI > -DI by {(pos_di_value - neg_di_value):.1f})")
            else:
                print(f"🔴 Bearish trend (-DI > +DI by {(neg_di_value - pos_di_value):.1f})")
            
            # Trend Strength
            if adx_value >= ADX_EXTREME:
                print(f"🔥 Extremely strong trend (ADX: {adx_value:.1f})")
            elif adx_value >= ADX_THRESHOLD:
                print(f"💪 Strong trend (ADX: {adx_value:.1f})")
            else:
                print(f"⚠️ Weak trend (ADX: {adx_value:.1f}) - may be ranging market")

    if USE_MACD_FILTER:
        macd_line, signal_line, histogram = calculate_macd(df)
        print(f"\nMACD Analysis:")
        print(f"MACD Line: {macd_line.iloc[-1]:.5f}")
        print(f"Signal Line: {signal_line.iloc[-1]:.5f}")
        print(f"Histogram: {histogram.iloc[-1]:.5f}")
        if histogram.iloc[-1] > 0:
            print(f"🟢 Bullish momentum (Histogram: {histogram.iloc[-1]:.5f})")
        else:
            print(f"🔴 Bearish momentum (Histogram: {histogram.iloc[-1]:.5f})")
    
    # Log AMA values
    write_ama_diagnostics(symbol, "M5", latest, prev)
    
    # Determine signal based on AMA crossover
    signal = 'NEUTRAL'
    
    # Analyze volume patterns early
    volume_analysis = analyze_volume_patterns(df)
    vpa_confirms = False
    if volume_analysis:
        print("\nVolume Price Analysis (VPA):")
        print(f"Volume trend: {'Increasing' if volume_analysis['volume_increasing'] else 'Decreasing'}")
        print(f"Volume vs Average: {'Above' if volume_analysis['volume_above_avg'] else 'Below'}")
        print(f"Volume ratio: {volume_analysis['volume_ratio']:.2f}x average")
        print(f"Price spread: {'Wide' if volume_analysis['wide_spread'] else 'Normal'}")
        
        # VPA validation
        vpa_confirms = (
            volume_analysis['volume_increasing'] and 
            volume_analysis['volume_above_avg'] and
            volume_analysis['volume_ratio'] > 1.2
        )
        if vpa_confirms:
            print("✅ Volume analysis confirms the signal")
        else:
            print("⚠️ Volume analysis does not confirm the signal")
    
    # Calculate the gap between AMA50 and AMA200 as a percentage
    ama_gap_percent = abs(latest['ma_medium'] - latest['ma_long']) / latest['ma_long'] * 100
    min_gap_percent = MIN_AMA_GAP_PERCENT  # Minimum gap between AMAs from config
    
    # Check if there's a sufficient gap between AMAs
    sufficient_gap = ama_gap_percent >= min_gap_percent
    
    if latest['ma_medium'] > latest['ma_long']:
        # Check if price is above AMA50 to confirm bullish trend
        price_confirms_trend = latest['close'] > latest['ma_medium']
        
        # For BUY signals:
        # AMA50 > AMA200 AND Price > AMA50, then check 2/3 supporting filters
        if latest['ma_medium'] > latest['ma_long'] and latest['close'] > latest['ma_medium']:
            # Check supporting filters (need 2/3 to confirm)
            filter_count = 0
            if macd_filter_passed and roc_filter_passed:
                filter_count += 1
                print("✅ Momentum Filter Confirmed (ROC + MACD)")
            if adx_filter_passed:
                filter_count += 1
                print("✅ Trend Strength Filter Confirmed (ADX > 20)")
            if volume_analysis and bb_filter_passed and volume_analysis['volume_ratio'] > 1.2:
                filter_count += 1
                print("✅ Volume/Volatility Filter Confirmed (Volume > 1.2x + BB expansion)")
                
            if filter_count >= 2:
                signal = 'BUY'
                print("🟢 Bullish Setup: AMA50 > AMA200")
                print(f"🟢 Price confirmation: Price ({latest['close']:.5f}) > AMA50 ({latest['ma_medium']:.5f})")
                print(f"🟢 {filter_count}/3 Supporting Filters Confirmed")
                
                if prev['ma_medium'] <= prev['ma_long']:
                    print("🟢 Fresh Golden Cross Detected!")
            else:
                print(f"⚠️ Only {filter_count}/3 Supporting Filters Confirmed - Signal Not Valid")
        else:
            print(f"⚠️ BUY conditions not met")
            
    elif latest['ma_medium'] < latest['ma_long']:
        # Check if price is below AMA50 to confirm bearish trend
        price_confirms_trend = latest['close'] < latest['ma_medium']
        
        # For SELL signals:
        # AMA50 < AMA200 AND Price < AMA50, then check 2/3 supporting filters
        if latest['ma_medium'] < latest['ma_long'] and latest['close'] < latest['ma_medium']:
            # Check supporting filters (need 2/3 to confirm)
            filter_count = 0
            if macd_filter_passed and roc_filter_passed:
                filter_count += 1
                print("✅ Momentum Filter Confirmed (ROC + MACD)")
            if adx_filter_passed:
                filter_count += 1
                print("✅ Trend Strength Filter Confirmed (ADX > 20)")
            if volume_analysis and bb_filter_passed and volume_analysis['volume_ratio'] > 1.2:
                filter_count += 1
                print("✅ Volume/Volatility Filter Confirmed (Volume > 1.2x + BB expansion)")
                
            if filter_count >= 2:
                signal = 'SELL'
                print("🔴 Bearish Setup: AMA50 < AMA200")
                print(f"🔴 Price confirmation: Price ({latest['close']:.5f}) < AMA50 ({latest['ma_medium']:.5f})")
                print(f"🔴 {filter_count}/3 Supporting Filters Confirmed")
                
                if prev['ma_medium'] >= prev['ma_long']:
                    print("🔴 Fresh Death Cross Detected!")
            else:
                print(f"⚠️ Only {filter_count}/3 Supporting Filters Confirmed - Signal Not Valid")
        else:
            print(f"⚠️ SELL conditions not met")
    
    # Check VWMA alignment with AMA
    vwma_confirms = False
    if 'vwma_medium' in df.columns and 'vwma_long' in df.columns:
        vwma_aligned = (
            (signal == 'BUY' and df['vwma_medium'].iloc[-1] > df['vwma_long'].iloc[-1]) or
            (signal == 'SELL' and df['vwma_medium'].iloc[-1] < df['vwma_long'].iloc[-1])
        )
        if vwma_aligned:
            print("✅ VWMA confirms trend direction")
            vwma_confirms = True
        else:
            print("⚠️ VWMA does not confirm trend direction")
            
    write_diagnostic_log(symbol, f"M5 AMA Signal: {signal}")
    write_diagnostic_log(symbol, f"AMA Gap: {ama_gap_percent:.2f}%, Price confirms trend: {price_confirms_trend if 'price_confirms_trend' in locals() else 'N/A'}")
    write_diagnostic_log(symbol, f"VWMA confirmation: {vwma_confirms}")
    
    # Check trading conditions
    current_time = datetime.now()
    if not check_cooldown(symbol, current_time):
        return
        
    # Calculate MACD
        macd_line, signal_line, histogram = calculate_macd(df)
        recent_hist = histogram.tail(MACD_CONSECUTIVE_BARS + 1)
        write_macd_diagnostics(symbol, TIMEFRAME, macd_line, signal_line, histogram, recent_hist)
        
    # Calculate OBV
    obv = calculate_obv(df)
    obv_sma = obv.rolling(window=20).mean()  # 20-period SMA of OBV
    
    print(f"\nOBV Analysis:")
    print(f"Current OBV: {obv.iloc[-1]:.0f}")
    print(f"OBV SMA(20): {obv_sma.iloc[-1]:.0f}")
    
    # Check if OBV confirms price movement
    obv_confirms_trend = False
    if signal == 'BUY':
        if obv.iloc[-1] > obv_sma.iloc[-1]:
            print("🟢 OBV above its SMA - Volume confirms uptrend")
            obv_confirms_trend = True
        else:
            print("⚠️ OBV below its SMA - Volume not confirming uptrend")
    elif signal == 'SELL':
        if obv.iloc[-1] < obv_sma.iloc[-1]:
            print("🔴 OBV below its SMA - Volume confirms downtrend")
            obv_confirms_trend = True
        else:
            print("⚠️ OBV above its SMA - Volume not confirming downtrend")
    
    write_diagnostic_log(symbol, f"OBV trend confirmation: {obv_confirms_trend}")
    
    # Print MACD values
    print(f"\nMACD Analysis:")
    print(f"MACD Line: {macd_line.iloc[-1]:.5f}")
    print(f"Signal Line: {signal_line.iloc[-1]:.5f}")
    print(f"Histogram: {histogram.iloc[-1]:.5f}")
    
    # Print MACD momentum status without blocking the trade
    if USE_MACD_FILTER:
        macd_buy, macd_sell = analyze_macd_momentum(df, latest, prev, TIMEFRAME, symbol)
        if signal == 'BUY':
            if macd_buy > 0:
                print(f"🟢 Strong bullish momentum (MACD Histogram: {histogram.iloc[-1]:.5f})")
            else:
                print(f"ℹ️ No additional MACD momentum confirmation")
        elif signal == 'SELL':
            if macd_sell > 0:
                print(f"🔴 Strong bearish momentum (MACD Histogram: {histogram.iloc[-1]:.5f})")
            else:
                print(f"ℹ️ No additional MACD momentum confirmation")
    
    roc_filter_passed = True
    if roc_value is not None:
        if signal == 'BUY':
            roc_filter_passed = roc_value > 0  # Positive ROC for bullish trend
            if roc_filter_passed:
                print(f"✅ ROC filter passed: Positive momentum ({roc_value:.2f}%)")
            else:
                print(f"⚠️ ROC filter failed: Negative momentum ({roc_value:.2f}%)")
        else:  # SELL signal
            roc_filter_passed = roc_value < 0  # Negative ROC for bearish trend
            if roc_filter_passed:
                print(f"✅ ROC filter passed: Negative momentum ({roc_value:.2f}%)")
            else:
                print(f"⚠️ ROC filter failed: Positive momentum ({roc_value:.2f}%)")
            
            write_diagnostic_log(symbol, f"ROC filter: {roc_filter_passed} ({roc_value:.2f}%)")

        # Calculate Bollinger Bands
        upper_band, middle_band, lower_band, bandwidth = calculate_bollinger_bands(df)
        if upper_band is not None:
            current_price = latest['close']
            
            print(f"\nBollinger Bands Analysis:")
            print(f"Upper Band: {upper_band.iloc[-1]:.5f}")
            print(f"Middle Band: {middle_band.iloc[-1]:.5f}")
            print(f"Lower Band: {lower_band.iloc[-1]:.5f}")
            print(f"Bandwidth: {bandwidth.iloc[-1]:.2f}%")
            
            # Volatility-based filter using Bollinger Bands
            bb_filter_passed = True
            
            # Check for volatility expansion/contraction
            current_bandwidth = bandwidth.iloc[-1]
            prev_bandwidth = bandwidth.iloc[-2]
            
            # Calculate bandwidth change as percentage
            bandwidth_change = ((current_bandwidth - prev_bandwidth) / prev_bandwidth) * 100
            
            # Calculate Keltner Channels
            kc_upper, kc_middle, kc_lower, kc_width = calculate_keltner_channels(
                df, KC_PERIOD, KC_ATR_MULT, KC_USE_EMA
            )
            
            # Print detailed volatility analysis
            print("\nVolatility Indicators Analysis:")
            print("\n1. Bollinger Bands Details:")
            print(f"🔍 Current Bandwidth: {current_bandwidth:.2f}%")
            print(f"🔍 Previous Bandwidth: {prev_bandwidth:.2f}%")
            print(f"📊 Bandwidth Change: {bandwidth_change:+.2f}%")
            print(f"📏 Price Distance from Middle Band: {((current_price - middle_band.iloc[-1]) / middle_band.iloc[-1] * 100):+.2f}%")
            print(f"📈 Upper Band Distance: {((upper_band.iloc[-1] - middle_band.iloc[-1]) / middle_band.iloc[-1] * 100):.2f}%")
            print(f"📉 Lower Band Distance: {((middle_band.iloc[-1] - lower_band.iloc[-1]) / middle_band.iloc[-1] * 100):.2f}%")
            
            if signal == 'BUY':
                # Check for volatility expansion on buy signals
                if bandwidth_change > 0:  # Expanding volatility
                    print(f"✅ BB filter passed: Volatility expanding ({bandwidth_change:.2f}% bandwidth increase)")
                else:
                    bb_filter_passed = False
                    print(f"⚠️ BB filter failed: Volatility contracting ({abs(bandwidth_change):.2f}% bandwidth decrease)")
            else:  # SELL signal
                # Also check for volatility expansion on sell signals
                if bandwidth_change > 0:  # Expanding volatility
                    print(f"✅ BB filter passed: Volatility expanding ({bandwidth_change:.2f}% bandwidth increase)")
                else:
                    bb_filter_passed = False
                    print(f"⚠️ BB filter failed: Volatility contracting ({abs(bandwidth_change):.2f}% bandwidth decrease)")
            
            write_diagnostic_log(symbol, f"Bollinger Bands filter: {bb_filter_passed} (Bandwidth: {bandwidth.iloc[-1]:.2f}%)")
            
            # Calculate ATR
            atr = calculate_atr(df, ATR_PERIOD)
            current_atr = atr.iloc[-1]
            avg_atr = atr.rolling(window=ATR_PERIOD*2).mean().iloc[-1]
            atr_ratio = current_atr / avg_atr
            
            print("\n2. Keltner Channels Details:")
            print(f"Upper Channel: {kc_upper.iloc[-1]:.5f}")
            print(f"Middle Line: {kc_middle.iloc[-1]:.5f}")
            print(f"Lower Channel: {kc_lower.iloc[-1]:.5f}")
            print(f"Channel Width: {kc_width.iloc[-1]:.2f}%")
            print(f"📊 Price Position: {((current_price - kc_middle.iloc[-1]) / kc_middle.iloc[-1] * 100):+.2f}%")
            
            # Compare BB and KC for volatility consensus
            bb_kc_ratio = bandwidth.iloc[-1] / kc_width.iloc[-1]
            print(f"\nVolatility Consensus:")
            print(f"BB/KC Ratio: {bb_kc_ratio:.2f}")
            print(f"{'🟢' if bb_kc_ratio > 1 else '🔴'} {'Expanding' if bb_kc_ratio > 1 else 'Contracting'} volatility")
            
            print("\n3. ATR Analysis:")
            print(f"Current ATR: {current_atr:.5f}")
            print(f"Average ATR: {avg_atr:.5f}")
            print(f"ATR Ratio: {atr_ratio:.2f}x")
        
        atr_filter_passed = MIN_ATR_MULT <= atr_ratio <= MAX_ATR_MULT
        if not atr_filter_passed:
            if atr_ratio < MIN_ATR_MULT:
                print(f"⚠️ ATR filter failed: Volatility too low ({atr_ratio:.2f}x < {MIN_ATR_MULT:.2f}x)")
            else:
                print(f"⚠️ ATR filter failed: Volatility too high ({atr_ratio:.2f}x > {MAX_ATR_MULT:.2f}x)")
        else:
            print(f"✅ ATR filter passed: Normal volatility ({atr_ratio:.2f}x)")
            
    # Proceed with trade if signal is valid
        if signal in ['BUY', 'SELL']:  # Signal was already validated with 2/3 filters
            write_diagnostic_log(symbol, "All filters (ADX, MACD, ROC, BB) passed")
            is_buy = signal == 'BUY'
            
            # Check for existing positions that might conflict
            if not handle_existing_positions(symbol, {'overall_signal': signal}, current_time):
                return
                
            # Get fresh data for risk calculations
            risk_df = get_historical_data(symbol, TIMEFRAME, bars_count=50)
            if risk_df is None:
                print(f"No historical data available for {symbol}")
                return
                
            # Calculate base trade parameters using effective risk
            base_lot_size, sl_pips, tp_pips = calculate_trade_parameters(symbol, is_buy, risk_df, effective_risk)
            
            # Adjust position size based on volume confirmation and VWMA alignment
            volume_multiplier = 1.0
            
            # Volume analysis adjustment
            if volume_analysis and vpa_confirms:
                if volume_analysis['volume_ratio'] > 2.0:
                    volume_multiplier *= 1.2  # +20% for strong volume
                    print(f"📈 +20% position size: Strong volume confirmation")
                    print(f"Volume ratio: {volume_analysis['volume_ratio']:.2f}x average")
            else:
                volume_multiplier *= 0.8  # -20% for weak volume
                print(f"📉 -20% position size: Weak volume confirmation")
            
            # VWMA alignment adjustment
            if vwma_confirms:
                volume_multiplier *= 1.1  # +10% for VWMA confirmation
                print(f"📈 +10% position size: VWMA confirms trend")
            else:
                volume_multiplier *= 0.9  # -10% for VWMA divergence
                print(f"📉 -10% position size: VWMA divergence")
            
            final_lot_size = base_lot_size * volume_multiplier
            
            if market_open:
                # Pre-execution validation
                analysis_price = latest['close']
                is_valid, message = validate_execution_conditions(symbol, analysis_price, signal, TIMEFRAME)
                
                if not is_valid:
                    print(f"❌ Trade execution aborted: {message}")
                    write_diagnostic_log(symbol, f"Trade aborted: {message}")
                    return
                    
                print(f"\nPosition Sizing:")
                print(f"Base lot size: {base_lot_size:.2f}")
                print(f"Volume multiplier: {volume_multiplier:.2f}")
                print(f"Final lot size: {final_lot_size:.2f}")
                
                # Log price position relative to AMA50
                price_position = "above" if latest['close'] > latest['ma_medium'] else "below"
                print(f"✅ Price {price_position} AMA50 ({latest['close']:.5f} vs {latest['ma_medium']:.5f})")
                
                last_trade_times[symbol] = current_time
                execute_trade(symbol, is_buy, final_lot_size, sl_pips, tp_pips)
