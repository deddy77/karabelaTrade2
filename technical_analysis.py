"""Technical analysis module for market analysis"""
import numpy as np
import pandas as pd
import MetaTrader5 as mt5
from datetime import datetime, timedelta

def calculate_moving_averages(df, periods=[20, 50, 200]):
    """Calculate multiple moving averages"""
    results = {}
    for period in periods:
        ma = df['close'].rolling(window=period).mean()
        results[f'MA{period}'] = ma.iloc[-1]
        results[f'MA{period}_direction'] = 'Up' if ma.iloc[-1] > ma.iloc[-2] else 'Down'
    return results

def calculate_rsi(df, period=14):
    """Calculate RSI indicator"""
    delta = df['close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    
    current_rsi = rsi.iloc[-1]
    rsi_condition = "Overbought" if current_rsi > 70 else "Oversold" if current_rsi < 30 else "Neutral"
    
    return {
        "RSI": current_rsi,
        "RSI_condition": rsi_condition
    }

def calculate_support_resistance(df, periods=20):
    """Calculate support and resistance levels"""
    high_max = df['high'].rolling(window=periods).max()
    low_min = df['low'].rolling(window=periods).min()
    
    current_price = df['close'].iloc[-1]
    resistance = high_max[high_max > current_price].min()
    support = low_min[low_min < current_price].max()
    
    return {
        "support": support,
        "resistance": resistance,
        "current_price": current_price
    }

def calculate_atr(df, period=14):
    """Calculate Average True Range"""
    high = df['high']
    low = df['low']
    close = df['close']
    
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    
    tr = pd.DataFrame({
        'tr1': tr1,
        'tr2': tr2,
        'tr3': tr3
    }).max(axis=1)
    
    atr = tr.rolling(window=period).mean()
    
    return {
        "ATR": atr.iloc[-1],
        "ATR_percent": (atr.iloc[-1] / df['close'].iloc[-1]) * 100
    }

def analyze_volume(df):
    """Analyze volume patterns"""
    avg_volume = df['tick_volume'].rolling(window=20).mean()
    current_volume = df['tick_volume'].iloc[-1]
    
    volume_ratio = current_volume / avg_volume.iloc[-1]
    volume_trend = "High" if volume_ratio > 1.5 else "Low" if volume_ratio < 0.5 else "Normal"
    
    return {
        "volume_ratio": volume_ratio,
        "volume_trend": volume_trend,
        "avg_volume": avg_volume.iloc[-1]
    }

def identify_trend(df, short_period=20, long_period=50):
    """Identify market trend"""
    short_ma = df['close'].rolling(window=short_period).mean()
    long_ma = df['close'].rolling(window=long_period).mean()
    
    current_trend = "Uptrend" if short_ma.iloc[-1] > long_ma.iloc[-1] else "Downtrend"
    trend_strength = abs(short_ma.iloc[-1] - long_ma.iloc[-1]) / long_ma.iloc[-1] * 100
    
    return {
        "trend": current_trend,
        "strength": trend_strength,
        "short_ma": short_ma.iloc[-1],
        "long_ma": long_ma.iloc[-1]
    }

def analyze_volatility(df):
    """Analyze market volatility"""
    returns = df['close'].pct_change()
    volatility = returns.std() * np.sqrt(252)  # Annualized volatility
    
    recent_volatility = returns.tail(20).std() * np.sqrt(252)
    volatility_change = (recent_volatility - volatility) / volatility * 100
    
    conditions = {
        "state": "High" if recent_volatility > volatility * 1.2 else "Low" if recent_volatility < volatility * 0.8 else "Normal",
        "trend": "Increasing" if volatility_change > 10 else "Decreasing" if volatility_change < -10 else "Stable"
    }
    
    return {
        "current": recent_volatility,
        "historical": volatility,
        "change": volatility_change,
        "conditions": conditions
    }

def run_technical_analysis(df):
    """Run comprehensive technical analysis"""
    try:
        results = {
            "time": datetime.now(),
            "moving_averages": calculate_moving_averages(df),
            "rsi": calculate_rsi(df),
            "support_resistance": calculate_support_resistance(df),
            "atr": calculate_atr(df),
            "volume": analyze_volume(df),
            "trend": identify_trend(df),
            "volatility": analyze_volatility(df)
        }
        
        # Determine overall market conditions
        conditions = []
        
        # Check trend strength
        if results["trend"]["strength"] > 2.0:
            conditions.append(f"Strong {results['trend']['trend']}")
        
        # Check RSI conditions
        if results["rsi"]["RSI_condition"] != "Neutral":
            conditions.append(results["rsi"]["RSI_condition"])
        
        # Check volume conditions
        if results["volume"]["volume_trend"] != "Normal":
            conditions.append(f"{results['volume']['volume_trend']} Volume")
        
        # Check volatility conditions
        vol_state = results["volatility"]["conditions"]["state"]
        if vol_state != "Normal":
            conditions.append(f"{vol_state} Volatility")
        
        results["market_conditions"] = conditions if conditions else ["Normal Trading Conditions"]
        
        return results
        
    except Exception as e:
        print(f"Error in technical analysis: {str(e)}")
        return None

def format_analysis_report(results):
    """Format technical analysis results for display"""
    if not results:
        return "Technical analysis failed"
        
    report = [
        "=== Technical Analysis Report ===",
        f"Time: {results['time'].strftime('%Y-%m-%d %H:%M:%S')}",
        "\nMarket Conditions:",
        "- " + "\n- ".join(results["market_conditions"]),
        "\nTrend Analysis:",
        f"Direction: {results['trend']['trend']}",
        f"Strength: {results['trend']['strength']:.2f}%",
        "\nKey Levels:",
        f"Support: {results['support_resistance']['support']:.5f}",
        f"Resistance: {results['support_resistance']['resistance']:.5f}",
        f"Current: {results['support_resistance']['current_price']:.5f}",
        "\nIndicators:",
        f"RSI: {results['rsi']['RSI']:.2f} ({results['rsi']['RSI_condition']})",
        f"ATR: {results['atr']['ATR']:.5f} ({results['atr']['ATR_percent']:.2f}%)",
        "\nVolume Analysis:",
        f"Trend: {results['volume']['volume_trend']}",
        f"Ratio: {results['volume']['volume_ratio']:.2f}x average",
        "\nVolatility:",
        f"State: {results['volatility']['conditions']['state']}",
        f"Trend: {results['volatility']['conditions']['trend']}"
    ]
    
    return "\n".join(report)
