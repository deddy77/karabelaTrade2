# ================================
# Trading Strategy Configuration
# ================================

# Timeframes for analysis
ANALYSIS_TIMEFRAMES = ["M5", "M15", "H1"]  # Multi-timeframe analysis

# Trading settings for multiple symbols  
SYMBOLS = ["EURUSD", "AUDUSD", "GBPUSD", "USDCHF"]
TIMEFRAME = "M5"  # Primary timeframe

# Market Structure Settings
USE_PRICE_ACTION = True  # Required by strategy code
USE_SWING_POINTS = True
USE_DYNAMIC_SR = True
MIN_PATTERN_BARS = 3
SUPPORT_RESISTANCE_LOOKBACK = 20
DYNAMIC_SR_LOOKBACK = 50
DYNAMIC_SR_MIN_TOUCHES = 2
DYNAMIC_SR_BUFFER_PIPS = 3

# MAIN SIGNAL - AMA Crossover
USE_ADAPTIVE_MA = True
MA_MEDIUM = 50   # AMA50 - Main signal line
MA_LONG = 200   # AMA200 - Main trend line
MIN_AMA_GAP_PERCENT = 0.02  # Minimum gap required
PRIMARY_SIGNAL = "AMA_CROSS"

# Pivot Points Settings (Required by strategy)
USE_PIVOT_POINTS = True
PIVOT_TYPE = "STANDARD"
PIVOT_TIMEFRAME = "D1"
PIVOT_BUFFER_PIPS = 2
USE_PIVOT_SR_FILTER = True
PIVOT_REVERSAL_THRESHOLD = 0.5

# Adaptive MA settings
AMA_FAST_EMA = 2
AMA_SLOW_EMA = 30

# === SUPPORTING FILTERS (2 out of 3 needed) ===

# 1. Momentum Filter
USE_MOMENTUM_FILTER = True
# RSI Settings
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
USE_RSI_FILTER = False  # Not used in main strategy, kept for compatibility

# ROC Settings
ROC_PERIOD = 14
ROC_THRESHOLD = 0  # Positive/Negative threshold

# MACD Settings
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
MACD_GROWING_FACTOR = 1.05  # Minimum growth between bars

# 2. Trend Strength Filter
USE_TREND_FILTER = True
ADX_PERIOD = 14
ADX_THRESHOLD = 20    # Strong trend threshold
DI_ALIGNMENT = True   # Check +DI/-DI alignment with trend

# 3. Volume/Volatility Filter
USE_VOL_FILTER = True
VOLUME_MA_PERIOD = 20
MIN_VOLUME_RATIO = 1.2  # Minimum volume ratio vs average

# Volatility Indicators
# Keltner Channels
KC_PERIOD = 20
KC_ATR_MULT = 2.0
KC_USE_EMA = True  # Use EMA instead of SMA for middle line

# Bollinger Bands for Volatility
BB_PERIOD = 20
BB_STD_DEV = 2
BB_MIN_EXPANSION = 0.05  # 5% minimum bandwidth expansion
USE_BB_FILTER = True
BB_EXTENSION_THRESHOLD = 0.8
MIN_BB_BANDWIDTH = 0.5

# Risk Management
DEFAULT_RISK_PERCENT = 1.0
MIN_LOT = 0.04
MAX_LOT = 10.0
DEFAULT_TP_MULTIPLIER = 2.0
DEFAULT_TP_PIPS = None

# ATR Settings for Stop Loss
ATR_PERIOD = 14
MAX_ATR_MULT = 2.0
MIN_ATR_MULT = 0.3

# Trading Hours (EST)
MARKET_OPEN_DAY = 6  # Sunday
MARKET_CLOSE_DAY = 4  # Friday
MARKET_OPEN_HOUR = 17  # 5PM EST

# Multi-Timeframe Analysis Settings
MTF_WEIGHTS = {
    "M5": 0.5,
    "M15": 0.3,
    "H1": 0.2
}
MTF_AGREEMENT_THRESHOLD = 0.7  # 70% agreement needed between timeframes
MTF_INDICATORS = {
    "MA_CROSSOVER": True,
    "RSI": True,
    "PRICE_ACTION": True
}

# ADX Filter Settings
USE_ADX_FILTER = True
ADX_EXTREME = 40  # Extremely strong trend threshold

# MACD Filter Settings
USE_MACD_FILTER = True
MACD_CONSECUTIVE_BARS = 3  # Number of consecutive bars to check
MACD_ZERO_CROSS_CONFIRM = True  # Require zero-line cross confirmation

# Trading Sessions
TRADING_SESSIONS = {
    "Asian": {"start_hour": 19, "end_hour": 4},   # 7PM-4AM EST
    "London": {"start_hour": 3, "end_hour": 12},  # 3AM-12PM EST
    "NewYork": {"start_hour": 8, "end_hour": 17}  # 8AM-5PM EST
}

# Session Risk Settings
SESSION_PARAMS = {
    "Asian": {
        "risk_multiplier": 0.7,
        "max_spread": 15
    },
    "London": {
        "risk_multiplier": 1.0,
        "max_spread": 15
    },
    "NewYork": {
        "risk_multiplier": 1.0,
        "max_spread": 15
    }
}

# Symbol-specific settings
SYMBOL_SETTINGS = {
    "EURUSD": {"MAX_SPREAD": 15, "TP_MULTIPLIER": 2.0},
    "GBPUSD": {"MAX_SPREAD": 15, "TP_MULTIPLIER": 2.0},
    "USDCAD": {"MAX_SPREAD": 15, "TP_MULTIPLIER": 2.0},
    "AUDUSD": {"MAX_SPREAD": 15, "TP_MULTIPLIER": 2.0},
    "USDCHF": {"MAX_SPREAD": 15, "TP_MULTIPLIER": 2.0},
}

# Exit Strategy Settings
USE_TRAILING_STOP = False
TRAILING_STOP_ACTIVATION_PIPS = 15
TRAILING_STOP_DISTANCE_PIPS = 10
USE_DYNAMIC_TP = False
DYNAMIC_TP_ATR_MULTIPLIER = 3.0
CHECK_EXIT_INTERVAL = 60

# Daily Trading Limits
DAILY_PROFIT_TARGET = 50  # Stop when $50 profit made
DAILY_MAX_LOSS = -30     # Stop if $30 loss reached
RESET_TIME = "00:00"     # Daily reset time

# News Trading Settings
MINUTES_BEFORE_NEWS = 30
MINUTES_AFTER_NEWS = 60
NEWS_CHECK_INTERVAL = 5

# Common Settings
MAGIC_NUMBER = 123456
SLIPPAGE = 100

# Logging Settings
LOG_FILE = "logs/trade_log.txt"

# Discord notification
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1359973769204203591/pKz6EZE353Q4scGiHYGJPI4nm7vlt8rMjPnWZmW8S1M_9kc7UOIFQv6y0oSEgn4-TQDw"

# For backward compatibility
SYMBOL = SYMBOLS[0]
