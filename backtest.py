# ================================
# ai-trading-bot/backtest.py
# ================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import os
import json
from tabulate import tabulate
import MetaTrader5 as mt5

from strategy import (
    calculate_ama, calculate_rsi, calculate_adx,
    detect_price_patterns
)
from mt5_helper import get_historical_data
from config import (
    SYMBOLS, TIMEFRAME, MA_MEDIUM, MA_LONG, 
    USE_ADAPTIVE_MA, AMA_FAST_EMA, AMA_SLOW_EMA,
    RSI_PERIOD, RSI_OVERBOUGHT, RSI_OVERSOLD, USE_RSI_FILTER,
    USE_PRICE_ACTION, USE_ADX_FILTER, ADX_PERIOD, ADX_THRESHOLD,
    MIN_AMA_GAP_PERCENT
)

class Trade:
    """Class to represent a single trade in the backtest"""
    def __init__(self, symbol, entry_time, entry_price, direction, lot_size, sl_price, tp_price):
        self.symbol = symbol
        self.entry_time = entry_time
        self.entry_price = entry_price
        self.direction = direction  # 'BUY' or 'SELL'
        self.lot_size = lot_size
        self.sl_price = sl_price
        self.tp_price = tp_price
        self.exit_time = None
        self.exit_price = None
        self.exit_reason = None  # 'TP', 'SL', 'EXIT_SIGNAL', 'MANUAL'
        self.profit_pips = None
        self.profit_money = None
        self.max_profit_pips = 0
        self.max_drawdown_pips = 0
        self.trade_duration = None
        
    def close_trade(self, exit_time, exit_price, exit_reason):
        """Close the trade and calculate profit/loss"""
        self.exit_time = exit_time
        self.exit_price = exit_price
        self.exit_reason = exit_reason
        
        # Calculate profit in pips
        pip_multiplier = 10000 if not self.symbol.endswith("JPY") else 100
        if self.direction == 'BUY':
            self.profit_pips = (exit_price - self.entry_price) * pip_multiplier
        else:  # SELL
            self.profit_pips = (self.entry_price - exit_price) * pip_multiplier
            
        # Calculate profit in money (assuming $10 per pip for 1.0 lot)
        pip_value = 10  # $10 per pip for 1.0 lot for major pairs
        self.profit_money = self.profit_pips * pip_value * self.lot_size
        
        # Calculate trade duration
        self.trade_duration = exit_time - self.entry_time
        
        return self.profit_pips, self.profit_money
        
    def update_trade_metrics(self, current_time, current_price):
        """Update max profit and drawdown metrics during trade"""
        pip_multiplier = 10000 if not self.symbol.endswith("JPY") else 100
        
        if self.direction == 'BUY':
            current_profit_pips = (current_price - self.entry_price) * pip_multiplier
        else:  # SELL
            current_profit_pips = (self.entry_price - current_price) * pip_multiplier
            
        # Update max profit
        if current_profit_pips > self.max_profit_pips:
            self.max_profit_pips = current_profit_pips
            
        # Update max drawdown (from peak profit)
        if current_profit_pips < self.max_profit_pips:
            current_drawdown = self.max_profit_pips - current_profit_pips
            if current_drawdown > self.max_drawdown_pips:
                self.max_drawdown_pips = current_drawdown
                
    def to_dict(self):
        """Convert trade to dictionary for serialization"""
        return {
            'symbol': self.symbol,
            'direction': self.direction,
            'entry_time': self.entry_time.strftime('%Y-%m-%d %H:%M:%S') if self.entry_time else None,
            'entry_price': self.entry_price,
            'exit_time': self.exit_time.strftime('%Y-%m-%d %H:%M:%S') if self.exit_time else None,
            'exit_price': self.exit_price,
            'exit_reason': self.exit_reason,
            'lot_size': self.lot_size,
            'sl_price': self.sl_price,
            'tp_price': self.tp_price,
            'profit_pips': self.profit_pips,
            'profit_money': self.profit_money,
            'max_profit_pips': self.max_profit_pips,
            'max_drawdown_pips': self.max_drawdown_pips,
            'trade_duration': str(self.trade_duration) if self.trade_duration else None
        }

