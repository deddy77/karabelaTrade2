# Forex Trading Bot with Backtesting Framework

[![Test Coverage](https://img.shields.io/badge/test%20coverage-85%25-brightgreen.svg)](TESTING.md)

A comprehensive forex trading bot with strategy implementation, risk management, and backtesting capabilities.

## Features

- **Automated Trading**: Implements AMA50/AMA200 crossover strategy with multiple confirmation filters
- **Risk Management**: Dynamic position sizing based on account balance and market volatility
- **Exit Management**: Trailing stops and dynamic take profit levels
- **Backtesting Framework**: Test and optimize strategies on historical data
- **Multi-Symbol Support**: Trade multiple currency pairs simultaneously
- **Session-Based Trading**: Adjust parameters based on market sessions (Asian, London, New York)
- **Profit Management**: Daily profit targets and maximum loss limits

## Components

- **Main Trading System**:
  - `main.py`: Entry point for the trading bot
  - `strategy.py`: Trading strategy implementation
  - `risk_manager.py`: Position sizing and risk control
  - `exit_manager.py`: Trade exit management
  - `profit_manager.py`: Daily profit tracking
  - `mt5_helper.py`: MetaTrader 5 integration
  - `session_manager.py`: Market session management and pair selection

- **Testing Framework**:
  - `test_session_manager.py`: Tests for session management
  - `test_config.py`: Configuration validation tests
  - `run_tests.py`: Test runner script
  - See [Testing Guide](TESTING.md) for detailed testing documentation

- **Backtesting Framework**:
  - `backtest.py`: Core backtesting engine
  - `run_backtest.py`: User-friendly script to run backtests
  - `backtesting_guide.md`: Documentation for the backtesting framework

## Getting Started

### Prerequisites

- Python 3.8 or higher
- MetaTrader 5 installed
- Required Python packages (see `requirements.txt`)

### Installation

1. Clone the repository:
```
git clone https://github.com/yourusername/forex-trading-bot.git
cd forex-trading-bot
```

2. Install dependencies:
```
pip install -r requirements.txt
```

Note: For Windows users, if you need TA-Lib functionality, download the appropriate wheel file from [here](https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib) and install it with:
```
pip install path/to/downloaded/wheel/file.whl
```

### Configuration

Edit `config.py` to customize:
- Trading symbols (automatically selected based on active sessions)
- Timeframes (dynamically adjusted for session overlaps)
- Strategy parameters
- Risk management settings
- Exit strategy settings
- Session-specific parameters

### Testing

Run the test suite:
```bash
python run_tests.py
```

See the [Testing Guide](TESTING.md) for detailed information about:
- Test structure and organization
- Running specific test suites
- Adding new tests
- Testing best practices

## Usage

### Live Trading

Run the trading bot:
```
python main.py
```

### Backtesting

Run the backtesting framework:
```
python run_backtest.py
```

This will present you with several options:
1. Run backtest for a single symbol
2. Run parameter optimization
3. Run multi-symbol backtest
4. Run walk-forward analysis

## Documentation

- `TESTING.md`: Comprehensive testing guide
- `adx_filter_guide.md`: Guide to the ADX trend strength filter
- `exit_strategy_guide.md`: Documentation for the exit strategy features
- `ml_integration_design.md`: Design document for future ML integration
- `backtesting_guide.md`: Comprehensive guide to the backtesting framework

## Future Enhancements

- Machine Learning integration for improved signal generation
- Portfolio-level backtesting
- Monte Carlo simulation for risk assessment
- Web-based dashboard for monitoring and control

## License

This project is licensed under the MIT License - see the LICENSE file for details.
