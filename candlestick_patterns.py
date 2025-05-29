# ================================
# Candlestick Pattern Analysis Module
# ================================

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional, Any

def is_doji(open_price: float, close_price: float, high_price: float, low_price: float, 
           body_threshold: float = 0.1) -> bool:
    """
    Identify Doji pattern - when open and close are very close
    """
    body_size = abs(close_price - open_price)
    full_range = high_price - low_price
    
    if full_range == 0:
        return False
    
    body_ratio = body_size / full_range
    return body_ratio <= body_threshold

def is_hammer(open_price: float, close_price: float, high_price: float, low_price: float,
              is_bullish: bool = True) -> bool:
    """
    Identify Hammer/Hanging Man pattern
    - Small body at the top
    - Long lower shadow (at least 2x body size)
    - Little to no upper shadow
    """
    body_size = abs(close_price - open_price)
    lower_shadow = min(open_price, close_price) - low_price
    upper_shadow = high_price - max(open_price, close_price)
    full_range = high_price - low_price
    
    if full_range == 0 or body_size == 0:
        return False
    
    # Body should be small (less than 30% of full range)
    body_ratio = body_size / full_range
    if body_ratio > 0.3:
        return False
    
    # Lower shadow should be at least 2x body size
    if lower_shadow < (body_size * 2):
        return False
    
    # Upper shadow should be small (less than body size)
    if upper_shadow > body_size:
        return False
    
    # For bullish hammer, close should be higher than open
    if is_bullish and close_price <= open_price:
        return False
    
    return True

def is_engulfing(prev_open: float, prev_close: float, curr_open: float, curr_close: float,
                 is_bullish: bool = True) -> bool:
    """
    Identify Bullish/Bearish Engulfing pattern
    """
    if is_bullish:
        # Previous candle should be bearish (red)
        if prev_close >= prev_open:
            return False
        # Current candle should be bullish (green) and engulf previous
        return (curr_close > curr_open and 
                curr_open < prev_close and 
                curr_close > prev_open)
    else:
        # Previous candle should be bullish (green)
        if prev_close <= prev_open:
            return False
        # Current candle should be bearish (red) and engulf previous
        return (curr_close < curr_open and 
                curr_open > prev_close and 
                curr_close < prev_open)

def is_piercing_line(prev_open: float, prev_close: float, curr_open: float, curr_close: float) -> bool:
    """
    Identify Piercing Line pattern (bullish reversal)
    """
    # Previous candle should be bearish
    if prev_close >= prev_open:
        return False
    
    # Current candle should be bullish
    if curr_close <= curr_open:
        return False
    
    # Current open should be below previous close
    if curr_open >= prev_close:
        return False
    
    # Current close should penetrate at least 50% of previous body
    prev_body_midpoint = (prev_open + prev_close) / 2
    return curr_close > prev_body_midpoint

def is_dark_cloud_cover(prev_open: float, prev_close: float, curr_open: float, curr_close: float) -> bool:
    """
    Identify Dark Cloud Cover pattern (bearish reversal)
    """
    # Previous candle should be bullish
    if prev_close <= prev_open:
        return False
    
    # Current candle should be bearish
    if curr_close >= curr_open:
        return False
    
    # Current open should be above previous close
    if curr_open <= prev_close:
        return False
    
    # Current close should penetrate at least 50% of previous body
    prev_body_midpoint = (prev_open + prev_close) / 2
    return curr_close < prev_body_midpoint

def is_shooting_star(open_price: float, close_price: float, high_price: float, low_price: float) -> bool:
    """
    Identify Shooting Star pattern (bearish reversal)
    """
    body_size = abs(close_price - open_price)
    upper_shadow = high_price - max(open_price, close_price)
    lower_shadow = min(open_price, close_price) - low_price
    full_range = high_price - low_price
    
    if full_range == 0 or body_size == 0:
        return False
    
    # Body should be small (less than 30% of full range)
    body_ratio = body_size / full_range
    if body_ratio > 0.3:
        return False
    
    # Upper shadow should be at least 2x body size
    if upper_shadow < (body_size * 2):
        return False
    
    # Lower shadow should be small
    if lower_shadow > body_size:
        return False
    
    return True

