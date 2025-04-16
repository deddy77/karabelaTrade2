#!/bin/bash
# Script to package the trading bot for deployment

# Create temporary directory
mkdir -p trading-bot-deploy

# Copy all necessary files
cp main.py trading-bot-deploy/
cp *.py trading-bot-deploy/  # All other Python files
cp requirements.txt trading-bot-deploy/
cp deployment_guide.txt trading-bot-deploy/
cp -r logs trading-bot-deploy/  # Copy logs directory if needed

# Create zip package
zip -r trading-bot-deploy.zip trading-bot-deploy

# Clean up
rm -rf trading-bot-deploy

echo "Package created: trading-bot-deploy.zip"
echo "Transfer this zip file to your Azure VM and follow the deployment guide"
