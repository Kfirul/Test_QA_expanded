"""Shared pytest fixtures."""
import pytest

from src.utils.config import load_config
from src.testing.emulator_manager import EmulatorManager


@pytest.fixture(scope="session")
def config():
    """The project's loaded configuration."""
    return load_config()


@pytest.fixture(scope="session")
def emulators(config):
    """
    Start the ammeter emulators once for the whole test session.

    Daemon threads stop automatically when the test process exits, so there is
    no teardown step. Used by integration tests that need live servers.
    """
    manager = EmulatorManager(config["ammeters"], host=config["testing"]["connection"]["host"])
    manager.start()
    return manager
