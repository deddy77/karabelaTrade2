# Backtesting Framework Guide

This document explains how to use the backtesting framework to evaluate and optimize trading strategies.

## Overview

The backtesting framework allows you to:

1. Test your trading strategy on historical data
2. Optimize strategy parameters
3. Analyze performance metrics
4. Perform multi-symbol backtests
5. Conduct walk-forward analysis

## Getting Started

### Prerequisites

Before using the backtesting framework, ensure you have all required dependencies installed:

```bash
pip install -r requirements.txt
```

### Running a Backtest

To run a backtest, use the `run_backtest.py` script:

```bash
python run_backtest.py
```

This will present you with several options:

1. Run backtest for a single symbol
2. Run parameter optimization
3. Run multi-symbol backtest
4. Run walk-forward analysis

## Backtesting Features

### Single Symbol Backtest

This option allows you to test your strategy on a single symbol with the current configuration settings. The backtest will:

- Fetch historical data for the specified symbol and timeframe
- Apply the trading strategy rules
- Generate entry and exit signals
- Track trades and calculate performance metrics
- Produce an equity curve and detailed trade list

### Parameter Optimization

This option helps you find the optimal parameters for your strategy by:

- Testing multiple parameter combinations
- Evaluating each combination on historical data
- Ranking results based on profitability, win rate, and other metrics
- Identifying the best-performing parameter set

You can optimize various parameters including:
- Moving average periods
- AMA gap percentage
- ADX threshold
- RSI settings

### Multi-Symbol Backtest

This option allows you to test your strategy across multiple symbols to:

- Evaluate strategy performance across different markets
- Identify which symbols work best with your strategy
- Calculate aggregate performance metrics
- Compare results between symbols

### Walk-Forward Analysis

Walk-forward analysis is an advanced technique that helps validate your strategy's robustness by:

1. Dividing historical data into multiple windows
2. For each window:
   - Optimizing parameters on the in-sample portion
   - Testing those parameters on the out-of-sample portion
3. Analyzing the out-of-sample results to determine if the strategy is robust

This approach helps prevent curve-fitting and provides a more realistic assessment of strategy performance.

## Understanding Backtest Results

### Performance Metrics

The backtest results include the following key metrics:

- **Total Trades**: Number of trades executed during the backtest period
- **Win Rate**: Percentage of profitable trades
- **Profit Factor**: Gross profit divided by gross loss
- **Total Profit**: Total profit in pips and money
- **Average Profit/Loss**: Average profit and loss per trade
- **Maximum Drawdown**: Largest peak-to-trough decline in equity
- **Average Trade Duration**: Average time a trade was held

### Output Files

The backtest framework generates several output files in the `backtest_results` directory:

- **JSON Results**: Complete backtest results including all metrics and parameters
- **CSV Trade List**: Detailed list of all trades with entry/exit times, prices, and results
- **Equity Curve Chart**: Visual representation of account equity over time
- **Parameter Optimization Results**: For optimization runs, the best parameters are saved

## Advanced Usage

### Custom Parameter Ranges

You can modify the parameter ranges in `run_backtest.py` to test different values:

```python
parameter_ranges = {
    'ma_medium': [20, 50, 100],
    'ma_long': [100, 200, 300],
    'min_ama_gap_percent': [0.03, 0.05, 0.1],
    'adx_threshold': [20, 25, 30]
}
```

### Extending the Framework

The backtesting framework is designed to be modular and extensible. You can:

1. Add new indicators in the `strategy.py` file
2. Implement custom entry/exit rules in the `check_entry_signals` and `check_exit_signals` methods
3. Add new performance metrics to the `BacktestResult` class
4. Create custom visualization functions

## Interpreting Results

When analyzing backtest results, consider the following:

1. **Statistical Significance**: Ensure you have enough trades to draw meaningful conclusions
2. **Robustness**: Check if the strategy performs well across different symbols and time periods
3. **Parameter Sensitivity**: If small parameter changes drastically affect results, the strategy may be curve-fitted
4. **Drawdown**: Consider the maximum drawdown relative to total returns
5. **Win Rate vs. Profit Factor**: A strategy with a lower win rate but higher profit factor may be preferable

## Best Practices

1. **Start Simple**: Begin with a single symbol and basic parameters
2. **Validate Assumptions**: Use walk-forward analysis to validate your strategy
3. **Avoid Overfitting**: Don't optimize too many parameters simultaneously
4. **Consider Transaction Costs**: Include spread and commission in your analysis
5. **Test Different Market Conditions**: Ensure your strategy works in trending and ranging markets
6. **Compare to Benchmark**: Compare your strategy to a simple buy-and-hold approach

## Troubleshooting

### Common Issues

1. **No Data Available**: Ensure you have historical data for the specified symbol and timeframe
2. **No Trades Generated**: Check if your entry/exit conditions are too restrictive
3. **Memory Errors**: Reduce the amount of historical data or optimize your code
4. **Unrealistic Results**: Verify that your backtest includes spread, slippage, and other real-world factors

## Future Enhancements

The backtesting framework will be enhanced with:

1. **Machine Learning Integration**: As outlined in `ml_integration_design.md`
2. **Monte Carlo Simulation**: To assess the probability distribution of returns
3. **Portfolio Backtesting**: To test multiple strategies simultaneously
4. **Risk-Adjusted Metrics**: Sharpe ratio, Sortino ratio, and other risk-adjusted performance metrics
5. **Interactive Visualizations**: More detailed and interactive charts

## Conclusion

The backtesting framework provides a comprehensive set of tools to evaluate and optimize your trading strategy. By thoroughly testing your strategy on historical data, you can gain confidence in its performance before deploying it in a live trading environment.

Remember that past performance is not indicative of future results, and backtesting should be just one component of your overall strategy development process.
