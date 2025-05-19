# ================================
# Trading Strategy Configuration
# ================================
from typing import Dict, List, Any, Union

CONFIG_VERSION = "1.1.0"  # Added validation and fixed FIXED_SL/TP_POINTS naming

# Configuration Constants
POINTS_PER_PIP = {
    'JPY': 1,   # For JPY pairs, 1 pip = 1 point (0.01)
    'DEFAULT': 10  # For other pairs, 1 pip = 10 points (0.0001)
}

def get_points_per_pip(symbol: str) -> int:
    """Get the number of points per pip for a given symbol"""
    return POINTS_PER_PIP['JPY'] if symbol.endswith('JPY') else POINTS_PER_PIP['DEFAULT']

def validate_number(value: float, min_val: float, max_val: float, default: float, name: str) -> float:
    """Validate numeric configuration values"""
    try:
        num_value = float(value)
        if min_val <= num_value <= max_val:
            return num_value
        print(f"Warning: {name} value {value} outside range [{min_val}, {max_val}]. Using default: {default}")
        return default
    except (TypeError, ValueError):
        print(f"Warning: Invalid {name} value. Using default: {default}")
        return default

def convert_pips_to_points(pips: float, symbol: str) -> int:
    """Convert pips to points based on symbol type"""
    points_per_pip = get_points_per_pip(symbol)
    return int(pips * points_per_pip)

def validate_points(value: float, min_points: int = 10, max_points: int = 1000, default: int = 100) -> int:
    """Validate point values for SL/TP settings"""
    return int(validate_number(value, min_points, max_points, default, "points"))

def validate_pips(value: float, min_pips: float = 1, max_pips: float = 100, default: float = 10) -> float:
    """Validate pip values"""
    return validate_number(value, min_pips, max_pips, default, "pips")

def validate_timeframe(tf: str) -> str:
    """Validate timeframe string"""
    valid_timeframes = ["M1", "M5", "M15", "H1", "H4", "D1"]
    return tf if tf in valid_timeframes else "M5"

def validate_risk_settings() -> None:
    """Validate risk management settings"""
    global DEFAULT_RISK_PERCENT, MIN_LOT, MAX_LOT
    DEFAULT_RISK_PERCENT = validate_number(DEFAULT_RISK_PERCENT, 0.1, 5.0, 1.0, "risk_percent")
    MIN_LOT = validate_number(MIN_LOT, 0.01, 0.1, 0.01, "min_lot")
    MAX_LOT = validate_number(MAX_LOT, 0.1, 20.0, 10.0, "max_lot")

# Import session manager
from session_manager import SessionManager
session_mgr = SessionManager()

# Get base timeframe from session manager
TIMEFRAME = session_mgr.get_base_timeframe()  # Will be updated dynamically per session

# Function to get analysis timeframes based on primary timeframe
def get_analysis_timeframes(primary_tf: str) -> List[str]:
    timeframe_hierarchy = {
        "M1": ["M1", "M5", "M15"],
        "M5": ["M5", "M15", "H1"],
        "M15": ["M15", "H1", "H4"],
        "H1": ["H1", "H4", "D1"],
        "H4": ["H4", "D1", "W1"]
    }
    return timeframe_hierarchy.get(primary_tf, ["M5", "M15", "H1"])

# Get tradeable symbols from session manager
SYMBOLS = session_mgr.get_all_tradeable_pairs()

# Analysis timeframes are dynamically set based on primary timeframe
ANALYSIS_TIMEFRAMES = get_analysis_timeframes(TIMEFRAME)

# Timeframe multipliers for adjusting analysis periods
TIMEFRAME_MULTIPLIERS = {
    "M1": 1,
    "M5": 5,
    "M15": 15,
    "H1": 60,
    "H4": 240
}