class BacktestResult:
    """Class to store and analyze backtest results"""
    def __init__(self, symbol, timeframe, start_date, end_date, initial_balance, trades, equity_curve, parameters):
        self.symbol = symbol
        self.timeframe = timeframe
        self.start_date = start_date
        self.end_date = end_date
        self.initial_balance = initial_balance
        self.trades = trades
        self.equity_curve = equity_curve
        self.parameters = parameters
        
        # Calculate performance metrics
        self.calculate_metrics()
        
    def calculate_metrics(self):
        """Calculate performance metrics from trades"""
        if not self.trades:
            self.metrics = {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'avg_profit_pips': 0,
                'avg_loss_pips': 0,
                'profit_factor': 0,
                'total_profit_pips': 0,
                'total_profit_money': 0,
                'max_drawdown_pips': 0,
                'max_drawdown_percent': 0,
                'avg_trade_duration': timedelta(0)
            }
            return
            
        # Basic counts
        total_trades = len(self.trades)
        winning_trades = len([t for t in self.trades if t.profit_pips > 0])
        losing_trades = len([t for t in self.trades if t.profit_pips <= 0])
        
        # Win rate
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # Profit metrics
        if winning_trades > 0:
            avg_profit_pips = sum([t.profit_pips for t in self.trades if t.profit_pips > 0]) / winning_trades
        else:
            avg_profit_pips = 0
            
        if losing_trades > 0:
            avg_loss_pips = sum([abs(t.profit_pips) for t in self.trades if t.profit_pips <= 0]) / losing_trades
        else:
            avg_loss_pips = 0
            
        total_profit_pips = sum([t.profit_pips for t in self.trades])
        total_profit_money = sum([t.profit_money for t in self.trades])
        
        # Profit factor
        gross_profit = sum([t.profit_pips for t in self.trades if t.profit_pips > 0])
        gross_loss = sum([abs(t.profit_pips) for t in self.trades if t.profit_pips <= 0])
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Drawdown
        max_drawdown_pips = 0
        max_drawdown_percent = 0
        peak_equity = self.initial_balance
        
        for i, equity in enumerate(self.equity_curve['equity']):
            if equity > peak_equity:
                peak_equity = equity
            else:
                drawdown = peak_equity - equity
                drawdown_percent = (drawdown / peak_equity) * 100
                if drawdown_percent > max_drawdown_percent:
                    max_drawdown_percent = drawdown_percent
                    max_drawdown_pips = drawdown / 10  # Approximate conversion
        
        # Average trade duration
        durations = [t.trade_duration for t in self.trades if t.trade_duration is not None]
        avg_trade_duration = sum(durations, timedelta(0)) / len(durations) if durations else timedelta(0)
        
        # Store metrics
        self.metrics = {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'avg_profit_pips': avg_profit_pips,
            'avg_loss_pips': avg_loss_pips,
            'profit_factor': profit_factor,
            'total_profit_pips': total_profit_pips,
            'total_profit_money': total_profit_money,
            'max_drawdown_pips': max_drawdown_pips,
            'max_drawdown_percent': max_drawdown_percent,
            'avg_trade_duration': avg_trade_duration
        }
        
    def print_summary(self):
        """Print a summary of backtest results"""
        print("\n" + "="*50)
        print(f"BACKTEST RESULTS: {self.symbol} {self.timeframe}")
        print("="*50)
        print(f"Period: {self.start_date.strftime('%Y-%m-%d')} to {self.end_date.strftime('%Y-%m-%d')}")
        print(f"Initial Balance: ${self.initial_balance:.2f}")
        print(f"Final Balance: ${self.equity_curve['equity'].iloc[-1]:.2f}")
        print(f"Total Return: {((self.equity_curve['equity'].iloc[-1] - self.initial_balance) / self.initial_balance) * 100:.2f}%")
        print("-"*50)
        print(f"Total Trades: {self.metrics['total_trades']}")
        print(f"Winning Trades: {self.metrics['winning_trades']} ({self.metrics['win_rate']*100:.2f}%)")
        print(f"Losing Trades: {self.metrics['losing_trades']}")
        print(f"Profit Factor: {self.metrics['profit_factor']:.2f}")
        print(f"Total Profit: {self.metrics['total_profit_pips']:.2f} pips (${self.metrics['total_profit_money']:.2f})")
        print(f"Average Profit: {self.metrics['avg_profit_pips']:.2f} pips")
        print(f"Average Loss: {self.metrics['avg_loss_pips']:.2f} pips")
        print(f"Maximum Drawdown: {self.metrics['max_drawdown_percent']:.2f}%")
        print(f"Average Trade Duration: {self.metrics['avg_trade_duration']}")
        print("="*50)
        
    def plot_equity_curve(self, show_trades=True):
        """Plot equity curve and trades"""
        plt.figure(figsize=(12, 8))
        
        # Plot equity curve
        plt.subplot(2, 1, 1)
        plt.plot(self.equity_curve['time'], self.equity_curve['equity'], label='Equity')
        plt.title(f'Equity Curve - {self.symbol} {self.timeframe}')
        plt.ylabel('Equity ($)')
        plt.grid(True)
        plt.legend()
        
        # Format x-axis dates
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
        plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=7))  # Weekly ticks
        plt.gcf().autofmt_xdate()
        
        # Plot trades
        if show_trades and self.trades:
            plt.subplot(2, 1, 2)
            
            # Extract trade data
            trade_times = [t.exit_time for t in self.trades if t.exit_time is not None]
            trade_profits = [t.profit_pips for t in self.trades if t.exit_time is not None]
            
            # Color based on profit/loss
            colors = ['green' if p > 0 else 'red' for p in trade_profits]
            
            plt.bar(trade_times, trade_profits, color=colors, alpha=0.7)
            plt.title('Trade Results (pips)')
            plt.ylabel('Profit/Loss (pips)')
            plt.grid(True)
            
            # Format x-axis dates
            plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
            plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=7))  # Weekly ticks
            plt.gcf().autofmt_xdate()
        
        plt.tight_layout()
        
        # Create 'backtest_results' directory if it doesn't exist
        os.makedirs('backtest_results', exist_ok=True)
        
        # Save plot
        filename = f"backtest_results/{self.symbol}_{self.timeframe}_{self.start_date.strftime('%Y%m%d')}_{self.end_date.strftime('%Y%m%d')}.png"
        plt.savefig(filename)
        print(f"Equity curve saved to {filename}")
        
        plt.show()
        
    def save_results(self):
        """Save backtest results to file"""
        # Create 'backtest_results' directory if it doesn't exist
        os.makedirs('backtest_results', exist_ok=True)
        
        # Convert trades to dictionaries
        trade_dicts = [t.to_dict() for t in self.trades]
        
        # Convert equity curve to list of dictionaries
        equity_data = []
        for i, row in self.equity_curve.iterrows():
            equity_data.append({
                'time': row['time'].strftime('%Y-%m-%d %H:%M:%S'),
                'equity': row['equity']
            })
        
        # Create results dictionary
        results = {
            'symbol': self.symbol,
            'timeframe': self.timeframe,
            'start_date': self.start_date.strftime('%Y-%m-%d'),
            'end_date': self.end_date.strftime('%Y-%m-%d'),
            'initial_balance': self.initial_balance,
            'parameters': self.parameters,
            'metrics': {
                'total_trades': self.metrics['total_trades'],
                'winning_trades': self.metrics['winning_trades'],
                'losing_trades': self.metrics['losing_trades'],
                'win_rate': self.metrics['win_rate'],
                'avg_profit_pips': self.metrics['avg_profit_pips'],
                'avg_loss_pips': self.metrics['avg_loss_pips'],
                'profit_factor': self.metrics['profit_factor'],
                'total_profit_pips': self.metrics['total_profit_pips'],
                'total_profit_money': self.metrics['total_profit_money'],
                'max_drawdown_pips': self.metrics['max_drawdown_pips'],
                'max_drawdown_percent': self.metrics['max_drawdown_percent'],
                'avg_trade_duration': str(self.metrics['avg_trade_duration'])
            },
            'trades': trade_dicts,
            'equity_curve': equity_data
        }
        
        # Save to JSON file
        filename = f"backtest_results/{self.symbol}_{self.timeframe}_{self.start_date.strftime('%Y%m%d')}_{self.end_date.strftime('%Y%m%d')}.json"
        with open(filename, 'w') as f:
            json.dump(results, f, indent=4)
            
        print(f"Backtest results saved to {filename}")
        
        # Save trade list to CSV
        trade_df = pd.DataFrame(trade_dicts)
        csv_filename = f"backtest_results/{self.symbol}_{self.timeframe}_{self.start_date.strftime('%Y%m%d')}_{self.end_date.strftime('%Y%m%d')}_trades.csv"
        trade_df.to_csv(csv_filename, index=False)
        print(f"Trade list saved to {csv_filename}")

