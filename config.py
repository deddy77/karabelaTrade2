# ================================
# Trading Strategy Configuration
# ================================

# Trading settings for multiple symbols
SYMBOLS = ["EURUSD",]  # Trade all major pairs
TIMEFRAME = "M5"  # Primary timeframe for execution

# Moving Average settings
USE_ADAPTIVE_MA = True
MA_MEDIUM = 50  # Medium line (AMA50)
MA_LONG = 200  # Long line (AMA200)
PRIMARY_SIGNAL = "AMA_CROSS"  # Use AMA200/AMA50 cross as primary signal

# Adaptive MA settings
AMA_FAST_EMA = 2
AMA_SLOW_EMA = 30

# Risk Management
MIN_LOT = 0.01  # Smallest allowed lot size
MAX_LOT = 10.0  # Largest allowed lot size
DEFAULT_RISK_PERCENT = 1.0  # 1% of balance risked per trade
DEFAULT_TP_MULTIPLIER = 2.0  # Take profit as multiple of stop loss (fallback)
DEFAULT_TP_PIPS = 5  # Fixed take profit in pips (override multiplier if set)

# Daily settings
DAILY_PROFIT_TARGET = 50  # Stop when $50 profit made
DAILY_MAX_LOSS = -30      # Optional: Stop if $30 loss
RESET_TIME = "00:00"      # Daily reset time (HH:MM)

# Symbol-specific settings
SYMBOL_SETTINGS = {
    "EURUSD": {"MAX_SPREAD": 40, "TP_MULTIPLIER": 2.0},
    "GBPUSD": {"MAX_SPREAD": 60, "TP_MULTIPLIER": 2.0},
    "USDCAD": {"MAX_SPREAD": 50, "TP_MULTIPLIER": 2.0},
    "AUDUSD": {"MAX_SPREAD": 60, "TP_MULTIPLIER": 2.0},
    "USDCHF": {"MAX_SPREAD": 60, "TP_MULTIPLIER": 2.0},
}

# Common settings
MAGIC_NUMBER = 123456
SLIPPAGE = 100

# Trading hours (Sunday 5PM to Friday 5PM EST)
MARKET_OPEN_DAY = 6  # Sunday
MARKET_CLOSE_DAY = 4  # Friday
MARKET_OPEN_HOUR = 17  # 5PM

# News Avoidance Settings
MINUTES_BEFORE_NEWS = 30  # Avoid trading 30 minutes before high impact news
MINUTES_AFTER_NEWS = 60   # Avoid trading 60 minutes after high impact news
NEWS_CHECK_INTERVAL = 5   # Check for news every 5 minutes

# Discord notification
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1359973769204203591/pKz6EZE353Q4scGiHYGJPI4nm7vlt8rMjPnWZmW8S1M_9kc7UOIFQv6y0oSEgn4-TQDw"

# Logging
LOG_FILE = "logs/trade_log.txt"

# For backward compatibility (use first symbol as default)
SYMBOL = SYMBOLS[0]
