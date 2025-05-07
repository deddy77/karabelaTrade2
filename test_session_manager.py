"""
Test suite for the SessionManager class.
Tests session prioritization, pair selection, and overlap handling.

Run tests with:
python -m unittest test_session_manager.py -v
"""

import unittest
from datetime import datetime
from zoneinfo import ZoneInfo
from session_manager import SessionManager

class TestSessionManager(unittest.TestCase):
    """Test case for SessionManager class methods and functionality"""
    def setUp(self):
        self.session_mgr = SessionManager()
        
    def verify_pair_status(self, pair: str, time_str: str, expected_status: dict, msg: str = ""):
        """Helper method to verify pair trading status at specific time"""
        hour, minute = map(int, time_str.split(':'))
        test_time = datetime(2025, 5, 7, hour, minute, tzinfo=ZoneInfo("America/New_York"))
        status = self.session_mgr.get_pair_priority(pair, test_time)
        
        for key, expected_value in expected_status.items():
            self.assertEqual(status[key], expected_value, 
                           f"{msg} - Expected {key}={expected_value}, got {status[key]}")
        
    def test_get_all_tradeable_pairs(self):
        """Test that get_all_tradeable_pairs returns correct list of pairs"""
        pairs = self.session_mgr.get_all_tradeable_pairs()
        
        # Check that we have pairs from all sessions
        self.assertTrue(len(pairs) > 0, "Should return at least some tradeable pairs")
        
        # Test pairs by category
        test_pairs = {
            "Major Pairs": {
                "pairs": ["EURUSD", "GBPUSD", "USDJPY"],
                "description": "Major currency pairs"
            },
            "Secondary Pairs": {
                "pairs": ["USDCHF", "EURCHF", "NZDUSD"],
                "description": "Secondary major pairs"
            },
            "Cross Pairs": {
                "pairs": ["EURGBP", "AUDNZD", "GBPCAD", "EURAUD"],
                "description": "Cross/Minor pairs"
            },
            "Exotic Pairs": {
                "pairs": ["ZARJPY", "SGDJPY", "CNHJPY"],
                "description": "Exotic currency pairs"
            }
        }
        
        # Test each category
        for category, data in test_pairs.items():
            with self.subTest(category=category):
                for pair in data["pairs"]:
                    self.assertIn(
                        pair, pairs, 
                        f"{category} - {pair} should be included ({data['description']})"
                    )
            
        # Verify pairs are unique (no duplicates from overlap sessions)
        self.assertEqual(len(pairs), len(set(pairs)), "Should not have duplicate pairs")
        
        # Verify pairs are sorted
        self.assertEqual(pairs, sorted(pairs), "Pairs should be sorted alphabetically")
        
        # Print detailed analysis
        print(f"\nTradeable Pairs Analysis:")
        print(f"Total pairs: {len(pairs)}")
        print("\nCategory coverage:")
        for category, data in test_pairs.items():
            included = sum(1 for p in data["pairs"] if p in pairs)
            total = len(data["pairs"])
            print(f"- {category}: {included}/{total} pairs included")
        
    def test_pair_priority_in_overlap(self):
        """Test pair priority detection during London-NY overlap session"""
        # Test during London-NY overlap (10:00 AM EST)
        test_time = datetime(2025, 5, 7, 10, 0, tzinfo=ZoneInfo("America/New_York"))
        
        # EURUSD is a primary pair during London-NY overlap
        eurusd_status = self.session_mgr.get_pair_priority("EURUSD", test_time)
        self.assertEqual(eurusd_status["priority"], "OVERLAP")
        self.assertTrue(eurusd_status["is_overlap"])
        
        # Verify timeframe is faster during overlap
        params = self.session_mgr.get_session_parameters("EURUSD", test_time)
        self.assertEqual(params["timeframe"], "M1")  # Should use faster timeframe during overlap
        
    def test_pair_priority_outside_session(self):
        """Test pair priority detection during inactive periods"""
        # Test during quiet period (18:30 EST - between NY close and Sydney open)
        test_time = datetime(2025, 5, 7, 18, 30, tzinfo=ZoneInfo("America/New_York"))
        
        # Test various pairs during quiet period
        test_cases = [
            ("EURUSD", "INACTIVE", "Major pair should be inactive between sessions"),
            ("AUDUSD", "INACTIVE", "AUD pair should be inactive before Sydney session"),
            ("USDJPY", "INACTIVE", "JPY pair should be inactive after NY close"),
            ("USDCAD", "INACTIVE", "CAD pair should be inactive after NY close")
        ]
        
        for pair, expected_priority, message in test_cases:
            status = self.session_mgr.get_pair_priority(pair, test_time)
            self.assertEqual(status["priority"], expected_priority, message)
            self.assertFalse(status["is_overlap"])
            self.assertEqual(status["priority_level"], self.session_mgr.PRIORITIES["INACTIVE"])
            self.assertEqual(len(status["active_sessions"]), 0)
            
    def test_secondary_and_cross_pairs(self):
        """Test priority levels for secondary and cross pairs"""
        # Test during London session (08:00 EST)
        test_time = datetime(2025, 5, 7, 8, 0, tzinfo=ZoneInfo("America/New_York"))
        
        # Test various pair types
        test_cases = [
            ("EURUSD", "OVERLAP", "Major pair should be overlap during London-NY"),
            ("USDCHF", "SECONDARY", "CHF pair should be secondary in London"),
            ("EURCHF", "SECONDARY", "EUR cross should be secondary in London"),
            ("AUDNZD", "INACTIVE", "AUD/NZD cross should be inactive in London")
        ]
        
        for pair, expected_priority, message in test_cases:
            status = self.session_mgr.get_pair_priority(pair, test_time)
            self.assertEqual(status["priority"], expected_priority, message)
        
    def test_session_overlap_handling(self):
        """Test trading parameter adjustments during session overlaps"""
        # Test during Tokyo-London overlap (3:30 AM EST)
        test_time = datetime(2025, 5, 7, 3, 30, tzinfo=ZoneInfo("America/New_York"))
        
        # USDJPY should be in overlap session
        usdjpy_status = self.session_mgr.get_pair_priority("USDJPY", test_time)
        self.assertEqual(usdjpy_status["priority"], "OVERLAP")
        self.assertTrue(usdjpy_status["is_overlap"])
        
        # Verify overlap session parameters
        params = self.session_mgr.get_session_parameters("USDJPY", test_time)
        self.assertTrue(params["should_trade"])
        self.assertLess(params["min_spread"], 2.0)  # Should have tighter spread requirements
        self.assertGreater(params["lot_size_multiplier"], 1.0)  # Should have increased lot size

    def test_pair_status_across_sessions(self):
        """Test pair trading status across all sessions and transitions"""
        # Test cases: (pair, time, expected_status, description)
        test_scenarios = [
            # Sydney session
            ("AUDUSD", "18:00", {
                "priority": "PRIMARY",
                "is_overlap": False
            }, "AUD/USD during Sydney session"),
            
            # Sydney-Tokyo overlap
            ("USDJPY", "20:30", {
                "priority": "OVERLAP",
                "is_overlap": True
            }, "USD/JPY during Sydney-Tokyo overlap"),
            
            # Tokyo session
            ("EURJPY", "22:00", {
                "priority": "PRIMARY",
                "is_overlap": False
            }, "EUR/JPY during Tokyo session"),
            
            # Tokyo-London overlap
            ("GBPJPY", "03:30", {
                "priority": "OVERLAP",
                "is_overlap": True
            }, "GBP/JPY during Tokyo-London overlap"),
            
            # London session
            ("EURGBP", "07:00", {
                "priority": "PRIMARY",
                "is_overlap": False
            }, "EUR/GBP during London session"),
            
            # London-NY overlap
            ("EURUSD", "09:00", {
                "priority": "OVERLAP",
                "is_overlap": True
            }, "EUR/USD during London-NY overlap"),
            
            # NY session
            ("USDCAD", "14:00", {
                "priority": "PRIMARY",
                "is_overlap": False
            }, "USD/CAD during NY session"),
            
            # Quiet period
            ("EURUSD", "18:30", {
                "priority": "INACTIVE",
                "is_overlap": False
            }, "EUR/USD during quiet period")
        ]
        
        for pair, time, expected, desc in test_scenarios:
            with self.subTest(pair=pair, time=time, description=desc):
                self.verify_pair_status(pair, time, expected, desc)

    def test_timeframe_adjustments(self):
        """Test timeframe adjustments across different sessions and overlaps"""
        test_cases = [
            # Standard sessions
            ("EURUSD", "14:00", "M5", "Base timeframe during regular NY session"),
            ("GBPUSD", "07:00", "M5", "Base timeframe during regular London session"),
            ("USDJPY", "22:00", "M5", "Base timeframe during regular Tokyo session"),
            
            # Overlap periods - should use faster timeframe
            ("EURUSD", "09:00", "M1", "Faster timeframe during London-NY overlap"),
            ("USDJPY", "03:30", "M1", "Faster timeframe during Tokyo-London overlap"),
            ("AUDJPY", "20:30", "M1", "Faster timeframe during Sydney-Tokyo overlap"),
            
            # Inactive period - should still return base timeframe
            ("EURUSD", "18:30", "M5", "Base timeframe during inactive period")
        ]
        
        for pair, time, expected_tf, desc in test_cases:
            with self.subTest(pair=pair, time=time, description=desc):
                hour, minute = map(int, time.split(':'))
                test_time = datetime(2025, 5, 7, hour, minute, tzinfo=ZoneInfo("America/New_York"))
                
                # Get timeframe from session parameters
                params = self.session_mgr.get_session_parameters(pair, test_time)
                self.assertEqual(
                    params["timeframe"],
                    expected_tf,
                    f"{desc}: Expected {expected_tf}, got {params['timeframe']}"
                )

    def test_pairs_statistics(self):
        """Test detailed statistics about tradeable pairs"""
        stats = self.session_mgr.get_pairs_stats()
        
        # Test overall structure
        self.assertIn("total_pairs", stats)
        self.assertIn("by_session", stats)
        self.assertIn("by_overlap", stats)
        self.assertIn("by_category", stats)
        
        # Test session coverage
        for session in ["SYDNEY", "TOKYO", "LONDON", "NEWYORK"]:
            self.assertIn(session, stats["by_session"])
            session_stats = stats["by_session"][session]
            self.assertGreater(session_stats["total"], 0)
            self.assertGreater(len(session_stats["pairs"]), 0)
        
        # Test overlap session coverage
        for overlap in ["SYDNEY-TOKYO", "TOKYO-LONDON", "LONDON-NEWYORK"]:
            self.assertIn(overlap, stats["by_overlap"])
            overlap_stats = stats["by_overlap"][overlap]
            self.assertGreater(overlap_stats["total"], 0)
            self.assertGreater(len(overlap_stats["pairs"]), 0)
        
        # Test category stats
        categories = ["primary", "secondary", "cross", "overlap_only"]
        for category in categories:
            self.assertIn(category, stats["by_category"])
            self.assertIsInstance(stats["by_category"][category], list)
        
        # Print detailed statistics
        print("\nPair Statistics Analysis:")
        print(f"Total unique pairs: {stats['total_pairs']}")
        print("\nBy Session:")
        for session, data in stats["by_session"].items():
            print(f"{session}: {data['total']} pairs ({data['primary']} primary, "
                  f"{data['secondary']} secondary, {data['cross']} cross)")
        
        print("\nBy Overlap Period:")
        for overlap, data in stats["by_overlap"].items():
            print(f"{overlap}: {data['total']} pairs")
        
        print("\nBy Category:")
        for category, pairs in stats["by_category"].items():
            print(f"{category}: {len(pairs)} pairs")

if __name__ == '__main__':
    unittest.main()