class Backtester:
    """Main backtesting class"""
    def __init__(self, symbol, timeframe, start_date, end_date, initial_balance=10000, lot_size=0.1):
        self.symbol = symbol
        self.timeframe = timeframe
        self.start_date = start_date
        self.end_date = end_date
        self.initial_balance = initial_balance
        self.lot_size = lot_size
        self.current_balance = initial_balance
        self.trades = []
        self.open_trades = []
        self.equity_curve = []
        
        # Strategy parameters (default to config values)
        self.parameters = {
            'ma_medium': MA_MEDIUM,
            'ma_long': MA_LONG,
            'use_adaptive_ma': USE_ADAPTIVE_MA,
            'ama_fast_ema': AMA_FAST_EMA,
            'ama_slow_ema': AMA_SLOW_EMA,
            'use_rsi_filter': USE_RSI_FILTER,
            'rsi_period': RSI_PERIOD,
            'rsi_overbought': RSI_OVERBOUGHT,
            'rsi_oversold': RSI_OVERSOLD,
            'use_price_action': USE_PRICE_ACTION,
            'use_adx_filter': USE_ADX_FILTER,
            'adx_period': ADX_PERIOD,
            'adx_threshold': ADX_THRESHOLD,
            'min_ama_gap_percent': MIN_AMA_GAP_PERCENT
        }
        
    def set_parameters(self, parameters):
        """Set strategy parameters for backtesting"""
        self.parameters.update(parameters)
        
    def prepare_data(self):
        """Fetch and prepare historical data for backtesting"""
        print(f"Fetching historical data for {self.symbol} {self.timeframe}...")
        
        # Get historical data
        df = get_historical_data(self.symbol, self.timeframe, bars_count=5000)
        if df is None or len(df) == 0:
            raise ValueError(f"No historical data available for {self.symbol} on {self.timeframe}")
            
        # Filter data by date range
        df['time'] = pd.to_datetime(df['time'])
        df = df[(df['time'] >= self.start_date) & (df['time'] <= self.end_date)]
        
        if len(df) == 0:
            raise ValueError(f"No data available for the specified date range")
            
        print(f"Loaded {len(df)} bars from {df['time'].min()} to {df['time'].max()}")
        
        # Calculate indicators
        if self.parameters['use_adaptive_ma']:
            df['ma_medium'] = calculate_ama(df, self.parameters['ma_medium'], 
                                           self.parameters['ama_fast_ema'], 
                                           self.parameters['ama_slow_ema'])
            df['ma_long'] = calculate_ama(df, self.parameters['ma_long'], 
                                         self.parameters['ama_fast_ema'], 
                                         self.parameters['ama_slow_ema'])
        else:
            df['ma_medium'] = df['close'].rolling(window=self.parameters['ma_medium']).mean()
            df['ma_long'] = df['close'].rolling(window=self.parameters['ma_long']).mean()
            
        if self.parameters['use_rsi_filter']:
            df['rsi'] = calculate_rsi(df, self.parameters['rsi_period'])
            
        if self.parameters['use_adx_filter']:
            df['adx'] = calculate_adx(df, self.parameters['adx_period'])
            
        # Drop NaN values
        df = df.dropna()
        
        return df
        
    def run_backtest(self):
        """Run the backtest"""
        print(f"Running backtest for {self.symbol} {self.timeframe}...")
        print(f"Period: {self.start_date} to {self.end_date}")
        print(f"Initial Balance: ${self.initial_balance}")
        
        # Prepare data
        df = self.prepare_data()
        
        # Initialize equity curve
        equity_data = {'time': [], 'equity': []}
        
        # Iterate through each bar
        for i in range(1, len(df)):
            current_bar = df.iloc[i]
            previous_bar = df.iloc[i-1]
            
            # Current time and price
            current_time = current_bar['time']
            current_price = current_bar['close']
            
            # Update open trades
            self.update_open_trades(current_time, current_bar)
            
            # Check for entry signals
            self.check_entry_signals(current_time, current_bar, previous_bar)
            
            # Check for exit signals
            self.check_exit_signals(current_time, current_bar, previous_bar)
            
            # Update equity curve
            equity_data['time'].append(current_time)
            equity_data['equity'].append(self.current_balance)
            
        # Close any remaining open trades at the end of the backtest
        final_bar = df.iloc[-1]
        for trade in self.open_trades[:]:
            self.close_trade(trade, final_bar['time'], final_bar['close'], 'END_OF_BACKTEST')
            
        # Create equity curve DataFrame
        equity_df = pd.DataFrame(equity_data)
        
        # Create backtest result
        result = BacktestResult(
            symbol=self.symbol,
            timeframe=self.timeframe,
            start_date=self.start_date,
            end_date=self.end_date,
            initial_balance=self.initial_balance,
            trades=self.trades,
            equity_curve=equity_df,
            parameters=self.parameters
        )
        
        return result
        
    def check_entry_signals(self, current_time, current_bar, previous_bar):
        """Check for entry signals based on strategy rules"""
        # Calculate the gap between AMA50 and AMA200 as a percentage
        ama_gap_percent = abs(current_bar['ma_medium'] - current_bar['ma_long']) / current_bar['ma_long'] * 100
        sufficient_gap = ama_gap_percent >= self.parameters['min_ama_gap_percent']
        
        # Debug print to see if we're getting close to generating signals
        if ama_gap_percent > (self.parameters['min_ama_gap_percent'] * 0.5):
            print(f"Time: {current_time}, Close: {current_bar['close']:.5f}, AMA Gap: {ama_gap_percent:.2f}%, " +
                  f"AMA50: {current_bar['ma_medium']:.5f}, AMA200: {current_bar['ma_long']:.5f}")
            
            # Print crossover status
            if current_bar['ma_medium'] > current_bar['ma_long'] and previous_bar['ma_medium'] <= previous_bar['ma_long']:
                print(f"POTENTIAL BUY SIGNAL: AMA50 crossed above AMA200")
            elif current_bar['ma_medium'] < current_bar['ma_long'] and previous_bar['ma_medium'] >= previous_bar['ma_long']:
                print(f"POTENTIAL SELL SIGNAL: AMA50 crossed below AMA200")
        
        # Check ADX if enabled
        adx_filter_passed = True
        if self.parameters['use_adx_filter'] and 'adx' in current_bar:
            adx_filter_passed = current_bar['adx'] >= self.parameters['adx_threshold']
            if ama_gap_percent > (self.parameters['min_ama_gap_percent'] * 0.5):
                print(f"ADX: {current_bar.get('adx', 'N/A')}, Filter passed: {adx_filter_passed}")
            
        # Check RSI if enabled
        rsi_filter_passed = True
        if self.parameters['use_rsi_filter'] and 'rsi' in current_bar:
            # For buy signals, RSI should be below overbought
            # For sell signals, RSI should be above oversold
            rsi_value = current_bar['rsi']
            rsi_buy_ok = rsi_value < self.parameters['rsi_overbought']
            rsi_sell_ok = rsi_value > self.parameters['rsi_oversold']
            if ama_gap_percent > (self.parameters['min_ama_gap_percent'] * 0.5):
                print(f"RSI: {rsi_value:.1f}, Buy OK: {rsi_buy_ok}, Sell OK: {rsi_sell_ok}")
            
        # BUY SIGNAL
        if (current_bar['ma_medium'] > current_bar['ma_long'] and 
            previous_bar['ma_medium'] <= previous_bar['ma_long'] and
            sufficient_gap and
            current_bar['close'] > current_bar['ma_medium'] and
            adx_filter_passed and
            (not self.parameters['use_rsi_filter'] or rsi_buy_ok)):
            
            # Calculate stop loss and take profit
            sl_pips = 20  # Default SL pips
            tp_pips = sl_pips * 2  # Default TP multiplier
            
            # Convert pips to price
            pip_value = 0.0001 if not self.symbol.endswith("JPY") else 0.01
            sl_price = current_bar['close'] - (sl_pips * pip_value)
            tp_price = current_bar['close'] + (tp_pips * pip_value)
            
            # Create and add trade
            trade = Trade(
                symbol=self.symbol,
                entry_time=current_time,
                entry_price=current_bar['close'],
                direction='BUY',
                lot_size=self.lot_size,
                sl_price=sl_price,
                tp_price=tp_price
            )
            
            self.open_trades.append(trade)
            
        # SELL SIGNAL
        elif (current_bar['ma_medium'] < current_bar['ma_long'] and 
              previous_bar['ma_medium'] >= previous_bar['ma_long'] and
              sufficient_gap and
              current_bar['close'] < current_bar['ma_medium'] and
              adx_filter_passed and
              (not self.parameters['use_rsi_filter'] or rsi_sell_ok)):
            
            # Calculate stop loss and take profit
            sl_pips = 20  # Default SL pips
            tp_pips = sl_pips * 2  # Default TP multiplier
            
            # Convert pips to price
            pip_value = 0.0001 if not self.symbol.endswith("JPY") else 0.01
            sl_price = current_bar['close'] + (sl_pips * pip_value)
            tp_price = current_bar['close'] - (tp_pips * pip_value)
            
            # Create and add trade
            trade = Trade(
                symbol=self.symbol,
                entry_time=current_time,
                entry_price=current_bar['close'],
                direction='SELL',
                lot_size=self.lot_size,
                sl_price=sl_price,
                tp_price=tp_price
            )
            
            self.open_trades.append(trade)
            
    def check_exit_signals(self, current_time, current_bar, previous_bar):
        """Check for exit signals based on strategy rules"""
        for trade in self.open_trades[:]:
            # Check for stop loss hit
            if trade.direction == 'BUY' and current_bar['low'] <= trade.sl_price:
                self.close_trade(trade, current_time, trade.sl_price, 'SL')
                continue
                
            if trade.direction == 'SELL' and current_bar['high'] >= trade.sl_price:
                self.close_trade(trade, current_time, trade.sl_price, 'SL')
                continue
                
            # Check for take profit hit
            if trade.direction == 'BUY' and current_bar['high'] >= trade.tp_price:
                self.close_trade(trade, current_time, trade.tp_price, 'TP')
                continue
                
            if trade.direction == 'SELL' and current_bar['low'] <= trade.tp_price:
                self.close_trade(trade, current_time, trade.tp_price, 'TP')
                continue
                
            # Check for exit signal (opposite crossover)
            if trade.direction == 'BUY' and current_bar['ma_medium'] < current_bar['ma_long'] and previous_bar['ma_medium'] >= previous_bar['ma_long']:
                self.close_trade(trade, current_time, current_bar['close'], 'EXIT_SIGNAL')
                continue
                
            if trade.direction == 'SELL' and current_bar['ma_medium'] > current_bar['ma_long'] and previous_bar['ma_medium'] <= previous_bar['ma_long']:
                self.close_trade(trade, current_time, current_bar['close'], 'EXIT_SIGNAL')
                continue
                
    def update_open_trades(self, current_time, current_bar):
        """Update metrics for open trades"""
        for trade in self.open_trades:
            trade.update_trade_metrics(current_time, current_bar['close'])
            
    def close_trade(self, trade, exit_time, exit_price, exit_reason):
        """Close a trade and update account balance"""
        # Close the trade
        profit_pips, profit_money = trade.close_trade(exit_time, exit_price, exit_reason)
        
        # Update account balance
        self.current_balance += profit_money
        
        # Move from open trades to completed trades
        self.open_trades.remove(trade)
        self.trades.append(trade)

