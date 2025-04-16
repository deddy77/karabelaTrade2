# profit_manager.py
from datetime import datetime, time
from config import DAILY_PROFIT_TARGET, DAILY_MAX_LOSS
from mt5_helper import send_discord_notification

class ProfitManager:
    def __init__(self):
        self.initial_balance = None
        self.current_day = None
        self.target_reached = False
        self.profit = 0
        
    def initialize_day(self, balance):
        self.initial_balance = balance
        self.current_day = datetime.now().date()
        self.target_reached = False
        print(f"\n📅 New trading day started | Target: +${DAILY_PROFIT_TARGET}")
        
    def update(self, current_balance):
        if datetime.now().date() != self.current_day:
            self.initialize_day(current_balance)
            
        self.profit = current_balance - self.initial_balance
        
        if not self.target_reached and self.profit >= DAILY_PROFIT_TARGET:
            self.target_reached = True
            send_discord_notification(f"🏆 DAILY TARGET REACHED! Profit: +${self.profit:.2f}")
        
        if self.profit <= DAILY_MAX_LOSS:
            send_discord_notification(f"🔻 MAX DAILY LOSS! Loss: ${abs(self.profit):.2f}")
            return False
            
        return True
    
    def get_profit(self):
        return self.profit

# Remove this line if present:
# pm = ProfitManager()  # DELETE THIS LINE