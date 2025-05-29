"""Test the enhanced position detection fix"""
from enhanced_position_detection import debug_position_detection
from mt5_helper import connect

def test_fix():
    """Test the position detection fix"""
    print("🧪 Testing Enhanced Position Detection Fix...")

    if not connect():
        print("❌ Failed to connect to MT5")
        return

    debug_position_detection("EURUSD")

if __name__ == "__main__":
    test_fix()
