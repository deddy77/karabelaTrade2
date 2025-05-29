"""Test script to verify candlestick pattern detection"""
import pandas as pd
import numpy as np
from candlestick_patterns import comprehensive_pattern_analysis
from mt5_helper import connect, get_historical_data
from config import SYMBOL, TIMEFRAME, MA_MEDIUM, MA_LONG, AMA_FAST_EMA, AMA_SLOW_EMA

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

def test_pattern_detection():
    """Test the pattern detection with current market data"""
    print("🧪 Testing Candlestick Pattern Detection...")

    if not connect():
        print("❌ Failed to connect to MT5")
        return

    # Get market data
    df = get_historical_data(SYMBOL, TIMEFRAME, bars_count=400)
    if df is None:
        print("❌ Failed to get market data")
        return

    # Calculate AMAs
    df['ama_50'] = calculate_ama(df, MA_MEDIUM, AMA_FAST_EMA, AMA_SLOW_EMA)
    df['ama_200'] = calculate_ama(df, MA_LONG, AMA_FAST_EMA, AMA_SLOW_EMA)
    df = df.dropna()

    if len(df) < 10:
        print("❌ Not enough data points")
        return

    # Test pattern analysis
    pattern_analysis = comprehensive_pattern_analysis(df, df['ama_50'], df['ama_200'])

    print(f"\n📊 Pattern Analysis Results for {SYMBOL}:")
    print(f"=" * 50)

    # Show recent candle data
    latest = df.iloc[-1]
    previous = df.iloc[-2]

    print(f"📈 Recent Candle Data:")
    print(f"   Previous: O:{previous['open']:.5f} H:{previous['high']:.5f} L:{previous['low']:.5f} C:{previous['close']:.5f}")
    print(f"   Latest:   O:{latest['open']:.5f} H:{latest['high']:.5f} L:{latest['low']:.5f} C:{latest['close']:.5f}")

    # Show candlestick analysis
    candlestick_analysis = pattern_analysis['candlestick_analysis']
    print(f"\n🕯️ Candlestick Analysis:")
    print(f"   Signal: {candlestick_analysis['signal']}")
    print(f"   Bullish patterns: {candlestick_analysis['bullish_patterns']}")
    print(f"   Bearish patterns: {candlestick_analysis['bearish_patterns']}")
    print(f"   Total patterns found: {len(candlestick_analysis['patterns'])}")

    if candlestick_analysis['patterns']:
        print(f"\n📊 Patterns Found:")
        for pattern in candlestick_analysis['patterns']:
            print(f"   - {pattern['pattern']}: {pattern['type']} ({pattern['strength']})")
    else:
        print(f"\n📊 No significant patterns detected")

        # Debug: Check individual pattern conditions
        print(f"\n🔍 Debug - Testing individual patterns:")

        # Test Doji
        body_size = abs(latest['close'] - latest['open'])
        full_range = latest['high'] - latest['low']
        body_ratio = body_size / full_range if full_range > 0 else 0
        print(f"   DOJI test: body_ratio={body_ratio:.4f} (threshold=0.1) - {'✅' if body_ratio <= 0.1 else '❌'}")

        # Test Hammer
        lower_shadow = min(latest['open'], latest['close']) - latest['low']
        upper_shadow = latest['high'] - max(latest['open'], latest['close'])
        print(f"   HAMMER test: lower_shadow={lower_shadow:.5f}, body_size={body_size:.5f}, ratio={lower_shadow/(body_size+0.00001):.2f}")

        # Test Shooting Star
        print(f"   SHOOTING_STAR test: upper_shadow={upper_shadow:.5f}, body_size={body_size:.5f}, ratio={upper_shadow/(body_size+0.00001):.2f}")

    # Show trend analysis
    trend_analysis = pattern_analysis['trend_analysis']
    print(f"\n📈 Trend Analysis:")
    print(f"   Long-term: {trend_analysis['long_term_trend']}")
    print(f"   Short-term: {trend_analysis['short_term_momentum']}")
    print(f"   Conflict: {trend_analysis['trend_conflict']}")
    print(f"   Recommendation: {trend_analysis['recommendation']}")
    print(f"   Confidence: {trend_analysis['confidence']}")

    # Show final recommendation
    print(f"\n🎯 Final Results:")
    print(f"   Recommendation: {pattern_analysis['final_recommendation']}")
    print(f"   Confidence: {pattern_analysis['confidence_level']}")

    print(f"\n✅ Pattern detection test complete!")

if __name__ == "__main__":
    test_pattern_detection()
