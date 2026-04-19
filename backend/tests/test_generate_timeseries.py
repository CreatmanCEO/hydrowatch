"""Tests for time series generation with anomalies."""
import pandas as pd
import numpy as np
import pytest
from data_generator.generate_timeseries import (
    generate_well_timeseries,
    AnomalyInjector,
    generate_all_timeseries,
)


class TestTimeSeriesGeneration:

    def test_correct_columns(self):
        df, _ = generate_well_timeseries("W-001", days=30)
        expected_cols = {"timestamp", "well_id", "debit_ls", "tds_mgl",
                         "ph", "chloride_mgl", "water_level_m", "temperature_c"}
        assert expected_cols.issubset(set(df.columns))

    def test_correct_length(self):
        df, _ = generate_well_timeseries("W-001", days=365, measurements_per_day=4)
        assert len(df) == 365 * 4

    def test_values_in_realistic_ranges(self):
        df, _ = generate_well_timeseries("W-001", days=90, seed=42)
        assert df["debit_ls"].min() >= 0
        assert 500 < df["tds_mgl"].mean() < 15000
        assert 6.0 < df["ph"].mean() < 9.5
        assert df["water_level_m"].min() > 0

    def test_anomaly_injection_debit_decline(self):
        ts = np.full(1000, 10.0)
        result = AnomalyInjector.gradual_decline(ts, start_idx=200, duration=300, decline_pct=0.4)
        assert result[100] == pytest.approx(10.0, abs=0.1)  # before anomaly
        assert result[800] == pytest.approx(6.0, abs=0.5)   # after: 40% decline

    def test_anomaly_log_populated(self):
        _, anomaly_log = generate_well_timeseries("W-001", days=365, inject_anomalies=True)
        assert len(anomaly_log) > 0
        assert all("type" in a for a in anomaly_log)


class TestBatchGeneration:

    def test_generates_for_all_wells(self):
        well_ids = ["W-001", "W-002", "W-003"]
        result = generate_all_timeseries(well_ids, days=30)
        assert len(result) == 3
        assert all(wid in result for wid in well_ids)
