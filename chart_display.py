"""Chart display module for technical analysis visualization"""
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import mplfinance as mpf
import pandas as pd
from datetime import datetime, timedelta

class ChartDisplay:
    def __init__(self, frame):
        self.frame = frame
        self.current_pair = None
        self.figure = plt.Figure(figsize=(12, 6), dpi=100)
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.figure, master=frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(fill='both', expand=True)
        
        # Configure subplots
        self.price_ax = self.figure.add_subplot(211)  # Price chart
        self.indicator_ax = self.figure.add_subplot(212)  # Indicators
        
        self.figure.tight_layout()
    
    def plot_data(self, df, analysis_results=None):
        """Plot candlestick chart with technical indicators"""
        if df is None or len(df) == 0:
            return
            
        # Clear previous plots
        self.price_ax.clear()
        self.indicator_ax.clear()
        
        # Convert time column if needed
        if not isinstance(df.index, pd.DatetimeIndex):
            df.set_index('time', inplace=True)
        
        # Plot candlestick chart
        mpf.plot(df, type='candle', style='charles',
                title=f'{self.current_pair} Price Chart',
                ax=self.price_ax, volume=False)
        
        # Add moving averages if available
        if analysis_results and 'moving_averages' in analysis_results:
            ma_data = analysis_results['moving_averages']
            periods = [20, 50, 200]  # Standard MA periods
            colors = ['blue', 'red', 'green']
            
            for period, color in zip(periods, colors):
                ma = df['close'].rolling(window=period).mean()
                self.price_ax.plot(df.index, ma, 
                    label=f'MA{period}', color=color, alpha=0.7)
        
        # Add support/resistance levels if available
        if analysis_results and 'support_resistance' in analysis_results:
            sr_data = analysis_results['support_resistance']
            if 'support' in sr_data and sr_data['support']:
                self.price_ax.axhline(y=sr_data['support'], 
                    color='green', linestyle='--', alpha=0.5, label='Support')
            if 'resistance' in sr_data and sr_data['resistance']:
                self.price_ax.axhline(y=sr_data['resistance'], 
                    color='red', linestyle='--', alpha=0.5, label='Resistance')
        
        # Plot RSI
        if analysis_results and 'rsi' in analysis_results:
            rsi_data = df['close'].diff()
            gain = (rsi_data.where(rsi_data > 0, 0)).rolling(window=14).mean()
            loss = (-rsi_data.where(rsi_data < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            rsi = 100 - (100 / (1 + rs))
            
            self.indicator_ax.plot(df.index, rsi, label='RSI', color='purple')
            self.indicator_ax.axhline(y=70, color='red', linestyle='--', alpha=0.5)
            self.indicator_ax.axhline(y=30, color='green', linestyle='--', alpha=0.5)
            self.indicator_ax.set_ylim(0, 100)
            self.indicator_ax.set_ylabel('RSI')
        
        # Add volume bars at the bottom
        volume_data = df['tick_volume']
        normalized_volume = volume_data * (df['close'].mean() / volume_data.mean())
        self.indicator_ax.bar(df.index, normalized_volume, 
            alpha=0.3, color='gray', label='Volume')
        
        # Add legends
        self.price_ax.legend(loc='upper left')
        self.indicator_ax.legend(loc='upper left')
        
        # Format axes
        self.price_ax.grid(True, alpha=0.3)
        self.indicator_ax.grid(True, alpha=0.3)
        
        # Rotate x-axis labels for better readability
        for ax in [self.price_ax, self.indicator_ax]:
            ax.tick_params(axis='x', rotation=45)
        
        self.figure.tight_layout()
        self.canvas.draw()
    
    def update_pair(self, pair, df=None, analysis_results=None):
        """Update the chart for a new pair"""
        self.current_pair = pair
        if df is not None:
            self.plot_data(df, analysis_results)
    
    def clear(self):
        """Clear the chart"""
        self.price_ax.clear()
        self.indicator_ax.clear()
        self.canvas.draw()

def create_analysis_window(df, analysis_results, pair):
    """Create a popup window with detailed analysis charts"""
    import tkinter as tk
    from tkinter import ttk
    
    window = tk.Toplevel()
    window.title(f"Technical Analysis - {pair}")
    window.geometry("1000x800")
    
    frame = ttk.Frame(window)
    frame.pack(fill='both', expand=True)
    
    chart = ChartDisplay(frame)
    chart.update_pair(pair, df, analysis_results)
    
    # Add control panel below chart
    control_frame = ttk.Frame(window)
    control_frame.pack(fill='x', padx=5, pady=5)
    
    # Add timeframe selector
    ttk.Label(control_frame, text="Timeframe:").pack(side='left', padx=5)
    timeframes = ['M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1']
    tf_combo = ttk.Combobox(control_frame, values=timeframes, state='readonly')
    tf_combo.set('M5')
    tf_combo.pack(side='left', padx=5)
    
    # Add indicators selector
    ttk.Label(control_frame, text="Indicators:").pack(side='left', padx=5)
    indicators = ['MA', 'RSI', 'Volume', 'Support/Resistance']
    for indicator in indicators:
        var = tk.BooleanVar(value=True)
        ttk.Checkbutton(control_frame, text=indicator, 
            variable=var).pack(side='left', padx=5)
    
    return window
