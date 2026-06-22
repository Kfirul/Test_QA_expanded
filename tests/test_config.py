"""Unit tests for config loading and validation."""
import pytest

from src.utils.config import load_config


def test_load_default_config_has_ammeters():
    config = load_config()
    assert "ammeters" in config
    for name in ("greenlee", "entes", "circutor"):
        assert name in config["ammeters"]
        assert "port" in config["ammeters"][name]
        assert "command" in config["ammeters"][name]


def test_missing_file_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_config(str(tmp_path / "nope.yaml"))


def test_invalid_config_without_ammeters_raises(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("testing:\n  sampling: {}\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_config(str(bad))


def test_ammeter_missing_port_raises(tmp_path):
    bad = tmp_path / "bad.yaml"
    bad.write_text("ammeters:\n  greenlee:\n    command: x\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_config(str(bad))