def run_backtest_for_symbol(symbol, timeframe='M5', start_date=None, end_date=None, initial_balance=10000, lot_size=0.1, parameters=None):
    """Run a backtest for a single symbol with specified parameters"""
    # Set default dates if not provided
    if start_date is None:
        start_date = datetime.now() - timedelta(days=90)  # 90 days ago
    if end_date is None:
        end_date = datetime.now()
        
    # Create backtester
    backtester = Backtester(
        symbol=symbol,
        timeframe=timeframe,
        start_date=start_date,
        end_date=end_date,
        initial_balance=initial_balance,
        lot_size=lot_size
    )
    
    # Set custom parameters if provided
    if parameters:
        backtester.set_parameters(parameters)
        
    # Run backtest
    result = backtester.run_backtest()
    
    # Print summary
    result.print_summary()
    
    # Plot equity curve
    result.plot_equity_curve()
    
    # Save results
    result.save_results()
    
    return result

def run_parameter_optimization(symbol, parameter_ranges, timeframe='M5', start_date=None, end_date=None, initial_balance=10000, lot_size=0.1):
    """Run parameter optimization for a strategy"""
    # Set default dates if not provided
    if start_date is None:
        start_date = datetime.now() - timedelta(days=90)  # 90 days ago
    if end_date is None:
        end_date = datetime.now()
        
    print(f"Running parameter optimization for {symbol}...")
    print(f"Period: {start_date} to {end_date}")
    
    # Track best parameters and results
    best_result = None
    best_parameters = None
    best_profit = -float('inf')
    
    # Generate all parameter combinations
    import itertools
    param_names = list(parameter_ranges.keys())
    param_values = list(parameter_ranges.values())
    param_combinations = list(itertools.product(*param_values))
    
    print(f"Testing {len(param_combinations)} parameter combinations...")
    
    # Create results table
    results_table = []
    
    # Test each parameter combination
    for i, combination in enumerate(param_combinations):
        # Create parameters dictionary
        parameters = {param_names[j]: combination[j] for j in range(len(param_names))}
        
        print(f"\nTesting combination {i+1}/{len(param_combinations)}:")
        for param, value in parameters.items():
            print(f"  {param}: {value}")
        
        # Create backtester
        backtester = Backtester(
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            initial_balance=initial_balance,
            lot_size=lot_size
        )
        
        # Set parameters
        backtester.set_parameters(parameters)
        
        # Run backtest
        try:
            result = backtester.run_backtest()
            
            # Check if this is the best result so far
            if result.metrics['total_profit_money'] > best_profit:
                best_profit = result.metrics['total_profit_money']
                best_result = result
                best_parameters = parameters.copy()
                
            # Add to results table
            results_table.append([
                i+1,
                str(parameters),
                result.metrics['total_trades'],
                f"{result.metrics['win_rate']*100:.2f}%",
                result.metrics['profit_factor'],
                f"{result.metrics['total_profit_pips']:.2f}",
                f"${result.metrics['total_profit_money']:.2f}",
                f"{result.metrics['max_drawdown_percent']:.2f}%"
            ])
                
        except Exception as e:
            print(f"Error testing combination: {str(e)}")
            continue
    
    # Print results table
    print("\n" + "="*100)
    print("PARAMETER OPTIMIZATION RESULTS")
    print("="*100)
    
    headers = ["#", "Parameters", "Trades", "Win Rate", "Profit Factor", "Profit (pips)", "Profit ($)", "Max DD (%)"]
    print(tabulate(results_table, headers=headers, tablefmt="grid"))
    
    # Print best parameters
    if best_parameters:
        print("\n" + "="*50)
        print("BEST PARAMETERS:")
        print("="*50)
        for param, value in best_parameters.items():
            print(f"{param}: {value}")
        print(f"Profit: ${best_profit:.2f}")
        
        # Save best parameters to file
        os.makedirs('backtest_results', exist_ok=True)
        filename = f"backtest_results/{symbol}_{timeframe}_best_parameters.json"
        with open(filename, 'w') as f:
            json.dump(best_parameters, f, indent=4)
        print(f"Best parameters saved to {filename}")
        
        # Return best result and parameters
        return best_result, best_parameters
    else:
        print("No valid parameter combinations found.")
        return None, None

