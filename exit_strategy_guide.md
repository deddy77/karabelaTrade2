# Advanced Exit Strategy Guide

This document explains the advanced exit strategy features implemented in the trading bot.

## Overview

The trading bot now includes two powerful exit strategy features:

1. **Trailing Stop Loss**: Automatically moves your stop loss to lock in profits as the trade moves in your favor
2. **Dynamic Take Profit**: Sets take profit levels based on market volatility using ATR (Average True Range)

These features help maximize profits on winning trades while still protecting your capital.

## Configuration

The exit strategy features can be configured in `config.py`:

```python
# Exit Strategy Settings
USE_TRAILING_STOP = True  # Enable trailing stop loss
TRAILING_STOP_ACTIVATION_PIPS = 15  # Activate trailing stop when profit reaches this many pips
TRAILING_STOP_DISTANCE_PIPS = 10  # Distance to maintain for trailing stop
USE_DYNAMIC_TP = True  # Enable dynamic take profit based on market conditions
DYNAMIC_TP_ATR_MULTIPLIER = 3.0  # Multiplier for ATR to set dynamic take profit
CHECK_EXIT_INTERVAL = 60  # Check and update exit levels every 60 seconds
```

## Trailing Stop Loss

The trailing stop loss feature works as follows:

1. When a trade is opened, the bot monitors the trade's profit
2. Once the profit reaches `TRAILING_STOP_ACTIVATION_PIPS` (default: 15 pips), the trailing stop is activated
3. The stop loss is then moved to maintain a distance of `TRAILING_STOP_DISTANCE_PIPS` (default: 10 pips) from the highest/lowest price reached
4. For buy positions, the stop loss only moves up (never down)
5. For sell positions, the stop loss only moves down (never up)

This allows you to:
- Lock in profits as the market moves in your favor
- Let winning trades run while protecting accumulated profits
- Automatically exit the trade if the market reverses

## Dynamic Take Profit

The dynamic take profit feature works as follows:

1. The bot calculates the Average True Range (ATR) for the symbol
2. The take profit level is set at a distance of `ATR * DYNAMIC_TP_ATR_MULTIPLIER` from the entry price
3. For buy positions: TP = Entry Price + (ATR * Multiplier)
4. For sell positions: TP = Entry Price - (ATR * Multiplier)

This ensures that:
- Take profit levels adapt to current market volatility
- In volatile markets, take profit is set further away to capture larger moves
- In quiet markets, take profit is set closer to lock in profits sooner

## How It Works Together

The bot checks and updates exit levels for all open positions every `CHECK_EXIT_INTERVAL` seconds (default: 60 seconds). This means:

1. As a trade moves in your favor, the trailing stop will move to lock in profits
2. If market volatility increases, the dynamic take profit may adjust to capture larger moves
3. The trade will exit when either:
   - Price hits the trailing stop loss (market reverses)
   - Price hits the dynamic take profit (profit target reached)
   - You manually close the position

## Recommended Settings

- **Trending Markets**: Use a larger `TRAILING_STOP_DISTANCE_PIPS` (15-20 pips) to avoid getting stopped out by normal market fluctuations
- **Volatile Markets**: Increase `DYNAMIC_TP_ATR_MULTIPLIER` (4.0-5.0) to capture larger price swings
- **Ranging Markets**: Use a smaller `TRAILING_STOP_DISTANCE_PIPS` (5-10 pips) to lock in profits quickly

## Monitoring

The bot logs all trailing stop and dynamic take profit adjustments:
- In the console output
- In the trade log file
- Via Discord notifications (if configured)

This allows you to monitor how the exit strategy is performing and make adjustments as needed.