# Function to adjust period based on timeframe
def adjust_period(base_period: int, from_tf: str = "M5", to_tf: str = TIMEFRAME) -> int:
    """
    Adjust indicator period based on timeframe changes
    Args:
        base_period: Base period to adjust
        from_tf: Source timeframe (default: M5)
        to_tf: Target timeframe (default: current TIMEFRAME)
    Returns:
        Adjusted period value
    """
    from_minutes = TIMEFRAME_MULTIPLIERS.get(from_tf, 5)
    to_minutes = TIMEFRAME_MULTIPLIERS.get(to_tf, 5)
    return max(2, int((base_period * from_minutes) / to_minutes))

# Market Structure Settings
USE_PRICE_ACTION = True
USE_SWING_POINTS = True
USE_DYNAMIC_SR = True
MIN_PATTERN_BARS = adjust_period(3)
SUPPORT_RESISTANCE_LOOKBACK = adjust_period(20)
DYNAMIC_SR_LOOKBACK = adjust_period(50)
DYNAMIC_SR_MIN_TOUCHES = 2
DYNAMIC_SR_BUFFER_PIPS = 3

# MAIN SIGNAL - AMA Crossover
USE_ADAPTIVE_MA = True
MA_MEDIUM = adjust_period(50)   # AMA50 - Main signal line
MA_LONG = adjust_period(200)    # AMA200 - Main trend line
MIN_AMA_GAP_PERCENT = 0.05      # Minimum gap required
PRIMARY_SIGNAL = "AMA_CROSS"

# Pivot Points Settings
USE_PIVOT_POINTS = True
PIVOT_TYPE = "STANDARD"
PIVOT_TIMEFRAME = "D1"
PIVOT_BUFFER_PIPS = 2
USE_PIVOT_SR_FILTER = True
PIVOT_REVERSAL_THRESHOLD = 0.5

# Adaptive MA settings
AMA_FAST_EMA = 2
AMA_SLOW_EMA = 30

# === FILTER CONFIGURATION ===

# Supporting Filters Configuration
USE_SUPPORTING_FILTERS = True  # Master switch for all supporting filters
REQUIRED_FILTER_CONFIRMATIONS = 2  # Must have 2 out of 3 filters confirm

# RSI Settings
RSI_PERIOD = adjust_period(14)
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
USE_RSI_FILTER = True

# MACD Settings
MACD_FAST = adjust_period(12)
MACD_SLOW = adjust_period(26)
MACD_SIGNAL = adjust_period(9)
MACD_GROWING_FACTOR = 1.05
USE_MACD_FILTER = True
MACD_CONSECUTIVE_BARS = 3
MACD_ZERO_CROSS_CONFIRM = True

# ADX Settings
ADX_PERIOD = adjust_period(14)
ADX_THRESHOLD = 20
ADX_EXTREME = 40
USE_ADX_FILTER = True

# Bollinger Bands Settings
BB_PERIOD = adjust_period(20)
BB_STD_DEV = 2
BB_MIN_EXPANSION = 0.05
USE_BB_FILTER = True
BB_EXTENSION_THRESHOLD = 0.8
MIN_BB_BANDWIDTH = 0.5

# =================================
# Risk Management and Position Sizing
# =================================
DEFAULT_RISK_PERCENT = 1.0     # Risk per trade (1% of account)
MIN_LOT = 0.01                # Minimum lot size
MAX_LOT = 10.0               # Maximum lot size for 1:30 leverage compliance
MAX_LEVERAGE_PER_TRADE = 30   # Maximum leverage per trade (1:30)
SCALE_IN_PERIOD = True       # Scale in during evaluation period

# =================================
# Stop Loss and Take Profit Settings
# =================================
# General Configuration
USE_FIXED_SLTP = False       # Set to True to use fixed SL/TP values instead of dynamic

# Fixed SL/TP Values (used when USE_FIXED_SLTP = True)
# Note: For 4-digit pairs: 1 pip = 10 points (0.0001)
#       For JPY pairs: 1 pip = 1 point (0.01)
FIXED_SL_POINTS = 100        # 10 pips = 100 points
FIXED_TP_POINTS = 200        # 20 pips = 200 points