def run_multi_symbol_backtest(symbols=None, timeframe='M5', start_date=None, end_date=None, initial_balance=10000, lot_size=0.1, parameters=None):
    """Run backtest on multiple symbols"""
    if symbols is None:
        symbols = SYMBOLS
        
    # Set default dates if not provided
    if start_date is None:
        start_date = datetime.now() - timedelta(days=90)  # 90 days ago
    if end_date is None:
        end_date = datetime.now()
        
    print(f"Running multi-symbol backtest on {len(symbols)} symbols...")
    print(f"Period: {start_date} to {end_date}")
    
    # Track results for each symbol
    results = {}
    
    # Create results table
    results_table = []
    
    # Test each symbol
    for symbol in symbols:
        print(f"\nTesting {symbol}...")
        
        # Create backtester
        backtester = Backtester(
            symbol=symbol,
            timeframe=timeframe,
            start_date=start_date,
            end_date=end_date,
            initial_balance=initial_balance,
            lot_size=lot_size
        )
        
        # Set parameters if provided
        if parameters:
            backtester.set_parameters(parameters)
        
        # Run backtest
        try:
            result = backtester.run_backtest()
            results[symbol] = result
            
            # Add to results table
            results_table.append([
                symbol,
                result.metrics['total_trades'],
                f"{result.metrics['win_rate']*100:.2f}%",
                result.metrics['profit_factor'],
                f"{result.metrics['total_profit_pips']:.2f}",
                f"${result.metrics['total_profit_money']:.2f}",
                f"{result.metrics['max_drawdown_percent']:.2f}%"
            ])
                
        except Exception as e:
            print(f"Error testing {symbol}: {str(e)}")
            continue
    
    # Print results table
    print("\n" + "="*80)
    print("MULTI-SYMBOL BACKTEST RESULTS")
    print("="*80)
    
    headers = ["Symbol", "Trades", "Win Rate", "Profit Factor", "Profit (pips)", "Profit ($)", "Max DD (%)"]
    print(tabulate(results_table, headers=headers, tablefmt="grid"))
    
    # Calculate aggregate metrics
    total_trades = sum(r.metrics['total_trades'] for r in results.values())
    total_profit_pips = sum(r.metrics['total_profit_pips'] for r in results.values())
    total_profit_money = sum(r.metrics['total_profit_money'] for r in results.values())
    
    # Calculate aggregate win rate
    winning_trades = sum(r.metrics['winning_trades'] for r in results.values())
    aggregate_win_rate = winning_trades / total_trades if total_trades > 0 else 0
    
    # Calculate aggregate profit factor
    gross_profit = sum(sum(t.profit_pips for t in r.trades if t.profit_pips > 0) for r in results.values())
    gross_loss = sum(sum(abs(t.profit_pips) for t in r.trades if t.profit_pips <= 0) for r in results.values())
    aggregate_profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
    
    print("\n" + "="*50)
    print("AGGREGATE METRICS:")
    print("="*50)
    print(f"Total Trades: {total_trades}")
    print(f"Win Rate: {aggregate_win_rate*100:.2f}%")
    print(f"Profit Factor: {aggregate_profit_factor:.2f}")
    print(f"Total Profit: {total_profit_pips:.2f} pips (${total_profit_money:.2f})")
    print("="*50)
    
    return results

