"""Tool: Get time series history for a single well with trend analysis."""

import os
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import linregress

from models.schemas import WellHistory


def _get_data_dir() -> str:
    return os.environ.get("DATA_DIR", "./data")


def get_well_history(
    well_id: str,
    parameter: str = "debit_ls",
    last_n_days: int | None = None,
) -> WellHistory:
    """Get time series for a well with trend analysis."""
    csv_path = Path(_get_data_dir()) / "observations" / f"{well_id}.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"No observation data for well {well_id}")

    df = pd.read_csv(csv_path, parse_dates=["timestamp"])
    df = df.sort_values("timestamp")

    valid_params = {
        "debit_ls",
        "tds_mgl",
        "ph",
        "chloride_mgl",
        "water_level_m",
        "temperature_c",
    }
    if parameter not in valid_params:
        raise KeyError(f"Unknown parameter '{parameter}'. Valid: {', '.join(sorted(valid_params))}")

    if last_n_days is not None:
        cutoff = df["timestamp"].max() - pd.Timedelta(days=last_n_days)
        df = df[df["timestamp"] >= cutoff]

    timestamps = df["timestamp"].dt.strftime("%Y-%m-%dT%H:%M:%S").tolist()
    values = df[parameter].tolist()

    # Trend analysis via linear regression
    x = np.arange(len(values), dtype=float)
    y = np.array(values, dtype=float)
    mask = ~np.isnan(y)
    if mask.sum() > 2:
        slope = linregress(x[mask], y[mask]).slope
        mean_val = np.mean(y[mask])
        relative_slope = slope / mean_val if mean_val != 0 else 0
        if relative_slope > 0.0001:
            trend = "rising"
        elif relative_slope < -0.0001:
            trend = "falling"
        else:
            trend = "stable"
    else:
        trend = "stable"

    return WellHistory(
        well_id=well_id,
        parameter=parameter,
        timestamps=timestamps,
        values=values,
        trend=trend,
    )
