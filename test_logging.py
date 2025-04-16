import os
from datetime import datetime

def write_diagnostic_log(symbol, message):
    """Write diagnostic messages to a log file"""
    os.makedirs("logs", exist_ok=True)
    log_file = f"logs/{symbol}_diagnostics.log"
    with open(log_file, "a") as f:
        f.write(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - {message}\n")

# Test the logging function
write_diagnostic_log("TEST", "This is a test message")
print("Test log message written")
