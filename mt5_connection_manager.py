import time
import MetaTrader5 as mt5
import os
from datetime import datetime
from discord_notify import send_discord_notification

class MT5ConnectionManager:
    def __init__(self, check_interval=300, max_reconnect_attempts=5):
        """
        Initialize the MT5 connection manager.
        
        Args:
            check_interval (int): Time between connection checks in seconds (default: 300s/5min)
            max_reconnect_attempts (int): Maximum number of reconnection attempts before giving up
        """
        self.check_interval = check_interval
        self.last_check_time = 0
        self.connection_state = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = max_reconnect_attempts
        self.backoff_times = [10, 30, 60, 120, 300]  # seconds
        self.connection_events = []
        self.log_file = "logs/connection_log.txt"
        
        # Create logs directory if it doesn't exist
        os.makedirs(os.path.dirname(self.log_file), exist_ok=True)
        
    def check_connection(self, force=False):
        """
        Check if MT5 is connected and the connection is healthy.
        
        Args:
            force (bool): Force a connection check regardless of the check interval
            
        Returns:
            bool: True if connected and healthy, False otherwise
        """
        current_time = time.time()
        if force or (current_time - self.last_check_time) >= self.check_interval:
            self.last_check_time = current_time
            
            # Check if MT5 is initialized
            if not mt5.initialize():
                self.log_connection_event("MT5 not initialized")
                self.connection_state = False
                self.attempt_reconnect()
                return False
                
            # Check if terminal is connected
            if not mt5.terminal_info().connected:
                self.log_connection_event("MT5 terminal not connected")
                self.connection_state = False
                self.attempt_reconnect()
                return False
                
            # Verify connection is actually working with a simple data request
            try:
                # Try to get account info as a basic check
                account_info = mt5.account_info()
                if account_info is None:
                    raise Exception("Failed to get account info")
                    
                # Try to get symbol info as an additional check
                symbol_info = mt5.symbol_info("EURUSD")
                if symbol_info is None:
                    raise Exception("Failed to get symbol info")
                    
                # Connection is healthy
                self.connection_state = True
                self.reconnect_attempts = 0
                return True
                
            except Exception as e:
                self.log_connection_event(f"MT5 connection check failed: {e}")
                self.connection_state = False
                self.attempt_reconnect()
                return False
                
        return self.connection_state
        
    def attempt_reconnect(self):
        """
        Attempt to reconnect to MT5 with exponential backoff.
        
        Returns:
            bool: True if reconnection was successful, False otherwise
        """
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            self.log_connection_event("Maximum reconnection attempts reached")
            send_discord_notification("⚠️ MT5 CONNECTION CRITICAL: Maximum reconnection attempts reached")
            return False
              
        backoff_time = self.backoff_times[min(self.reconnect_attempts, len(self.backoff_times)-1)]
        self.log_connection_event(f"Attempting to reconnect (attempt {self.reconnect_attempts+1}) after {backoff_time}s")
        time.sleep(backoff_time)
        
        # Shutdown MT5 if it's already initialized
        mt5.shutdown()
        time.sleep(1)
        
        # Try to initialize MT5
        if not mt5.initialize():
            self.reconnect_attempts += 1
            error_code = mt5.last_error()
            self.log_connection_event(f"MT5 reconnection failed: Error code {error_code}")
            return False
        
        # Check if we can get account info
        account_info = mt5.account_info()
        if account_info is None:
            self.reconnect_attempts += 1
            self.log_connection_event("MT5 reconnection failed: Could not get account info")
            return False
            
        # Reconnection successful
        self.log_connection_event("MT5 reconnection successful")
        send_discord_notification("✅ MT5 connection restored")
        self.connection_state = True
        self.reconnect_attempts = 0
        return True
        
    def log_connection_event(self, message):
        """
        Log a connection event to the connection log file and store in memory.
        
        Args:
            message (str): The message to log
        """
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} - {message}"
        
        # Store in memory
        self.connection_events.append(log_entry)
        if len(self.connection_events) > 100:  # Keep only the last 100 events
            self.connection_events = self.connection_events[-100:]
            
        # Write to log file
        with open(self.log_file, "a") as f:
            f.write(f"{log_entry}\n")
            
        # Print to console
        print(f"CONNECTION: {log_entry}")
        
    def get_connection_status_report(self):
        """
        Get a report of the connection status.
        
        Returns:
            str: A report of the connection status
        """
        status = "Connected" if self.connection_state else "Disconnected"
        last_check = datetime.fromtimestamp(self.last_check_time).strftime("%Y-%m-%d %H:%M:%S")
        
        report = f"MT5 Connection Status: {status}\n"
        report += f"Last Check: {last_check}\n"
        report += f"Reconnection Attempts: {self.reconnect_attempts}/{self.max_reconnect_attempts}\n"
        
        if len(self.connection_events) > 0:
            report += "\nRecent Connection Events:\n"
            for event in self.connection_events[-5:]:  # Show last 5 events
                report += f"- {event}\n"
                
        return report
