"""Telegram notification handler for KarabelaTrade"""
import json
import requests
from datetime import datetime
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, ENABLE_TELEGRAM_NOTIFICATIONS

def send_telegram_notification(message):
    """
    Send a notification to Telegram
    Returns True if successful, False otherwise
    """
    if not ENABLE_TELEGRAM_NOTIFICATIONS:
        return True

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Warning: Telegram notifications enabled but token or chat ID not set")
        return False

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }

        response = requests.post(
            url,
            data=json.dumps(data),
            headers={"Content-Type": "application/json"}
        )

        if response.status_code == 200:
            return True
        else:
            print(f"Failed to send Telegram notification: {response.status_code}")
            if response.status_code == 400:
                print(f"Response content: {response.text}")
            return False

    except Exception as e:
        print(f"Error sending Telegram notification: {str(e)}")
        return False

def send_trend_conflict_notification(symbol, long_term_trend, short_term_momentum, confidence="MEDIUM"):
    """
    Send notification when trend conflict is detected
    """
    if not ENABLE_TELEGRAM_NOTIFICATIONS:
        return True

    message = f"🚨 <b>TREND CONFLICT DETECTED</b> - {symbol}\n"
    message += f"📈 Long-term: <b>{long_term_trend}</b>\n"
    message += f"📉 Short-term: <b>{short_term_momentum}</b>\n"
    message += f"⏳ Trading halted until conflict resolves\n"
    message += f"🎯 Confidence: {confidence}"

    return send_telegram_notification(message)

def send_position_risk_notification(symbol, position_type, recommendation, confidence="MEDIUM"):
    """
    Send notification when existing position may be at risk
    """
    if not ENABLE_TELEGRAM_NOTIFICATIONS:
        return True

    position_emoji = "🟢" if position_type.upper() == "LONG" else "🔴"
    message = f"⚠️ <b>POSITION RISK ALERT</b> - {symbol}\n"
    message += f"{position_emoji} Existing <b>{position_type.upper()}</b> position may be at risk\n"
    message += f"📊 Current recommendation: <b>{recommendation}</b>\n"
    message += f"🔧 Consider manual review or tighter stop losses\n"
    message += f"🎯 Confidence: {confidence}"

    return send_telegram_notification(message)

def send_pattern_detection_notification(symbol, patterns, signal):
    """
    Send notification when significant candlestick patterns are detected
    """
    if not ENABLE_TELEGRAM_NOTIFICATIONS:
        return True

    if not patterns or signal == "NEUTRAL":
        return True

    signal_emoji = "🟢" if signal == "BULLISH" else "🔴" if signal == "BEARISH" else "⚠️"
    message = f"📊 <b>PATTERN DETECTED</b> - {symbol}\n"
    message += f"{signal_emoji} Signal: <b>{signal}</b>\n"

    # Add top 3 most significant patterns
    for i, pattern in enumerate(patterns[:3]):
        strength_emoji = "🔥" if pattern['strength'] == "VERY_HIGH" else "🟡" if pattern['strength'] == "HIGH" else "🔵"
        message += f"{strength_emoji} {pattern['pattern']}: {pattern['type']} ({pattern['strength']})\n"

    return send_telegram_notification(message)

def send_enhanced_trade_notification(symbol, action, lot_size, price, reason=None, confidence=None, timeframe="M5"):
    """
    Send enhanced trade notification with more context
    """
    if not ENABLE_TELEGRAM_NOTIFICATIONS:
        return True

    action_emoji = "🟢" if action.upper() == "BUY" else "🔴" if action.upper() == "SELL" else "🟠"
    message = f"{action_emoji} <b>{action.upper()} SIGNAL</b> - {symbol} ({timeframe})\n"
    message += f"💰 Volume: <b>{lot_size}</b> lots at <b>{price}</b>\n"

    if reason:
        message += f"📊 Reason: {reason}\n"
    if confidence:
        message += f"🎯 Confidence: {confidence}"

    return send_telegram_notification(message)

def test_telegram_notification():
    """Test Telegram notification settings"""
    if not ENABLE_TELEGRAM_NOTIFICATIONS:
        print("Telegram notifications are disabled")
        return True

    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram bot token or chat ID not set")
        return False

    success = send_telegram_notification("🤖 KarabelaTrade Bot test notification")
    if success:
        print("Telegram notification test successful")
    else:
        print("Telegram notification test failed")
    return success

if __name__ == "__main__":
    test_telegram_notification()
