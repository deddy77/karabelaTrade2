# ================================
# ai-trading-bot/run_backtest.py
# ================================

from datetime import datetime, timedelta
from backtest import (
    run_backtest_for_symbol,
    run_parameter_optimization,
    run_multi_symbol_backtest
)
from config import SYMBOLS

def main():
    """Main function to run backtesting"""
    print("=" * 50)
    print("FOREX TRADING BOT BACKTESTING")
    print("=" * 50)
    
    print("\nSelect an option:")
    print("1. Run backtest for a single symbol")
    print("2. Run parameter optimization")
    print("3. Run multi-symbol backtest")
    print("4. Run walk-forward analysis")
    
    choice = input("\nEnter your choice (1-4): ")
    
    # Default settings
    default_timeframe = "M5"
    default_days = 90
    default_symbol = "EURUSD"
    
    if choice == "1":
        # Single symbol backtest
        symbol = input(f"Enter symbol (default: {default_symbol}): ") or default_symbol
        timeframe = input(f"Enter timeframe (default: {default_timeframe}): ") or default_timeframe
        days = int(input(f"Enter number of days to backtest (default: {default_days}): ") or default_days)
        start_date = datetime.now() - timedelta(days=days)
        
        print(f"\nRunning backtest for {symbol} on {timeframe} timeframe...")
        print(f"Period: {start_date.strftime('%Y-%m-%d')} to {datetime.now().strftime('%Y-%m-%d')}")
        
        run_backtest_for_symbol(symbol, timeframe, start_date)
        
    elif choice == "2":
        # Parameter optimization
        symbol = input(f"Enter symbol (default: {default_symbol}): ") or default_symbol
        timeframe = input(f"Enter timeframe (default: {default_timeframe}): ") or default_timeframe
        days = int(input(f"Enter number of days to backtest (default: {default_days}): ") or default_days)
        start_date = datetime.now() - timedelta(days=days)
        
        print("\nSelect parameters to optimize:")
        print("1. Moving Average periods")
        print("2. AMA gap percentage")
        print("3. ADX threshold")
        print("4. RSI settings")
        print("5. All parameters")
        
        param_choice = input("\nEnter your choice (1-5): ")
        
        # Define parameter ranges based on user choice
        if param_choice == "1":
            parameter_ranges = {
                'ma_medium': [20, 50, 100],
                'ma_long': [100, 200, 300]
            }
        elif param_choice == "2":
            parameter_ranges = {
                'min_ama_gap_percent': [0.03, 0.05, 0.07, 0.1]
            }
        elif param_choice == "3":
            parameter_ranges = {
                'adx_threshold': [15, 20, 25, 30, 35]
            }
        elif param_choice == "4":
            parameter_ranges = {
                'rsi_period': [7, 14, 21],
                'rsi_overbought': [65, 70, 75, 80],
                'rsi_oversold': [20, 25, 30, 35]
            }
        else:  # All parameters
            parameter_ranges = {
                'ma_medium': [20, 50, 100],
                'ma_long': [100, 200, 300],
                'min_ama_gap_percent': [0.03, 0.05, 0.1],
                'adx_threshold': [20, 25, 30],
                'rsi_period': [7, 14, 21],
                'rsi_overbought': [70, 80],
                'rsi_oversold': [20, 30]
            }
        
        print(f"\nRunning parameter optimization for {symbol} on {timeframe} timeframe...")
        print(f"Period: {start_date.strftime('%Y-%m-%d')} to {datetime.now().strftime('%Y-%m-%d')}")
        print("Parameters to optimize:", parameter_ranges.keys())
        
        run_parameter_optimization(symbol, parameter_ranges, timeframe, start_date)
        
    elif choice == "3":
        # Multi-symbol backtest
        symbols_input = input(f"Enter symbols separated by comma (default: all configured symbols): ")
        if symbols_input:
            symbols = [s.strip() for s in symbols_input.split(",")]
        else:
            symbols = SYMBOLS
            
        timeframe = input(f"Enter timeframe (default: {default_timeframe}): ") or default_timeframe
        days = int(input(f"Enter number of days to backtest (default: {default_days}): ") or default_days)
        start_date = datetime.now() - timedelta(days=days)
        
        print(f"\nRunning multi-symbol backtest on {len(symbols)} symbols...")
        print(f"Symbols: {', '.join(symbols)}")
        print(f"Period: {start_date.strftime('%Y-%m-%d')} to {datetime.now().strftime('%Y-%m-%d')}")
        
        run_multi_symbol_backtest(symbols, timeframe, start_date)
        
    elif choice == "4":
        # Walk-forward analysis
        symbol = input(f"Enter symbol (default: {default_symbol}): ") or default_symbol
        timeframe = input(f"Enter timeframe (default: {default_timeframe}): ") or default_timeframe
        total_days = int(input(f"Enter total number of days to analyze (default: 180): ") or 180)
        window_days = int(input(f"Enter window size in days (default: 30): ") or 30)
        
        # Calculate start date for the entire analysis
        total_start_date = datetime.now() - timedelta(days=total_days)
        
        print(f"\nRunning walk-forward analysis for {symbol} on {timeframe} timeframe...")
        print(f"Total period: {total_start_date.strftime('%Y-%m-%d')} to {datetime.now().strftime('%Y-%m-%d')}")
        print(f"Window size: {window_days} days")
        
        # Define parameter ranges for optimization
        parameter_ranges = {
            'ma_medium': [20, 50, 100],
            'ma_long': [100, 200, 300],
            'min_ama_gap_percent': [0.03, 0.05, 0.1],
            'adx_threshold': [20, 25, 30]
        }
        
        # Track results for each window
        window_results = []
        
        # Iterate through time windows
        for i in range(0, total_days - window_days, window_days):
            window_start = total_start_date + timedelta(days=i)
            window_end = window_start + timedelta(days=window_days)
            
            print(f"\nWindow {i//window_days + 1}: {window_start.strftime('%Y-%m-%d')} to {window_end.strftime('%Y-%m-%d')}")
            
            # Optimization phase (in-sample)
            print("Optimization phase (in-sample)...")
            best_result, best_parameters = run_parameter_optimization(
                symbol, 
                parameter_ranges, 
                timeframe, 
                window_start, 
                window_end
            )
            
            if best_parameters:
                # Validation phase (out-of-sample)
                validation_start = window_end
                validation_end = validation_start + timedelta(days=window_days)
                if validation_end > datetime.now():
                    validation_end = datetime.now()
                    
                print(f"Validation phase (out-of-sample): {validation_start.strftime('%Y-%m-%d')} to {validation_end.strftime('%Y-%m-%d')}")
                
                validation_result = run_backtest_for_symbol(
                    symbol,
                    timeframe,
                    validation_start,
                    validation_end,
                    parameters=best_parameters
                )
                
                # Store results
                window_results.append({
                    'window': i//window_days + 1,
                    'in_sample_period': f"{window_start.strftime('%Y-%m-%d')} to {window_end.strftime('%Y-%m-%d')}",
                    'out_of_sample_period': f"{validation_start.strftime('%Y-%m-%d')} to {validation_end.strftime('%Y-%m-%d')}",
                    'best_parameters': best_parameters,
                    'in_sample_profit': best_result.metrics['total_profit_money'],
                    'out_of_sample_profit': validation_result.metrics['total_profit_money'],
                    'in_sample_trades': best_result.metrics['total_trades'],
                    'out_of_sample_trades': validation_result.metrics['total_trades'],
                    'in_sample_win_rate': best_result.metrics['win_rate'],
                    'out_of_sample_win_rate': validation_result.metrics['win_rate']
                })
        
        # Print summary of walk-forward analysis
        print("\n" + "=" * 80)
        print("WALK-FORWARD ANALYSIS SUMMARY")
        print("=" * 80)
        
        for result in window_results:
            print(f"\nWindow {result['window']}:")
            print(f"In-sample period: {result['in_sample_period']}")
            print(f"Out-of-sample period: {result['out_of_sample_period']}")
            print(f"Best parameters: {result['best_parameters']}")
            print(f"In-sample profit: ${result['in_sample_profit']:.2f} ({result['in_sample_trades']} trades, {result['in_sample_win_rate']*100:.2f}% win rate)")
            print(f"Out-of-sample profit: ${result['out_of_sample_profit']:.2f} ({result['out_of_sample_trades']} trades, {result['out_of_sample_win_rate']*100:.2f}% win rate)")
        
        # Calculate overall performance
        total_out_of_sample_profit = sum(r['out_of_sample_profit'] for r in window_results)
        total_out_of_sample_trades = sum(r['out_of_sample_trades'] for r in window_results)
        
        print("\n" + "=" * 50)
        print("OVERALL OUT-OF-SAMPLE PERFORMANCE:")
        print("=" * 50)
        print(f"Total profit: ${total_out_of_sample_profit:.2f}")
        print(f"Total trades: {total_out_of_sample_trades}")
        print("=" * 50)
        
    else:
        print("Invalid choice")

if __name__ == "__main__":
    main()
