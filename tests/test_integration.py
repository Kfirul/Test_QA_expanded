"""
End-to-end integration tests that exercise the real socket emulators.

Marked ``integration`` (slower); run just the fast unit tests with:
    pytest -m "not integration"
"""
import pytest

from Ammeters.client import get_current_measurement
from src.testing.test_framework import AmmeterTestFramework

pytestmark = pytest.mark.integration

# Plausible current ranges per ammeter, from the emulator formulas.
EXPECTED_RANGES = {
    "greenlee": (0.0, 100.0),   # V/R, 1..10 / 0.1..100
    "entes": (5.0, 200.0),      # B*K, 0.01..0.1 * 500..2000
    "circutor": (0.0, 0.1),     # sum(V*dt), small
}


@pytest.mark.parametrize("ammeter", ["greenlee", "entes", "circutor"])
def test_single_measurement(emulators, config, ammeter):
    spec = config["ammeters"][ammeter]
    value = get_current_measurement(spec["port"], spec["command"])
    low, high = EXPECTED_RANGES[ammeter]
    assert isinstance(value, float)
    assert low <= value <= high


def test_framework_run_test(emulators, tmp_path):
    framework = AmmeterTestFramework(start_emulators=False)
    framework.config["testing"]["sampling"] = {
        "measurements_count": 8,
        "total_duration_seconds": None,
        "sampling_frequency_hz": 20.0,
    }
    framework.config["result_management"]["output_dir"] = str(tmp_path)
    framework.config["analysis"]["visualization"]["enabled"] = False

    result = framework.run_test("greenlee")
    assert result.statistics["count"] == 8
    assert result.metadata["failed_samples"] == 0
    assert (tmp_path / result.folder_name / "result.json").exists()


def test_framework_run_all_and_compare(emulators, tmp_path):
    framework = AmmeterTestFramework(start_emulators=False)
    framework.config["testing"]["sampling"] = {
        "measurements_count": 6,
        "total_duration_seconds": None,
        "sampling_frequency_hz": 20.0,
    }
    framework.config["result_management"]["output_dir"] = str(tmp_path)
    framework.config["analysis"]["visualization"]["enabled"] = False

    results = framework.run_all()
    assert set(results) == {"greenlee", "entes", "circutor"}

    comparison = framework.compare(results)
    assert comparison["most_reliable"] in results


def test_unknown_ammeter_raises():
    framework = AmmeterTestFramework(start_emulators=False)
    with pytest.raises(KeyError):
        framework.run_test("nonexistent")
