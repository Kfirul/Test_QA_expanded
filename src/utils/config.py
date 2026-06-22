"""Configuration loading: YAML parsing, project-root path resolution, validation."""
import os
import yaml
from typing import Dict

# Project root = two levels up from this file (src/utils/config.py -> project root).
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_CONFIG_PATH = os.path.join(PROJECT_ROOT, "config", "config.yaml")


def load_config(config_path: str = DEFAULT_CONFIG_PATH) -> Dict:
    """
    Load the YAML configuration file.

    The path is resolved relative to the project root when a relative path is
    given, so the framework works no matter which directory it is launched from
    (cross-platform / cross-cwd robustness).
    """
    if not os.path.isabs(config_path):
        candidate = os.path.join(PROJECT_ROOT, config_path)
        config_path = candidate if os.path.exists(candidate) else config_path

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f) or {}

    _validate(config)
    return config


def _validate(config: Dict) -> None:
    """Minimal sanity-checking so failures are explicit, not mysterious KeyErrors."""
    if "ammeters" not in config or not config["ammeters"]:
        raise ValueError("Config error: no 'ammeters' defined.")
    for name, spec in config["ammeters"].items():
        if not isinstance(spec, dict) or "port" not in spec or "command" not in spec:
            raise ValueError(f"Config error: ammeter '{name}' must define 'port' and 'command'.")
