import os
from typing import Dict, List

import matplotlib
matplotlib.use("Agg")  # headless backend: works on any machine, no display needed
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="whitegrid")


def _values(result) -> List[float]:
    return [s["value"] for s in result.samples
            if s.get("value") is not None and s["value"] == s["value"]]  # drop None/NaN


def plot_histogram(result, out_dir: str) -> str:
    """Distribution of measured current for a single run."""
    path = os.path.join(out_dir, "histogram.png")
    plt.figure(figsize=(8, 5))
    sns.histplot(_values(result), kde=True, color="steelblue")
    plt.axvline(result.statistics.get("mean", 0), color="red", linestyle="--", label="mean")
    plt.title(f"{result.ammeter_type} - Current Distribution")
    plt.xlabel("Current (A)")
    plt.ylabel("Count")
    plt.legend()
    plt.tight_layout()
    plt.savefig(path, dpi=120)
    plt.close()
    return path


def plot_time_series(result, out_dir: str) -> str:
    """Measured current over time for a single run."""
    path = os.path.join(out_dir, "time_series.png")
    ts = [s["timestamp"] for s in result.samples if s.get("value") is not None]
    vals = [s["value"] for s in result.samples if s.get("value") is not None]
    plt.figure(figsize=(8, 5))
    plt.plot(ts, vals, marker="o", markersize=3, color="darkgreen")
    plt.title(f"{result.ammeter_type} - Current vs Time")
    plt.xlabel("Time (s)")
    plt.ylabel("Current (A)")
    plt.tight_layout()
    plt.savefig(path, dpi=120)
    plt.close()
    return path


def plot_comparison(results: Dict[str, "object"], out_path: str) -> str:
    """Box-plot comparing the current distributions of multiple ammeters."""
    data, labels = [], []
    for name, res in results.items():
        vals = _values(res)
        if vals:
            data.append(vals)
            labels.append(name)
    plt.figure(figsize=(8, 5))
    plt.boxplot(data, tick_labels=labels, showmeans=True)
    plt.title("Ammeter Comparison - Current Distributions")
    plt.ylabel("Current (A)")
    plt.tight_layout()
    plt.savefig(out_path, dpi=120)
    plt.close()
    return out_path
