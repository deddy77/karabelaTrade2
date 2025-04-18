# ================================
# ai-trading-bot/main.py
# ================================

from strategy import check_signal_and_trade
from mt5_helper import connect, shutdown, send_discord_notification, check_and_add_sltp, check_connection
from exit_manager import exit_manager
import time
import traceback
import MetaTrader5 as mt5
from datetime import datetime, timedelta
import os
from config import LOG_FILE, TIMEFRAME, SYMBOLS
from profit_manager import ProfitManager

# Create a global instance of ProfitManager that can be imported from other modules
pm = ProfitManager()

def main():
    """Main bot function"""
    print("=" * 50)
    print("FOREX TRADING BOT STARTING")
    print("=" * 50)
    print(f"Bot started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Trading symbols: {', '.join(SYMBOLS)}")
    
    # Create logs directory if it doesn't exist
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    
    # Connect to MetaTrader 5
    if not connect():
        print("Failed to connect to MetaTrader 5. Exiting...")
        return
    
    # Initialize profit manager
    account_info = mt5.account_info()
    pm.initialize_day(account_info.balance)
    
    # Set sleep time to 1 minute regardless of timeframe
    sleep_time = 60  # 1 minute in seconds
    
    # Special initial check for recent crossovers
    print("\nPerforming initial check for recent crossovers...")
    from strategy import check_recent_crossovers
    for symbol in SYMBOLS:
        print(f"\nChecking {symbol}:")
        check_recent_crossovers(20, symbol)  # Check last 20 minutes

    try:
        print(f"\nBot will check for signals every {sleep_time//60} minutes")
        print("Press Ctrl+C to stop the bot")
        
        while True:
            try:
                # Check profit status
                account_info = mt5.account_info()
                if not pm.update(account_info.balance):
                    print("Max daily loss hit! Stopping...")
                    break
                    
                if pm.target_reached:
                    print(f"Daily target achieved (+${pm.get_profit():.2f}). Waiting...")
                    time.sleep(sleep_time)
                    continue
                
                # Calculate next check time
                next_check_time = datetime.now() + timedelta(seconds=sleep_time)
                print(f"\nWaiting for next check at {next_check_time.strftime('%H:%M:%S')}")
                
                # Check MT5 connection
                if not check_connection():
                    print("MT5 connection lost. Attempting to reconnect...")
                    if not connect():
                        print("Failed to reconnect to MT5. Waiting for next cycle...")
                        time.sleep(sleep_time)
                        continue
                    print("Successfully reconnected to MT5.")
                
                # Check each symbol
                for symbol in SYMBOLS:
                    try:
                        print(f"\nChecking {symbol}:")
                        check_signal_and_trade(symbol)
                        # Verify and add SL/TP if missing
                        check_and_add_sltp(symbol)
                    except Exception as symbol_error:
                        error_msg = f"Error processing symbol {symbol}: {str(symbol_error)}"
                        print(f"❌ {error_msg}")
                        send_discord_notification(f"⚠️ ERROR: {error_msg}")
                        # Continue with next symbol
                        continue
                
                # Check and update exit levels for all symbols
                try:
                    print("\nUpdating exit levels for all positions...")
                    exit_manager.check_all_symbols()
                except Exception as exit_error:
                    error_msg = f"Error updating exit levels: {str(exit_error)}"
                    print(f"❌ {error_msg}")
                    send_discord_notification(f"⚠️ EXIT ERROR: {error_msg}")
                
                time.sleep(sleep_time)
                
            except Exception as cycle_error:
                # Handle errors in the main trading cycle
                error_msg = f"Error in main trading cycle: {str(cycle_error)}"
                print(f"❌ {error_msg}")
                print(f"Stack trace: {traceback.format_exc()}")
                send_discord_notification(f"⚠️ CYCLE ERROR: {error_msg}")
                
                # Try to reconnect to MT5 if needed
                if not check_connection():
                    print("Attempting to reconnect to MT5 after error...")
                    connect()
                
                # Wait before continuing
                print(f"Waiting {sleep_time} seconds before next cycle...")
                time.sleep(sleep_time)
            
    except KeyboardInterrupt:
        print("\nBot stopped manually.")
    except Exception as e:
        print(f"\nError occurred: {e}")
    finally:
        # Daily report
        send_discord_notification(
            f"📊 Daily Final Report\nProfit: ${pm.get_profit():.2f}"
        )
        shutdown()
        print("Bot shut down.")

if __name__ == "__main__":
    main()
