"""Unit tests for the error simulation (bonus)."""
import math

import pytest

from src.testing.error_injector import ErrorInjector


def test_disabled_by_default():
    injector = ErrorInjector()
    assert injector.enabled is False


def test_passthrough_when_no_faults():
    injector = ErrorInjector(drop_rate=0.0, corrupt_rate=0.0)
    read = injector.wrap(lambda: 3.14)
    assert read() == 3.14


def test_drop_rate_one_always_raises():
    injector = ErrorInjector(drop_rate=1.0)
    read = injector.wrap(lambda: 1.0)
    with pytest.raises(ConnectionError):
        read()


def test_corrupt_rate_one_changes_value():
    injector = ErrorInjector(corrupt_rate=1.0, seed=42)
    read = injector.wrap(lambda: 1.0)
    value = read()
    # Corruption is either NaN or an implausible spike, never the original 1.0.
    assert math.isnan(value) or value != 1.0


def test_seed_is_reproducible():
    a = ErrorInjector(drop_rate=0.5, seed=7).wrap(lambda: 1.0)
    b = ErrorInjector(drop_rate=0.5, seed=7).wrap(lambda: 1.0)
    results_a, results_b = [], []
    for results, read in ((results_a, a), (results_b, b)):
        for _ in range(20):
            try:
                results.append(read())
            except ConnectionError:
                results.append("dropped")
    assert results_a == results_b
