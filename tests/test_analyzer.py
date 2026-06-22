"""Unit tests for the statistical analysis and comparison logic."""
import math

import pytest

from src.testing.analyzer import compute_statistics, evaluate_consistency, compare_ammeters


def test_compute_statistics_known_values():
    stats = compute_statistics([1.0, 2.0, 3.0, 4.0, 5.0])
    assert stats["count"] == 5
    assert stats["mean"] == pytest.approx(3.0)
    assert stats["median"] == pytest.approx(3.0)
    assert stats["min"] == pytest.approx(1.0)
    assert stats["max"] == pytest.approx(5.0)
    assert stats["range"] == pytest.approx(4.0)
    # Sample standard deviation (ddof=1) of 1..5 is sqrt(2.5).
    assert stats["std_dev"] == pytest.approx(math.sqrt(2.5))
    assert stats["coefficient_of_variation"] == pytest.approx(math.sqrt(2.5) / 3.0)


def test_compute_statistics_ignores_none_and_nan():
    stats = compute_statistics([2.0, None, float("nan"), 4.0])
    assert stats["count"] == 2
    assert stats["mean"] == pytest.approx(3.0)


def test_compute_statistics_empty():
    assert compute_statistics([]) == {"count": 0}
    assert compute_statistics([None, float("nan")]) == {"count": 0}


def test_single_value_has_zero_std():
    stats = compute_statistics([7.0])
    assert stats["count"] == 1
    assert stats["std_dev"] == 0.0


def test_evaluate_consistency_regular_cadence():
    consistency = evaluate_consistency([0.0, 1.0, 2.0, 3.0])
    assert consistency["mean_interval"] == pytest.approx(1.0)
    assert consistency["interval_jitter"] == pytest.approx(0.0)


def test_evaluate_consistency_too_few_points():
    consistency = evaluate_consistency([0.0])
    assert consistency["mean_interval"] is None


def test_compare_ammeters_ranks_by_coefficient_of_variation():
    stats_by = {
        "noisy": compute_statistics([1.0, 5.0, 9.0]),     # high CV
        "steady": compute_statistics([10.0, 10.1, 9.9]),  # low CV
    }
    comparison = compare_ammeters(stats_by)
    assert comparison["most_reliable"] == "steady"
    assert comparison["ranking"][0]["ammeter"] == "steady"
    assert comparison["ranking"][0]["rank"] == 1


def test_compare_ammeters_skips_empty():
    comparison = compare_ammeters({"empty": {"count": 0}})
    assert comparison["most_reliable"] is None
    assert comparison["ranking"] == []
