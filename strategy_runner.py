"""Strategy runner for managing trading strategies across multiple pairs"""
import threading
import queue
from datetime import datetime
import MetaTrader5 as mt5
from mt5_helper import (
    get_historical_data, check_market_conditions,
    has_buy_position, has_sell_position,
    open_buy_order, open_sell_order, close_all_positions
)
from session_manager import SessionManager
from risk_manager import calculate_lot_size
from market_diagnostics import run_full_diagnostics
from technical_analysis import run_technical_analysis, format_analysis_report
from discord_notify import send_discord_notification

class StrategyRunner:
    def __init__(self, log_callback=None):
        self.session_manager = SessionManager()
        self.log_callback = log_callback
        self.is_running = False
        self.active_pairs = {}
        self.analysis_results = {}
        self.message_queue = queue.Queue()
        self.strategy_threads = {}
        
    def log(self, message):
        """Log messages using callback if available"""
        if self.log_callback:
            self.log_callback(message)
        else:
            print(message)
            
    def start(self):
        """Start the strategy runner"""
        if self.is_running:
            return
            
        self.is_running = True
        self.active_pairs = {
            pair: {
                "spread": 0,
                "positions": 0,
                "status": "Initializing",
                "last_analysis": None,
                "market_conditions": []
            } for pair in self.session_manager.get_all_tradeable_pairs()
        }
        
        # Start individual strategy threads for each pair
        for pair in self.active_pairs:
            thread = threading.Thread(
                target=self.run_pair_strategy,
                args=(pair,),
                daemon=True
            )
            self.strategy_threads[pair] = thread
            thread.start()
            
        self.log("Strategy runner started")
        
    def stop(self):
        """Stop the strategy runner"""
        if not self.is_running:
            return
            
        self.is_running = False
        self.log("Stopping strategy runner...")
        
        # Wait for all threads to complete
        for pair, thread in self.strategy_threads.items():
            thread.join(timeout=5.0)
            if thread.is_alive():
                self.log(f"Warning: Strategy thread for {pair} is still running")
                
        self.strategy_threads.clear()
        self.log("Strategy runner stopped")
        
    def run_pair_strategy(self, pair):
        """Run strategy for a single pair"""
        while self.is_running:
            try:
                # Get current session priority
                current_time = datetime.now()
                status = self.session_manager.get_pair_priority(pair, current_time)
                self.active_pairs[pair]["status"] = status["priority"]
                
                # Skip if pair shouldn't be traded in current session
                if not status["priority_level"] > 0:
                    self.active_pairs[pair]["market_conditions"] = ["Inactive Session"]
                    threading.Event().wait(60)
                    continue
                    
                # Run market diagnostics
                diagnostics = run_full_diagnostics(pair)
                if not diagnostics["is_healthy"]:
                    self.active_pairs[pair].update({
                        "status": "Market conditions unsuitable",
                        "market_conditions": diagnostics["market"]["messages"]
                    })
                    threading.Event().wait(60)
                    continue
                    
                # Get historical data
                df = get_historical_data(pair, status["timeframe"], bars_count=200)
                if df is None:
                    self.active_pairs[pair]["status"] = "Failed to get market data"
                    threading.Event().wait(60)
                    continue
                
                # Run technical analysis
                analysis = run_technical_analysis(df)
                if analysis:
                    self.analysis_results[pair] = analysis
                    self.active_pairs[pair].update({
                        "last_analysis": current_time,
                        "market_conditions": analysis["market_conditions"]
                    })
                    
                    # Log significant market conditions
                    if analysis["market_conditions"] != ["Normal Trading Conditions"]:
                        conditions = ", ".join(analysis["market_conditions"])
                        self.log(f"{pair}: {conditions}")
                
                # Calculate lot size based on risk parameters
                lot_size = calculate_lot_size(
                    balance=diagnostics["account"]["data"]["balance"],
                    risk_percent=status["effective_risk_percent"],
                    stop_loss_pips=20,  # Default value, should be calculated based on ATR
                    pip_value=diagnostics["market"]["data"].get("pip_value", 10)
                )
                
                # Store analysis results
                self.analysis_results[pair] = {
                    "time": current_time,
                    "session": status["active_sessions"],
                    "timeframe": status["timeframe"],
                    "risk_percent": status["effective_risk_percent"],
                    "lot_size": lot_size,
                    "diagnostics": diagnostics,
                    "technical": analysis
                }
                
                # Update pair status
                self.active_pairs[pair].update({
                    "spread": diagnostics["market"]["data"].get("spread", 0),
                    "status": f"Monitoring ({status['priority']})"
                })
                
                # Wait before next update
                threading.Event().wait(60)
                
            except Exception as e:
                self.log(f"Error in strategy for {pair}: {str(e)}")
                self.active_pairs[pair]["status"] = f"Error: {str(e)}"
                threading.Event().wait(60)
                
    def get_pair_status(self, pair):
        """Get current status for a pair"""
        return self.active_pairs.get(pair, {})
        
    def get_analysis(self, pair):
        """Get latest analysis results for a pair"""
        return self.analysis_results.get(pair, {})
        
    def get_active_pairs(self):
        """Get list of currently active pairs"""
        return [
            pair for pair, data in self.active_pairs.items()
            if "Error" not in data.get("status", "")
        ]
        
    def format_analysis_report(self, pair):
        """Format analysis results for display"""
        analysis = self.get_analysis(pair)
        if not analysis:
            return f"No analysis available for {pair}"
            
        report = [
            f"=== Analysis Report for {pair} ===",
            f"Time: {analysis['time'].strftime('%Y-%m-%d %H:%M:%S')}",
            f"Session: {', '.join(analysis['session'])}",
            f"Timeframe: {analysis['timeframe']}",
            f"Risk: {analysis['risk_percent']:.2f}%",
            f"Lot Size: {analysis['lot_size']:.2f}",
            "\nDiagnostics:",
            "Market Health: " + ("✓" if analysis['diagnostics']['market']['is_healthy'] else "⚠"),
            "Account Health: " + ("✓" if analysis['diagnostics']['account']['is_healthy'] else "⚠"),
            "Trading Health: " + ("✓" if analysis['diagnostics']['trading']['is_healthy'] else "⚠")
        ]
        
        # Add technical analysis if available
        if analysis.get('technical'):
            report.append("\nTechnical Analysis:")
            report.extend([
                "Market Conditions:",
                "- " + "\n- ".join(analysis['technical']['market_conditions']),
                f"\nTrend: {analysis['technical']['trend']['trend']} "
                f"(Strength: {analysis['technical']['trend']['strength']:.2f}%)",
                f"RSI: {analysis['technical']['rsi']['RSI']:.2f} "
                f"({analysis['technical']['rsi']['RSI_condition']})",
                f"Volume: {analysis['technical']['volume']['volume_trend']} "
                f"({analysis['technical']['volume']['volume_ratio']:.2f}x avg)",
                f"Volatility: {analysis['technical']['volatility']['conditions']['state']} "
                f"({analysis['technical']['volatility']['conditions']['trend']})"
            ])
            
        # Add any warning messages
        warnings = []
        for category in ['market', 'account', 'trading']:
            warnings.extend(analysis['diagnostics'][category]['messages'])
        
        if warnings:
            report.append("\nWarnings:")
            for warning in warnings:
                report.append(f"⚠ {warning}")
                
        return "\n".join(report)
