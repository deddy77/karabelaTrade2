import time
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from mt5_helper import (
    connect, check_connection, get_historical_data,
    has_buy_position, has_sell_position,
    open_buy_order, open_sell_order, close_all_positions
)
from config import SYMBOL, TIMEFRAME, MA_MEDIUM, MA_LONG, AMA_FAST_EMA, AMA_SLOW_EMA
from profit_manager import update_positions
from risk_manager import calculate_lot_size, determine_lot
from candlestick_patterns import comprehensive_pattern_analysis
from enhanced_position_detection import (
    has_buy_position_any_magic, has_sell_position_any_magic,
    analyze_position_risk, should_avoid_new_trades
)
from discord_notify import (
    send_trend_conflict_notification, send_position_risk_notification,
    send_recommendation_change_notification, send_pattern_detection_notification,
    send_enhanced_trade_notification
)

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

def run_strategy():
    """
    Main trading strategy loop.
    This function is called when running in command-line mode.
    When using GUI mode, the trading logic is handled by the GUI class.
    """
    print(f"Starting strategy for {SYMBOL} on {TIMEFRAME} timeframe")

    while True:
        try:
            # Check MT5 connection
            if not check_connection():
                print("Lost connection to MT5, attempting to reconnect...")
                if not connect():
                    print("Failed to reconnect to MT5")
                    break
              # Get latest market data with more bars for AMA200
            df = get_historical_data(SYMBOL, TIMEFRAME, bars_count=400)
            if df is None:
                print("Failed to get market data")
                time.sleep(60)
                continue

            # Check if we have enough data for AMA200
            if len(df) < MA_LONG + 50:
                print(f"Not enough historical data (need at least {MA_LONG + 50} bars)")
                time.sleep(60)
                continue

            # Update existing positions
            update_positions(SYMBOL)

            # Calculate AMAs
            df['ama_50'] = calculate_ama(df, MA_MEDIUM, AMA_FAST_EMA, AMA_SLOW_EMA)  # AMA50
            df['ama_200'] = calculate_ama(df, MA_LONG, AMA_FAST_EMA, AMA_SLOW_EMA)    # AMA200
            df = df.dropna()

            if len(df) < 10:
                print("Not enough data points after calculating AMAs")
                time.sleep(60)
                continue

            latest = df.iloc[-1]
            previous = df.iloc[-2]
            current_price = latest['close']
            ama_50 = latest['ama_50']
            ama_200 = latest['ama_200']

            print(f"\n📊 Market Analysis for {SYMBOL}:")
            print(f"Price: {current_price:.5f} | AMA50: {ama_50:.5f} | AMA200: {ama_200:.5f}")

            # Determine basic AMA trend signal
            ama_trend_signal = 'NEUTRAL'
            if ama_50 > ama_200:
                ama_trend_signal = 'BUY'
                print("🟢 Bullish Setup: AMA50 > AMA200")
                if previous['ama_50'] <= previous['ama_200']:
                    print("🟢 Fresh Golden Cross Detected!")
            elif ama_50 < ama_200:
                ama_trend_signal = 'SELL'
                print("🔴 Bearish Setup: AMA50 < AMA200")
                if previous['ama_50'] >= previous['ama_200']:
                    print("🔴 Fresh Death Cross Detected!")

            # Comprehensive pattern analysis to detect trend conflicts
            pattern_analysis = comprehensive_pattern_analysis(df, df['ama_50'], df['ama_200'])

            print(f"\n🔍 Pattern Analysis:")
            print(f"Long-term Trend: {pattern_analysis['trend_analysis']['long_term_trend']}")
            print(f"Short-term Momentum: {pattern_analysis['trend_analysis']['short_term_momentum']}")
            print(f"Trend Conflict: {pattern_analysis['trend_analysis']['trend_conflict']}")
            print(f"Recommendation: {pattern_analysis['final_recommendation']}")
            print(f"Confidence: {pattern_analysis['confidence_level']}")

            # Display candlestick patterns if any
            if pattern_analysis['candlestick_analysis']['patterns']:
                print(f"📊 Candlestick Patterns Found:")
                for pattern in pattern_analysis['candlestick_analysis']['patterns']:
                    print(f"  - {pattern['pattern']}: {pattern['type']} ({pattern['strength']})")
            else:
                print(f"📊 No significant candlestick patterns detected")
                print(f"   Signal: {pattern_analysis['candlestick_analysis']['signal']}")

            # Final trading decision based on comprehensive analysis
            final_signal = 'NEUTRAL'
            confidence = pattern_analysis['confidence_level']
            recommendation = pattern_analysis['final_recommendation']

            # Only trade with HIGH confidence or when no trend conflict exists
            if confidence in ['HIGH', 'MEDIUM'] and not pattern_analysis['trend_analysis']['trend_conflict']:
                if recommendation == 'BUY' and ama_trend_signal == 'BUY':
                    final_signal = 'BUY'
                elif recommendation == 'SELL' and ama_trend_signal == 'SELL':
                    final_signal = 'SELL'
                elif recommendation in ['CAUTIOUS_BUY'] and ama_trend_signal == 'BUY':
                    final_signal = 'BUY'
                elif recommendation in ['CAUTIOUS_SELL'] and ama_trend_signal == 'SELL':
                    final_signal = 'SELL'

            # If there's a trend conflict, wait for it to resolve
            if pattern_analysis['trend_analysis']['trend_conflict']:
                print(f"⚠️ TREND CONFLICT DETECTED - Waiting for resolution")
                print(f"Long-term: {pattern_analysis['trend_analysis']['long_term_trend']}")
                print(f"Short-term: {pattern_analysis['trend_analysis']['short_term_momentum']}")
                # Send Discord notification for trend conflict
                send_trend_conflict_notification(
                    SYMBOL,
                    pattern_analysis['trend_analysis']['long_term_trend'],
                    pattern_analysis['trend_analysis']['short_term_momentum'],
                    confidence
                )
                final_signal = 'NEUTRAL'

            print(f"\n🎯 Final Trading Signal: {final_signal}")

            # Enhanced Position Detection - Check ALL positions regardless of magic number
            has_buy_any_magic = has_buy_position_any_magic(SYMBOL)
            has_sell_any_magic = has_sell_position_any_magic(SYMBOL)

            # Analyze position risk based on current trend
            long_term_trend = pattern_analysis['trend_analysis']['long_term_trend']
            position_risk_analysis = analyze_position_risk(SYMBOL, long_term_trend)

            # Check if we should avoid new trades due to conflicting positions
            should_avoid, avoid_reason = should_avoid_new_trades(SYMBOL, final_signal, long_term_trend)

            print(f"\n🔍 Enhanced Position Analysis:")
            print(f"Positions (Any Magic): BUY={has_buy_any_magic}, SELL={has_sell_any_magic}")
            print(f"Position Risk Detected: {position_risk_analysis['has_risk']}")
            if position_risk_analysis['has_risk']:
                print(f"⚠️ Position Risk Warnings:")
                for rec in position_risk_analysis['recommendations']:
                    print(f"   {rec}")

            if should_avoid:
                print(f"⚠️ TRADE AVOIDED: {avoid_reason}")
                print(f"   Recommendation: Consider manual review of existing positions")
                final_signal = 'NEUTRAL'  # Override signal to avoid conflicting trades

            # Calculate position size
            try:
                is_buy_signal = final_signal == 'BUY'
                lot_size, stop_loss_pips = determine_lot(SYMBOL, df, is_buy_signal)
            except Exception as e:
                print(f"Error calculating lot size: {e}")
                from config import MIN_LOT
                lot_size = MIN_LOT
                stop_loss_pips = 20
              # Trading Logic: Enhanced AMA Strategy with Pattern Analysis
            has_buy = has_buy_position(SYMBOL)
            has_sell = has_sell_position(SYMBOL)

            # Execute trades based on comprehensive analysis
            if final_signal == 'BUY' and not has_buy:
                print(f"🟢 BUY SIGNAL: Opening long position - Lot: {lot_size}")
                print(f"   Reason: {recommendation} with {confidence} confidence")
                success = open_buy_order(SYMBOL, lot_size, stop_loss_pips, 20)  # 20 pips TP
                if success:
                    print(f"✅ Buy order placed successfully")
                else:
                    print(f"❌ Failed to place buy order")

            elif final_signal == 'SELL' and not has_sell:
                print(f"🔴 SELL SIGNAL: Opening short position - Lot: {lot_size}")
                print(f"   Reason: {recommendation} with {confidence} confidence")
                success = open_sell_order(SYMBOL, lot_size, stop_loss_pips, 20)  # 20 pips TP
                if success:
                    print(f"✅ Sell order placed successfully")
                else:
                    print(f"❌ Failed to place sell order")

            # Close opposing positions if strong signal reverses
            if final_signal == 'BUY' and has_sell and confidence == 'HIGH':
                print(f"🔄 Closing sell positions due to strong buy signal")
                close_all_positions(SYMBOL)
            elif final_signal == 'SELL' and has_buy and confidence == 'HIGH':
                print(f"🔄 Closing buy positions due to strong sell signal")
                close_all_positions(SYMBOL)

            # If we have a position but signals suggest waiting, inform user
            if (has_buy or has_sell) and recommendation in ['WAIT_FOR_PULLBACK_END', 'WAIT_FOR_BOUNCE_END']:
                print(f"⚠️ Warning: Existing position may be at risk")
                print(f"   Current trend momentum is against the position")
                print(f"   Consider manual review or tighter stop losses")
                # Send Discord notification for position risk
                position_type = "LONG" if has_buy else "SHORT"
                send_position_risk_notification(
                    SYMBOL,
                    position_type,
                    recommendation,
                    confidence
                )

            # Log current status
            if has_buy or has_sell:
                position_type = "Long" if has_buy else "Short"
                print(f"📈 Current Position: {position_type}")
            else:
                print(f"⏸️ No open positions")

            # Sleep to avoid excessive API calls
            time.sleep(60)

        except KeyboardInterrupt:
            print("\nStrategy stopped by user")
            break
        except Exception as e:
            print(f"Error in strategy: {str(e)}")
            time.sleep(60)

