# Ammeter Testing Framework

A configuration-driven Quality-Assurance framework for testing current-measurement
systems built on three ammeter emulators (**Greenlee**, **ENTES**, **CIRCUTOR**).
Each emulator runs as a TCP socket server on its own thread and answers
measurement requests with a current value (Amps). The framework drives all three
through one unified interface, collects timed samples, computes statistics,
visualises and archives every run, and ranks the ammeters by reliability.

---

## Quick Start

```sh
# 1. Install dependencies (see "Libraries" below)
py -m pip install -r requirements.txt        # Windows  (use python3 on Linux/Mac)

# 2. Smoke test - start the emulators and read one measurement from each
py main.py

# 3. Full framework demo - sample, analyse, visualise, archive, compare
py examples/run_tests.py
```

Results are written under `results/` (one folder per run + a `comparison.png`
and `results/logs/`).

### Command-line interface

`cli.py` runs tests and inspects saved runs without editing `config.yaml`:

```sh
py cli.py run                          # test all ammeters (config defaults)
py cli.py run -a greenlee -n 50 -f 10  # 50 samples @ 10 Hz, greenlee only
py cli.py run --errors                 # enable error simulation
py cli.py run --no-plots -o out        # skip plots, custom output directory
py cli.py list                         # list saved runs
py cli.py show results/<run_folder>    # print a saved run's summary
py cli.py --help                       # full option reference
```

### Running the tests

```sh
py -m pip install -r requirements-dev.txt   # adds pytest
py -m pytest                                # full suite
py -m pytest -m "not integration"           # fast unit tests only (no sockets)
```

The suite covers the sampling logic, statistics/comparison, error simulation,
result archiving and config validation as **unit tests**, plus **integration
tests** that start the real emulators and run end-to-end.

> On Windows the Microsoft-Store `python` shim may be a no-op; use the `py`
> launcher as shown. On Linux/Mac use `python3`.

---

## The Ammeters

| Ammeter  | Port | Command                                   | Method                  | Formula        |
|----------|------|-------------------------------------------|-------------------------|----------------|
| Greenlee | 5000 | `MEASURE_GREENLEE -get_measurement`       | Ohm's Law               | `I = V / R`    |
| ENTES    | 5001 | `MEASURE_ENTES -get_data`                 | Hall Effect             | `I = B * K`    |
| CIRCUTOR | 5002 | `MEASURE_CIRCUTOR -get_measurement -current` | Rogowski Coil        | `I = Σ(V·dt)`  |

Ports and commands are defined once in `config/config.yaml` and used everywhere.

---

## Project Structure

```
.
├── main.py                     # Smoke test: start emulators + one request each
├── cli.py                      # Command-line interface (run / list / show)
├── requirements.txt            # Python dependencies
├── requirements-dev.txt        # Dev/test dependencies (adds pytest)
├── pytest.ini                  # pytest configuration
├── config/
│   └── config.yaml             # Single source of truth (ammeters, sampling, analysis, errors)
├── Ammeters/                   # Emulator infrastructure (provided; minimally fixed)
│   ├── base_ammeter.py         #   Abstract socket-server base class
│   ├── Greenlee_Ammeter.py     #   Greenlee emulator (Ohm's Law)
│   ├── Entes_Ammeter.py        #   ENTES emulator (Hall effect)
│   ├── Circutor_Ammeter.py     #   CIRCUTOR emulator (Rogowski coil)
│   └── client.py               #   Socket client (now returns the measured value)
├── src/
│   ├── testing/
│   │   ├── test_framework.py   # AmmeterTestFramework - unified API / orchestrator
│   │   ├── emulator_manager.py # Starts emulators on threads, waits until ports are ready
│   │   ├── sampler.py          # Resolves count/duration/frequency + timed collection
│   │   ├── analyzer.py         # Statistics, consistency, cross-ammeter comparison
│   │   ├── visualizer.py       # Histogram / time-series / comparison plots
│   │   ├── error_injector.py   # Error simulation (dropped / corrupted samples)
│   │   └── result.py           # TestResult: run-id, metadata, JSON save/load, retrieval
│   └── utils/
│       ├── config.py           # YAML loader + path resolution + validation
│       ├── logger.py           # File + console logging
│       └── Utils.py            # generate_random_float (used by emulators)
├── examples/
│   └── run_tests.py            # End-to-end demonstration
├── tests/                      # Unit + integration tests (pytest)
│   ├── conftest.py             #   Shared fixtures (config, emulators)
│   ├── test_sampler.py         #   Sampling plan resolution + collection loop
│   ├── test_analyzer.py        #   Statistics, consistency, comparison
│   ├── test_error_injector.py  #   Error simulation
│   ├── test_result.py          #   Save/load/list archiving
│   ├── test_config.py          #   Config loading + validation
│   └── test_integration.py     #   End-to-end against live emulators
├── results/                    # Generated: per-run folders, plots, logs
└── docs/
    └── DESIGN.md               # Design decisions & rationale
```

Each importable package (`Ammeters/`, `src/`, `src/utils/`, `src/testing/`) also contains
an `__init__.py` marker (omitted above for brevity).

See `docs/DESIGN.md` for the file-by-file purpose and the reasoning behind the design.

---

## What the Framework Does (mapped to the exercise)

