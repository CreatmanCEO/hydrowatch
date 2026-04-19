"""Generate synthetic time series with anomaly injection for groundwater wells."""
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd


class AnomalyInjector:
    """Inject realistic anomalies into time series."""

    @staticmethod
    def gradual_decline(
        ts: np.ndarray,
        start_idx: int,
        duration: int,
        decline_pct: float,
    ) -> np.ndarray:
        """Gradual decline over duration (e.g., debit decline from clogging)."""
        result = ts.copy()
        end_idx = min(start_idx + duration, len(ts))
        baseline = ts[start_idx]
        target = baseline * (1 - decline_pct)

        # Apply decline ramp
        for i in range(start_idx, end_idx):
            progress = (i - start_idx) / duration
            result[i] = baseline - (baseline - target) * progress

        # After decline, stay at reduced level
        if end_idx < len(ts):
            final_value = result[end_idx - 1] if end_idx > start_idx else target
            if baseline != 0:
                result[end_idx:] = result[end_idx:] * (final_value / baseline)
            else:
                result[end_idx:] = target

        return result

    @staticmethod
    def sudden_spike(
        ts: np.ndarray,
        start_idx: int,
        duration: int,
        spike_factor: float,
    ) -> np.ndarray:
        """Sudden spike (e.g., TDS spike from contamination event)."""
        result = ts.copy()
        end_idx = min(start_idx + duration, len(ts))
        result[start_idx:end_idx] *= spike_factor
        return result

    @staticmethod
    def sensor_fault(
        ts: np.ndarray,
        start_idx: int,
        duration: int,
        fault_value: float = 0.0,
    ) -> np.ndarray:
        """Sensor fault — stuck or zero readings."""
        result = ts.copy()
        end_idx = min(start_idx + duration, len(ts))
        result[start_idx:end_idx] = fault_value
        return result


# Default base parameters for well time series generation
DEFAULT_BASE_PARAMS = {
    "debit_ls": {"mean": 10.0, "std": 1.5, "seasonal_amp": 1.0},
    "tds_mgl": {"mean": 4500.0, "std": 200.0, "seasonal_amp": 300.0},
    "ph": {"mean": 7.8, "std": 0.1, "seasonal_amp": 0.05},
    "chloride_mgl": {"mean": 2000.0, "std": 100.0, "seasonal_amp": 150.0},
    "water_level_m": {"mean": 45.0, "std": 1.0, "seasonal_amp": 3.0},
    "temperature_c": {"mean": 32.0, "std": 0.3, "seasonal_amp": 2.0},
}


