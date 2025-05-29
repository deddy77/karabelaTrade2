"""Debug script to check all positions and identify the magic number issue"""
import MetaTrader5 as mt5
from mt5_helper import connect
from config import SYMBOL, MAGIC_NUMBER

def debug_all_positions():
    """Check all positions to see what magic numbers they have"""
    print("🔍 Debugging Position Detection...")

    if not connect():
        print("❌ Failed to connect to MT5")
        return

    # Get ALL positions (no filtering)
    all_positions = mt5.positions_get()
    if not all_positions:
        print("❌ No positions found at all")
        return

    print(f"\n📊 Found {len(all_positions)} total positions:")
    print("=" * 60)

    for i, pos in enumerate(all_positions):
        print(f"Position {i+1}:")
        print(f"  Symbol: {pos.symbol}")
        print(f"  Type: {'BUY' if pos.type == 0 else 'SELL'}")
        print(f"  Volume: {pos.volume}")
        print(f"  Magic: {pos.magic}")
        print(f"  Ticket: {pos.ticket}")
        print(f"  Comment: {pos.comment}")
        print(f"  Open Price: {pos.price_open}")
        print(f"  Current Price: {pos.price_current}")
        print(f"  Profit: {pos.profit}")
        print("-" * 40)

    # Check EURUSD positions specifically
    eurusd_positions = mt5.positions_get(symbol=SYMBOL)
    if eurusd_positions:
        print(f"\n📈 {SYMBOL} positions found: {len(eurusd_positions)}")
        for pos in eurusd_positions:
            print(f"  {'BUY' if pos.type == 0 else 'SELL'} {pos.volume} lots, Magic: {pos.magic}")
    else:
        print(f"\n❌ No {SYMBOL} positions found")

    # Check what our bot's magic number filter finds
    print(f"\n🤖 Bot's Magic Number: {MAGIC_NUMBER}")
    bot_positions = [pos for pos in all_positions if pos.magic == MAGIC_NUMBER]
    print(f"Positions matching bot's magic number: {len(bot_positions)}")

    if bot_positions:
        for pos in bot_positions:
            print(f"  {pos.symbol}: {'BUY' if pos.type == 0 else 'SELL'} {pos.volume} lots")

    return all_positions

def test_position_functions():
    """Test the current position detection functions"""
    from mt5_helper import has_buy_position, has_sell_position, get_positions

    print(f"\n🧪 Testing Position Detection Functions:")
    print(f"has_buy_position('{SYMBOL}'): {has_buy_position(SYMBOL)}")
    print(f"has_sell_position('{SYMBOL}'): {has_sell_position(SYMBOL)}")

    positions = get_positions(SYMBOL)
    print(f"get_positions('{SYMBOL}'): {len(positions)} positions")
    for pos in positions:
        print(f"  {'BUY' if pos.type == 0 else 'SELL'} {pos.volume} lots, Magic: {pos.magic}")

if __name__ == "__main__":
    all_pos = debug_all_positions()
    test_position_functions()
