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
            "username": "KarabelaTrade Bot"
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
            if response.status_code == 400:
                print(f"Response content: {response.text}")
            return False

    except Exception as e:
        print(f"Error sending Discord notification: {str(e)}")
        return False

def send_trend_conflict_notification(symbol, long_term_trend, short_term_momentum, confidence="MEDIUM"):
    """
    Send notification when trend conflict is detected
    """
    if not ENABLE_DISCORD_NOTIFICATIONS:
        return True

    message = f"🚨 **TREND CONFLICT DETECTED** - {symbol}\n"
    message += f"📈 Long-term: **{long_term_trend}**\n"
    message += f"📉 Short-term: **{short_term_momentum}**\n"
    message += f"⏳ Trading halted until conflict resolves\n"
    message += f"🎯 Confidence: {confidence}"

    return send_discord_notification(message)

def send_position_risk_notification(symbol, position_type, recommendation, confidence="MEDIUM"):
    """
    Send notification when existing position may be at risk
    """
    if not ENABLE_DISCORD_NOTIFICATIONS:
        return True

    position_emoji = "🟢" if position_type.upper() == "LONG" else "🔴"
    message = f"⚠️ **POSITION RISK ALERT** - {symbol}\n"
    message += f"{position_emoji} Existing **{position_type.upper()}** position may be at risk\n"
    message += f"📊 Current recommendation: **{recommendation}**\n"
    message += f"🔧 Consider manual review or tighter stop losses\n"
    message += f"🎯 Confidence: {confidence}"

    return send_discord_notification(message)

def send_recommendation_change_notification(symbol, old_recommendation, new_recommendation, confidence="MEDIUM"):
    """
    Send notification when trading recommendation changes
    """
    if not ENABLE_DISCORD_NOTIFICATIONS:
        return True

    # Skip notification if recommendation hasn't actually changed
    if old_recommendation == new_recommendation:
        return True

    message = f"🎯 **RECOMMENDATION CHANGE** - {symbol}\n"
    message += f"📊 Changed from **{old_recommendation}** → **{new_recommendation}**\n"
    message += f"🎯 Confidence: {confidence}"

    return send_discord_notification(message)

def send_pattern_detection_notification(symbol, patterns, signal):
    """
    Send notification when significant candlestick patterns are detected
    """
    if not ENABLE_DISCORD_NOTIFICATIONS:
        return True

    if not patterns or signal == "NEUTRAL":
        return True

    signal_emoji = "🟢" if signal == "BULLISH" else "🔴" if signal == "BEARISH" else "⚠️"
    message = f"📊 **PATTERN DETECTED** - {symbol}\n"
    message += f"{signal_emoji} Signal: **{signal}**\n"

    # Add top 3 most significant patterns
    for i, pattern in enumerate(patterns[:3]):
        strength_emoji = "🔥" if pattern['strength'] == "VERY_HIGH" else "🟡" if pattern['strength'] == "HIGH" else "🔵"
        message += f"{strength_emoji} {pattern['pattern']}: {pattern['type']} ({pattern['strength']})\n"

    return send_discord_notification(message)

def send_enhanced_trade_notification(symbol, action, lot_size, price, reason=None, confidence=None, timeframe="M5"):
    """
    Send enhanced trade notification with more context
    """
    if not ENABLE_DISCORD_NOTIFICATIONS:
        return True

    action_emoji = "🟢" if action.upper() == "BUY" else "🔴" if action.upper() == "SELL" else "🟠"
    message = f"{action_emoji} **{action.upper()} SIGNAL** - {symbol} ({timeframe})\n"
    message += f"💰 Volume: **{lot_size}** lots at **{price}**\n"

    if reason:
        message += f"📊 Reason: {reason}\n"
    if confidence:
        message += f"🎯 Confidence: {confidence}"

    return send_discord_notification(message)

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
