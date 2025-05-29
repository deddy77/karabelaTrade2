# Use Python 3.8 as base image
FROM python:3.8-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    DEBIAN_FRONTEND=noninteractive

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libx11-6 \
    libxext6 \
    libxrender1 \
    libxinerama1 \
    libxi6 \
    libxrandr2 \
    libxcursor1 \
    libxtst6 \
    tk-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p logs/trades logs/analysis logs/diagnostics data/charts

# Set Python path
ENV PYTHONPATH=/app

# Create non-root user
RUN groupadd -r tradingbot && \
    useradd -r -g tradingbot -d /app -s /sbin/nologin -c "Trading Bot User" tradingbot && \
    chown -R tradingbot:tradingbot /app

# Switch to non-root user
USER tradingbot

# Set up environment check and initialization
RUN python initialize.py

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import MetaTrader5 as mt5; exit(0 if mt5.initialize() else 1)"

# Default command (can be overridden)
CMD ["python", "run_gui.py"]

# Additional metadata
LABEL maintainer="KarabelaTrade Team" \
      version="2.0.0" \
      description="KarabelaTrade Bot - Forex Trading Bot" \
      repository="https://github.com/karabelatrade/kbt2"

# Documentation for users
COPY README.md QUICKSTART.md ./

# Usage instructions in container
RUN echo '#!/bin/bash\n\
echo "KarabelaTrade Bot Container"\n\
echo "-------------------------"\n\
echo "Available commands:"\n\
echo "  python run_gui.py         - Start the trading bot"\n\
echo "  python -m pytest          - Run tests"\n\
echo "  python format_code.py     - Format code"\n\
echo "  python version_check.py   - Check version"\n\
' > /app/usage.sh && chmod +x /app/usage.sh

# Volume for persistent data
VOLUME ["/app/data", "/app/logs"]

# Expose port for future web interface
EXPOSE 8080

# Note: When running the container, you'll need to:
# 1. Mount the config file: -v /path/to/config.py:/app/config.py
# 2. Mount the data directory: -v /path/to/data:/app/data
# 3. Mount the logs directory: -v /path/to/logs:/app/logs
# 4. Set environment variables for MT5 connection if needed
# Example:
# docker run -d \
#   -v /path/to/config.py:/app/config.py \
#   -v /path/to/data:/app/data \
#   -v /path/to/logs:/app/logs \
#   -e MT5_LOGIN=your_login \
#   -e MT5_PASSWORD=your_password \
#   -e MT5_SERVER=your_server \
#   karabelatrade/kbt2:latest