def analyze_price_momentum(df: pd.DataFrame, lookback: int = 5) -> Dict[str, Any]:
    """
    Analyze price momentum within the recent candles
    """
    if len(df) < lookback + 1:
        return {"momentum": "INSUFFICIENT_DATA", "strength": 0}
    
    recent_df = df.tail(lookback + 1)
    
    # Calculate price changes
    price_changes = recent_df['close'].diff().dropna()
      # Count bullish vs bearish candles
    bullish_count = sum(1 for i in range(len(recent_df)) 
                       if recent_df.iloc[i]['close'] > recent_df.iloc[i]['open'])
    bearish_count = len(recent_df) - bullish_count
      # Calculate momentum strength with proper type handling
    if len(price_changes) == 0:
        total_movement = 0.0
        net_movement = 0.0
    else:
        # Convert to numpy array for reliable calculations
        price_changes_values = price_changes.to_numpy()
        total_movement = float(np.sum(np.abs(price_changes_values)))
        net_movement = float(np.sum(price_changes_values))
    
    momentum_strength = abs(net_movement) / total_movement if total_movement > 0 else 0.0
    
    # Determine momentum direction
    if net_movement > 0:
        momentum = "BULLISH"
    elif net_movement < 0:
        momentum = "BEARISH"
    else:
        momentum = "SIDEWAYS"
    
    return {
        "momentum": momentum,
        "strength": momentum_strength,
        "bullish_candles": bullish_count,
        "bearish_candles": bearish_count,
        "net_movement": net_movement,
        "recent_high": recent_df['high'].max(),
        "recent_low": recent_df['low'].min()
    }

def detect_trend_within_trend(df: pd.DataFrame, ma_short: pd.Series, ma_long: pd.Series) -> Dict[str, Any]:
    """
    Detect short-term trend within longer-term trend
    """
    if len(df) < 10:
        return {"trend_conflict": False, "recommendation": "INSUFFICIENT_DATA"}
    
    latest = df.iloc[-1]
    
    # Long-term trend from MA crossover
    long_term_trend = "BULLISH" if ma_short.iloc[-1] > ma_long.iloc[-1] else "BEARISH"
    
    # Short-term momentum analysis
    momentum_analysis = analyze_price_momentum(df, lookback=5)
    short_term_momentum = momentum_analysis["momentum"]
    
    # Price position relative to MAs
    price = latest['close']
    above_short_ma = price > ma_short.iloc[-1]
    above_long_ma = price > ma_long.iloc[-1]
    
    # Detect trend conflicts
    trend_conflict = False
    recommendation = "HOLD"
    confidence = "LOW"
    
    if long_term_trend == "BULLISH":
        if short_term_momentum == "BEARISH" or not above_short_ma:
            trend_conflict = True
            recommendation = "WAIT_FOR_PULLBACK_END"
            confidence = "HIGH" if momentum_analysis["strength"] > 0.6 else "MEDIUM"
        elif above_short_ma and above_long_ma and short_term_momentum == "BULLISH":
            recommendation = "BUY"
            confidence = "HIGH"
        else:
            recommendation = "CAUTIOUS_BUY"
            confidence = "MEDIUM"
    
    elif long_term_trend == "BEARISH":
        if short_term_momentum == "BULLISH" or above_short_ma:
            trend_conflict = True
            recommendation = "WAIT_FOR_BOUNCE_END"
            confidence = "HIGH" if momentum_analysis["strength"] > 0.6 else "MEDIUM"
        elif not above_short_ma and not above_long_ma and short_term_momentum == "BEARISH":
            recommendation = "SELL"
            confidence = "HIGH"
        else:
            recommendation = "CAUTIOUS_SELL"
            confidence = "MEDIUM"
    
    return {
        "long_term_trend": long_term_trend,
        "short_term_momentum": short_term_momentum,
        "trend_conflict": trend_conflict,
        "recommendation": recommendation,
        "confidence": confidence,
        "price_above_short_ma": above_short_ma,
        "price_above_long_ma": above_long_ma,
        "momentum_strength": momentum_analysis["strength"],
        "momentum_details": momentum_analysis
    }

