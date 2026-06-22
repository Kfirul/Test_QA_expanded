import logging
import os
from datetime import datetime


class TestLogger:
    """
    Thin wrapper around the standard ``logging`` module that writes both to a
    timestamped file (under results/logs) and to the console.

    The original implementation created a logger but never attached a handler
    or formatter, so nothing was ever written. This version wires both up.
    """

    def __init__(self, test_name: str, log_dir: str = "results/logs"):
        self._test_name = test_name
        self._log_dir = log_dir
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        os.makedirs(self._log_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(self._log_dir, f"{timestamp}_{self._test_name}.log")

        logger = logging.getLogger(f"test_{self._test_name}")
        logger.setLevel(logging.INFO)
        logger.propagate = False

        # Avoid duplicate handlers if a logger with this name already exists.
        if not logger.handlers:
            fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setFormatter(fmt)
            logger.addHandler(file_handler)

            console_handler = logging.StreamHandler()
            console_handler.setFormatter(fmt)
            logger.addHandler(console_handler)

        return logger

    def info(self, message: str):
        self.logger.info(message)

    def error(self, message: str):
        self.logger.error(message)

    def debug(self, message: str):
        self.logger.debug(message)

    def warning(self, message: str):
        self.logger.warning(message)
