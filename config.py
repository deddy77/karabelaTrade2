# ================================
# Trading Strategy Configuration
# ================================

# Primary timeframe setting (can be changed to M1, M5, M15, H1, H4)
TIMEFRAME = "M15"  # Primary timeframe

# Function to get analysis timeframes based on primary timeframe
def get_analysis_timeframes(primary_tf):
    timeframe_hierarchy = {
        "M1": ["M1", "M5", "M15"],
        "M5": ["M5", "M15", "H1"],
        "M15": ["M15", "H1", "H4"],
        "H1": ["H1", "H4", "D1"],
        "H4": ["H4", "D1", "W1"]
    }
    return timeframe_hierarchy.get(primary_tf, ["M5", "M15", "H1"])

# Trading settings for multiple symbols  
SYMBOLS = ["EURUSD", "AUDUSD", "GBPUSD", "USDCHF"]

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
def adjust_period(base_period, from_tf="M5", to_tf=TIMEFRAME):
    from_minutes = TIMEFRAME_MULTIPLIERS.get(from_tf, 5)
    to_minutes = TIMEFRAME_MULTIPLIERS.get(to_tf, 5)
    return max(2, int((base_period * from_minutes) / to_minutes))

# Market Structure Settings
USE_PRICE_ACTION = True  # Required by strategy code
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
MA_LONG = adjust_period(200)   # AMA200 - Main trend line
MIN_AMA_GAP_PERCENT = 0.05  # Minimum gap required
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

# === FILTER CONFIGURATION ===

from typing import Dict, List, Any, Union

# Define SUPPORTING_FILTERS first to avoid reference errors
SUPPORTING_FILTERS: Dict[str, Dict[str, Any]] = {
    # 1. Momentum Filter
    "MOMENTUM": {
        "ENABLED": True,
        "REQUIRES": [],  # No dependencies
        "COMPONENTS": {
            "RSI": {
                "ENABLED": True,
                "PERIOD": 14,
                "OVERBOUGHT": 70,
                "OVERSOLD": 30
            },
            "ROC": {
                "ENABLED": True,
                "PERIOD": 14,
                "THRESHOLD": 0
            },
            "MACD": {
                "ENABLED": True,
                "FAST": 12,
                "SLOW": 26,
                "SIGNAL": 9,
                "GROWING_FACTOR": 1.05
            }
        }
    },
    
    # 2. Trend Strength Filter
    "TREND": {
        "ENABLED": True,
        "REQUIRES": [],  # No dependencies
        "COMPONENTS": {
            "ADX": {
                "ENABLED": True,
                "PERIOD": 14,
                "THRESHOLD": 20,
                "EXTREME": 40
            },
            "DI": {
                "ENABLED": True,
                "ALIGNMENT_CHECK": True
            }
        }
    },
    
    # 3. Volume/Volatility Filter - Requires Momentum Filter
    "VOLATILITY": {
        "ENABLED": True,
        "REQUIRES": ["MOMENTUM"],  # Requires momentum filter to be enabled
        "COMPONENTS": {
            "VOLUME": {
                "ENABLED": True,
                "MA_PERIOD": 20,
                "MIN_RATIO": 1.2
            },
            "KELTNER": {
                "ENABLED": True,
                "PERIOD": 20,
                "ATR_MULT": 2.0,
                "USE_EMA": True
            },
            "BOLLINGER": {
                "ENABLED": True,
                "PERIOD": 20,
                "STD_DEV": 2,
                "MIN_EXPANSION": 0.05,
                "EXTENSION_THRESHOLD": 0.8,
                "MIN_BANDWIDTH": 0.5
            }
        }
    }
}