if __name__ == "__main__":
    # Example usage
    print("Backtesting Framework")
    print("1. Run backtest for a single symbol")
    print("2. Run parameter optimization")
    print("3. Run multi-symbol backtest")
    choice = input("Enter your choice (1-3): ")
    
    if choice == "1":
        symbol = input("Enter symbol (default: EURUSD): ") or "EURUSD"
        timeframe = input("Enter timeframe (default: M5): ") or "M5"
        days = int(input("Enter number of days to backtest (default: 90): ") or "90")
        start_date = datetime.now() - timedelta(days=days)
        
        run_backtest_for_symbol(symbol, timeframe, start_date)
        
    elif choice == "2":
        symbol = input("Enter symbol (default: EURUSD): ") or "EURUSD"
        timeframe = input("Enter timeframe (default: M5): ") or "M5"
        days = int(input("Enter number of days to backtest (default: 90): ") or "90")
        start_date = datetime.now() - timedelta(days=days)
        
        # Example parameter ranges
        parameter_ranges = {
            'ma_medium': [20, 50, 100],
            'ma_long': [100, 200, 300],
            'min_ama_gap_percent': [0.03, 0.05, 0.1],
            'adx_threshold': [20, 25, 30]
        }
        
        run_parameter_optimization(symbol, parameter_ranges, timeframe, start_date)
        
    elif choice == "3":
        timeframe = input("Enter timeframe (default: M5): ") or "M5"
        days = int(input("Enter number of days to backtest (default: 90): ") or "90")
        start_date = datetime.now() - timedelta(days=days)
        
        run_multi_symbol_backtest(timeframe=timeframe, start_date=start_date)
        
    else:
        print("Invalid choice")
