"""
Test runner script for the trading bot.
Runs all test suites and reports results.
"""

import unittest
import sys

def run_all_tests():
    """Run all test suites and return True if all tests pass"""
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test modules
    test_modules = [
        'test_session_manager',
        'test_config'
    ]
    
    for module in test_modules:
        try:
            # Add tests from each module
            tests = loader.loadTestsFromName(module)
            suite.addTests(tests)
        except Exception as e:
            print(f"Error loading tests from {module}: {str(e)}")
            return False
    
    # Run the tests and collect results
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Generate test summary
    total_tests = result.testsRun
    passed_tests = total_tests - len(result.failures) - len(result.errors)
    success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    print("\n=== Test Coverage Analysis ===")
    print("Session Time Coverage:")
    test_times = {
        "Sydney Session": ["17:00-02:00", "18:00", "19:30"],
        "Tokyo Session": ["20:00-05:00", "22:00", "23:30"],
        "London Session": ["03:00-12:00", "07:00", "08:30"],
        "New York Session": ["08:00-17:00", "14:00", "15:30"],
        "Overlap Periods": {
            "Sydney-Tokyo": ["20:00-02:00", "20:30", "21:30"],
            "Tokyo-London": ["03:00-05:00", "03:30", "04:30"],
            "London-NY": ["08:00-12:00", "09:00", "10:30"]
        },
        "Quiet Periods": ["18:30", "02:30", "06:30", "17:30"]
    }
    
    for session, times in test_times.items():
        if isinstance(times, dict):
            print(f"\n{session}:")
            for overlap, overlap_times in times.items():
                print(f"  {overlap}: {', '.join(overlap_times)}")
        else:
            print(f"{session}: {', '.join(times)}")
    
    print("\n=== Test Summary ===")
    print(f"Total Tests Run: {total_tests}")
    print(f"Tests Passed: {passed_tests}")
    print(f"Tests Failed: {len(result.failures)}")
    print(f"Tests Errored: {len(result.errors)}")
    print(f"Success Rate: {success_rate:.1f}%")

    print("\n=== Coverage Analysis ===")
    test_pairs = {
        "Major Pairs": [
            "EUR/USD", "GBP/USD", "USD/JPY", "USD/CHF",
            "USD/CAD", "AUD/USD", "NZD/USD"
        ],
        "Cross Pairs": [
            "EUR/GBP", "EUR/JPY", "GBP/JPY", "EUR/CHF",
            "EUR/CAD", "GBP/CAD", "AUD/JPY", "NZD/JPY"
        ],
        "Commodity Pairs": [
            "AUD/USD", "USD/CAD", "NZD/USD"
        ],
        "Exotic Pairs": [
            "EUR/NOK", "USD/SGD", "USD/ZAR", "USD/HKD",
            "USD/THB", "USD/CNH"
        ]
    }

    category_stats = {}
    total_tested = 0
    total_pairs = 0

    for category, pairs in test_pairs.items():
        tested_pairs = []
        for pair in pairs:
            standard_pair = pair.replace("/", "")
            is_tested = (
                f"test_pair_priority_in_overlap with {standard_pair}" in str(suite) or
                f"test_timeframe_adjustments with {standard_pair}" in str(suite) or
                f"test_secondary_and_cross_pairs with {standard_pair}" in str(suite)
            )
            if is_tested:
                tested_pairs.append(pair)
                total_tested += 1
        
        category_stats[category] = {
            "total": len(pairs),
            "tested": len(tested_pairs),
            "pairs": pairs,
            "tested_pairs": tested_pairs
        }
        total_pairs += len(pairs)

    # Print coverage statistics
    print("\nPair Coverage by Category:")
    print("-" * 50)
    for category, stats in category_stats.items():
        coverage = (stats["tested"] / stats["total"] * 100) if stats["total"] > 0 else 0
        print(f"\n{category}:")
        print(f"Coverage: {coverage:.1f}% ({stats['tested']}/{stats['total']} pairs)")
        print("Tested Pairs:", ", ".join(stats["tested_pairs"]) if stats["tested_pairs"] else "None")
        print("Untested Pairs:", ", ".join(set(stats["pairs"]) - set(stats["tested_pairs"])) if stats["tested_pairs"] else "All")

    # Feature coverage analysis
    features = {
        "Session Management": [
            "Regular session detection",
            "Overlap period detection",
            "Quiet period detection",
            "Session transitions"
        ],
        "Pair Priority": [
            "Primary pair handling",
            "Secondary pair handling",
            "Cross pair handling",
            "Overlap pair priority"
        ],
        "Trading Parameters": [
            "Timeframe adjustments",
            "Spread requirements",
            "Lot size multipliers",
            "Stop loss / Take profit"
        ],
        "Configuration": [
            "Dynamic symbol generation",
            "Session-based settings",
            "Parameter inheritance",
            "Default handling"
        ]
    }

    # Count tested features based on test method names
    feature_stats = {}
    total_features = 0
    tested_features = 0

    print("\n=== Feature Coverage ===")
    print("-" * 50)
    for category, feature_list in features.items():
        tested = sum(1 for feature in feature_list if any(
            feature.lower().replace(" ", "_") in str(suite).lower() for test in suite
        ))
        coverage = (tested / len(feature_list) * 100)
        feature_stats[category] = {
            "total": len(feature_list),
            "tested": tested,
            "coverage": coverage
        }
        total_features += len(feature_list)
        tested_features += tested
        
        print(f"\n{category}:")
        print(f"Coverage: {coverage:.1f}% ({tested}/{len(feature_list)} features)")
        for feature in feature_list:
            is_tested = any(feature.lower().replace(" ", "_") in str(suite).lower() for test in suite)
            print(f"  {'✓' if is_tested else '•'} {feature}")

    print("\nOverall Statistics:")
    print("-" * 50)
    print(f"Pair Coverage: {(total_tested / total_pairs * 100):.1f}% ({total_tested}/{total_pairs} pairs)")
    print(f"Feature Coverage: {(tested_features / total_features * 100):.1f}% ({tested_features}/{total_features} features)")
    
    if result.failures:
        print("\nFailures:")
        for failure in result.failures:
            test_case = failure[0]
            print(f"- {test_case.id()}")
    
    if result.errors:
        print("\nErrors:")
        for error in result.errors:
            test_case = error[0]
            print(f"- {test_case.id()}")
    
    # Return True if all tests passed
    return result.wasSuccessful()

if __name__ == '__main__':
    print("Running all trading bot tests...\n")
    success = run_all_tests()
    
    # Exit with appropriate status code
    sys.exit(0 if success else 1)