def _generate_base_signal(
    n_points: int,
    mean: float,
    std: float,
    seasonal_amp: float,
    measurements_per_day: int,
    ar_coef: float = 0.85,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """Generate base signal: mean + seasonal + diurnal + AR(1) noise."""
    if rng is None:
        rng = np.random.default_rng()

    t = np.arange(n_points)

    # Seasonal component (yearly cycle)
    seasonal = seasonal_amp * np.sin(2 * np.pi * t / (365 * measurements_per_day))

    # Diurnal component (daily cycle, smaller)
    diurnal = seasonal_amp * 0.1 * np.sin(2 * np.pi * t / measurements_per_day)

    # AR(1) correlated noise
    noise = np.zeros(n_points)
    noise[0] = rng.normal(0, std)
    for i in range(1, n_points):
        noise[i] = ar_coef * noise[i - 1] + rng.normal(0, std * (1 - ar_coef**2) ** 0.5)

    signal = mean + seasonal + diurnal + noise
    return signal


def generate_well_timeseries(
    well_id: str,
    days: int = 365,
    measurements_per_day: int = 4,
    inject_anomalies: bool = True,
    base_params: dict | None = None,
    seed: int | None = None,
) -> tuple[pd.DataFrame, list[dict]]:
    """
    Generate time series for a single well.

    Returns:
        Tuple of (DataFrame, anomaly_log list).
    """
    if seed is None:
        seed = hash(well_id) % (2**31)
    rng = np.random.default_rng(seed)

    n_points = days * measurements_per_day
    params = base_params or DEFAULT_BASE_PARAMS

    # Randomize base params slightly per well
    well_params = {}
    for param, cfg in params.items():
        well_params[param] = {
            "mean": cfg["mean"] * rng.uniform(0.7, 1.3),
            "std": cfg["std"] * rng.uniform(0.5, 1.5),
            "seasonal_amp": cfg["seasonal_amp"] * rng.uniform(0.5, 1.5),
        }

    # Generate base signals
    data = {}
    for param, cfg in well_params.items():
        data[param] = _generate_base_signal(
            n_points,
            cfg["mean"],
            cfg["std"],
            cfg["seasonal_amp"],
            measurements_per_day,
            rng=rng,
        )

    # Ensure non-negative values
    data["debit_ls"] = np.maximum(data["debit_ls"], 0.0)
    data["water_level_m"] = np.maximum(data["water_level_m"], 1.0)
    data["tds_mgl"] = np.maximum(data["tds_mgl"], 500.0)
    data["ph"] = np.clip(data["ph"], 6.0, 9.5)
    data["chloride_mgl"] = np.maximum(data["chloride_mgl"], 50.0)
    data["temperature_c"] = np.clip(data["temperature_c"], 20.0, 50.0)

    # Inject anomalies
    anomaly_log = []
    if inject_anomalies and n_points > 200:
        # Decide which anomalies to inject (1-3 per well)
        n_anomalies = rng.integers(1, 4)
        anomaly_types = rng.choice(
            ["debit_decline", "tds_spike", "sensor_fault"],
            size=n_anomalies,
            replace=False,
        )

        for atype in anomaly_types:
            start = int(rng.integers(n_points // 5, n_points * 3 // 5))
            duration = int(rng.integers(n_points // 10, n_points // 4))

            if atype == "debit_decline":
                decline_pct = float(rng.uniform(0.25, 0.50))
                data["debit_ls"] = AnomalyInjector.gradual_decline(
                    data["debit_ls"], start, duration, decline_pct
                )
                anomaly_log.append({
                    "type": "debit_decline",
                    "start_idx": start,
                    "duration": duration,
                    "decline_pct": round(decline_pct, 3),
                    "parameter": "debit_ls",
                })

            elif atype == "tds_spike":
                spike_factor = float(rng.uniform(1.5, 3.0))
                spike_dur = max(duration // 3, 10)
                data["tds_mgl"] = AnomalyInjector.sudden_spike(
                    data["tds_mgl"], start, spike_dur, spike_factor
                )
                anomaly_log.append({
                    "type": "tds_spike",
                    "start_idx": start,
                    "duration": spike_dur,
                    "spike_factor": round(spike_factor, 2),
                    "parameter": "tds_mgl",
                })

            elif atype == "sensor_fault":
                fault_dur = max(duration // 5, 5)
                data["ph"] = AnomalyInjector.sensor_fault(
                    data["ph"], start, fault_dur, fault_value=0.0
                )
                anomaly_log.append({
                    "type": "sensor_fault",
                    "start_idx": start,
                    "duration": fault_dur,
                    "fault_value": 0.0,
                    "parameter": "ph",
                })

    # Build timestamps
    start_date = datetime(2024, 1, 1)
    hours_step = 24 // measurements_per_day
    timestamps = [
        start_date + timedelta(hours=i * hours_step)
        for i in range(n_points)
    ]

    df = pd.DataFrame({
        "timestamp": timestamps,
        "well_id": well_id,
        "debit_ls": np.round(data["debit_ls"], 3),
        "tds_mgl": np.round(data["tds_mgl"], 1),
        "ph": np.round(data["ph"], 2),
        "chloride_mgl": np.round(data["chloride_mgl"], 1),
        "water_level_m": np.round(data["water_level_m"], 2),
        "temperature_c": np.round(data["temperature_c"], 1),
    })

    return df, anomaly_log


def generate_all_timeseries(
    well_ids: list[str],
    days: int = 365,
    measurements_per_day: int = 4,
    output_dir: str | None = None,
) -> dict[str, pd.DataFrame]:
    """
    Generate time series for all wells.

    Returns:
        Dict mapping well_id -> DataFrame.
    """
    result = {}

    for well_id in well_ids:
        df, anomaly_log = generate_well_timeseries(
            well_id, days=days, measurements_per_day=measurements_per_day
        )
        result[well_id] = df

        if output_dir:
            out_path = Path(output_dir)
            out_path.mkdir(parents=True, exist_ok=True)
            df.to_csv(out_path / f"{well_id}.csv", index=False)

    return result


def main():
    """Generate time series for all wells from wells.geojson."""
    data_dir = Path(__file__).resolve().parent.parent.parent / "data"
    geojson_path = data_dir / "wells.geojson"

    with open(geojson_path) as f:
        geojson = json.load(f)

    well_ids = [f["properties"]["id"] for f in geojson["features"]]
    obs_dir = data_dir / "observations"

    result = generate_all_timeseries(
        well_ids, days=365, output_dir=str(obs_dir)
    )
    print(f"Generated {len(result)} time series -> observations/")


if __name__ == "__main__":
    main()
