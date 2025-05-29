# Trading Settings
SYMBOL = "EURUSD"  # Default trading symbol
TIMEFRAME = "M5"   # Default timeframe

# Moving Average Settings
MA_MEDIUM = 50     # AMA50
MA_LONG = 200      # AMA200
AMA_FAST_EMA = 2   # Fast EMA period for AMA
AMA_SLOW_EMA = 30  # Slow EMA period for AMA

# MT5 Settings
MAGIC_NUMBER = 123456  # Unique identifier for this bot's trades
SLIPPAGE = 20         # Maximum allowed slippage in points

# Position Size Limits
MIN_LOT = 0.01        # Minimum lot size allowed
MAX_LOT = 10.0        # Maximum lot size allowed
LEVERAGE_LIMIT = 30   # Maximum allowed leverage (e.g., 30:1)

# Trading Limits
DAILY_PROFIT_TARGET = 150.0  # Daily profit target: 10% of $5,000
DAILY_MAX_LOSS = -200.0      # Maximum daily loss: 4% of $5,000
MAX_TOTAL_LOSS = -6.0        # Maximum total drawdown percentage: 6%

# Account Settings
ACCOUNT_SIZE = 5000.0        # Blueberry Funded account size
RISK_PER_TRADE = 1.0         # Risk percentage per trade (1.0 = 1%)
DEFAULT_RISK_PERCENT = 1.0    # Default risk if not specified
MAX_SPREAD = 20              # Maximum allowed spread in points

# Evaluation Settings
EVALUATION_MIN_DAYS = 3      # Blueberry minimum trading days for evaluation
PAYOUT_CYCLE_DAYS = 14       # Blueberry payout frequency

# File Paths
LOG_FILE = "logs/trades.log"

# Discord Notifications
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1359973769204203591/pKz6EZE353Q4scGiHYGJPI4nm7vlt8rMjPnWZmW8S1M_9kc7UOIFQv6y0oSEgn4-TQDw"      # Your Discord webhook URL here
ENABLE_DISCORD_NOTIFICATIONS = True   # Set to True to enable notifications

# Default symbol-specific settings
SYMBOL_SETTINGS = {
    "EURUSD": {
        "MAX_SPREAD": 20,
        "TP_MULTIPLIER": 2.0  # TP = SL * multiplier
    },
    "GBPUSD": {
        "MAX_SPREAD": 25,
        "TP_MULTIPLIER": 2.0
    },
    "USDJPY": {
        "MAX_SPREAD": 20,
        "TP_MULTIPLIER": 2.0
    }
}

# Market Hours (EST/EDT)
MARKET_OPEN_DAY = 6   # Sunday (0 = Monday, 6 = Sunday)
MARKET_CLOSE_DAY = 4  # Friday
MARKET_OPEN_HOUR = 17 # 5 PM

# Optional settings
DEFAULT_TP_MULTIPLIER = 2.0  # Default take profit multiplier if not specified in SYMBOL_SETTINGS
DEFAULT_TP_PIPS = None       # If set, use fixed TP pips instead of multiplier

# Stop Loss and Take Profit Settings
USE_FIXED_SLTP = False       # Set to True to use fixed SL/TP points, False for dynamic
FIXED_SL_POINTS = 200        # Fixed stop loss in points (when USE_FIXED_SLTP = True)
FIXED_TP_POINTS = 400        # Fixed take profit in points (when USE_FIXED_SLTP = True)
