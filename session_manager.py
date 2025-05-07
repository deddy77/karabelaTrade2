from datetime import datetime, time
from typing import Dict, List, Optional
from zoneinfo import ZoneInfo

class SessionManager:
    def __init__(self):
        # Base timeframe configuration
        self._base_timeframe = "M5"  # Default base timeframe

        # Regular trading sessions with times in US/Eastern
        self.TRADING_SESSIONS = {
            "SYDNEY": {
                "start": "17:00",
                "end": "02:00",
                "primary_pairs": ["AUDUSD", "AUDJPY", "AUDNZD", "AUDCAD", "AUDCHF"],
                "secondary_pairs": ["NZDUSD", "NZDJPY", "NZDCAD", "NZDCHF"],
                "cross_pairs": ["AUDNZD", "GBPAUD", "EURAUD"]
            },
            "TOKYO": {
                "start": "20:00",
                "end": "05:00",
                "primary_pairs": ["USDJPY", "EURJPY", "GBPJPY"],
                "secondary_pairs": ["AUDJPY", "NZDJPY", "CADJPY", "CHFJPY"],
                "cross_pairs": ["ZARJPY", "SGDJPY", "CNHJPY"]
            },
            "LONDON": {
                "start": "03:00",
                "end": "12:00",
                "primary_pairs": ["EURUSD", "GBPUSD", "EURGBP"],
                "secondary_pairs": ["USDCHF", "EURCHF", "GBPCHF"],
                "cross_pairs": ["EURGBP", "EURCHF", "GBPCHF"]
            },
            "NEWYORK": {
                "start": "08:00",
                "end": "17:00",
                "primary_pairs": ["EURUSD", "USDCAD", "USDJPY"],
                "secondary_pairs": ["GBPUSD", "AUDUSD", "NZDUSD"],
                "cross_pairs": ["EURCAD", "GBPCAD", "CADJPY"]
            }
        }

        # High-liquidity overlap sessions with most active pairs
        self.OVERLAP_SESSIONS = {
            "SYDNEY-TOKYO": {
                "start": "20:00",
                "end": "02:00",
                "pairs": [
                    # Major JPY pairs
                    "USDJPY", "AUDJPY", "NZDJPY",
                    # AUD pairs during Asian trading
                    "AUDUSD", "AUDNZD",
                    # NZD pairs during Asian trading
                    "NZDUSD"
                ]
            },
            "TOKYO-LONDON": {
                "start": "03:00",
                "end": "05:00",
                "pairs": [
                    # JPY crosses highly active
                    "USDJPY", "EURJPY", "GBPJPY",
                    # Early European pairs
                    "EURUSD", "GBPUSD",
                    # Asian influence still present
                    "AUDJPY", "NZDJPY"
                ]
            },
            "LONDON-NEWYORK": {
                "start": "08:00",
                "end": "12:00",
                "pairs": [
                    # Major pairs peak liquidity
                    "EURUSD", "GBPUSD", "USDJPY",
                    # European crosses
                    "EURGBP", "EURJPY", "GBPJPY",
                    # USD pairs peak activity
                    "USDCHF", "USDCAD"
                ]
            }
        }

        # Trading priorities
        self.PRIORITIES = {
            "OVERLAP": 3,   # Highest priority during session overlaps
            "PRIMARY": 2,   # High priority during main session
            "SECONDARY": 1, # Lower priority during main session
            "INACTIVE": 0   # Not traded during current session
        }

    def _parse_time(self, time_str: str) -> time:
        """Convert time string to time object"""
        hour, minute = map(int, time_str.split(':'))
        return time(hour, minute)

    def _is_time_in_range(self, start: str, end: str, current: datetime) -> bool:
        """Check if current time is within the given range"""
        start_time = self._parse_time(start)
        end_time = self._parse_time(end)
        current_time = current.time()

        if start_time > end_time:  # Session crosses midnight
            return current_time >= start_time or current_time <= end_time
        return start_time <= current_time <= end_time

    def get_active_sessions(self, current_time: Optional[datetime] = None) -> List[str]:
        """Get currently active trading sessions"""
        if current_time is None:
            current_time = datetime.now(ZoneInfo("America/New_York"))

        active_sessions = []
        
        # Check regular sessions
        for session, details in self.TRADING_SESSIONS.items():
            if self._is_time_in_range(details["start"], details["end"], current_time):
                active_sessions.append(session)

        return active_sessions

    def get_active_overlaps(self, current_time: Optional[datetime] = None) -> List[str]:
        """Get currently active overlap sessions"""
        if current_time is None:
            current_time = datetime.now(ZoneInfo("America/New_York"))

        active_overlaps = []
        
        # Check overlap sessions
        for overlap, details in self.OVERLAP_SESSIONS.items():
            if self._is_time_in_range(details["start"], details["end"], current_time):
                active_overlaps.append(overlap)

        return active_overlaps

    def get_pair_priority(self, pair: str, current_time: Optional[datetime] = None) -> Dict:
        """Get trading priority and status for a currency pair"""
        if current_time is None:
            current_time = datetime.now(ZoneInfo("America/New_York"))

        result = {
            "priority": "INACTIVE",
            "priority_level": self.PRIORITIES["INACTIVE"],
            "active_sessions": [],
            "is_overlap": False,
            "timeframe": "M5",  # Default timeframe
            "lot_size_multiplier": 1.0  # Default multiplier
        }

        # Check overlap sessions first (highest priority)
        active_overlaps = self.get_active_overlaps(current_time)
        for overlap in active_overlaps:
            if pair in self.OVERLAP_SESSIONS[overlap]["pairs"]:
                result.update({
                    "priority": "OVERLAP",
                    "priority_level": self.PRIORITIES["OVERLAP"],
                    "active_sessions": [overlap],
                    "is_overlap": True,
                    "timeframe": self.get_overlap_timeframe(),  # Dynamic timeframe for overlaps
                    "lot_size_multiplier": 1.2  # Increase lot size by 20%
                })
                return result

        # Check regular sessions
        active_sessions = self.get_active_sessions(current_time)
        for session in active_sessions:
            if pair in self.TRADING_SESSIONS[session]["primary_pairs"]:
                result.update({
                    "priority": "PRIMARY",
                    "priority_level": self.PRIORITIES["PRIMARY"],
                    "active_sessions": active_sessions
                })
                return result

        # Check if pair should be traded as secondary or cross in any active session
        for session in active_sessions:
            session_details = self.TRADING_SESSIONS[session]
            if pair in session_details.get("secondary_pairs", []):
                result.update({
                    "priority": "SECONDARY",
                    "priority_level": self.PRIORITIES["SECONDARY"],
                    "active_sessions": active_sessions
                })
                return result
            elif pair in session_details.get("cross_pairs", []):
                result.update({
                    "priority": "SECONDARY",  # Cross pairs trade at secondary priority
                    "priority_level": self.PRIORITIES["SECONDARY"],
                    "active_sessions": active_sessions
                })
                return result

        return result

    def should_trade_pair(self, pair: str, current_time: Optional[datetime] = None) -> bool:
        """Determine if a pair should be traded based on current sessions"""
        status = self.get_pair_priority(pair, current_time)
        return status["priority_level"] > self.PRIORITIES["INACTIVE"]

    def get_session_parameters(self, pair: str, base_risk_percent: Optional[float] = None, current_time: Optional[datetime] = None) -> Dict:
        """Get trading parameters based on current session"""
        from config import DEFAULT_RISK_PERCENT, SYMBOL_SETTINGS
        
        status = self.get_pair_priority(pair, current_time)
        
        # Get risk percent - use symbol specific if available, else base_risk_percent or DEFAULT
        symbol_risk = SYMBOL_SETTINGS.get(pair, {}).get("RISK_PERCENT", None)
        effective_risk = symbol_risk or base_risk_percent or DEFAULT_RISK_PERCENT
        
        params = {
            "should_trade": status["priority_level"] > self.PRIORITIES["INACTIVE"],
            "timeframe": status["timeframe"],
            "lot_size_multiplier": status["lot_size_multiplier"],
            "status": status,
            "base_risk_percent": effective_risk
        }

        # Add additional session-based parameters
        if status["is_overlap"]:
            params.update({
                "min_spread": 1.5,  # Tighter spread requirements during overlaps
                "atr_multiplier": 1.2,  # Increased ATR multiplier for volatility
                "min_pip_target": 10,  # Lower pip target due to M1 timeframe
                "risk_multiplier": 1.2  # Increase risk during high-liquidity periods
            })
        else:
            params.update({
                "min_spread": 2.0,  # Normal spread requirements
                "atr_multiplier": 1.0,  # Normal ATR multiplier
                "min_pip_target": 15,  # Standard pip target
                "risk_multiplier": 1.0  # Normal risk during regular sessions
            })

        # Calculate effective risk for the session
        params["effective_risk_percent"] = params["base_risk_percent"] * params["risk_multiplier"]

        return params

    def get_base_timeframe(self) -> str:
        """Get the base timeframe for trading"""
        return self._base_timeframe

    def set_base_timeframe(self, timeframe: str) -> None:
        """Set the base timeframe for trading"""
        allowed_timeframes = ["M1", "M5", "M15", "H1", "H4"]
        if timeframe not in allowed_timeframes:
            raise ValueError(f"Invalid timeframe. Must be one of {allowed_timeframes}")
        self._base_timeframe = timeframe

    def get_overlap_timeframe(self) -> str:
        """Get the appropriate timeframe for overlap sessions"""
        # During overlaps, use a faster timeframe than the base
        timeframe_order = ["M1", "M5", "M15", "H1", "H4"]
        current_index = timeframe_order.index(self._base_timeframe)
        # Use one timeframe faster during overlaps, but not faster than M1
        return timeframe_order[max(0, current_index - 1)]

    def get_session_timeframe(self, pair: str, current_time: Optional[datetime] = None) -> str:
        """Get the appropriate timeframe based on current session"""
        status = self.get_pair_priority(pair, current_time)
        if status["is_overlap"]:
            return self.get_overlap_timeframe()
        return self.get_base_timeframe()

    def get_all_tradeable_pairs(self) -> List[str]:
        """Get a list of all pairs that can be traded across all sessions"""
        tradeable_pairs = set()
        
        # Add pairs from regular sessions (all categories)
        for session in self.TRADING_SESSIONS.values():
            tradeable_pairs.update(session["primary_pairs"])
            tradeable_pairs.update(session.get("secondary_pairs", []))
            tradeable_pairs.update(session.get("cross_pairs", []))
            
        # Add pairs from overlap sessions
        for overlap in self.OVERLAP_SESSIONS.values():
            tradeable_pairs.update(overlap["pairs"])
            
        return sorted(list(tradeable_pairs))

    def get_pairs_stats(self) -> Dict:
        """Get detailed statistics about tradeable pairs"""
        stats = {
            "total_pairs": 0,
            "by_session": {},
            "by_overlap": {},
            "by_category": {
                "primary": set(),
                "secondary": set(),
                "cross": set(),
                "overlap_only": set()
            }
        }
        
        # Gather regular session pairs
        regular_pairs = set()
        for session, details in self.TRADING_SESSIONS.items():
            session_pairs = set()
            session_pairs.update(details["primary_pairs"])
            session_pairs.update(details.get("secondary_pairs", []))
            session_pairs.update(details.get("cross_pairs", []))
            
            stats["by_session"][session] = {
                "total": len(session_pairs),
                "primary": len(details["primary_pairs"]),
                "secondary": len(details.get("secondary_pairs", [])),
                "cross": len(details.get("cross_pairs", [])),
                "pairs": sorted(list(session_pairs))
            }
            regular_pairs.update(session_pairs)
            
            # Update category sets
            stats["by_category"]["primary"].update(details["primary_pairs"])
            stats["by_category"]["secondary"].update(details.get("secondary_pairs", []))
            stats["by_category"]["cross"].update(details.get("cross_pairs", []))
        
        # Gather overlap session pairs
        overlap_pairs = set()
        for overlap, details in self.OVERLAP_SESSIONS.items():
            overlap_pairs.update(details["pairs"])
            stats["by_overlap"][overlap] = {
                "total": len(details["pairs"]),
                "pairs": sorted(details["pairs"])
            }
        
        # Find pairs that only appear in overlap sessions
        stats["by_category"]["overlap_only"] = overlap_pairs - regular_pairs
        
        # Convert sets to sorted lists
        for category in stats["by_category"]:
            stats["by_category"][category] = sorted(list(stats["by_category"][category]))
        
        # Calculate total unique pairs
        all_pairs = regular_pairs.union(overlap_pairs)
        stats["total_pairs"] = len(all_pairs)
        
        return stats
