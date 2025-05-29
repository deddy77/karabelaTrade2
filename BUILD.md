# Building KarabelaTrade Bot

## Development Installation

### Windows
1. Clone the repository
2. Run `build_package.bat`
   - Creates virtual environment
   - Installs dependencies
   - Builds package
   - Installs in development mode
   - Runs environment tests

### Linux/Mac
1. Clone the repository
2. Make script executable:
   ```bash
   chmod +x build_package.sh
   ```
3. Run the build script:
   ```bash
   ./build_package.sh
   ```

## Manual Installation Steps

1. Create virtual environment:
   ```bash
   python -m venv venv
   ```

2. Activate virtual environment:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`

3. Install build tools:
   ```bash
   python -m pip install --upgrade pip
   pip install wheel build twine
   ```

4. Build package:
   ```bash
   python -m build
   ```

5. Install in development mode:
   ```bash
   pip install -e .
   ```

## Running Tests
After installation:
```bash
python test_environment.py
```

## Command Line Tools
The installation provides these commands:
- `karabelatrade` - Launch the trading bot
- `kbt-test` - Run environment tests
- `kbt-version` - Show version information

## Creating Distribution Packages

### Source Distribution
```bash
python -m build --sdist
```

### Wheel Distribution
```bash
python -m build --wheel
```

### Both Source and Wheel
```bash
python -m build
```

## Directory Structure
```
KBT2/
├── data/              # Data storage
├── logs/              # Log files
│   ├── trades/       # Trade logs
│   ├── analysis/     # Analysis logs
│   └── diagnostics/  # System diagnostics
├── tests/            # Test files
└── karabelatrade/    # Main package
```

## Package Contents
- GUI application
- Technical analysis tools
- Session management
- Risk management
- MT5 integration
- Discord notifications

## Development Guidelines

### Code Style
- Follow PEP 8
- Use type hints
- Include docstrings
- Write unit tests

### Git Workflow
1. Create feature branch
2. Make changes
3. Run tests
4. Submit pull request

### Version Control
Version numbers follow semantic versioning:
- MAJOR version for incompatible API changes
- MINOR version for new features
- PATCH version for bug fixes

## Common Issues

### Installation Problems
1. Python version mismatch:
   - Ensure Python 3.8 or higher
   - Check `python --version`

2. Missing dependencies:
   - Run `pip install -r requirements.txt`
   - Check error messages for specific packages

3. MT5 connection issues:
   - Verify MetaTrader 5 is installed
   - Check MT5 terminal is running
   - Enable AutoTrading

### Build Issues
1. Virtual environment problems:
   - Delete venv directory
   - Create new environment
   - Reinstall dependencies

2. Permission errors:
   - Run as administrator (Windows)
   - Use sudo (Linux)

3. Path issues:
   - Ensure correct working directory
   - Check PATH environment variable

## Support
For issues:
1. Check error logs
2. Review documentation
3. Submit detailed bug report
