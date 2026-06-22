import json
import os
import platform
import sys
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Dict, List, Optional


@dataclass
class TestResult:
    """
    A single test run's complete record: identity, configuration, raw samples,
    statistics and metadata. Serialises to a self-contained ``result.json`` so
    runs can be archived, retrieved and compared later.
    """
    # Not a pytest test class despite the "Test" prefix.
    __test__ = False

    ammeter_type: str
    command: str
    port: int
    run_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))

    sampling_plan: Dict = field(default_factory=dict)
    statistics: Dict = field(default_factory=dict)
    consistency: Dict = field(default_factory=dict)
    samples: List[Dict] = field(default_factory=list)
    metadata: Dict = field(default_factory=dict)

    def __post_init__(self):
        # Stamp environment metadata for reproducibility.
        self.metadata.setdefault("python_version", sys.version.split()[0])
        self.metadata.setdefault("platform", platform.platform())

    @property
    def folder_name(self) -> str:
        ts = self.timestamp.replace(":", "").replace("-", "").replace("T", "_")
        return f"{ts}_{self.ammeter_type}_{self.run_id}"

    def to_dict(self) -> Dict:
        return asdict(self)

    def save(self, output_dir: str = "results", save_raw_samples: bool = True) -> str:
        """Write the run to ``output_dir/<folder_name>/result.json`` and return that folder."""
        run_dir = os.path.join(output_dir, self.folder_name)
        os.makedirs(run_dir, exist_ok=True)

        data = self.to_dict()
        if not save_raw_samples:
            data.pop("samples", None)

        with open(os.path.join(run_dir, "result.json"), "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        return run_dir

    @classmethod
    def load(cls, path: str) -> "TestResult":
        """Load a result from a result.json file or its containing folder."""
        if os.path.isdir(path):
            path = os.path.join(path, "result.json")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls(**data)


def list_results(output_dir: str = "results") -> List[str]:
    """Return saved run folders (newest first) for historical retrieval/comparison."""
    if not os.path.isdir(output_dir):
        return []
    runs = [
        os.path.join(output_dir, d)
        for d in os.listdir(output_dir)
        if os.path.isfile(os.path.join(output_dir, d, "result.json"))
    ]
    return sorted(runs, reverse=True)
