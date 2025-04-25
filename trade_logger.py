import os
import json
from datetime import datetime
import pandas as pd
from typing import Dict, List, Optional

class TradeLogger:
    def __init__(self, log_file="logs/trade_history.json"):
        self.log_file = log_file
        os.makedirs(os.path.dirname(log_file), exist_ok=True)
        
        # Initialize empty log if file doesn't exist
        if not os.path.exists(log_file):
            with open(log_file, 'w') as f:
                json.dump([], f)

    def log_trade_entry(self, symbol: str, direction: str, entry_price: float,
                       size: float, sl_pips: int, tp_pips: int, strategy: str) -> None:
        """Log a new trade entry with all relevant details"""
        trade = {
            'symbol': symbol,
            'direction': direction,
            'entry_time': datetime.now().isoformat(),
            'entry_price': entry_price,
            'size': size,
            'stop_loss_pips': sl_pips,
            'take_profit_pips': tp_pips,
            'strategy': strategy,
            'exit_time': None,
            'exit_price': None,
            'profit_loss': None,
            'status': 'OPEN'
        }
        
        self._append_trade(trade)

    def log_trade_exit(self, symbol: str, exit_price: float) -> None:
        """Log a trade exit and calculate P&L"""
        trades = self._load_trades()
        
        # Find most recent OPEN trade for this symbol
        open_trades = [t for t in trades 
                      if t['symbol'] == symbol and t['status'] == 'OPEN']
        
        if not open_trades:
            return
            
        trade = open_trades[-1]  # Get most recent open trade
        trade['exit_time'] = datetime.now().isoformat()
        trade['exit_price'] = exit_price
        trade['status'] = 'CLOSED'
        
        # Calculate P&L
        if trade['direction'] == 'BUY':
            trade['profit_loss'] = (exit_price - trade['entry_price']) * trade['size']
        else:  # SELL
            trade['profit_loss'] = (trade['entry_price'] - exit_price) * trade['size']
            
        self._update_trade(trade)

    def get_trade_history(self, symbol: Optional[str] = None) -> List[Dict]:
        """Get all trades or filter by symbol"""
        trades = self._load_trades()
        if symbol:
            return [t for t in trades if t['symbol'] == symbol]
        return trades

    def calculate_performance(self, symbol: Optional[str] = None) -> Dict:
        """Calculate performance metrics for all trades or specific symbol"""
        trades = self.get_trade_history(symbol)
        if not trades:
            return {}
            
        closed_trades = [t for t in trades if t['status'] == 'CLOSED']
        open_trades = [t for t in trades if t['status'] == 'OPEN']
        
        # Basic metrics
        total_trades = len(closed_trades)
        winning_trades = len([t for t in closed_trades if t['profit_loss'] > 0])
        losing_trades = total_trades - winning_trades
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        # Profit metrics
        total_profit = sum(t['profit_loss'] for t in closed_trades if t['profit_loss'] > 0)
        total_loss = abs(sum(t['profit_loss'] for t in closed_trades if t['profit_loss'] < 0))
        profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
        
        # Risk metrics
        avg_risk = sum(t['stop_loss_pips'] for t in closed_trades) / total_trades if total_trades > 0 else 0
        avg_reward = sum(t['take_profit_pips'] for t in closed_trades) / total_trades if total_trades > 0 else 0
        risk_reward = avg_reward / avg_risk if avg_risk > 0 else 0
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'total_profit': total_profit,
            'total_loss': total_loss,
            'profit_factor': profit_factor,
            'avg_risk_pips': avg_risk,
            'avg_reward_pips': avg_reward,
            'risk_reward_ratio': risk_reward,
            'open_trades': len(open_trades)
        }

    def generate_report(self) -> str:
        """Generate a formatted performance report"""
        metrics = self.calculate_performance()
        
        report = [
            "=== Trading Performance Report ===",
            f"Total Trades: {metrics['total_trades']}",
            f"Winning Trades: {metrics['winning_trades']}",
            f"Losing Trades: {metrics['losing_trades']}",
            f"Win Rate: {metrics['win_rate']:.1%}",
            f"Total Profit: ${metrics['total_profit']:,.2f}",
            f"Total Loss: ${metrics['total_loss']:,.2f}",
            f"Profit Factor: {metrics['profit_factor']:.2f}",
            f"Avg Risk (pips): {metrics['avg_risk_pips']:.1f}",
            f"Avg Reward (pips): {metrics['avg_reward_pips']:.1f}",
            f"Risk/Reward Ratio: 1:{metrics['risk_reward_ratio']:.2f}",
            f"Open Trades: {metrics['open_trades']}"
        ]
        
        return "\n".join(report)

    def _load_trades(self) -> List[Dict]:
        """Load all trades from log file"""
        try:
            with open(self.log_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _append_trade(self, trade: Dict) -> None:
        """Add a new trade to the log"""
        trades = self._load_trades()
        trades.append(trade)
        self._save_trades(trades)

    def _update_trade(self, updated_trade: Dict) -> None:
        """Update an existing trade in the log"""
        trades = self._load_trades()
        for i, trade in enumerate(trades):
            if (trade['symbol'] == updated_trade['symbol'] and 
                trade['entry_time'] == updated_trade['entry_time']):
                trades[i] = updated_trade
                break
        self._save_trades(trades)

    def _save_trades(self, trades: List[Dict]) -> None:
        """Save all trades to log file"""
        with open(self.log_file, 'w') as f:
            json.dump(trades, f, indent=2)

# Global logger instance
logger = TradeLogger()

def log_trade_entry(symbol: str, direction: str, entry_price: float,
                   size: float, sl_pips: int, tp_pips: int, strategy: str) -> None:
    """Convenience function to log trade entries"""
    logger.log_trade_entry(symbol, direction, entry_price, size, sl_pips, tp_pips, strategy)

def log_trade_exit(symbol: str, exit_price: float) -> None:
    """Convenience function to log trade exits"""
    logger.log_trade_exit(symbol, exit_price)

def get_performance_report() -> str:
    """Get formatted performance report"""
    return logger.generate_report()
