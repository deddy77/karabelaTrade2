import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import queue
import os
import sys
from datetime import datetime
import MetaTrader5 as mt5
import pandas as pd
from mt5_helper import (
    connect, check_connection, shutdown, get_positions,
    get_historical_data, check_market_conditions, close_all_positions
)
from profit_manager import update_positions, get_profit_manager
from risk_manager import get_current_leverage_usage, calculate_lot_size
from session_manager import SessionManager
from market_diagnostics import run_full_diagnostics
from discord_notify import test_discord_notification
from strategy_runner import StrategyRunner
from chart_display import create_analysis_window
from config import (
    SYMBOL, TIMEFRAME, DISCORD_WEBHOOK_URL, ENABLE_DISCORD_NOTIFICATIONS,
    SYMBOL_SETTINGS
)

class TradingBotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("KarabelaTrade Bot Control")
        self.root.geometry("1200x800")  # Increased size for more content
        
        # Initialize variables
        self.is_running = False
        self.log_queue = queue.Queue()
        self.bot_thread = None
        self.diagnostics_data = None
        self.session_manager = SessionManager()
        self.strategy_runner = StrategyRunner(log_callback=self.log)
        
        # Create main notebook (tabbed interface)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create tabs
        self.create_control_tab()
        self.create_sessions_tab()
        self.create_positions_tab()
        self.create_diagnostics_tab()
        self.create_analysis_tab()
        self.create_settings_tab()
        
        # Start update timers
        self.check_logs()
        self.update_status_timer()
    
    def create_control_tab(self):
        """Create the main control tab"""
        control_frame = ttk.Frame(self.notebook)
        self.notebook.add(control_frame, text="Control Panel")
        
        # Top control panel
        controls = ttk.LabelFrame(control_frame, text="Bot Controls")
        controls.pack(fill=tk.X, padx=5, pady=5)
        
        # Start Button
        self.start_button = ttk.Button(
            controls, text="Start Bot", command=self.start_bot)
        self.start_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Stop Button
        self.stop_button = ttk.Button(
            controls, text="Stop Bot", command=self.stop_bot, 
            state=tk.DISABLED)
        self.stop_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Status Label
        self.status_label = ttk.Label(
            controls, text="Status: Stopped", foreground="red")
        self.status_label.pack(side=tk.LEFT, padx=20)
        
        # Account info panel
        account_frame = ttk.LabelFrame(control_frame, text="Account Information")
        account_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.account_label = ttk.Label(account_frame, 
            text="Account: Not Connected")
        self.account_label.pack(anchor=tk.W, padx=5, pady=2)
        
        self.balance_label = ttk.Label(account_frame, 
            text="Balance: --")
        self.balance_label.pack(anchor=tk.W, padx=5, pady=2)
        
        self.equity_label = ttk.Label(account_frame, 
            text="Equity: --")
        self.equity_label.pack(anchor=tk.W, padx=5, pady=2)
        
        self.leverage_label = ttk.Label(account_frame, 
            text="Leverage Usage: --")
        self.leverage_label.pack(anchor=tk.W, padx=5, pady=2)
        
        # Log viewer
        log_frame = ttk.LabelFrame(control_frame, text="Log Viewer")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.log_display = scrolledtext.ScrolledText(
            log_frame, wrap=tk.WORD, width=70, height=20)
        self.log_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.clear_button = ttk.Button(
            log_frame, text="Clear Logs", command=self.clear_logs)
        self.clear_button.pack(anchor=tk.E, padx=5, pady=5)
    
    def create_sessions_tab(self):
        """Create the trading sessions tab"""
        sessions_frame = ttk.Frame(self.notebook)
        self.notebook.add(sessions_frame, text="Trading Sessions")
        
        # Session status
        status_frame = ttk.LabelFrame(sessions_frame, text="Active Sessions")
        status_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.session_labels = {}
        for session in ["SYDNEY", "TOKYO", "LONDON", "NEWYORK"]:
            label = ttk.Label(status_frame, 
                text=f"{session}: Inactive", foreground="gray")
            label.pack(anchor=tk.W, padx=5, pady=2)
            self.session_labels[session] = label
            
        # Overlap periods
        overlap_frame = ttk.LabelFrame(sessions_frame, text="Overlap Periods")
        overlap_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.overlap_labels = {}
        for overlap in ["SYDNEY-TOKYO", "TOKYO-LONDON", "LONDON-NEWYORK"]:
            label = ttk.Label(overlap_frame, 
                text=f"{overlap}: Inactive", foreground="gray")
            label.pack(anchor=tk.W, padx=5, pady=2)
            self.overlap_labels[overlap] = label
        
        # Pair status table
        pairs_frame = ttk.LabelFrame(sessions_frame, text="Tradeable Pairs")
        pairs_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        columns = ("Pair", "Session", "Priority", "Status", "Spread")
        self.pairs_tree = ttk.Treeview(pairs_frame, columns=columns, 
            show="headings")
        
        for col in columns:
            self.pairs_tree.heading(col, text=col)
            self.pairs_tree.column(col, width=100)
            
        self.pairs_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def create_positions_tab(self):
        """Create the positions management tab"""
        positions_frame = ttk.Frame(self.notebook)
        self.notebook.add(positions_frame, text="Open Positions")
        
        columns = ("Ticket", "Symbol", "Type", "Volume", "Price", 
            "SL", "TP", "Profit", "Swap", "Time")
        self.positions_tree = ttk.Treeview(
            positions_frame, columns=columns, show="headings")
        
        for col in columns:
            self.positions_tree.heading(col, text=col)
            self.positions_tree.column(col, width=100)
            
        self.positions_tree.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        controls_frame = ttk.Frame(positions_frame)
        controls_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Button(controls_frame, text="Close Selected", 
            command=self.close_selected_position).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Close All", 
            command=self.close_all_positions).pack(side=tk.LEFT, padx=5)
        ttk.Button(controls_frame, text="Refresh", 
            command=self.refresh_positions).pack(side=tk.LEFT, padx=5)
    
    def create_diagnostics_tab(self):
        """Create the diagnostics tab"""
        diagnostics_frame = ttk.Frame(self.notebook)
        self.notebook.add(diagnostics_frame, text="Diagnostics")
        
        # Market conditions
        market_frame = ttk.LabelFrame(diagnostics_frame, text="Market Conditions")
        market_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.market_health_label = ttk.Label(market_frame, 
            text="Market Health: --")
        self.market_health_label.pack(anchor=tk.W, padx=5, pady=2)
        
        self.spread_label = ttk.Label(market_frame, 
            text="Current Spread: --")
        self.spread_label.pack(anchor=tk.W, padx=5, pady=2)
        
        # Risk metrics
        risk_frame = ttk.LabelFrame(diagnostics_frame, text="Risk Metrics")
        risk_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.leverage_usage_label = ttk.Label(risk_frame, 
            text="Current Leverage: --")
        self.leverage_usage_label.pack(anchor=tk.W, padx=5, pady=2)
        
        self.drawdown_label = ttk.Label(risk_frame, 
            text="Max Drawdown: --")
        self.drawdown_label.pack(anchor=tk.W, padx=5, pady=2)
        
        # Analysis output
        analysis_frame = ttk.LabelFrame(diagnostics_frame, text="Analysis")
        analysis_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.analysis_text = scrolledtext.ScrolledText(
            analysis_frame, wrap=tk.WORD, width=70, height=20)
        self.analysis_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    def create_analysis_tab(self):
        """Create the pair analysis tab"""
        analysis_frame = ttk.Frame(self.notebook)
        self.notebook.add(analysis_frame, text="Analysis")
        
        # Create pair selector and controls
        control_frame = ttk.Frame(analysis_frame)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(control_frame, text="Select Pair:").pack(side=tk.LEFT, padx=5)
        self.pair_var = tk.StringVar()
        self.pair_combo = ttk.Combobox(control_frame, 
            textvariable=self.pair_var, state="readonly")
        self.pair_combo.pack(side=tk.LEFT, padx=5)
        
        refresh_btn = ttk.Button(control_frame, text="Refresh", 
            command=self.refresh_analysis)
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        show_chart_btn = ttk.Button(control_frame, text="Show Chart", 
            command=self.show_detailed_chart)
        show_chart_btn.pack(side=tk.LEFT, padx=5)
        
        # Create analysis text display
        report_frame = ttk.LabelFrame(analysis_frame, text="Analysis Report")
        report_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.analysis_display = scrolledtext.ScrolledText(
            report_frame, wrap=tk.WORD, width=70, height=30)
        self.analysis_display.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Bind pair selection
        self.pair_combo.bind('<<ComboboxSelected>>', self.on_pair_selected)
    
    def create_settings_tab(self):
        """Create the settings tab"""
        settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(settings_frame, text="Settings")
        
        # Notifications section
        notif_frame = ttk.LabelFrame(settings_frame, text="Notifications")
        notif_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.notif_enabled = tk.BooleanVar(value=ENABLE_DISCORD_NOTIFICATIONS)
        self.notif_checkbox = ttk.Checkbutton(
            notif_frame, text="Enable Discord Notifications",
            variable=self.notif_enabled)
        self.notif_checkbox.pack(anchor=tk.W, padx=5, pady=2)
        
        webhook_frame = ttk.Frame(notif_frame)
        webhook_frame.pack(fill=tk.X, padx=5, pady=2)
        
        ttk.Label(webhook_frame, text="Webhook URL:").pack(side=tk.LEFT)
        self.webhook_entry = ttk.Entry(webhook_frame, width=50)
        self.webhook_entry.pack(side=tk.LEFT, padx=5)
        self.webhook_entry.insert(0, DISCORD_WEBHOOK_URL)
        
        self.test_notif_button = ttk.Button(
            webhook_frame, text="Test", command=self.test_notifications)
        self.test_notif_button.pack(side=tk.LEFT, padx=5)
    
    def update_status_timer(self):
        """Update status every second"""
        if self.is_running:
            self.update_status()
            self.update_sessions()
            self.update_positions()
            
        self.root.after(1000, self.update_status_timer)
    
    def update_status(self):
        """Update all status displays"""
        try:
            if mt5.initialize():
                # Update account info
                account_info = mt5.account_info()
                if account_info:
                    self.account_label.config(
                        text=f"Account: {account_info.login} ({account_info.server})")
                    self.balance_label.config(
                        text=f"Balance: ${account_info.balance:.2f}")
                    self.equity_label.config(
                        text=f"Equity: ${account_info.equity:.2f}")
                    
                    # Update leverage usage
                    leverage = get_current_leverage_usage()
                    self.leverage_label.config(
                        text=f"Leverage Usage: {leverage:.1f}x")
                    
                # Update pair statuses in the pairs tree
                self.pairs_tree.delete(*self.pairs_tree.get_children())
                for pair in self.strategy_runner.active_pairs:
                    status = self.strategy_runner.get_pair_status(pair)
                    self.pairs_tree.insert("", "end", values=(
                        pair,
                        status.get("session", "--"),
                        status.get("priority", "--"),
                        status.get("status", "--"),
                        status.get("spread", "--")
                    ))
                    
                # Update analysis if a pair is selected
                if self.pair_var.get():
                    self.on_pair_selected(None)
                    
        except Exception as e:
            self.log(f"Error updating status: {str(e)}")
    
    def update_sessions(self):
        """Update session status displays"""
        try:
            current_time = datetime.now()
            
            # Update regular sessions
            active_sessions = self.session_manager.get_active_sessions(current_time)
            for session, label in self.session_labels.items():
                is_active = session in active_sessions
                label.config(
                    text=f"{session}: {'Active' if is_active else 'Inactive'}",
                    foreground="green" if is_active else "gray")
            
            # Update overlap periods
            active_overlaps = self.session_manager.get_active_overlaps(current_time)
            for overlap, label in self.overlap_labels.items():
                is_active = overlap in active_overlaps
                label.config(
                    text=f"{overlap}: {'Active' if is_active else 'Inactive'}",
                    foreground="green" if is_active else "gray")
                
        except Exception as e:
            self.log(f"Error updating sessions: {str(e)}")
    
    def update_positions(self):
        """Update positions display"""
        try:
            self.positions_tree.delete(*self.positions_tree.get_children())
            for pair in self.strategy_runner.active_pairs:
                positions = get_positions(pair)
                for pos in positions:
                    self.positions_tree.insert("", "end", values=(
                        pos.ticket,
                        pos.symbol,
                        "BUY" if pos.type == mt5.ORDER_TYPE_BUY else "SELL",
                        pos.volume,
                        pos.price_open,
                        pos.sl,
                        pos.tp,
                        pos.profit,
                        pos.swap,
                        datetime.fromtimestamp(pos.time).strftime("%Y-%m-%d %H:%M:%S")
                    ))
        except Exception as e:
            self.log(f"Error updating positions: {str(e)}")
    
    def refresh_analysis(self):
        """Refresh the analysis display"""
        # Update pair list
        active_pairs = self.strategy_runner.get_active_pairs()
        self.pair_combo['values'] = active_pairs
        
        # Update current pair analysis
        self.on_pair_selected(None)
    
    def on_pair_selected(self, event):
        """Handle pair selection"""
        pair = self.pair_var.get()
        if not pair:
            return
            
        # Get and display analysis
        report = self.strategy_runner.format_analysis_report(pair)
        self.analysis_display.delete(1.0, tk.END)
        self.analysis_display.insert(tk.END, report)
    
    def show_detailed_chart(self):
        """Show detailed chart analysis window"""
        pair = self.pair_var.get()
        if not pair:
            messagebox.showwarning("Warning", "Please select a pair first")
            return
        
        # Get latest data for the pair
        df = get_historical_data(pair, TIMEFRAME, bars_count=200)
        analysis = self.strategy_runner.get_analysis(pair)
        
        if df is not None and 'technical' in analysis:
            window = create_analysis_window(df, analysis['technical'], pair)
            window.transient(self.root)  # Make window modal
            window.focus_set()
        else:
            messagebox.showerror("Error", "Failed to get chart data")
    
    def close_selected_position(self):
        """Close the selected position"""
        selected = self.positions_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "No position selected")
            return
            
        item = self.positions_tree.item(selected[0])
        symbol = item["values"][1]
        ticket = item["values"][0]
        
        if messagebox.askyesno("Confirm", f"Close position {ticket} for {symbol}?"):
            close_all_positions(symbol)
            self.refresh_positions()
    
    def close_all_positions(self):
        """Close all open positions"""
        if messagebox.askyesno("Confirm", "Close all positions?"):
            for pair in self.strategy_runner.active_pairs:
                close_all_positions(pair)
            self.refresh_positions()
    
    def refresh_positions(self):
        """Refresh the positions display"""
        self.update_positions()
    
    def start_bot(self):
        """Start the trading bot"""
        if not self.is_running:
            if not connect():
                messagebox.showerror("Error", "Failed to connect to MetaTrader 5")
                return
            
            self.log("Running initial diagnostics...")
            
            # Start the strategy runner
            self.strategy_runner.start()
            
            self.is_running = True
            self.start_button.config(state=tk.DISABLED)
            self.stop_button.config(state=tk.NORMAL)
            self.status_label.config(text="Status: Running", foreground="green")
            
            self.log("Bot started successfully")
            self.update_status()
            
            # Initialize analysis tab
            self.refresh_analysis()
    
    def stop_bot(self):
        """Stop the trading bot"""
        if self.is_running:
            self.is_running = False
            self.start_button.config(state=tk.NORMAL)
            self.stop_button.config(state=tk.DISABLED)
            self.status_label.config(text="Status: Stopped", foreground="red")
            
            # Stop the strategy runner
            self.strategy_runner.stop()
            shutdown()
            
            self.log("Bot stopped")
    
    def test_notifications(self):
        """Test Discord notifications"""
        global ENABLE_DISCORD_NOTIFICATIONS, DISCORD_WEBHOOK_URL
        ENABLE_DISCORD_NOTIFICATIONS = self.notif_enabled.get()
        DISCORD_WEBHOOK_URL = self.webhook_entry.get()
        
        if test_discord_notification():
            messagebox.showinfo("Success", "Discord notification test successful!")
        else:
            messagebox.showerror(
                "Error", 
                "Failed to send Discord notification. Check your settings.")
    
    def log(self, message):
        """Add a message to the log queue"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_queue.put(f"[{timestamp}] {message}")
    
    def check_logs(self):
        """Check for new log messages and display them"""
        while not self.log_queue.empty():
            message = self.log_queue.get()
            self.log_display.insert(tk.END, message + "\n")
            self.log_display.see(tk.END)
        
        self.root.after(100, self.check_logs)
    
    def clear_logs(self):
        """Clear the log display"""
        self.log_display.delete(1.0, tk.END)

def main():
    root = tk.Tk()
    app = TradingBotGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
