# ================================
# Trading Strategy Configuration
# ================================

# Trading settings for multiple symbols
SYMBOLS = ["EURUSD", "AUDUSD", "GBPUSD", "USDCHF"]  # Trade all major pairs
TIMEFRAME = "M5"  # Primary timeframe for execution (M1, M5, M15, M30, H1, H4, D1)

# Moving Average settings (MAIN TRADING SIGNAL)
USE_ADAPTIVE_MA = True
MA_MEDIUM = 50   # AMA50 - Main signal line
MA_LONG = 200   # AMA200 - Main trend line
PRIMARY_SIGNAL = "AMA_CROSS"  # AMA50/AMA200 crossover as primary signal
MIN_AMA_GAP_PERCENT = 0.02  # Minimum gap between AMAs for valid signal

# Adaptive MA settings
AMA_FAST_EMA = 2
AMA_SLOW_EMA = 30

# Trend Confirmation Indicators
# 1. ADX - Trend Strength
USE_ADX_FILTER = True  # Enable ADX as trend strength confirmation
ADX_PERIOD = 14       # Standard period
ADX_THRESHOLD = 20    # Minimum ADX for trend confirmation
ADX_EXTREME = 50      # Strong trend indication

# 2. MACD - Momentum Confirmation
USE_MACD_FILTER = True   # Use MACD as momentum confirmation
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
MACD_CONSECUTIVE_BARS = 2    # Number of confirming bars needed
MACD_GROWING_FACTOR = 1.05   # Minimum growth between bars
MACD_ZERO_CROSS_CONFIRM = False  # Optional zero line confirmation

# 3. RSI - Overbought/Oversold Filter (Support Signal)
USE_RSI_FILTER = True  # Use RSI as confirmation
RSI_PERIOD = 14       # Standard period
RSI_OVERBOUGHT = 75   # Increased to prevent early exits
RSI_OVERSOLD = 25     # Increased to prevent early exits

# Volatility Settings
ATR_PERIOD = 14
MAX_ATR_MULT = 2.0  # Maximum ATR multiple for volatility check
MIN_ATR_MULT = 0.3  # Minimum ATR multiple for volatility check

# Volatility Indicators Settings
# Keltner Channels
KC_PERIOD = 20
KC_ATR_MULT = 2.0
KC_USE_EMA = True  # Use EMA instead of SMA for middle line

# Bollinger Bands Settings
USE_BB_FILTER = True
BB_PERIOD = 20
BB_STD_DEV = 2
BB_EXTENSION_THRESHOLD = 0.8  # Maximum allowed price extension
MIN_BB_BANDWIDTH = 0.5  # Minimum bandwidth percentage to trade

# Market Structure Settings
USE_PRICE_ACTION = True  # Enable price action pattern confirmation
MIN_PATTERN_BARS = 3    # Minimum bars needed to form a pattern
SUPPORT_RESISTANCE_LOOKBACK = 20  # Bars to analyze for S/R levels
USE_SWING_POINTS = True  # Enable swing high/low detection
SWING_LEFT_BARS = 3     # Bars to left for swing point confirmation
SWING_RIGHT_BARS = 3    # Bars to right for swing point confirmation
MIN_SWING_DISTANCE_PIPS = 10  # Minimum distance between swing points
USE_DYNAMIC_SR = True   # Enable dynamic support/resistance levels
DYNAMIC_SR_LOOKBACK = 50  # Bars to analyze for dynamic S/R levels
DYNAMIC_SR_MIN_TOUCHES = 2  # Minimum touches to confirm a level
DYNAMIC_SR_BUFFER_PIPS = 3  # Buffer zone around dynamic levels

# Pivot Points Settings
USE_PIVOT_POINTS = True  # Enable pivot point analysis
PIVOT_TYPE = "STANDARD"  # STANDARD or FIBONACCI
PIVOT_TIMEFRAME = "D1"  # Calculate pivots on Daily timeframe
PIVOT_BUFFER_PIPS = 2  # Buffer zone around pivot levels
USE_PIVOT_SR_FILTER = True  # Use pivot points as trade filters
PIVOT_REVERSAL_THRESHOLD = 0.5  # Minimum distance from pivot for reversal trades

