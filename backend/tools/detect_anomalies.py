"""Tool: Detect anomalies in well time series data."""
import json
import os
from pathlib import Path

import pandas as pd
import numpy as np
from scipy.stats import linregress

from models.schemas import AnomalyCard

DATA_DIR = os.environ.get("DATA_DIR", "./data")


def _detect_debit_decline(df: pd.DataFrame, well_id: str) -> list[AnomalyCard]:
    """Detect gradual debit decline via linear regression on recent window."""
    cards = []
    values = df["debit_ls"].values
    n = len(values)
    if n < 100:
        return cards

    # Compare first quarter vs last quarter
    q1 = values[:n // 4]
    q4 = values[3 * n // 4:]
    mean_q1 = float(np.mean(q1))
    mean_q4 = float(np.mean(q4))

    if mean_q1 > 0:
        change_pct = (mean_q4 - mean_q1) / mean_q1 * 100
        if change_pct < -15:  # >15% decline
            severity = "critical" if change_pct < -40 else "high" if change_pct < -25 else "medium"
            cards.append(AnomalyCard(
                severity=severity,
                well_id=well_id,
                anomaly_type="debit_decline",
                title=f"Debit decline: {change_pct:.1f}%",
                description=f"Flow rate declined from {mean_q1:.1f} to {mean_q4:.1f} L/s over observation period",
                value_current=round(mean_q4, 2),
                value_baseline=round(mean_q1, 2),
                change_pct=round(change_pct, 1),
                recommendation="Schedule pump inspection and well rehabilitation assessment",
            ))
    return cards


def _detect_tds_spike(df: pd.DataFrame, well_id: str) -> list[AnomalyCard]:
    """Detect sudden TDS spikes (contamination events)."""
    cards = []
    values = df["tds_mgl"].values
    if len(values) < 50:
        return cards

    # Rolling stats
    window = min(50, len(values) // 4)
    rolling_mean = pd.Series(values).rolling(window, center=True).mean().values
    rolling_std = pd.Series(values).rolling(window, center=True).std().values

    # Find points > 3 sigma above rolling mean
    with np.errstate(invalid="ignore"):
        z_scores = np.where(rolling_std > 0, (values - rolling_mean) / rolling_std, 0)

    spike_mask = z_scores > 3.0
    if spike_mask.any():
        spike_max = float(np.max(values[spike_mask]))
        baseline = float(np.nanmean(rolling_mean))
        change_pct = (spike_max - baseline) / baseline * 100 if baseline > 0 else 0

        severity = "high" if change_pct > 50 else "medium" if change_pct > 20 else "low"
        cards.append(AnomalyCard(
            severity=severity,
            well_id=well_id,
            anomaly_type="tds_spike",
            title=f"TDS spike detected: {spike_max:.0f} mg/L",
            description=f"TDS spiked to {spike_max:.0f} from baseline {baseline:.0f} mg/L ({change_pct:.1f}% increase)",
            value_current=round(spike_max, 1),
            value_baseline=round(baseline, 1),
            change_pct=round(change_pct, 1),
            recommendation="Investigate potential contamination source; collect confirmation samples",
        ))
    return cards


def _detect_sensor_fault(df: pd.DataFrame, well_id: str) -> list[AnomalyCard]:
    """Detect sensor faults (zero or constant readings)."""
    cards = []
    for col in ["ph", "debit_ls", "water_level_m"]:
        if col not in df.columns:
            continue
        values = df[col].values

        # Check for zero runs
        zero_runs = 0
        max_run = 0
        for v in values:
            if v == 0.0:
                zero_runs += 1
                max_run = max(max_run, zero_runs)
            else:
                zero_runs = 0

        if max_run >= 5:
            cards.append(AnomalyCard(
                severity="medium",
                well_id=well_id,
                anomaly_type="sensor_fault",
                title=f"Sensor fault in {col}",
                description=f"{col} shows {max_run} consecutive zero readings — likely sensor malfunction",
                value_current=0.0,
                value_baseline=float(np.mean(values[values != 0])) if (values != 0).any() else 0.0,
                change_pct=-100.0,
                recommendation=f"Inspect {col} sensor; replace if confirmed faulty",
            ))
    return cards


def detect_anomalies(well_id: str | None = None) -> list[AnomalyCard]:
    """
    Detect anomalies for one well or all wells.

    Args:
        well_id: Specific well to analyze, or None for all wells.

    Returns:
        List of AnomalyCard objects.
    """
    obs_dir = Path(DATA_DIR) / "observations"
    cards = []

    if well_id:
        csv_files = [obs_dir / f"{well_id}.csv"]
    else:
        csv_files = sorted(obs_dir.glob("*.csv"))

    for csv_path in csv_files:
        if not csv_path.exists():
            continue
        wid = csv_path.stem
        df = pd.read_csv(csv_path, parse_dates=["timestamp"])
        df = df.sort_values("timestamp")

        cards.extend(_detect_debit_decline(df, wid))
        cards.extend(_detect_tds_spike(df, wid))
        cards.extend(_detect_sensor_fault(df, wid))

    # Sort by severity
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    cards.sort(key=lambda c: severity_order.get(c.severity, 4))

    return cards
