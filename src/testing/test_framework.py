"""The unified AmmeterTestFramework: orchestrates a full measurement test run."""
import os
import time
from dataclasses import asdict
from typing import Dict, List, Optional

from Ammeters.client import get_current_measurement
from src.utils.config import load_config, DEFAULT_CONFIG_PATH, PROJECT_ROOT
from src.utils.logger import TestLogger
from src.testing.emulator_manager import EmulatorManager
from src.testing.error_injector import ErrorInjector
from src.testing.sampler import resolve_sampling, collect_samples
from src.testing import analyzer, visualizer
from src.testing.result import TestResult


class AmmeterTestFramework:
    """
    Unified testing framework for all ammeter types.

    A single interface (:meth:`run_test`) drives any configured ammeter:
    it resolves the sampling plan, collects timed measurements through the
    socket client, computes statistics, optionally renders plots, and archives
    the run. Everything is driven by ``config.yaml``.
    """

    def __init__(self, config_path: str = DEFAULT_CONFIG_PATH, start_emulators: bool = True):
        self.config = load_config(config_path)
        self.logger = TestLogger("ammeter_framework")

        self._conn = self.config["testing"].get("connection", {})
        self._host = self._conn.get("host", "localhost")
        self._timeout = self._conn.get("timeout_seconds", 5.0)
        self._retries = max(1, int(self._conn.get("retries", 1)))
        self._retry_delay = self._conn.get("retry_delay_seconds", 0.0)

        self._emulators: Optional[EmulatorManager] = None
        if start_emulators:
            self.start_emulators()

    def start_emulators(self) -> None:
        self.logger.info("Starting ammeter emulators...")
        self._emulators = EmulatorManager(self.config["ammeters"], host=self._host)
        self._emulators.start()
        self.logger.info("All emulators ready.")

    def _output_dir(self) -> str:
        """Resolve the configured output dir; relative paths anchor to the project
        root so results always land in the same place regardless of the cwd."""
        out = self.config.get("result_management", {}).get("output_dir", "results")
        return out if os.path.isabs(out) else os.path.join(PROJECT_ROOT, out)

    # -- core: one ammeter --------------------------------------------------

    def _make_reader(self, port: int, command: str):
        """Build a read function with per-sample retry on transient failures."""
        def read() -> float:
            last_exc = None
            for attempt in range(self._retries):
                try:
                    return get_current_measurement(port, command, self._host, self._timeout)
                except Exception as exc:  # noqa: BLE001
                    last_exc = exc
                    if attempt < self._retries - 1 and self._retry_delay:
                        time.sleep(self._retry_delay)
            raise last_exc
        return read

    def run_test(self, ammeter_type: str) -> TestResult:
        if ammeter_type not in self.config["ammeters"]:
            raise KeyError(f"Unknown ammeter '{ammeter_type}'. "
                           f"Known: {list(self.config['ammeters'])}")
        spec = self.config["ammeters"][ammeter_type]
        port, command = spec["port"], spec["command"]

        sampling_cfg = self.config["testing"]["sampling"]
        plan = resolve_sampling(
            sampling_cfg.get("measurements_count"),
            sampling_cfg.get("total_duration_seconds"),
            sampling_cfg.get("sampling_frequency_hz"),
        )
        for note in plan.notes:
            self.logger.warning(f"[{ammeter_type}] {note}")
        self.logger.info(
            f"[{ammeter_type}] Collecting {plan.count} samples @ {plan.frequency:.3g} Hz "
            f"(~{plan.duration:.2f}s)"
        )

        reader = self._make_reader(port, command)

        # Error simulation (bonus) - wraps the reader if enabled in config.
        err_cfg = self.config.get("error_simulation", {})
        if err_cfg.get("enabled"):
            injector = ErrorInjector(err_cfg.get("drop_rate", 0.0),
                                     err_cfg.get("corrupt_rate", 0.0))
            reader = injector.wrap(reader)
            self.logger.warning(f"[{ammeter_type}] Error simulation ENABLED "
                                f"(drop={injector.drop_rate}, corrupt={injector.corrupt_rate})")

        samples = collect_samples(reader, plan)
        values = [s.value for s in samples]
        failures = [s for s in samples if s.value is None]
        if failures:
            self.logger.error(f"[{ammeter_type}] {len(failures)}/{len(samples)} samples failed.")

        stats = analyzer.compute_statistics(values)
        consistency = analyzer.evaluate_consistency([s.timestamp for s in samples])

        result = TestResult(
            ammeter_type=ammeter_type,
            command=command,
            port=port,
            sampling_plan=asdict(plan),
            statistics=stats,
            consistency=consistency,
            samples=[asdict(s) for s in samples],
            metadata={"failed_samples": len(failures), "host": self._host},
        )

        rm = self.config.get("result_management", {})
        run_dir = result.save(self._output_dir(), rm.get("save_raw_samples", True))
        self._maybe_plot(result, run_dir)
        self.logger.info(f"[{ammeter_type}] Saved run {result.run_id} -> {run_dir}")
        return result

    def _maybe_plot(self, result: TestResult, run_dir: str) -> None:
        viz = self.config.get("analysis", {}).get("visualization", {})
        if not viz.get("enabled"):
            return
        plot_types = viz.get("plot_types", [])
        try:
            if "histogram" in plot_types:
                visualizer.plot_histogram(result, run_dir)
            if "time_series" in plot_types:
                visualizer.plot_time_series(result, run_dir)
        except Exception as exc:  # noqa: BLE001 - plotting must never break a run
            self.logger.error(f"Plotting failed for {result.ammeter_type}: {exc}")

    # -- orchestration: all ammeters ---------------------------------------

    def run_all(self, ammeter_types: Optional[List[str]] = None) -> Dict[str, TestResult]:
        types = ammeter_types or list(self.config["ammeters"].keys())
        results: Dict[str, TestResult] = {}
        for t in types:
            self.logger.info(f"=== Testing {t} ===")
            results[t] = self.run_test(t)
        return results

    def compare(self, results: Dict[str, TestResult]) -> Dict:
        """Cross-ammeter reliability comparison + a comparison plot (bonus)."""
        cfg = self.config.get("analysis", {}).get("accuracy_comparison", {})
        if not cfg.get("enabled", False):
            return {}
        stats_by = {name: res.statistics for name, res in results.items()}
        comparison = analyzer.compare_ammeters(stats_by)

        viz = self.config.get("analysis", {}).get("visualization", {})
        if viz.get("enabled") and "comparison" in viz.get("plot_types", []):
            try:
                results_dir = self._output_dir()
                out = os.path.join(results_dir, "comparison.png")
                os.makedirs(results_dir, exist_ok=True)
                visualizer.plot_comparison(results, out)
                comparison["plot"] = out
            except Exception as exc:  # noqa: BLE001
                self.logger.error(f"Comparison plot failed: {exc}")

        self.logger.info(f"Most reliable ammeter: {comparison.get('most_reliable')}")
        return comparison
