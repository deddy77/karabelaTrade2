"""Test the enhanced strategy with position detection fix"""
from strategy import check_signal_and_trade
from mt5_helper import connect

def test_strategy_fix():
    """Test the enhanced strategy with position detection"""
    print("🧪 Testing Enhanced Strategy with Position Detection Fix...")
    print("=" * 70)

    if not connect():
        print("❌ Failed to connect to MT5")
        return

    print("✅ Connected to MT5")
    print("\n🚀 Running enhanced strategy check...")
    print("This should now detect ALL positions and show risk warnings!")
    print("=" * 70)

    # Run the enhanced strategy
    check_signal_and_trade("EURUSD")

if __name__ == "__main__":
    test_strategy_fix()
