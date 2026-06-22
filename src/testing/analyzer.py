"""Statistical analysis, sampling-consistency, and cross-ammeter comparison."""
from typing import Dict, List

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats


def compute_statistics(values: List[float]) -> Dict:
    """
    Compute the required statistical metrics for a set of measurements:
    mean, median, standard deviation, min, max -- plus range and the
    coefficient of variation (a normalised consistency measure, bonus).

    NaNs (e.g. from error simulation) are ignored so corrupted samples don't
    poison the statistics.
    """
    arr = np.asarray([v for v in values if v is not None], dtype=float)
    arr = arr[~np.isnan(arr)]

    if arr.size == 0:
        return {"count": 0}

    mean = float(np.mean(arr))
    std = float(np.std(arr, ddof=1)) if arr.size > 1 else 0.0
    cv = float(std / mean) if mean != 0 else float("nan")

    # 95% confidence interval of the mean (Student's t) - quantifies how
    # precisely the true mean current is known from this sample.
    if arr.size > 1 and std > 0:
        sem = scipy_stats.sem(arr)
        low, high = scipy_stats.t.interval(0.95, arr.size - 1, loc=mean, scale=sem)
        ci_95 = [float(low), float(high)]
    else:
        ci_95 = [mean, mean]

    return {
        "count": int(arr.size),
        "mean": mean,
        "median": float(np.median(arr)),
        "std_dev": std,
        "min": float(np.min(arr)),
        "max": float(np.max(arr)),
        "range": float(np.max(arr) - np.min(arr)),
        "coefficient_of_variation": cv,
        "confidence_interval_95": ci_95,
    }


def evaluate_consistency(timestamps: List[float]) -> Dict:
    """
    Performance-consistency (bonus): how regular was the sampling cadence?
    Reports the mean inter-sample interval and its jitter (std-dev).
    """
    if len(timestamps) < 2:
        return {"mean_interval": None, "interval_jitter": None}
    intervals = np.diff(np.asarray(timestamps, dtype=float))
    return {
        "mean_interval": float(np.mean(intervals)),
        "interval_jitter": float(np.std(intervals, ddof=1)) if intervals.size > 1 else 0.0,
    }


def compare_ammeters(stats_by_ammeter: Dict[str, Dict]) -> Dict:
    """
    Accuracy / reliability comparison across ammeter types (bonus).

    The emulators produce random currents with no shared ground-truth, so
    "accuracy" cannot be measured against a true value. Instead we quantify
    *precision / reliability* via the coefficient of variation (CV): the
    ammeter with the lowest CV produces the most consistent (reliable)
    readings. Returns a ranked table and the winner.
    """
    rows = []
    for name, st in stats_by_ammeter.items():
        if st.get("count", 0) == 0:
            continue
        rows.append({
            "ammeter": name,
            "mean": st["mean"],
            "std_dev": st["std_dev"],
            "coefficient_of_variation": st["coefficient_of_variation"],
            "range": st["range"],
            "samples": st["count"],
        })

    if not rows:
        return {"ranking": [], "most_reliable": None, "table": "(no data)"}

    df = pd.DataFrame(rows).sort_values("coefficient_of_variation").reset_index(drop=True)
    df.insert(0, "rank", df.index + 1)

    return {
        "ranking": df.to_dict(orient="records"),
        "most_reliable": df.iloc[0]["ammeter"],
        "table": df.to_string(index=False),
    }
