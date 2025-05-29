"""Discord notification handler for KarabelaTrade"""
import json
import requests
from datetime import datetime
from config import DISCORD_WEBHOOK_URL, ENABLE_DISCORD_NOTIFICATIONS

def send_discord_notification(message):
    """
    Send a notification to Discord webhook
    Returns True if successful, False otherwise
    """
    if not ENABLE_DISCORD_NOTIFICATIONS:
        return True
        
    if not DISCORD_WEBHOOK_URL:
        print("Warning: Discord notifications enabled but webhook URL not set")
        return False
        
    try:
        data = {
            "content": message,
            "username": "KarabelaTrade Bot",
            "avatar_url": "",  # Optional bot avatar
            "embeds": [{
                "color": 3447003,  # Blue color
                "timestamp": datetime.utcnow().isoformat()
            }]
        }
        
        response = requests.post(
            DISCORD_WEBHOOK_URL,
            data=json.dumps(data),
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 204:
            return True
        else:
            print(f"Failed to send Discord notification: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"Error sending Discord notification: {str(e)}")
        return False

def test_discord_notification():
    """Test Discord notification settings"""
    if not ENABLE_DISCORD_NOTIFICATIONS:
        print("Discord notifications are disabled")
        return True
        
    if not DISCORD_WEBHOOK_URL:
        print("Discord webhook URL not set")
        return False
        
    success = send_discord_notification("🤖 KarabelaTrade Bot test notification")
    if success:
        print("Discord notification test successful")
    else:
        print("Discord notification test failed")
    return success

if __name__ == "__main__":
    test_discord_notification()
