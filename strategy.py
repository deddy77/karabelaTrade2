import time
import MetaTrader5 as mt5
from mt5_helper import (
    connect, check_connection, get_historical_data,
    has_buy_position, has_sell_position,
    open_buy_order, open_sell_order, close_all_positions
)
from config import SYMBOL, TIMEFRAME
from profit_manager import update_positions
from risk_manager import calculate_lot_size

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
            
            # Get latest market data
            df = get_historical_data(SYMBOL, TIMEFRAME, bars_count=100)
            if df is None:
                print("Failed to get market data")
                time.sleep(60)
                continue
                  # Update existing positions
            update_positions(SYMBOL)            # Import technical analysis functions first
            from technical_analysis import (
                calculate_moving_averages, calculate_rsi, 
                identify_trend, analyze_volatility
            )
            
            # Analyze market conditions first to determine signal
            mas = calculate_moving_averages(df, periods=[20, 50])
            rsi_data = calculate_rsi(df)
            trend_data = identify_trend(df)
            volatility = analyze_volatility(df)
            
            current_price = df['close'].iloc[-1]
            ma20 = mas['MA20']
            ma50 = mas['MA50']
            rsi = rsi_data['RSI']
            
            # Determine buy signal for lot calculation
            preliminary_buy_signal = (
                current_price > ma20 and 
                ma20 > ma50 and 
                rsi < 70 and 
                trend_data['trend'] == 'Uptrend'
            )
            
            # Calculate position size based on actual signal
            try:
                from risk_manager import determine_lot
                lot_size, stop_loss_pips = determine_lot(SYMBOL, df, preliminary_buy_signal)
            except Exception as e:
                print(f"Error calculating lot size: {e}")
                from config import MIN_LOT
                lot_size = MIN_LOT            
            print(f"\n📊 Market Analysis for {SYMBOL}:")
            print(f"Price: {current_price:.5f} | MA20: {ma20:.5f} | MA50: {ma50:.5f}")
            print(f"RSI: {rsi:.1f} ({rsi_data['RSI_condition']}) | Trend: {trend_data['trend']}")
            
            # Trading Logic: Simple MA Crossover + RSI Filter
            has_buy = has_buy_position(SYMBOL)
            has_sell = has_sell_position(SYMBOL)
            
            # Buy Signal: Price above MA20, MA20 above MA50, RSI not overbought
            buy_signal = (
                current_price > ma20 and 
                ma20 > ma50 and 
                rsi < 70 and 
                trend_data['trend'] == 'Uptrend'
            )
            
            # Sell Signal: Price below MA20, MA20 below MA50, RSI not oversold  
            sell_signal = (
                current_price < ma20 and 
                ma20 < ma50 and 
                rsi > 30 and 
                trend_data['trend'] == 'Downtrend'
            )
            
            # Execute trades
            if buy_signal and not has_buy:
                print(f"🟢 BUY SIGNAL: Opening long position - Lot: {lot_size}")
                success = open_buy_order(SYMBOL, lot_size)
                if success:
                    print(f"✅ Buy order placed successfully")
                else:
                    print(f"❌ Failed to place buy order")
                    
            elif sell_signal and not has_sell:
                print(f"🔴 SELL SIGNAL: Opening short position - Lot: {lot_size}")
                success = open_sell_order(SYMBOL, lot_size)
                if success:
                    print(f"✅ Sell order placed successfully")
                else:
                    print(f"❌ Failed to place sell order")
            
            # Close opposing positions if signal reverses
            if buy_signal and has_sell:
                print(f"🔄 Closing sell positions due to buy signal")
                close_all_positions(SYMBOL)
            elif sell_signal and has_buy:
                print(f"🔄 Closing buy positions due to sell signal")
                close_all_positions(SYMBOL)
            
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

if __name__ == "__main__":
    if connect():
        run_strategy()
    else:
        print("Failed to connect to MetaTrader 5")