# Risk Management
MIN_LOT = 0.04
MAX_LOT = 10.0
DEFAULT_RISK_PERCENT = 1.0  # Risk per trade
DEFAULT_TP_MULTIPLIER = 2.0  # Take profit as multiple of stop loss
DEFAULT_TP_PIPS = None      # Use multiplier instead of fixed pips

# Exit Strategy Settings
USE_TRAILING_STOP = False  # Enable trailing stop loss
TRAILING_STOP_ACTIVATION_PIPS = 15  # Activate trailing stop when profit reaches this many pips
TRAILING_STOP_DISTANCE_PIPS = 10  # Distance to maintain for trailing stop
USE_DYNAMIC_TP = False  # Enable dynamic take profit based on market conditions
DYNAMIC_TP_ATR_MULTIPLIER = 3.0  # Multiplier for ATR to set dynamic take profit
CHECK_EXIT_INTERVAL = 60  # Check and update exit levels every 60 seconds

# Daily Trading Limits
DAILY_PROFIT_TARGET = 50  # Stop when $50 profit made
DAILY_MAX_LOSS = -30     # Stop if $30 loss reached
RESET_TIME = "00:00"     # Daily reset time (HH:MM)

# Symbol-specific settings
SYMBOL_SETTINGS = {
    "EURUSD": {"MAX_SPREAD": 15, "TP_MULTIPLIER": 2.0},
    "GBPUSD": {"MAX_SPREAD": 15, "TP_MULTIPLIER": 2.0},
    "USDCAD": {"MAX_SPREAD": 15, "TP_MULTIPLIER": 2.0},
    "AUDUSD": {"MAX_SPREAD": 15, "TP_MULTIPLIER": 2.0},
    "USDCHF": {"MAX_SPREAD": 15, "TP_MULTIPLIER": 2.0},
}

# Market Trading Hours (EST)
MARKET_OPEN_DAY = 6  # Sunday
MARKET_CLOSE_DAY = 4  # Friday
MARKET_OPEN_HOUR = 17  # 5PM EST

# Trading Sessions (EST)
TRADING_SESSIONS = {
    "Asian": {"start_hour": 19, "end_hour": 4},   # 7PM-4AM EST
    "London": {"start_hour": 3, "end_hour": 12},  # 3AM-12PM EST
    "NewYork": {"start_hour": 8, "end_hour": 17}  # 8AM-5PM EST
}

# Session Parameters
SESSION_PARAMS = {
    "Asian": {
        "risk_multiplier": 0.7,
        "use_rsi_filter": True,
        "max_spread": 15,
        "require_timeframe_agreement": False
    },
    "London": {
        "risk_multiplier": 1.0,
        "use_rsi_filter": True,
        "max_spread": 15
    },
    "NewYork": {
        "risk_multiplier": 1.0,
        "use_rsi_filter": True,
        "max_spread": 15
    }
}

# Multi-Timeframe Confirmation
ANALYSIS_TIMEFRAMES = ["M15", "H1"]  # Additional timeframes for trend confirmation
MTF_AGREEMENT_THRESHOLD = 70
MTF_WEIGHTS = {
    "M5": 1.0,   # Primary timeframe
    "M15": 0.3,  # Minor confirmation
    "H1": 0.5    # Major confirmation
}
MTF_INDICATORS = {
    "MA_CROSSOVER": True,  # Check MA cross on all timeframes
    "RSI": False,         # RSI only on primary timeframe
    "PRICE_ACTION": False # Price action only on primary timeframe
}

# News Trading Settings
MINUTES_BEFORE_NEWS = 30  # Avoid trading before high impact news
MINUTES_AFTER_NEWS = 60   # Longer wait after news for market to stabilize
NEWS_CHECK_INTERVAL = 5

# Common Settings
MAGIC_NUMBER = 123456
SLIPPAGE = 100

# Logging
LOG_FILE = "logs/trade_log.txt"

# Discord notification
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1359973769204203591/pKz6EZE353Q4scGiHYGJPI4nm7vlt8rMjPnWZmW8S1M_9kc7UOIFQv6y0oSEgn4-TQDw"

# For backward compatibility
SYMBOL = SYMBOLS[0]