# Update indicator periods based on timeframe
def update_indicator_periods() -> None:
    # Update momentum filter periods
    SUPPORTING_FILTERS["MOMENTUM"]["COMPONENTS"]["RSI"]["PERIOD"] = adjust_period(14)
    SUPPORTING_FILTERS["MOMENTUM"]["COMPONENTS"]["ROC"]["PERIOD"] = adjust_period(14)
    SUPPORTING_FILTERS["MOMENTUM"]["COMPONENTS"]["MACD"]["FAST"] = adjust_period(12)
    SUPPORTING_FILTERS["MOMENTUM"]["COMPONENTS"]["MACD"]["SLOW"] = adjust_period(26)
    SUPPORTING_FILTERS["MOMENTUM"]["COMPONENTS"]["MACD"]["SIGNAL"] = adjust_period(9)
    
    # Update trend filter periods
    SUPPORTING_FILTERS["TREND"]["COMPONENTS"]["ADX"]["PERIOD"] = adjust_period(14)
    
    # Update volatility filter periods
    SUPPORTING_FILTERS["VOLATILITY"]["COMPONENTS"]["VOLUME"]["MA_PERIOD"] = adjust_period(20)
    SUPPORTING_FILTERS["VOLATILITY"]["COMPONENTS"]["KELTNER"]["PERIOD"] = adjust_period(20)
    SUPPORTING_FILTERS["VOLATILITY"]["COMPONENTS"]["BOLLINGER"]["PERIOD"] = adjust_period(20)

# Call the function to update periods based on current timeframe
update_indicator_periods()

# Main Signal Configuration - AMA is the primary signal
MAIN_SIGNAL: Dict[str, Any] = {
    "TYPE": "AMA",  # Main signal type
    "ENABLED": True,  # Cannot be disabled as it's the main signal
    "PARAMETERS": {
        "MA_MEDIUM": 50,    # AMA50 - Main signal line
        "MA_LONG": 200,     # AMA200 - Main trend line
        "MIN_GAP_PERCENT": 0.05  # Minimum gap required
    }
}

# Supporting Filters Configuration
USE_SUPPORTING_FILTERS = True  # Master switch for all supporting filters
REQUIRED_FILTER_CONFIRMATIONS = 2  # Must have 2 out of 3 filters confirm when enabled

# When USE_SUPPORTING_FILTERS is False, only the main AMA signal is used
# When True, requires REQUIRED_FILTER_CONFIRMATIONS number of supporting filters

# Helper function to safely access nested dictionary values
def get_filter_value(filter_type: str, *keys: str, default: Any = None) -> Any:
    try:
        value = SUPPORTING_FILTERS[filter_type]
        for key in keys:
            value = value[key]
        return value
    except (KeyError, TypeError):
        return default

# Backward compatibility variables with type hints
USE_MOMENTUM_FILTER: bool = get_filter_value("MOMENTUM", "ENABLED", default=True)
USE_TREND_FILTER: bool = get_filter_value("TREND", "ENABLED", default=True)
USE_VOL_FILTER: bool = get_filter_value("VOLATILITY", "ENABLED", default=True)

# RSI Settings (backward compatibility)
RSI_PERIOD: int = get_filter_value("MOMENTUM", "COMPONENTS", "RSI", "PERIOD", default=14)
RSI_OVERBOUGHT: int = get_filter_value("MOMENTUM", "COMPONENTS", "RSI", "OVERBOUGHT", default=70)
RSI_OVERSOLD: int = get_filter_value("MOMENTUM", "COMPONENTS", "RSI", "OVERSOLD", default=30)
USE_RSI_FILTER: bool = get_filter_value("MOMENTUM", "COMPONENTS", "RSI", "ENABLED", default=True)

# ROC Settings (backward compatibility)
ROC_PERIOD: int = get_filter_value("MOMENTUM", "COMPONENTS", "ROC", "PERIOD", default=14)
ROC_THRESHOLD: int = get_filter_value("MOMENTUM", "COMPONENTS", "ROC", "THRESHOLD", default=0)

# MACD Settings (backward compatibility)
MACD_FAST: int = get_filter_value("MOMENTUM", "COMPONENTS", "MACD", "FAST", default=12)
MACD_SLOW: int = get_filter_value("MOMENTUM", "COMPONENTS", "MACD", "SLOW", default=26)
MACD_SIGNAL: int = get_filter_value("MOMENTUM", "COMPONENTS", "MACD", "SIGNAL", default=9)
MACD_GROWING_FACTOR: float = get_filter_value("MOMENTUM", "COMPONENTS", "MACD", "GROWING_FACTOR", default=1.05)

