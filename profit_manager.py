# profit_manager.py
from datetime import datetime, time
from config import (
    DAILY_PROFIT_TARGET, DAILY_MAX_LOSS, MAX_TOTAL_LOSS,
    EVALUATION_MIN_DAYS, ACCOUNT_SIZE, PAYOUT_CYCLE_DAYS
)
from mt5_helper import send_discord_notification

class ProfitManager:
    def __init__(self):
        self.initial_balance = None
        self.highest_balance = None
        self.current_day = None
        self.target_reached = False
        self.profit = 0
        self.trading_days = 0
        self.total_drawdown = 0
        self.start_date = None
        
    def initialize_day(self, balance):
        current_date = datetime.now().date()
        
        # First time initialization
        if self.start_date is None:
            self.start_date = current_date
            self.initial_balance = balance
            self.highest_balance = balance
            print(f"\n🚀 Challenge Started | Initial Balance: ${balance:.2f}")
            print(f"📊 Targets: +${DAILY_PROFIT_TARGET:.2f} profit | -${abs(DAILY_MAX_LOSS):.2f} max daily loss")
            
        # New day initialization
        if self.current_day != current_date:
            self.current_day = current_date
            self.target_reached = False
            self.trading_days += 1
            print(f"\n📅 Trading Day {self.trading_days} | Balance: ${balance:.2f}")
            
            if self.trading_days <= EVALUATION_MIN_DAYS:
                print(f"📋 Evaluation Period: Day {self.trading_days}/{EVALUATION_MIN_DAYS}")
        
    def update(self, current_balance):
        # Initialize or update day
        if datetime.now().date() != self.current_day:
            self.initialize_day(current_balance)
            
        self.profit = current_balance - self.initial_balance
        
        # Update highest balance
        if current_balance > self.highest_balance:
            self.highest_balance = current_balance
        
        # Calculate drawdown from highest balance
        self.total_drawdown = ((current_balance - self.highest_balance) / self.highest_balance) * 100
        
        # Check evaluation period
        in_evaluation = self.trading_days <= EVALUATION_MIN_DAYS
        
        # Daily profit target check
        if not self.target_reached and self.profit >= DAILY_PROFIT_TARGET:
            self.target_reached = True
            send_discord_notification(f"🏆 DAILY TARGET REACHED! Profit: +${self.profit:.2f}")
            
        # Check various stop conditions
        if self.profit <= DAILY_MAX_LOSS:
            send_discord_notification(f"🔻 MAX DAILY LOSS REACHED! Loss: ${abs(self.profit):.2f}")
            return False
            
        if self.total_drawdown <= MAX_TOTAL_LOSS:
            send_discord_notification(f"⛔ MAX TOTAL DRAWDOWN REACHED! Drawdown: {self.total_drawdown:.2f}%")
            return False
            
        # Log status
        print(f"\nStatus Update:")
        print(f"Total Profit: ${self.profit:.2f} ({(self.profit/self.initial_balance)*100:.1f}%)")
        print(f"Max Drawdown: {self.total_drawdown:.1f}%")
        print(f"Trading Days: {self.trading_days}")
        if in_evaluation:
            print(f"Evaluation Period: {self.trading_days}/{EVALUATION_MIN_DAYS} days")
            
        return True
    
    def get_profit(self):
        return self.profit

# Remove this line if present:
# pm = ProfitManager()  # DELETE THIS LINE
