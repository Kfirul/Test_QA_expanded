"""
End-to-end demonstration of the Ammeter Testing Framework.

Starts the emulators, runs a configured test against every ammeter, prints the
statistics, archives each run under results/, and performs a cross-ammeter
reliability comparison.

Run from the project root:  py examples/run_tests.py
"""
import os
import sys

# Make the project root importable regardless of the current working directory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.testing.test_framework import AmmeterTestFramework


def _print_stats(name, result):
    s = result.statistics
    print(f"\nResults for {name} (run {result.run_id}):")
    if s.get("count", 0) == 0:
        print("  no valid samples collected.")
        return
    print(f"  samples : {s['count']}")
    print(f"  mean    : {s['mean']:.4f} A")
    print(f"  median  : {s['median']:.4f} A")
    print(f"  std dev : {s['std_dev']:.4f} A")
    print(f"  min/max : {s['min']:.4f} / {s['max']:.4f} A")
    print(f"  CV      : {s['coefficient_of_variation']:.4f}")


def main():
    framework = AmmeterTestFramework()  # starts emulators automatically

    results = framework.run_all()
    for name, result in results.items():
        _print_stats(name, result)

    comparison = framework.compare(results)
    if comparison:
        print("\n=== Cross-ammeter reliability (lower CV = more reliable) ===")
        print(comparison["table"])
        print(f"\nMost reliable: {comparison['most_reliable']}")


if __name__ == "__main__":
    main()
