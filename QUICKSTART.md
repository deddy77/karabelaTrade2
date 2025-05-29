# KarabelaTrade Bot Quick Start Guide

## Installation

### Windows
1. Double-click `install.bat`
2. Wait for the installation to complete
3. Press any key to close the installer

### Linux/Mac
1. Open terminal in the KBT2 directory
2. Run: `chmod +x install.sh`
3. Run: `./install.sh`

## Configuration

1. Open `config.py` and set:
   - Discord webhook URL (optional)
   - Risk parameters (if needed)
   - Trading pairs in SYMBOL_SETTINGS

2. Make sure MetaTrader 5 is:
   - Installed and running
   - Logged in to your account
   - AutoTrading enabled
   - Allow algorithmic trading enabled

## Running the Bot

1. Start MetaTrader 5
2. Double-click `run_gui.py` or run:
   ```bash
   python run_gui.py
   ```

3. In the GUI:
   - Click "Start Bot"
   - Monitor the Control Panel for status
   - Use Analysis tab to view charts
   - Check Sessions tab for active pairs

## GUI Features

### Control Panel Tab
- Start/Stop bot
- Account information
- Real-time status
- Log viewer

### Sessions Tab
- Active trading sessions
- Overlap periods
- Tradeable pairs status

### Positions Tab
- Open positions
- Position management
- Close trades

### Analysis Tab
- Technical analysis
- Interactive charts
- Market conditions
- Trading signals

### Diagnostics Tab
- Market health
- Risk metrics
- System status

## Troubleshooting

1. Can't start the bot:
   - Check MetaTrader 5 is running
   - Verify account login
   - Check AutoTrading is enabled

2. No charts showing:
   - Make sure all dependencies are installed
   - Check MetaTrader 5 connection
   - Verify market is open

3. Dependencies error:
   - Run installer again
   - Check Python version (3.8+ required)
   - Install packages manually:
     ```bash
     pip install MetaTrader5 pandas numpy matplotlib mplfinance
     ```

## Support

For issues:
1. Check the log files in `logs/` directory
2. Review error messages in the GUI
3. Verify settings in `config.py`

## Safety Notes

- Always test in a demo account first
- Start with small position sizes
- Monitor risk levels
- Check market conditions before trading