1. **Unified Measurement API** — `AmmeterTestFramework.run_test(ammeter_type)` drives
   any ammeter; `run_all()` runs them all. Adding a new ammeter is a config-only change.
2. **Measurement Sampling** — configurable `measurements_count`, `total_duration_seconds`
   and `sampling_frequency_hz`. The sampler reconciles these (over-determined) knobs with
   a documented precedence and paces samples on a monotonic clock for accurate timing.
3. **Result Analysis** — mean, median, std-dev, min, max, range, and coefficient of
   variation, plus sampling-cadence consistency (jitter).
4. **Result Management** — every run gets a unique id and is archived to
   `results/<timestamp>_<ammeter>_<id>/result.json` with full metadata; `result.py`
   provides load/list helpers for historical retrieval and comparison.
5. **Accuracy / Reliability Assessment (bonus)** — ranks ammeters by coefficient of
   variation and identifies the most reliable measurement method.

**Bonus features implemented:** visualization (histogram, time-series, comparison
box-plot), error simulation, cross-ammeter accuracy comparison, and a fully
configuration-driven design.

---

## Configuration

Everything is controlled from `config/config.yaml`:

- `ammeters` — name → `port` + `command` (add a 4th here with no code changes).
- `testing.sampling` — `measurements_count`, `total_duration_seconds`, `sampling_frequency_hz`
  (set any to `null` to derive it from the others).
- `testing.connection` — host, per-request `timeout_seconds`, `retries`, `retry_delay_seconds`.
- `analysis` — which metrics, which plots, whether to run the accuracy comparison.
- `error_simulation` — `enabled`, `drop_rate`, `corrupt_rate` (bonus).
- `result_management` — `output_dir`, `save_raw_samples`.

---

## Bug Fixes Applied (required by the exercise)

The provided code could not run. The following were fixed; each is a minimal change
to the existing infrastructure:

1. **`main.py` did nothing** — the request lines were commented out, used the wrong
   (incomplete) commands (e.g. `b'MEASURE_GREENLEE'` instead of the full
   `MEASURE_GREENLEE -get_measurement` the server requires for its exact-match check),
   and relied on a fixed `time.sleep`. Rewritten to start the emulators via
   `EmulatorManager` and request from each using the exact commands from config.

2. **Port mismatch** — README said 5000/5001/5002 but `main.py` used 5001/5002/5003.
   Unified to 5000/5001/5002, now sourced from `config.yaml` so they can never drift.

3. **CIRCUTOR command mismatch** — the README listed `MEASURE_CIRCUTOR -get_measurement`
   but the emulator requires `MEASURE_CIRCUTOR -get_measurement -current`. Config now
   carries the exact byte-string the emulator checks against.

4. **`client.py` returned `None`** — it only *printed* the measurement, so it could not
   be consumed programmatically. Added `get_current_measurement(...)` which returns a
   `float` (with a socket timeout) and kept the original print helper as a thin wrapper.

5. **Greenlee `UnicodeEncodeError` on Windows** — `Greenlee_Ammeter.measure_current`
   printed the `Ω` symbol, which crashes on the Windows console (cp1252) and silently
   killed the Greenlee server thread (it returned "no data"). Replaced `Ω` with `Ohm`
   for cross-platform safety.

6. **"Address already in use" on restart** — `base_ammeter.start_server` did not set
   `SO_REUSEADDR` (the README hinted at this with the "increase sleep time" note). Added
   `SO_REUSEADDR` so emulators rebind cleanly between runs.

7. **Empty stubs** — `src/testing/test_framework.py` (a `pass` stub), `config/config.yaml`
   (all `NULL`), and `src/utils/logger.py` (created a logger but never attached a handler,
   so nothing was logged) were all implemented. `examples/run_tests.py` also called
   `run_test()` with no argument against a signature that required one — fixed.

8. **Missing package markers** — added `__init__.py` to `Ammeters/`, `src/`,
   `src/utils/`, `src/testing/` so the relative/absolute imports resolve reliably.

---

## Libraries Installed

From `requirements.txt` (installed with `py -m pip install -r requirements.txt`):

| Library      | Used for                                              |
|--------------|-------------------------------------------------------|
| `pyyaml`     | Reading `config.yaml`                                  |
| `numpy`      | Statistical computations                              |
| `scipy`      | 95% confidence interval of the mean (`scipy.stats`)   |
| `pandas`     | Building the cross-ammeter comparison table           |
| `matplotlib` | Plotting (headless `Agg` backend)                     |
| `seaborn`    | Histogram styling                                     |

Versions resolved at install time: numpy 2.4.6, scipy 1.17.1, pandas 3.0.3,
matplotlib 3.11.0, seaborn 0.13.2, pyyaml 6.0.3 (Python 3.11).

---

## Sample Results

A representative set of runs (one per ammeter) is committed under `results/`. Each run
folder contains:

- `result.json` — full record: run id, config snapshot, raw samples, statistics, metadata.
- `histogram.png` — distribution of measured current.
- `time_series.png` — current vs. time.

Plus a top-level `results/comparison.png` (box-plot across ammeters) and per-run logs
under `results/logs/`.

Because the emulators return random values within fixed physical ranges, CIRCUTOR and
ENTES are typically the most "reliable" (lowest coefficient of variation) while
Greenlee — whose `I = V/R` spans values near small resistances — shows the widest spread.
