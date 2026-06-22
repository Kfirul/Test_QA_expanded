"""Starts the ammeter emulators on threads and waits until their ports are ready."""
import socket
import threading
import time
from typing import Dict, Optional

from Ammeters.Greenlee_Ammeter import GreenleeAmmeter
from Ammeters.Entes_Ammeter import EntesAmmeter
from Ammeters.Circutor_Ammeter import CircutorAmmeter

# Maps the ammeter name used in config.yaml to its emulator class.
AMMETER_CLASSES = {
    "greenlee": GreenleeAmmeter,
    "entes": EntesAmmeter,
    "circutor": CircutorAmmeter,
}


class EmulatorManager:
    """
    Starts the ammeter emulators (each on its own daemon thread) and waits until
    their TCP ports are actually accepting connections, so a test run never races
    the server start-up. Ports/commands come from the config (config-driven).
    """

    def __init__(self, ammeters_config: Dict, host: str = "localhost"):
        self._ammeters_config = ammeters_config
        self._host = host
        self._threads: Dict[str, threading.Thread] = {}

    def start(self, wait_timeout: float = 10.0) -> None:
        for name, spec in self._ammeters_config.items():
            cls = AMMETER_CLASSES.get(name.lower())
            if cls is None:
                # Unknown ammeter in config (e.g. a future type without an emulator).
                continue
            if name in self._threads:
                continue
            emulator = cls(spec["port"])
            thread = threading.Thread(target=emulator.start_server, daemon=True)
            thread.start()
            self._threads[name] = thread

        self._wait_until_ready(wait_timeout)

    def _wait_until_ready(self, timeout: float) -> None:
        deadline = time.time() + timeout
        for name, spec in self._ammeters_config.items():
            if name.lower() not in AMMETER_CLASSES:
                continue
            port = spec["port"]
            while True:
                if self._port_open(port):
                    break
                if time.time() > deadline:
                    raise TimeoutError(
                        f"Emulator '{name}' on port {port} did not become ready in {timeout}s."
                    )
                time.sleep(0.05)

    def _port_open(self, port: int) -> bool:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.2)
            return s.connect_ex((self._host, port)) == 0
