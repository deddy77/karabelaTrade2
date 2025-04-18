# exit_manager.py - Advanced exit strategy management for trading bot
import MetaTrader5 as mt5
import time
import pandas as pd
from datetime import datetime
from config import (
    SYMBOL, TIMEFRAME, MAGIC_NUMBER, SYMBOLS,
    USE_TRAILING_STOP, TRAILING_STOP_ACTIVATION_PIPS, TRAILING_STOP_DISTANCE_PIPS,
    USE_DYNAMIC_TP, DYNAMIC_TP_ATR_MULTIPLIER, CHECK_EXIT_INTERVAL
)
from mt5_helper import log_trade, send_discord_notification, get_historical_data

class ExitManager:
    def __init__(self):
        self.last_check_time = {}
        self.trailing_stops_active = {}
        self.highest_prices = {}
        self.lowest_prices = {}
        
        # Initialize tracking dictionaries for all symbols
        for symbol in SYMBOLS:
            self.last_check_time[symbol] = datetime.now()
            self.trailing_stops_active[symbol] = {}
            self.highest_prices[symbol] = {}
            self.lowest_prices[symbol] = {}
    
    def calculate_atr(self, symbol, period=14):
        """Calculate Average True Range for dynamic exit levels"""
        try:
            # Get historical data
            df = get_historical_data(symbol, TIMEFRAME, bars_count=period+10)
            if df is None or len(df) < period:
                print(f"Not enough data to calculate ATR for {symbol}")
                return None
                
            # Calculate True Range
            df['high_low'] = df['high'] - df['low']
            df['high_close'] = abs(df['high'] - df['close'].shift(1))
            df['low_close'] = abs(df['low'] - df['close'].shift(1))
            df['tr'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
            
            # Calculate ATR
            atr = df['tr'].rolling(period).mean().iloc[-1]
            return atr
        except Exception as e:
            print(f"Error calculating ATR for {symbol}: {str(e)}")
            return None
    
    def get_pip_value(self, symbol):
        """Get pip value for the symbol"""
        try:
            symbol_info = mt5.symbol_info(symbol)
            if not symbol_info:
                print(f"Failed to get symbol info for {symbol}")
                return 0.0001  # Default for most forex pairs
                
            point = symbol_info.point
            return point * 10 if not symbol.endswith("JPY") else point
        except Exception as e:
            print(f"Error getting pip value for {symbol}: {str(e)}")
            return 0.0001  # Default fallback
    
    def pips_to_price(self, symbol, pips):
        """Convert pips to price value"""
        return pips * self.get_pip_value(symbol)
    
    def price_to_pips(self, symbol, price_diff):
        """Convert price difference to pips"""
        return price_diff / self.get_pip_value(symbol)
    
    def should_check_exits(self, symbol):
        """Determine if it's time to check exit conditions for a symbol"""
        now = datetime.now()
        time_diff = (now - self.last_check_time.get(symbol, now)).total_seconds()
        return time_diff >= CHECK_EXIT_INTERVAL
    
    def update_trailing_stop(self, position, symbol, current_price):
        """Update trailing stop for a position if conditions are met"""
        if not USE_TRAILING_STOP:
            return False
            
        position_id = position.ticket
        position_type = position.type  # 0 for buy, 1 for sell
        
        # Get pip value for this symbol
        pip_value = self.get_pip_value(symbol)
        
        # Check if this is a new position we haven't tracked yet
        if position_id not in self.trailing_stops_active[symbol]:
            self.trailing_stops_active[symbol][position_id] = False
            if position_type == 0:  # Buy position
                self.highest_prices[symbol][position_id] = position.price_current
            else:  # Sell position
                self.lowest_prices[symbol][position_id] = position.price_current
        
        # For buy positions
        if position_type == 0:
            # Update highest price seen
            if current_price > self.highest_prices[symbol][position_id]:
                self.highest_prices[symbol][position_id] = current_price
            
            # Calculate profit in pips
            profit_pips = self.price_to_pips(symbol, current_price - position.price_open)
            
            # Check if trailing stop should be activated
            if not self.trailing_stops_active[symbol][position_id] and profit_pips >= TRAILING_STOP_ACTIVATION_PIPS:
                self.trailing_stops_active[symbol][position_id] = True
                activation_msg = f"Trailing stop activated for BUY {symbol} (#{position_id}) at {profit_pips:.1f} pips profit"
                print(activation_msg)
                log_trade(activation_msg)
                send_discord_notification(f"🔄 {activation_msg}")
            
            # Update trailing stop if active
            if self.trailing_stops_active[symbol][position_id]:
                # Calculate new stop loss level
                new_sl = self.highest_prices[symbol][position_id] - self.pips_to_price(symbol, TRAILING_STOP_DISTANCE_PIPS)
                
                # Only move stop loss up, never down
                if position.sl == 0 or new_sl > position.sl:
                    # Prepare modification request
                    request = {
                        "action": mt5.TRADE_ACTION_SLTP,
                        "position": position_id,
                        "symbol": symbol,
                        "sl": new_sl,
                        "tp": position.tp,  # Keep existing TP
                        "magic": MAGIC_NUMBER
                    }
                    
                    # Send modification request
                    result = mt5.order_send(request)
                    if result.retcode == mt5.TRADE_RETCODE_DONE:
                        update_msg = f"Updated trailing stop for BUY {symbol} (#{position_id}) to {new_sl:.5f}"
                        print(update_msg)
                        log_trade(update_msg)
                        return True
                    else:
                        print(f"Failed to update trailing stop: {result.comment}")
        
        # For sell positions
        elif position_type == 1:
            # Update lowest price seen
            if current_price < self.lowest_prices[symbol][position_id] or self.lowest_prices[symbol][position_id] == 0:
                self.lowest_prices[symbol][position_id] = current_price
            
            # Calculate profit in pips
            profit_pips = self.price_to_pips(symbol, position.price_open - current_price)
            
            # Check if trailing stop should be activated
            if not self.trailing_stops_active[symbol][position_id] and profit_pips >= TRAILING_STOP_ACTIVATION_PIPS:
                self.trailing_stops_active[symbol][position_id] = True
                activation_msg = f"Trailing stop activated for SELL {symbol} (#{position_id}) at {profit_pips:.1f} pips profit"
                print(activation_msg)
                log_trade(activation_msg)
                send_discord_notification(f"🔄 {activation_msg}")
            
            # Update trailing stop if active
            if self.trailing_stops_active[symbol][position_id]:
                # Calculate new stop loss level
                new_sl = self.lowest_prices[symbol][position_id] + self.pips_to_price(symbol, TRAILING_STOP_DISTANCE_PIPS)
                
                # Only move stop loss down, never up
                if position.sl == 0 or new_sl < position.sl:
                    # Prepare modification request
                    request = {
                        "action": mt5.TRADE_ACTION_SLTP,
                        "position": position_id,
                        "symbol": symbol,
                        "sl": new_sl,
                        "tp": position.tp,  # Keep existing TP
                        "magic": MAGIC_NUMBER
                    }
                    
                    # Send modification request
                    result = mt5.order_send(request)
                    if result.retcode == mt5.TRADE_RETCODE_DONE:
                        update_msg = f"Updated trailing stop for SELL {symbol} (#{position_id}) to {new_sl:.5f}"
                        print(update_msg)
                        log_trade(update_msg)
                        return True
                    else:
                        print(f"Failed to update trailing stop: {result.comment}")
        
        return False
    
    def update_dynamic_tp(self, position, symbol):
        """Update take profit based on market volatility (ATR)"""
        if not USE_DYNAMIC_TP:
            return False
            
        position_id = position.ticket
        position_type = position.type  # 0 for buy, 1 for sell
        
        # Calculate ATR
        atr = self.calculate_atr(symbol)
        if atr is None:
            return False
            
        # Calculate dynamic take profit based on ATR
        dynamic_tp_price = atr * DYNAMIC_TP_ATR_MULTIPLIER
        
        # Convert to price
        if position_type == 0:  # Buy position
            new_tp = position.price_open + dynamic_tp_price
        else:  # Sell position
            new_tp = position.price_open - dynamic_tp_price
        
        # Only update if new TP is more favorable than current TP
        # For buy: new TP should be higher than current TP
        # For sell: new TP should be lower than current TP
        should_update = False
        if position_type == 0 and (position.tp == 0 or new_tp > position.tp):
            should_update = True
        elif position_type == 1 and (position.tp == 0 or new_tp < position.tp):
            should_update = True
            
        if should_update:
            # Prepare modification request
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "position": position_id,
                "symbol": symbol,
                "sl": position.sl,  # Keep existing SL
                "tp": new_tp,
                "magic": MAGIC_NUMBER
            }
            
            # Send modification request
            result = mt5.order_send(request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                update_msg = f"Updated dynamic TP for {'BUY' if position_type == 0 else 'SELL'} {symbol} (#{position_id}) to {new_tp:.5f} (ATR: {atr:.5f})"
                print(update_msg)
                log_trade(update_msg)
                return True
            else:
                print(f"Failed to update dynamic TP: {result.comment}")
        
        return False
    
    def check_and_update_exits(self, symbol=SYMBOL):
        """Check and update exit levels for all positions of a symbol"""
        if not self.should_check_exits(symbol):
            return
            
        # Update last check time
        self.last_check_time[symbol] = datetime.now()
        
        # Get all positions for this symbol
        positions = mt5.positions_get(symbol=symbol)
        if positions is None or len(positions) == 0:
            # Clean up tracking dictionaries if no positions
            self.trailing_stops_active[symbol] = {}
            self.highest_prices[symbol] = {}
            self.lowest_prices[symbol] = {}
            return
            
        # Get current price
        tick = mt5.symbol_info_tick(symbol)
        if not tick:
            print(f"Failed to get current price for {symbol}")
            return
            
        # Process each position
        for position in positions:
            # Skip positions not created by our bot
            if position.magic != MAGIC_NUMBER:
                continue
                
            # Get current price based on position type
            current_price = tick.bid if position.type == 0 else tick.ask
            
            # Update trailing stop if enabled
            if USE_TRAILING_STOP:
                self.update_trailing_stop(position, symbol, current_price)
                
            # Update dynamic take profit if enabled
            if USE_DYNAMIC_TP:
                self.update_dynamic_tp(position, symbol)
    
    def check_all_symbols(self):
        """Check and update exit levels for all symbols"""
        for symbol in SYMBOLS:
            try:
                self.check_and_update_exits(symbol)
            except Exception as e:
                print(f"Error checking exits for {symbol}: {str(e)}")
                continue

# Create a global instance that can be imported from other modules
exit_manager = ExitManager()
