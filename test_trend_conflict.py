# Test script to verify trend conflict detection
import pandas as pd
import numpy as np
from candlestick_patterns import comprehensive_pattern_analysis, detect_trend_within_trend

def create_test_data_with_pullback():
    """
    Create test data representing an uptrend (AMA50 > AMA200) 
    but with recent bearish momentum (pullback within the trend)
    """
    # Create 100 bars of data
    dates = pd.date_range(start='2024-01-01', periods=100, freq='5T')
    
    # Simulate an overall uptrend with a recent pullback
    base_trend = np.linspace(1.0800, 1.0900, 100)  # Overall upward trend
    
    # Add recent bearish movement (last 10 bars declining)
    pullback_bars = 10
    for i in range(100 - pullback_bars, 100):
        decline_factor = (i - (100 - pullback_bars)) * 0.0005
        base_trend[i] = base_trend[i] - decline_factor
    
    # Create OHLC data
    data = []
    for i, price in enumerate(base_trend):
        # Add some volatility
        high = price + np.random.uniform(0.0001, 0.0003)
        low = price - np.random.uniform(0.0001, 0.0003)
        
        # Recent bars are bearish (close < open)
        if i >= 90:  # Last 10 bars
            open_price = high - np.random.uniform(0.0001, 0.0002)
            close_price = low + np.random.uniform(0.0001, 0.0002)
        else:
            open_price = low + np.random.uniform(0.0001, 0.0002)
            close_price = high - np.random.uniform(0.0001, 0.0002)
        
        data.append({
            'time': dates[i],
            'open': open_price,
            'high': high,
            'low': low,
            'close': close_price,
            'volume': 1000
        })
    
    return pd.DataFrame(data)

def test_trend_conflict_detection():
    """Test the trend conflict detection functionality"""
    print("=== Testing Trend Conflict Detection ===")
    
    # Create test data
    df = create_test_data_with_pullback()
    
    # Create moving averages to simulate uptrend (AMA50 > AMA200)
    ma_short = pd.Series([1.0850] * len(df))  # AMA50 higher
    ma_long = pd.Series([1.0840] * len(df))   # AMA200 lower
    
    print(f"Data length: {len(df)}")
    print(f"Latest price: {df.iloc[-1]['close']:.5f}")
    print(f"AMA50: {ma_short.iloc[-1]:.5f}")
    print(f"AMA200: {ma_long.iloc[-1]:.5f}")
    print(f"Long-term trend: {'BULLISH' if ma_short.iloc[-1] > ma_long.iloc[-1] else 'BEARISH'}")
    
    # Test trend conflict detection
    result = detect_trend_within_trend(df, ma_short, ma_long)
    
    print("\n=== Trend Analysis Results ===")
    print(f"Long-term trend: {result['long_term_trend']}")
    print(f"Short-term momentum: {result['short_term_momentum']}")
    print(f"Trend conflict detected: {result['trend_conflict']}")
    print(f"Recommendation: {result['recommendation']}")
    print(f"Confidence: {result['confidence']}")
    print(f"Price above AMA50: {result['price_above_short_ma']}")
    print(f"Price above AMA200: {result['price_above_long_ma']}")
    print(f"Momentum strength: {result['momentum_strength']:.3f}")
    
    # Test comprehensive analysis
    print("\n=== Comprehensive Pattern Analysis ===")
    comprehensive_result = comprehensive_pattern_analysis(df, ma_short, ma_long)
    
    print(f"Final recommendation: {comprehensive_result['final_recommendation']}")
    print(f"Confidence level: {comprehensive_result['confidence_level']}")
    
    # Check if it correctly identifies the pullback situation
    if (result['long_term_trend'] == 'BULLISH' and 
        result['short_term_momentum'] == 'BEARISH' and 
        result['trend_conflict'] == True and
        result['recommendation'] == 'WAIT_FOR_PULLBACK_END'):
        print("\n✅ SUCCESS: Trend conflict correctly detected!")
        print("The bot should NOT take a long position during this pullback.")
    else:
        print("\n❌ ISSUE: Trend conflict detection may need adjustment.")
    
    return result

if __name__ == "__main__":
    try:
        test_trend_conflict_detection()
    except Exception as e:
        print(f"Error during test: {e}")
        import traceback
        traceback.print_exc()
