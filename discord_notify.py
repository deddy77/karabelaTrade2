# ================================
# ai-trading-bot/discord_notify.py
# ================================

import requests
import json
from config import DISCORD_WEBHOOK_URL

def send_discord_notification(message):
    """Send notification to Discord webhook"""
    if not DISCORD_WEBHOOK_URL:
        print("Discord webhook URL not configured. Skipping notification.")
        return False
    
    data = {
        "content": message,
        "username": "Karabela Trading Bot"
    }
    
    try:
        response = requests.post(
            DISCORD_WEBHOOK_URL,
            data=json.dumps(data),
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 204:
            print("Discord notification sent successfully")
            return True
        else:
            print(f"Failed to send Discord notification. Status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"Error sending Discord notification: {e}")
        return False