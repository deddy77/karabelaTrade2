"""
Test suite for configuration settings.
Verifies dynamic symbol generation and settings management.

Run tests with:
python -m unittest test_config.py -v
"""

import unittest
from config import (
    session_mgr, SYMBOLS, SYMBOL_SETTINGS, 
    DEFAULT_PAIR_SETTINGS, TIMEFRAME
)

class TestConfig(unittest.TestCase):
    """Test case for configuration settings and dynamic symbol management"""
    
    def test_dynamic_symbols_list(self):
        """Test that SYMBOLS list is generated from session manager"""
        # Get all tradeable pairs and stats from session manager
        expected_pairs = session_mgr.get_all_tradeable_pairs()
        stats = session_mgr.get_pairs_stats()
        
        # Compare with SYMBOLS list
        self.assertEqual(
            SYMBOLS, 
            expected_pairs, 
            "SYMBOLS list should match session manager's tradeable pairs"
        )
        
        # Print detailed analysis
        print("\nSymbols Configuration Analysis:")
        print(f"Total configured pairs: {len(SYMBOLS)}")
        print("\nSession Coverage:")
        for session, data in stats["by_session"].items():
            print(f"{session}: {data['total']} pairs")
            print(f"  Primary: {', '.join(sorted(set(data['pairs']) & set(SYMBOLS)))}")
        
        print("\nOverlap Period Coverage:")
        for overlap, data in stats["by_overlap"].items():
            active_pairs = sorted(set(data["pairs"]) & set(SYMBOLS))
            print(f"{overlap}: {len(active_pairs)} pairs")
            print(f"  Pairs: {', '.join(active_pairs)}")
    
    def test_symbol_settings_generation(self):
        """Test that settings are generated for all symbols"""
        # Check that we have settings for all symbols
        for symbol in SYMBOLS:
            self.assertIn(
                symbol, 
                SYMBOL_SETTINGS, 
                f"Should have settings for {symbol}"
            )
            
            # Verify all default settings are copied
            for key in DEFAULT_PAIR_SETTINGS:
                self.assertIn(
                    key, 
                    SYMBOL_SETTINGS[symbol], 
                    f"Setting {key} missing for {symbol}"
                )
                self.assertEqual(
                    SYMBOL_SETTINGS[symbol][key],
                    DEFAULT_PAIR_SETTINGS[key],
                    f"Setting {key} for {symbol} should match default"
                )
    
    def test_timeframe_from_session_manager(self):
        """Test that timeframe is properly set from session manager"""
        self.assertEqual(
            TIMEFRAME,
            session_mgr.get_base_timeframe(),
            "TIMEFRAME should match session manager's base timeframe"
        )

if __name__ == '__main__':
    unittest.main()
