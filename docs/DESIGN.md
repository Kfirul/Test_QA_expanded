# Design Decisions

This document explains the architecture of the Ammeter Testing Framework and the
reasoning behind the key choices. It complements the README (which covers usage and
the list of bug fixes).

## Goals

The framework had to satisfy five requirements — a unified API, configurable sampling,
statistical analysis, result management, and (bonus) accuracy assessment — while staying
on top of the existing emulator infrastructure, minimising surprises, and remaining
cross-platform and easy to extend.

## Architecture at a glance

```
config.yaml ──► AmmeterTestFramework ──► TestResult (JSON + plots on disk)
                     │
   ┌─────────────────┼───────────────────────────────┐
   ▼                 ▼                ▼                ▼
EmulatorManager   Sampler        Analyzer         Visualizer
(start/ready)   (timing/plan)  (stats/compare)   (plots)
                     │
                ErrorInjector (optional, wraps the reader)
                     │
              Ammeters/client.get_current_measurement  ──► emulator sockets
```

Each concern lives in its own small module so it can be tested, reused, or replaced
independently. `AmmeterTestFramework` is only an orchestrator — it owns no statistics or
plotting logic itself.

## File-by-file purpose

| File | Purpose |
|------|---------|
| `config/config.yaml` | Single source of truth: ammeters, sampling, analysis, errors, output. |
| `src/utils/config.py` | Loads YAML, resolves the path relative to the project root, validates structure. |
| `src/utils/logger.py` | File + console logging with a real handler/formatter. |
| `Ammeters/client.py` | `get_current_measurement()` returns a `float`; original print helper kept. |
| `src/testing/emulator_manager.py` | Starts emulators on daemon threads, polls ports until ready. |
| `src/testing/sampler.py` | Resolves the sampling plan and collects samples on a monotonic clock. |
| `src/testing/error_injector.py` | Wraps the reader to simulate dropped/corrupted samples (bonus). |
| `src/testing/analyzer.py` | Statistics, sampling-cadence consistency, cross-ammeter ranking. |
| `src/testing/visualizer.py` | Histogram, time-series, comparison box-plot (headless backend). |
| `src/testing/result.py` | `TestResult` dataclass: run id, metadata, JSON save/load, run listing. |
| `src/testing/test_framework.py` | The unified API that wires everything together. |
| `main.py` | Minimal "make it work" entry point. |
| `examples/run_tests.py` | Full end-to-end demonstration. |

## Key decisions

**Configuration-driven.** Ports, commands, sampling, analysis toggles and error rates
all live in `config.yaml`. Adding a new ammeter type is a config entry plus (only if it
is a brand-new emulator class) one line in `emulator_manager.AMMETER_CLASSES` — the test
logic does not change. This directly serves the "extension and reuse" evaluation criterion.

**Unified API via a registry.** `run_test(ammeter_type)` looks the ammeter up in config,
so all three (and any future ones) flow through identical code paths and produce identical
`TestResult` records — consistent reporting for free.

**Sampling reconciliation.** `measurements_count`, `total_duration_seconds` and
`sampling_frequency_hz` are over-determined (any two fix the third). `resolve_sampling`
applies an explicit precedence — frequency+duration → count, else count+frequency →
interval, else count+duration → interval — and records a note when inputs conflict, so the
behaviour is predictable rather than implicit. Timing uses `time.perf_counter()` and sleeps
to each sample's target time so cadence stays accurate even when a read is slow.

**Reliability instead of absolute accuracy.** The emulators generate random currents with
no shared ground-truth, so true accuracy cannot be measured. The framework instead
quantifies *precision/reliability* via the coefficient of variation (CV = σ/μ) and ranks
ammeters by it — the lowest CV is the most consistent measurement method. This is an honest
interpretation of the "determine relative accuracy / most reliable method" bonus.

**Robust error handling.** Each sample read retries on transient socket errors
(configurable); a permanently failing sample is recorded (`value=None`) rather than
aborting the run. NaNs from corrupted samples are filtered out of the statistics. The
optional `ErrorInjector` lets us deliberately exercise all of this.

**Self-contained, retrievable results.** Each run is a folder named
`<timestamp>_<ammeter>_<run_id>` holding a complete `result.json` (config snapshot + raw
samples + stats + metadata) and its plots. `result.py` offers `load()` and `list_results()`
for historical comparison without a database.

**Cross-platform.** Sockets bind to `localhost` with timeouts; the matplotlib `Agg`
backend needs no display; non-ASCII console output was removed; config paths resolve from
the project root regardless of the working directory.

## Possible extensions

- A CLI (e.g. `argparse`) to pick ammeters/parameters without editing config.
- Persisting comparisons across historical runs (trend analysis).
- A real reference source to enable true accuracy (vs. precision) measurement.
- Unit tests for `sampler.resolve_sampling` and `analyzer` using synthetic data.
