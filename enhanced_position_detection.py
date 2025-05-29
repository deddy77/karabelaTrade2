"""Enhanced position detection to fix the magic number filtering issue"""
import MetaTrader5 as mt5
from mt5_helper import connect
from config import SYMBOL, MAGIC_NUMBER

def get_all_positions(symbol=None, include_all_magic=True):
    """Get all positions, optionally filtered by symbol and magic number"""
    if symbol:
        positions = mt5.positions_get(symbol=symbol)
    else:
        positions = mt5.positions_get()

    if positions is None:
        return []

    if include_all_magic:
        return list(positions)
    else:
        return [pos for pos in positions if pos.magic == MAGIC_NUMBER]

def has_position_any_magic(symbol=SYMBOL, position_type=None):
    """Check if there are any positions for the symbol, regardless of magic number"""
    positions = get_all_positions(symbol, include_all_magic=True)

    if position_type is None:
        return len(positions) > 0

    return any(pos.type == position_type for pos in positions)

def has_sell_position_any_magic(symbol=SYMBOL):
    """Check if there is an open sell position with any magic number"""
    return has_position_any_magic(symbol, mt5.ORDER_TYPE_SELL)

def has_buy_position_any_magic(symbol=SYMBOL):
    """Check if there is an open buy position with any magic number"""
    return has_position_any_magic(symbol, mt5.ORDER_TYPE_BUY)

def analyze_position_risk(symbol=SYMBOL, long_term_trend="BULLISH", short_term_momentum="BULLISH"):
    """Analyze if existing positions are at risk based on trend analysis"""
    all_positions = get_all_positions(symbol, include_all_magic=True)

    if not all_positions:
        return {"has_risk": False, "message": "No positions found"}

    risk_analysis = {
        "has_risk": False,
        "risky_positions": [],
        "safe_positions": [],
        "recommendations": []
    }

    for pos in all_positions:
        position_type = "BUY" if pos.type == mt5.ORDER_TYPE_BUY else "SELL"

        # Check for trend conflicts
        if position_type == "SELL" and long_term_trend == "BULLISH":
            risk_analysis["has_risk"] = True
            risk_analysis["risky_positions"].append({
                "ticket": pos.ticket,
                "type": position_type,
                "volume": pos.volume,
                "profit": pos.profit,
                "risk_reason": "SELL position against BULLISH trend"
            })
            risk_analysis["recommendations"].append(
                f"⚠️ {position_type} position at risk: trend is {long_term_trend}"
            )

        elif position_type == "BUY" and long_term_trend == "BEARISH":
            risk_analysis["has_risk"] = True
            risk_analysis["risky_positions"].append({
                "ticket": pos.ticket,
                "type": position_type,
                "volume": pos.volume,
                "profit": pos.profit,
                "risk_reason": "BUY position against BEARISH trend"
            })
            risk_analysis["recommendations"].append(
                f"⚠️ {position_type} position at risk: trend is {long_term_trend}"
            )

        else:
            risk_analysis["safe_positions"].append({
                "ticket": pos.ticket,
                "type": position_type,
                "volume": pos.volume,
                "profit": pos.profit
            })

    return risk_analysis

def should_avoid_new_trades(symbol=SYMBOL, final_signal="BUY", long_term_trend="BULLISH"):
    """Determine if new trades should be avoided due to conflicting positions"""
    risk_analysis = analyze_position_risk(symbol, long_term_trend)

    if not risk_analysis["has_risk"]:
        return False, "No position conflicts detected"

    # Check if new signal conflicts with existing risky positions
    for risky_pos in risk_analysis["risky_positions"]:
        if final_signal == "BUY" and risky_pos["type"] == "SELL":
            return True, f"Avoiding new BUY order: existing SELL position is already at risk"
        elif final_signal == "SELL" and risky_pos["type"] == "BUY":
            return True, f"Avoiding new SELL order: existing BUY position is already at risk"

    return False, "New trade direction is compatible with existing positions"

def debug_position_detection(symbol=SYMBOL):
    """Debug function to show all position detection results"""
    print(f"\n🔍 Enhanced Position Detection Debug for {symbol}:")
    print("=" * 60)

    # Show all positions
    all_positions = get_all_positions(symbol, include_all_magic=True)
    print(f"Total positions found: {len(all_positions)}")

    for i, pos in enumerate(all_positions):
        print(f"  Position {i+1}:")
        print(f"    Type: {'BUY' if pos.type == 0 else 'SELL'}")
        print(f"    Volume: {pos.volume}")
        print(f"    Magic: {pos.magic}")
        print(f"    Profit: {pos.profit:.2f}")
        print(f"    Ticket: {pos.ticket}")

    # Test different detection methods
    print(f"\n🧪 Position Detection Results:")
    print(f"  has_buy_position_any_magic(): {has_buy_position_any_magic(symbol)}")
    print(f"  has_sell_position_any_magic(): {has_sell_position_any_magic(symbol)}")

    # Original functions
    from mt5_helper import has_buy_position, has_sell_position
    print(f"  has_buy_position() [magic filtered]: {has_buy_position(symbol)}")
    print(f"  has_sell_position() [magic filtered]: {has_sell_position(symbol)}")

    # Risk analysis
    risk_analysis = analyze_position_risk(symbol, "BULLISH", "BULLISH")
    print(f"\n⚠️ Risk Analysis:")
    print(f"  Has Risk: {risk_analysis['has_risk']}")
    print(f"  Risky Positions: {len(risk_analysis['risky_positions'])}")
    print(f"  Safe Positions: {len(risk_analysis['safe_positions'])}")

    for rec in risk_analysis['recommendations']:
        print(f"  {rec}")

if __name__ == "__main__":
    if connect():
        debug_position_detection()
    else:
        print("Failed to connect to MT5")