def analyze_candlestick_patterns(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Comprehensive candlestick pattern analysis
    """
    if len(df) < 2:
        return {"patterns": [], "signal": "INSUFFICIENT_DATA"}
    
    patterns_found = []
    latest = df.iloc[-1]
    previous = df.iloc[-2] if len(df) >= 2 else None
    
    # Single candle patterns
    if is_doji(latest['open'], latest['close'], latest['high'], latest['low']):
        patterns_found.append({"pattern": "DOJI", "type": "INDECISION", "strength": "MEDIUM"})
    
    if is_hammer(latest['open'], latest['close'], latest['high'], latest['low'], is_bullish=True):
        patterns_found.append({"pattern": "HAMMER", "type": "BULLISH_REVERSAL", "strength": "HIGH"})
    
    if is_hammer(latest['open'], latest['close'], latest['high'], latest['low'], is_bullish=False):
        patterns_found.append({"pattern": "HANGING_MAN", "type": "BEARISH_REVERSAL", "strength": "HIGH"})
    
    if is_shooting_star(latest['open'], latest['close'], latest['high'], latest['low']):
        patterns_found.append({"pattern": "SHOOTING_STAR", "type": "BEARISH_REVERSAL", "strength": "HIGH"})
    
    # Two candle patterns (if we have previous data)
    if previous is not None:
        if is_engulfing(previous['open'], previous['close'], latest['open'], latest['close'], is_bullish=True):
            patterns_found.append({"pattern": "BULLISH_ENGULFING", "type": "BULLISH_REVERSAL", "strength": "VERY_HIGH"})
        
        if is_engulfing(previous['open'], previous['close'], latest['open'], latest['close'], is_bullish=False):
            patterns_found.append({"pattern": "BEARISH_ENGULFING", "type": "BEARISH_REVERSAL", "strength": "VERY_HIGH"})
        
        if is_piercing_line(previous['open'], previous['close'], latest['open'], latest['close']):
            patterns_found.append({"pattern": "PIERCING_LINE", "type": "BULLISH_REVERSAL", "strength": "HIGH"})
        
        if is_dark_cloud_cover(previous['open'], previous['close'], latest['open'], latest['close']):
            patterns_found.append({"pattern": "DARK_CLOUD_COVER", "type": "BEARISH_REVERSAL", "strength": "HIGH"})
    
    # Determine overall signal
    bullish_patterns = [p for p in patterns_found if "BULLISH" in p["type"]]
    bearish_patterns = [p for p in patterns_found if "BEARISH" in p["type"]]
    
    if bullish_patterns and not bearish_patterns:
        signal = "BULLISH"
    elif bearish_patterns and not bullish_patterns:
        signal = "BEARISH"
    elif bullish_patterns and bearish_patterns:
        signal = "CONFLICTED"
    else:
        signal = "NEUTRAL"
    
    return {
        "patterns": patterns_found,
        "signal": signal,
        "bullish_patterns": len(bullish_patterns),
        "bearish_patterns": len(bearish_patterns)
    }

def comprehensive_pattern_analysis(df: pd.DataFrame, ma_short: pd.Series, ma_long: pd.Series) -> Dict[str, Any]:
    """
    Comprehensive analysis combining candlestick patterns and trend analysis
    """
    candlestick_analysis = analyze_candlestick_patterns(df)
    trend_analysis = detect_trend_within_trend(df, ma_short, ma_long)
    momentum_analysis = analyze_price_momentum(df)
    
    # Combine all analyses for final recommendation
    final_recommendation = "HOLD"
    confidence_level = "LOW"
    
    # Priority: Trend conflicts override everything
    if trend_analysis["trend_conflict"]:
        final_recommendation = trend_analysis["recommendation"]
        confidence_level = trend_analysis["confidence"]
    
    # If no trend conflict, check for strong candlestick signals
    elif candlestick_analysis["signal"] in ["BULLISH", "BEARISH"]:
        if trend_analysis["long_term_trend"] == "BULLISH" and candlestick_analysis["signal"] == "BULLISH":
            final_recommendation = "BUY"
            confidence_level = "HIGH"
        elif trend_analysis["long_term_trend"] == "BEARISH" and candlestick_analysis["signal"] == "BEARISH":
            final_recommendation = "SELL"
            confidence_level = "HIGH"
        else:
            final_recommendation = "WAIT"
            confidence_level = "MEDIUM"
    
    # Fallback to trend analysis
    else:
        final_recommendation = trend_analysis["recommendation"]
        confidence_level = trend_analysis["confidence"]
    
    return {
        "candlestick_analysis": candlestick_analysis,
        "trend_analysis": trend_analysis,
        "momentum_analysis": momentum_analysis,
        "final_recommendation": final_recommendation,
        "confidence_level": confidence_level,
        "timestamp": df.iloc[-1]['time'] if 'time' in df.columns else "N/A"
    }