def check_signal_and_trade(symbol=SYMBOL):
    """
    Check for trading signals and execute trades for a specific symbol
    Uses comprehensive pattern analysis to avoid bad trades during trend conflicts
    """
    try:
        # Get historical data with enough bars for AMA200
        df = get_historical_data(symbol, TIMEFRAME, bars_count=400)
        if df is None:
            print(f"Failed to get market data for {symbol}")
            return

        # Check if we have enough data for AMA200
        if len(df) < MA_LONG + 50:
            print(f"Not enough historical data for {symbol} (need at least {MA_LONG + 50} bars)")
            return

        # Update existing positions
        update_positions(symbol)

        # Calculate AMAs
        df['ama_50'] = calculate_ama(df, MA_MEDIUM, AMA_FAST_EMA, AMA_SLOW_EMA)  # AMA50
        df['ama_200'] = calculate_ama(df, MA_LONG, AMA_FAST_EMA, AMA_SLOW_EMA)    # AMA200
        df = df.dropna()

        if len(df) < 10:
            print(f"Not enough data points after calculating AMAs for {symbol}")
            return

        latest = df.iloc[-1]
        previous = df.iloc[-2]
        current_price = latest['close']
        ama_50 = latest['ama_50']
        ama_200 = latest['ama_200']

        print(f"📊 Market Analysis for {symbol}:")
        print(f"Price: {current_price:.5f} | AMA50: {ama_50:.5f} | AMA200: {ama_200:.5f}")

        # Determine basic AMA trend signal
        ama_trend_signal = 'NEUTRAL'
        if ama_50 > ama_200:
            ama_trend_signal = 'BUY'
            print("🟢 Bullish Setup: AMA50 > AMA200")
            if previous['ama_50'] <= previous['ama_200']:
                print("🟢 Fresh Golden Cross Detected!")
        elif ama_50 < ama_200:
            ama_trend_signal = 'SELL'
            print("🔴 Bearish Setup: AMA50 < AMA200")
            if previous['ama_50'] >= previous['ama_200']:
                print("🔴 Fresh Death Cross Detected!")

        # Comprehensive pattern analysis to detect trend conflicts
        pattern_analysis = comprehensive_pattern_analysis(df, df['ama_50'], df['ama_200'])

        print(f"🔍 Pattern Analysis:")
        print(f"Long-term Trend: {pattern_analysis['trend_analysis']['long_term_trend']}")
        print(f"Short-term Momentum: {pattern_analysis['trend_analysis']['short_term_momentum']}")
        print(f"Trend Conflict: {pattern_analysis['trend_analysis']['trend_conflict']}")
        print(f"Recommendation: {pattern_analysis['final_recommendation']}")
        print(f"Confidence: {pattern_analysis['confidence_level']}")

        # Display candlestick patterns if any
        if pattern_analysis['candlestick_analysis']['patterns']:
            print(f"📊 Candlestick Patterns Found:")
            for pattern in pattern_analysis['candlestick_analysis']['patterns']:
                print(f"  - {pattern['pattern']}: {pattern['type']} ({pattern['strength']})")

        # Final trading decision based on comprehensive analysis
        final_signal = 'NEUTRAL'
        confidence = pattern_analysis['confidence_level']
        recommendation = pattern_analysis['final_recommendation']

        # Only trade with HIGH or MEDIUM confidence and when no trend conflict exists
        if confidence in ['HIGH', 'MEDIUM'] and not pattern_analysis['trend_analysis']['trend_conflict']:
            if recommendation == 'BUY' and ama_trend_signal == 'BUY':
                final_signal = 'BUY'
            elif recommendation == 'SELL' and ama_trend_signal == 'SELL':
                final_signal = 'SELL'
            elif recommendation in ['CAUTIOUS_BUY'] and ama_trend_signal == 'BUY':
                final_signal = 'BUY'
            elif recommendation in ['CAUTIOUS_SELL'] and ama_trend_signal == 'SELL':
                final_signal = 'SELL'

        # If there's a trend conflict, wait for it to resolve
        if pattern_analysis['trend_analysis']['trend_conflict']:
            print(f"⚠️ TREND CONFLICT DETECTED - Waiting for resolution")
            print(f"Long-term: {pattern_analysis['trend_analysis']['long_term_trend']}")
            print(f"Short-term: {pattern_analysis['trend_analysis']['short_term_momentum']}")
            final_signal = 'NEUTRAL'

        print(f"🎯 Final Trading Signal: {final_signal}")

        # Enhanced Position Detection - Check ALL positions regardless of magic number
        has_buy_any_magic = has_buy_position_any_magic(symbol)
        has_sell_any_magic = has_sell_position_any_magic(symbol)

        # Analyze position risk based on current trend
        long_term_trend = pattern_analysis['trend_analysis']['long_term_trend']
        position_risk_analysis = analyze_position_risk(symbol, long_term_trend)

        # Check if we should avoid new trades due to conflicting positions
        should_avoid, avoid_reason = should_avoid_new_trades(symbol, final_signal, long_term_trend)

        print(f"\n🔍 Enhanced Position Analysis:")
        print(f"Positions (Any Magic): BUY={has_buy_any_magic}, SELL={has_sell_any_magic}")
        print(f"Position Risk Detected: {position_risk_analysis['has_risk']}")
        if position_risk_analysis['has_risk']:
            print(f"⚠️ Position Risk Warnings:")
            for rec in position_risk_analysis['recommendations']:
                print(f"   {rec}")

        if should_avoid:
            print(f"⚠️ TRADE AVOIDED: {avoid_reason}")
            print(f"   Recommendation: Consider manual review of existing positions")
            final_signal = 'NEUTRAL'  # Override signal to avoid conflicting trades

        # Calculate position size
        try:
            is_buy_signal = final_signal == 'BUY'
            lot_size, stop_loss_pips = determine_lot(symbol, df, is_buy_signal)
        except Exception as e:
            print(f"Error calculating lot size: {e}")
            from config import MIN_LOT
            lot_size = MIN_LOT
            stop_loss_pips = 20

        # Trading Logic: Enhanced AMA Strategy with Pattern Analysis
        has_buy = has_buy_position(symbol)
        has_sell = has_sell_position(symbol)

        # Execute trades based on comprehensive analysis
        if final_signal == 'BUY' and not has_buy:
            print(f"🟢 BUY SIGNAL: Opening long position - Lot: {lot_size}")
            print(f"   Reason: {recommendation} with {confidence} confidence")
            success = open_buy_order(symbol, lot_size, stop_loss_pips, 20)  # 20 pips TP
            if success:
                print(f"✅ Buy order placed successfully")
            else:
                print(f"❌ Failed to place buy order")

        elif final_signal == 'SELL' and not has_sell:
            print(f"🔴 SELL SIGNAL: Opening short position - Lot: {lot_size}")
            print(f"   Reason: {recommendation} with {confidence} confidence")
            success = open_sell_order(symbol, lot_size, stop_loss_pips, 20)  # 20 pips TP
            if success:
                print(f"✅ Sell order placed successfully")
            else:
                print(f"❌ Failed to place sell order")

        # Close opposing positions if strong signal reverses
        if final_signal == 'BUY' and has_sell and confidence == 'HIGH':
            print(f"🔄 Closing sell positions due to strong buy signal")
            close_all_positions(symbol)
        elif final_signal == 'SELL' and has_buy and confidence == 'HIGH':
            print(f"🔄 Closing buy positions due to strong sell signal")
            close_all_positions(symbol)

        # If we have a position but signals suggest waiting, inform user
        if (has_buy or has_sell) and recommendation in ['WAIT_FOR_PULLBACK_END', 'WAIT_FOR_BOUNCE_END']:
            print(f"⚠️ Warning: Existing position may be at risk")
            print(f"   Current trend momentum is against the position")
            print(f"   Consider manual review or tighter stop losses")

        # Log current status
        if has_buy or has_sell:
            position_type = "Long" if has_buy else "Short"
            print(f"📈 Current Position: {position_type}")
        else:
            print(f"⏸️ No open positions")

    except Exception as e:
        print(f"Error in check_signal_and_trade for {symbol}: {str(e)}")
        import traceback
        traceback.print_exc()

