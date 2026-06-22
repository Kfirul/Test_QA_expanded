"""Unit tests for result archiving and retrieval."""
from src.testing.result import TestResult, list_results


def _make_result():
    return TestResult(
        ammeter_type="greenlee",
        command="MEASURE_GREENLEE -get_measurement",
        port=5000,
        statistics={"count": 2, "mean": 1.5},
        samples=[{"index": 0, "timestamp": 0.0, "value": 1.0, "error": None},
                 {"index": 1, "timestamp": 0.1, "value": 2.0, "error": None}],
    )


def test_run_id_and_folder_name():
    result = _make_result()
    assert len(result.run_id) == 12
    assert result.ammeter_type in result.folder_name
    assert result.run_id in result.folder_name


def test_metadata_is_stamped():
    result = _make_result()
    assert "python_version" in result.metadata
    assert "platform" in result.metadata


def test_save_and_load_roundtrip(tmp_path):
    result = _make_result()
    run_dir = result.save(str(tmp_path))

    loaded = TestResult.load(run_dir)
    assert loaded.ammeter_type == result.ammeter_type
    assert loaded.run_id == result.run_id
    assert loaded.statistics == result.statistics
    assert len(loaded.samples) == 2


def test_save_without_raw_samples(tmp_path):
    result = _make_result()
    run_dir = result.save(str(tmp_path), save_raw_samples=False)
    loaded = TestResult.load(run_dir)
    assert loaded.samples == []


def test_list_results(tmp_path):
    _make_result().save(str(tmp_path))
    _make_result().save(str(tmp_path))
    runs = list_results(str(tmp_path))
    assert len(runs) == 2


def test_list_results_empty_dir(tmp_path):
    assert list_results(str(tmp_path / "does-not-exist")) == []
