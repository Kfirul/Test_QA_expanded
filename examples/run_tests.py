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


def main():
    framework = AmmeterTestFramework()  # starts emulators automatically

    results = framework.run_all()
    for result in results.values():
        print("\n" + result.summary_text())

    comparison = framework.compare(results)
    if comparison:
        print("\n=== Cross-ammeter reliability (lower CV = more reliable) ===")
        print(comparison["table"])
        print(f"\nMost reliable: {comparison['most_reliable']}")


if __name__ == "__main__":
    main()
