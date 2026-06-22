"""Unit tests for the sampling plan resolution and collection loop."""
import pytest

from src.testing.sampler import resolve_sampling, collect_samples, SamplingPlan


def test_frequency_and_duration_define_count():
    plan = resolve_sampling(None, total_duration_seconds=4.0, sampling_frequency_hz=5.0)
    assert plan.count == 20
    assert plan.frequency == 5.0
    assert plan.interval == pytest.approx(0.2)


def test_count_and_frequency_define_interval():
    plan = resolve_sampling(measurements_count=10, total_duration_seconds=None,
                            sampling_frequency_hz=2.0)
    assert plan.count == 10
    assert plan.interval == pytest.approx(0.5)
    assert plan.duration == pytest.approx(5.0)


def test_count_and_duration_define_interval():
    plan = resolve_sampling(measurements_count=10, total_duration_seconds=5.0,
                            sampling_frequency_hz=None)
    assert plan.count == 10
    assert plan.interval == pytest.approx(0.5)


def test_conflicting_inputs_prefer_frequency_and_duration_with_note():
    # count says 99 but 5 Hz * 4 s = 20 -> framework should use 20 and warn.
    plan = resolve_sampling(measurements_count=99, total_duration_seconds=4.0,
                            sampling_frequency_hz=5.0)
    assert plan.count == 20
    assert any("conflict" in note for note in plan.notes)


def test_no_inputs_uses_defaults():
    plan = resolve_sampling(None, None, None)
    assert plan.count == 10
    assert plan.frequency == 1.0
    assert plan.notes  # a note explaining the default was recorded


def test_collect_samples_returns_requested_count():
    plan = SamplingPlan(count=5, interval=0.0, frequency=1000.0, duration=0.0)
    samples = collect_samples(lambda: 1.23, plan)
    assert len(samples) == 5
    assert all(s.value == 1.23 for s in samples)
    assert all(s.error is None for s in samples)


def test_collect_samples_records_failures_without_crashing():
    plan = SamplingPlan(count=3, interval=0.0, frequency=1000.0, duration=0.0)

    def bad_read():
        raise ConnectionError("boom")

    samples = collect_samples(bad_read, plan)
    assert len(samples) == 3
    assert all(s.value is None for s in samples)
    assert all("boom" in s.error for s in samples)


def test_collect_samples_timestamps_are_monotonic():
    plan = SamplingPlan(count=4, interval=0.01, frequency=100.0, duration=0.04)
    samples = collect_samples(lambda: 0.0, plan)
    timestamps = [s.timestamp for s in samples]
    assert timestamps == sorted(timestamps)
