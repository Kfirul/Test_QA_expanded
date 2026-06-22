"""
Starts the three ammeter emulators and requests one measurement from each.

This is the minimal "make it work" entry point required by the exercise. The
ports and commands are read from config/config.yaml so they stay consistent
with the rest of the framework.

Run:  py main.py   (Windows)   or   python3 main.py
"""
from Ammeters.client import request_current_from_ammeter
from src.utils.config import load_config
from src.testing.emulator_manager import EmulatorManager


def main():
    config = load_config()
    ammeters = config["ammeters"]

    # Start every configured emulator and wait until the ports are accepting
    # connections (no fragile time.sleep guesswork).
    manager = EmulatorManager(ammeters, host=config["testing"]["connection"]["host"])
    manager.start()

    # Request one measurement from each ammeter using its exact command.
    for name, spec in ammeters.items():
        request_current_from_ammeter(spec["port"], spec["command"].encode("utf-8"))


if __name__ == "__main__":
    main()
