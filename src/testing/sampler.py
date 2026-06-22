"""Sampling-plan resolution and the timed measurement-collection loop."""
import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional


@dataclass
class SamplingPlan:
    """Resolved, concrete sampling parameters used for a run."""
    count: int
    interval: float            # seconds between consecutive samples
    frequency: float           # samples per second (1 / interval)
    duration: float            # expected total duration (count * interval)
    notes: List[str] = field(default_factory=list)


def resolve_sampling(measurements_count: Optional[int],
                     total_duration_seconds: Optional[float],
                     sampling_frequency_hz: Optional[float]) -> SamplingPlan:
    """
    Reconcile the three (over-determined) sampling knobs into a concrete plan.

    Precedence:
      1. frequency + duration -> count   = round(frequency * duration)
      2. count     + frequency -> interval = 1 / frequency
      3. count     + duration  -> interval = duration / count
    Missing combinations fall back to sensible defaults. When all three are
    given and disagree, frequency + duration win and a note is recorded.
    """
    notes: List[str] = []

    # Treat non-positive values as "not provided" (a count/duration/frequency of
    # zero or less is meaningless) so they don't silently distort the plan.
    def _positive(value, label):
        if value is not None and value <= 0:
            notes.append(f"Ignoring non-positive {label}={value}.")
            return None
        return value

    c = _positive(measurements_count, "measurements_count")
    d = _positive(total_duration_seconds, "total_duration_seconds")
    f = _positive(sampling_frequency_hz, "sampling_frequency_hz")

    if c is not None and d is not None and f is not None:
        derived = round(f * d)
        if derived != c:
            notes.append(
                f"count={c} conflicts with frequency*duration={derived}; "
                f"using frequency+duration -> count={derived}."
            )
        count = derived
        frequency = f
    elif f is not None and d is not None:
        count = max(1, round(f * d))
        frequency = f
    elif c is not None and f is not None:
        count = c
        frequency = f
    elif c is not None and d is not None:
        count = c
        frequency = c / d
    elif c is not None:
        count = c
        frequency = 1.0
        notes.append("Only count given; defaulting to 1 Hz.")
    elif d is not None:
        frequency = 1.0
        count = max(1, round(d))
        notes.append("Only duration given; defaulting to 1 Hz.")
    else:
        count = 10
        frequency = 1.0
        notes.append("No sampling parameters given; defaulting to 10 samples @ 1 Hz.")

    interval = 1.0 / frequency if frequency > 0 else 0.0
    return SamplingPlan(
        count=count,
        interval=interval,
        frequency=frequency,
        duration=count * interval,
        notes=notes,
    )


@dataclass
class Sample:
    index: int
    timestamp: float          # seconds since start of the run
    value: Optional[float]    # None if the sample failed
    error: Optional[str] = None


def collect_samples(read_fn: Callable[[], float], plan: SamplingPlan) -> List[Sample]:
    """
    Collect ``plan.count`` samples, pacing each to its target time using a
    monotonic clock so timing stays accurate even if ``read_fn`` is slow.

    ``read_fn`` raises on failure; the failure is captured per-sample so a
    single bad read never aborts the whole run.
    """
    samples: List[Sample] = []
    start = time.perf_counter()

    for i in range(plan.count):
        target = start + i * plan.interval
        now = time.perf_counter()
        if target > now:
            time.sleep(target - now)

        ts = time.perf_counter() - start
        try:
            value = read_fn()
            samples.append(Sample(index=i, timestamp=ts, value=value))
        except Exception as exc:  # noqa: BLE001 - record, don't crash the run
            samples.append(Sample(index=i, timestamp=ts, value=None, error=str(exc)))

    return samples
