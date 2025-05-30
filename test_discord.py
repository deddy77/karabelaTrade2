#!/usr/bin/env python3
"""Test Discord notifications for KarabelaTrade Bot"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from discord_notify import send_discord_notification
from config import ENABLE_DISCORD_NOTIFICATIONS, DISCORD_WEBHOOK_URL

def test_discord_notifications():
    """Test Discord notification functionality"""
    print("🧪 Testing Discord Notifications...")
    print(f"Discord Enabled: {ENABLE_DISCORD_NOTIFICATIONS}")
    print(f"Webhook URL: {'Set' if DISCORD_WEBHOOK_URL else 'Not Set'}")

    if not ENABLE_DISCORD_NOTIFICATIONS:
        print("❌ Discord notifications are disabled in config")
        return False

    if not DISCORD_WEBHOOK_URL:
        print("❌ Discord webhook URL is not configured")
        return False

    # Test basic notification
    test_message = (
        "🧪 **DISCORD TEST** - KarabelaTrade Bot\n"
        "📊 **Status:** Discord notifications are now active!\n"
        "🔧 **Features:**\n"
        "• Trend conflict alerts\n"
        "• Position updates (BUY/SELL)\n"
        "• Risk warnings\n"
        "• Order execution status\n"
        "✅ **System:** Ready for live trading notifications"
    )

    print("\n📤 Sending test message...")
    result = send_discord_notification(test_message)

    if result:
        print("✅ Discord notification sent successfully!")
        return True
    else:
        print("❌ Failed to send Discord notification")
        return False

if __name__ == "__main__":
    success = test_discord_notifications()
    sys.exit(0 if success else 1)
