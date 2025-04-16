# Script to package the trading bot for deployment
# PowerShell version of package_bot.sh

# Create temporary directory
New-Item -ItemType Directory -Force -Path "trading-bot-deploy"

# Copy all necessary files
Copy-Item "main.py" "trading-bot-deploy\"
Copy-Item "*.py" "trading-bot-deploy\"  # All other Python files
Copy-Item "requirements.txt" "trading-bot-deploy\"
Copy-Item "deployment_guide.txt" "trading-bot-deploy\"
Copy-Item -Recurse "logs" "trading-bot-deploy\"  # Copy logs directory if needed

# Create zip package
Compress-Archive -Path "trading-bot-deploy" -DestinationPath "trading-bot-deploy.zip" -Force

# Clean up
Remove-Item -Recurse -Force "trading-bot-deploy"

Write-Output "Package created: trading-bot-deploy.zip"
Write-Output "Transfer this zip file to your Azure VM and follow the deployment guide"