# Dynamic SL/TP Settings (used when USE_FIXED_SLTP = False)
DEFAULT_TP_MULTIPLIER = 2.0  # Multiplier for dynamic TP calculation
DEFAULT_TP_PIPS = None       # Fixed TP pips (if None, uses multiplier)

# =================================
# Support/Resistance Configuration
# =================================
# Dynamic S/R Settings
USE_DYNAMIC_SR = True
DYNAMIC_SR_LOOKBACK = adjust_period(50)    # Number of bars to look back
DYNAMIC_SR_MIN_TOUCHES = 2                 # Minimum touches to confirm level
DYNAMIC_SR_BUFFER_PIPS = 3                 # Buffer zone around S/R levels

# Swing Points Settings
SWING_LEFT_BARS = 3          # Bars to check on left side
SWING_RIGHT_BARS = 3         # Bars to check on right side

# ATR Settings for Stop Loss
ATR_PERIOD = adjust_period(14)
MAX_ATR_MULT = 2.0
MIN_ATR_MULT = 0.3

# Market Hours (EST)
MARKET_OPEN_DAY = 6  # Sunday
MARKET_CLOSE_DAY = 4  # Friday
MARKET_OPEN_HOUR = 17  # 5PM EST

# Multi-Timeframe Analysis Settings
MTF_WEIGHTS = {
    "M5": 0.5,
    "M15": 0.3,
    "H1": 0.2
}
MTF_AGREEMENT_THRESHOLD = 0.7
MTF_INDICATORS = {
    "MA_CROSSOVER": True,
    "RSI": True,
    "PRICE_ACTION": True
}

# Default settings for all pairs
DEFAULT_PAIR_SETTINGS = {
    "MAX_SPREAD": 15,
    "TP_MULTIPLIER": 2.0
}

# Generate settings for all tradeable pairs
SYMBOL_SETTINGS = {
    pair: DEFAULT_PAIR_SETTINGS.copy() 
    for pair in SYMBOLS
}

# Keltner Channel Settings
KC_PERIOD = adjust_period(20)
KC_ATR_MULT = 2.0
KC_USE_EMA = True

# News Trading Settings
MINUTES_BEFORE_NEWS = 30
MINUTES_AFTER_NEWS = 60
NEWS_CHECK_INTERVAL = 5

# Exit Strategy Settings
USE_TRAILING_STOP = False
TRAILING_STOP_ACTIVATION_PIPS = 15
TRAILING_STOP_DISTANCE_PIPS = 10
USE_DYNAMIC_TP = False
DYNAMIC_TP_ATR_MULTIPLIER = 3.0
CHECK_EXIT_INTERVAL = 60

# Challenge Parameters ($5000 Account)
ACCOUNT_SIZE = 5000          # Initial account size
DAILY_PROFIT_TARGET = 500    # 10% target ($500)
DAILY_MAX_LOSS = -200       # 4% daily loss limit ($200)
MAX_TOTAL_LOSS = -300       # 6% max drawdown ($300)
RESET_TIME = "00:00"        # Daily reset time

# Challenge Requirements
EVALUATION_MIN_DAYS = 3      # Minimum trading days required
PAYOUT_CYCLE_DAYS = 14      # Days between payouts
LEVERAGE_LIMIT = 30         # Maximum leverage 1:30

# Signal Validity Settings
MAX_SIGNAL_VALIDITY_SECONDS = 30  # Maximum time a signal remains valid
MAX_PRICE_DEVIATION_PIPS = 10     # Maximum allowed price deviation before execution
SIGNAL_RECHECK_REQUIRED = True    # Require signal revalidation before execution
EXECUTION_RETRY_DELAY = 1         # Seconds to wait between execution attempts

