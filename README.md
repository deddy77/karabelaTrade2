# KarabelaTrade Bot

A multi-pair trading bot with advanced analysis and visualization capabilities.

## Features

- Multi-pair trading with session-based management
- Real-time technical analysis
- Price charts with indicators
- Position tracking and risk management
- Discord notifications
- Session-aware trading windows
- Market diagnostics and health monitoring

## Installation

1. Install Python 3.8 or higher
2. Install MetaTrader 5
3. Install required packages:

```bash
pip install -r requirements.txt
```

## Setup

1. Configure MetaTrader 5:
   - Enable automated trading
   - Allow DLL imports
   - Configure your account credentials

2. Configure the bot:
   - Copy `config_example.py` to `config.py`
   - Update settings in `config.py`:
     * Trading pairs
     * Risk parameters
     * Session times
     * Discord webhook (optional)

## Running the Bot

### GUI Mode (Recommended)

Start the bot with the graphical interface:

```bash
python run_gui.py
```

The GUI provides:
- Real-time trading status
- Session management
- Position monitoring
- Technical analysis with charts
- Risk metrics
- Trading controls

### Chart Features

The bot includes advanced charting capabilities:
- Candlestick charts
- Moving averages (20, 50, 200 periods)
- RSI indicator
- Volume analysis
- Support/Resistance levels
- Session markers

To view charts:
1. Select a pair in the Analysis tab
2. Click "Show Chart"
3. Use the chart controls to:
   - Change timeframes
   - Toggle indicators
   - Analyze market conditions

### Trading Sessions

The bot manages trading based on major forex sessions:
- Sydney (17:00-02:00 EST)
- Tokyo (20:00-05:00 EST)
- London (03:00-12:00 EST)
- New York (08:00-17:00 EST)

Overlap periods are handled automatically for optimal trading conditions.

### Risk Management

Built-in risk management features:
- Per-trade risk limits
- Session-based position sizing
- Dynamic leverage control
- Drawdown protection
- Spread monitoring

## Configuration Options

### Core Settings (config.py)
```python
SYMBOL = "EURUSD"  # Default trading symbol
TIMEFRAME = "M5"   # Default timeframe
RISK_PER_TRADE = 1.0  # Risk percentage per trade
MAX_SPREAD = 20    # Maximum allowed spread
```

### Discord Notifications

To enable Discord notifications:
1. Create a webhook in your Discord server
2. Set `ENABLE_DISCORD_NOTIFICATIONS = True`
3. Add your webhook URL to `DISCORD_WEBHOOK_URL`

### Trading Sessions

Configure session times in `session_manager.py`:
```python
TRADING_SESSIONS = {
    "SYDNEY": {
        "start": "17:00",
        "end": "02:00",
        "pairs": ["AUDUSD", "NZDUSD", ...]
    },
    # Other sessions...
}
```

## Monitoring and Analysis

### Real-time Diagnostics
- Market health monitoring
- Spread analysis
- Session status
- Position tracking
- Risk metrics

### Technical Analysis
- Trend identification
- Support/Resistance levels
- Volume analysis
- Volatility measures
- Multiple timeframe analysis

## Troubleshooting

Common issues and solutions:

1. Connection Issues:
   ```
   Error: Failed to connect to MetaTrader 5
   ```
   - Verify MT5 is running
   - Check account credentials
   - Enable AutoTrading

2. Chart Display Issues:
   ```
   Error: Failed to get chart data
   ```
   - Install required packages
   - Check internet connection
   - Verify symbol availability

## Development

Contributing:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

### Testing

Run tests with:
```bash
python -m unittest tests/
```

## License

This project is licensed under the MIT License - see LICENSE file for details.

## Disclaimer

Trading forex carries significant risk. This bot is for educational purposes only. 
Always test thoroughly in a demo account first.