def check_recent_crossovers(lookback_minutes=20, symbol=SYMBOL):
    """
    Check for recent AMA crossovers within the specified timeframe
    """
    try:
        # Calculate how many bars to look back based on timeframe
        if TIMEFRAME == 'M5':
            bars_needed = lookback_minutes // 5
        elif TIMEFRAME == 'M15':
            bars_needed = lookback_minutes // 15
        elif TIMEFRAME == 'M30':
            bars_needed = lookback_minutes // 30
        elif TIMEFRAME == 'H1':
            bars_needed = lookback_minutes // 60
        else:
            bars_needed = 10  # Default fallback

        bars_needed = max(bars_needed, MA_LONG + 50)  # Ensure we have enough for AMA200

        df = get_historical_data(symbol, TIMEFRAME, bars_count=bars_needed)
        if df is None:
            print(f"Failed to get data for recent crossover check on {symbol}")
            return

        # Calculate AMAs
        df['ama_50'] = calculate_ama(df, MA_MEDIUM, AMA_FAST_EMA, AMA_SLOW_EMA)
        df['ama_200'] = calculate_ama(df, MA_LONG, AMA_FAST_EMA, AMA_SLOW_EMA)
        df = df.dropna()

        if len(df) < 5:
            print(f"Not enough data for crossover analysis on {symbol}")
            return

        # Check for recent crossovers
        for i in range(len(df) - 1, max(0, len(df) - bars_needed), -1):
            current = df.iloc[i]
            previous = df.iloc[i-1] if i > 0 else None

            if previous is not None:
                # Golden Cross (bullish)
                if (current['ama_50'] > current['ama_200'] and
                    previous['ama_50'] <= previous['ama_200']):
                    minutes_ago = (len(df) - 1 - i) * (5 if TIMEFRAME == 'M5' else 15)
                    print(f"🟢 Recent Golden Cross detected on {symbol} ({minutes_ago} minutes ago)")
                    return

                # Death Cross (bearish)
                elif (current['ama_50'] < current['ama_200'] and
                      previous['ama_50'] >= previous['ama_200']):
                    minutes_ago = (len(df) - 1 - i) * (5 if TIMEFRAME == 'M5' else 15)
                    print(f"🔴 Recent Death Cross detected on {symbol} ({minutes_ago} minutes ago)")
                    return

        print(f"ℹ️ No recent crossovers found on {symbol}")

    except Exception as e:
        print(f"Error checking recent crossovers for {symbol}: {str(e)}")

if __name__ == "__main__":
    if connect():
        run_strategy()
    else:
        print("Failed to connect to MetaTrader 5")