# ADX Settings (backward compatibility)
ADX_PERIOD: int = get_filter_value("TREND", "COMPONENTS", "ADX", "PERIOD", default=14)
ADX_THRESHOLD: int = get_filter_value("TREND", "COMPONENTS", "ADX", "THRESHOLD", default=20)
DI_ALIGNMENT: bool = get_filter_value("TREND", "COMPONENTS", "DI", "ALIGNMENT_CHECK", default=True)

# Volume/Volatility Settings (backward compatibility)
VOLUME_MA_PERIOD: int = get_filter_value("VOLATILITY", "COMPONENTS", "VOLUME", "MA_PERIOD", default=20)
MIN_VOLUME_RATIO: float = get_filter_value("VOLATILITY", "COMPONENTS", "VOLUME", "MIN_RATIO", default=1.2)

# Keltner Channels (backward compatibility)
KC_PERIOD: int = get_filter_value("VOLATILITY", "COMPONENTS", "KELTNER", "PERIOD", default=20)
KC_ATR_MULT: float = get_filter_value("VOLATILITY", "COMPONENTS", "KELTNER", "ATR_MULT", default=2.0)
KC_USE_EMA: bool = get_filter_value("VOLATILITY", "COMPONENTS", "KELTNER", "USE_EMA", default=True)

# Bollinger Bands (backward compatibility)
BB_PERIOD: int = get_filter_value("VOLATILITY", "COMPONENTS", "BOLLINGER", "PERIOD", default=20)
BB_STD_DEV: int = get_filter_value("VOLATILITY", "COMPONENTS", "BOLLINGER", "STD_DEV", default=2)
BB_MIN_EXPANSION: float = get_filter_value("VOLATILITY", "COMPONENTS", "BOLLINGER", "MIN_EXPANSION", default=0.05)
USE_BB_FILTER: bool = get_filter_value("VOLATILITY", "COMPONENTS", "BOLLINGER", "ENABLED", default=True)
BB_EXTENSION_THRESHOLD: float = get_filter_value("VOLATILITY", "COMPONENTS", "BOLLINGER", "EXTENSION_THRESHOLD", default=0.8)
MIN_BB_BANDWIDTH: float = get_filter_value("VOLATILITY", "COMPONENTS", "BOLLINGER", "MIN_BANDWIDTH", default=0.5)

# Risk Management
DEFAULT_RISK_PERCENT = 1.0
MIN_LOT = 0.04
MAX_LOT = 10.0
DEFAULT_TP_MULTIPLIER = 2.0
DEFAULT_TP_PIPS = None

# Fixed SL/TP Settings
USE_FIXED_SLTP = True  # If True, uses fixed values instead of risk management calculations
FIXED_TP_POINTS = 30   # Fixed take profit in points
FIXED_SL_POINTS = 300  # Fixed stop loss in points

# ATR Settings for Stop Loss
ATR_PERIOD = 14
MAX_ATR_MULT = 2.0
MIN_ATR_MULT = 0.3

# Trading Hours (EST)
MARKET_OPEN_DAY = 6  # Sunday
MARKET_CLOSE_DAY = 4  # Friday
MARKET_OPEN_HOUR = 17  # 5PM EST

# Function to get appropriate MTF weights based on timeframe
def get_mtf_weights(timeframe: str) -> Dict[str, float]:
    weights = {
        "M1": {"M1": 0.5, "M5": 0.3, "M15": 0.2},
        "M5": {"M5": 0.5, "M15": 0.3, "H1": 0.2},
        "M15": {"M15": 0.5, "H1": 0.3, "H4": 0.2},
        "H1": {"H1": 0.5, "H4": 0.3, "D1": 0.2},
        "H4": {"H4": 0.5, "D1": 0.3, "W1": 0.2}
    }
    return weights.get(timeframe, {"M5": 0.5, "M15": 0.3, "H1": 0.2})

# Multi-Timeframe Analysis Settings
MTF_WEIGHTS = get_mtf_weights(TIMEFRAME)
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