# Common Settings
MAGIC_NUMBER = 123456
SLIPPAGE = 100

# Logging Settings
LOG_FILE = "logs/trade_log.txt"

# Discord notification
DISCORD_WEBHOOK_URL = "https://discord.com/api/webhooks/1359973769204203591/pKz6EZE353Q4scGiHYGJPI4nm7vlt8rMjPnWZmW8S1M_9kc7UOIFQv6y0oSEgn4-TQDw"

# For backward compatibility
SYMBOL = SYMBOLS[0]

def validate_atr_settings():
    """Validate ATR-related settings"""
    global ATR_PERIOD, MAX_ATR_MULT, MIN_ATR_MULT
    ATR_PERIOD = max(5, int(ATR_PERIOD))
    MAX_ATR_MULT = validate_number(MAX_ATR_MULT, 1.0, 5.0, 2.0, "max_atr_mult")
    MIN_ATR_MULT = validate_number(MIN_ATR_MULT, 0.1, 1.0, 0.3, "min_atr_mult")

def validate_ma_settings():
    """Validate Moving Average settings"""
    global MA_MEDIUM, MA_LONG, MIN_AMA_GAP_PERCENT
    MA_MEDIUM = max(10, int(MA_MEDIUM))
    MA_LONG = max(50, int(MA_LONG))
    MIN_AMA_GAP_PERCENT = validate_number(MIN_AMA_GAP_PERCENT, 0.01, 1.0, 0.05, "min_ama_gap")

def init_config():
    """Initialize and validate configuration parameters"""
    try:
        global FIXED_SL_POINTS, FIXED_TP_POINTS, DYNAMIC_SR_LOOKBACK
        global SWING_LEFT_BARS, SWING_RIGHT_BARS, USE_DYNAMIC_SR
        global DEFAULT_RISK_PERCENT, MIN_LOT, MAX_LOT
        global TIMEFRAME, DEFAULT_TP_MULTIPLIER, USE_FIXED_SLTP

        # Validate SL/TP points
        FIXED_SL_POINTS = validate_points(FIXED_SL_POINTS)
        FIXED_TP_POINTS = validate_points(FIXED_TP_POINTS, default=FIXED_SL_POINTS * 2)

        # Validate Support/Resistance parameters
        DYNAMIC_SR_LOOKBACK = max(20, int(DYNAMIC_SR_LOOKBACK))
        SWING_LEFT_BARS = max(2, int(SWING_LEFT_BARS))
        SWING_RIGHT_BARS = max(2, int(SWING_RIGHT_BARS))

        # Validate risk settings
        validate_risk_settings()

        # Validate ATR settings
        validate_atr_settings()

        # Validate MA settings
        validate_ma_settings()

        # Validate timeframe
        TIMEFRAME = validate_timeframe(TIMEFRAME)

        # Validate trade multipliers
        DEFAULT_TP_MULTIPLIER = validate_number(DEFAULT_TP_MULTIPLIER, 1.0, 5.0, 2.0, "tp_multiplier")

        # Ensure essential flags are boolean
        USE_DYNAMIC_SR = bool(USE_DYNAMIC_SR)
        USE_FIXED_SLTP = bool(USE_FIXED_SLTP)

        print("Configuration validation completed successfully")
    except Exception as e:
        print(f"Error during configuration validation: {str(e)}")
        print("Using default values for invalid parameters")

def get_symbol_settings(symbol: str) -> Dict[str, Any]:
    """
    Get symbol-specific settings with fallback to defaults
    Args:
        symbol: The trading symbol to get settings for
    Returns:
        Dictionary containing symbol-specific settings
    """
    if symbol in SYMBOL_SETTINGS:
        return SYMBOL_SETTINGS[symbol]
    return DEFAULT_PAIR_SETTINGS.copy()

# Run configuration initialization
init_config()

# Version information
__version__ = CONFIG_VERSION
