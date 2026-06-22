import random
from typing import Callable


class ErrorInjector:
    """
    Wraps a measurement read function to simulate real-world faults (bonus:
    error simulation). Lets us verify the framework keeps going when the
    hardware/link misbehaves.

    - ``drop_rate``    : probability a read is forced to fail (raises).
    - ``corrupt_rate`` : probability a successful read is corrupted
                         (NaN or a wildly scaled value).
    """

    def __init__(self, drop_rate: float = 0.0, corrupt_rate: float = 0.0,
                 seed: int = None):
        self.drop_rate = float(drop_rate)
        self.corrupt_rate = float(corrupt_rate)
        self._rng = random.Random(seed)

    @property
    def enabled(self) -> bool:
        return self.drop_rate > 0 or self.corrupt_rate > 0

    def wrap(self, read_fn: Callable[[], float]) -> Callable[[], float]:
        def wrapped() -> float:
            if self._rng.random() < self.drop_rate:
                raise ConnectionError("Simulated dropped connection")

            value = read_fn()

            if self._rng.random() < self.corrupt_rate:
                if self._rng.random() < 0.5:
                    return float("nan")
                return value * self._rng.uniform(5, 50)  # implausible spike
            return value

        return wrapped
