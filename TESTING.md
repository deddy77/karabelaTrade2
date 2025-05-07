# Testing Guide

This document describes the testing setup and how to run tests for the trading bot.

## Test Structure

The tests are organized into several test suites:

1. `test_session_manager.py` - Tests for session management and trading hours
   - Session detection and prioritization
   - Currency pair selection based on sessions
   - Overlap period handling
   - Trading parameter adjustments

2. `test_config.py` - Tests for configuration settings
   - Dynamic symbol list generation
   - Symbol settings management
   - Timeframe configuration

## Running Tests

There are several ways to run the tests:

### 1. Run All Tests

Use the test runner script:
```bash
python run_tests.py
```

This will run all test suites and provide a detailed report, including:
- Test execution results
- Session time coverage
- Pair coverage by category
- Feature coverage analysis
- Overall statistics

### 2. Run Individual Test Suites

To run specific test suites:
```bash
# Run session manager tests
python -m unittest test_session_manager.py -v

# Run configuration tests
python -m unittest test_config.py -v
```

### 3. Run Specific Test Cases

To run a specific test case:
```bash
python -m unittest test_session_manager.py -k test_pair_priority_in_overlap
```

## Test Coverage Analysis

The test runner provides comprehensive coverage analysis:

### 1. Session Time Coverage
- Regular trading sessions (Sydney, Tokyo, London, New York)
- Overlap periods (Sydney-Tokyo, Tokyo-London, London-NY)
- Quiet periods between sessions
- Multiple test points within each session

### 2. Currency Pair Coverage
Tracks testing coverage across:
- Major Pairs (EUR/USD, GBP/USD, etc.)
- Cross Pairs (EUR/GBP, EUR/JPY, etc.)
- Commodity Pairs (AUD/USD, USD/CAD, etc.)
- Exotic Pairs (EUR/NOK, USD/SGD, etc.)

### 3. Feature Coverage
Monitors implementation of:
- Session Management Features
  - Regular session detection
  - Overlap period detection
  - Quiet period detection
  - Session transitions
- Pair Priority Features
  - Primary pair handling
  - Secondary pair handling
  - Cross pair handling
  - Overlap pair priority
- Trading Parameters
  - Timeframe adjustments
  - Spread requirements
  - Lot size multipliers
  - Stop loss / Take profit
- Configuration Features
  - Dynamic symbol generation
  - Session-based settings
  - Parameter inheritance
  - Default handling

### 4. Statistics and Reporting
The test runner generates:
- Overall test success rate
- Coverage percentages by category
- List of tested/untested pairs
- Feature implementation status
- Detailed failure reports

## Test Coverage Requirements

The test suite verifies:

### Session Management Tests (`test_session_manager.py`)
- ✓ Pair categorization (major, secondary, cross, exotic)
- ✓ Session detection and timing for all market sessions
- ✓ Currency pair prioritization (PRIMARY, SECONDARY, OVERLAP)
- ✓ Overlap period handling for three major overlaps
- ✓ Trading parameter adjustments (spreads, timeframes, lot sizes)
- ✓ Timeframe adjustments across different sessions
- ✓ Detailed pair statistics and analytics

### Configuration Tests (`test_config.py`)
- ✓ Dynamic symbol list generation from session manager
- ✓ Symbol settings generation with defaults
- ✓ Timeframe configuration and synchronization
- ✓ Session-based symbol filtering
- ✓ Trading parameter inheritance

### Key Metrics Verified
1. **Session Coverage**
   - Regular sessions: Sydney, Tokyo, London, New York
   - Overlap periods: Sydney-Tokyo, Tokyo-London, London-NY
   - Quiet periods: Proper pair deactivation

2. **Pair Categories**
   - Major pairs (e.g., EUR/USD, GBP/USD)
   - Secondary pairs (e.g., USD/CHF, EUR/CHF)
   - Cross pairs (e.g., EUR/GBP, AUD/NZD)
   - Exotic pairs (e.g., ZAR/JPY, SGD/JPY)

3. **Trading Parameters**
   - Timeframe adjustments (M1 during overlaps)
   - Spread requirements (tighter during overlaps)
   - Lot size multipliers
   - Priority levels

## Adding New Tests

When adding new functionality:

1. Create test cases before implementing features (TDD approach)
2. Place tests in appropriate test suite file
3. Add docstrings explaining test purpose
4. Include test in test_modules list in run_tests.py
5. Update coverage requirements if needed

## Best Practices

- Write descriptive test names that explain the behavior being tested
- Include docstrings for all test methods
- Test both success and failure cases
- Use meaningful assertions with descriptive messages
- Keep tests independent and isolated
- Monitor and maintain coverage metrics
- Document untested features and plan for coverage improvement
