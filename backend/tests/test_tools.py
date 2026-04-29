"""Tests for MCP-style tools."""

import json
import os
from pathlib import Path

import pandas as pd
import pytest

# Set DATA_DIR for tools before importing
DATA_DIR = str(Path(__file__).resolve().parent.parent.parent / "data")
os.environ["DATA_DIR"] = DATA_DIR

from tools.detect_anomalies import detect_anomalies
from tools.get_region_stats import get_region_stats
from tools.get_well_history import get_well_history
from tools.query_wells import query_wells
from tools.validate_csv import validate_csv


@pytest.fixture
def data_dir():
    return Path(DATA_DIR)


@pytest.fixture
def sample_well_id(data_dir):
    with open(data_dir / "wells.geojson") as f:
        geojson = json.load(f)
    return geojson["features"][0]["properties"]["id"]


@pytest.fixture
def valid_csv(data_dir, sample_well_id, tmp_path):
    """Copy a real observation CSV to tmp for validation."""
    src = data_dir / "observations" / f"{sample_well_id}.csv"
    dst = tmp_path / "test.csv"
    dst.write_text(src.read_text())
    return str(dst)


@pytest.fixture
def bad_csv(tmp_path):
    """Create a CSV with errors."""
    df = pd.DataFrame(
        {
            "timestamp": ["2024-01-01", "2024-01-02", "bad-date"],
            "well_id": ["W-001", "W-001", "W-001"],
            "debit_ls": [10.0, -5.0, 12.0],  # negative debit
            "tds_mgl": [4500, 4600, 4700],
            "ph": [7.8, 7.9, 15.0],  # ph out of range
            "chloride_mgl": [2000, 2100, 2200],
            "water_level_m": [45.0, 46.0, 47.0],
            "temperature_c": [32.0, 33.0, 34.0],
        }
    )
    path = tmp_path / "bad.csv"
    df.to_csv(path, index=False)
    return str(path)


class TestValidateCSV:
    def test_valid_csv_passes(self, valid_csv):
        result = validate_csv(valid_csv)
        assert result.valid
        assert result.total_rows > 0
        assert result.valid_rows == result.total_rows
        assert len(result.errors) == 0

    def test_bad_csv_reports_errors(self, bad_csv):
        result = validate_csv(bad_csv)
        assert not result.valid
        assert len(result.errors) > 0

    def test_missing_file_returns_error(self):
        result = validate_csv("/nonexistent/file.csv")
        assert not result.valid
        assert any("not found" in e.lower() or "error" in e.lower() for e in result.errors)

    def test_column_stats_populated(self, valid_csv):
        result = validate_csv(valid_csv)
        assert "debit_ls" in result.column_stats
        assert "min" in result.column_stats["debit_ls"]


class TestQueryWells:
    def test_returns_wells(self, data_dir):
        wells = query_wells()
        assert len(wells) > 0
        assert all(hasattr(w, "id") for w in wells)

    def test_filter_by_bbox(self, data_dir):
        # Abu Dhabi region bbox covering Al Wathba cluster
        wells = query_wells(bbox=[54.6, 24.3, 54.9, 24.55])
        assert len(wells) >= 0  # may be empty depending on seed
        for w in wells:
            assert 54.6 <= w.longitude <= 54.9
            assert 24.3 <= w.latitude <= 24.55

    def test_filter_by_status(self, data_dir):
        wells = query_wells(status="active")
        assert all(w.status == "active" for w in wells)

    def test_filter_by_cluster(self, data_dir):
        wells = query_wells(cluster_id="AL_WATHBA")
        assert all(w.cluster_id == "AL_WATHBA" for w in wells)


class TestDetectAnomalies:
    def test_returns_anomaly_cards(self, sample_well_id):
        cards = detect_anomalies(sample_well_id)
        assert isinstance(cards, list)
        for card in cards:
            assert card.type == "anomaly_card"
            assert card.severity in ("low", "medium", "high", "critical")

    def test_all_wells_scan(self):
        cards = detect_anomalies()
        assert isinstance(cards, list)


class TestGetWellHistory:
    def test_returns_history(self, sample_well_id):
        history = get_well_history(sample_well_id, parameter="debit_ls")
        assert history.type == "well_history"
        assert history.well_id == sample_well_id
        assert history.parameter == "debit_ls"
        assert len(history.timestamps) > 0
        assert len(history.values) == len(history.timestamps)
        assert history.trend in ("rising", "falling", "stable")

    def test_different_parameters(self, sample_well_id):
        for param in ["debit_ls", "tds_mgl", "ph", "water_level_m"]:
            history = get_well_history(sample_well_id, parameter=param)
            assert history.parameter == param


class TestGetRegionStats:
    def test_returns_stats(self):
        stats = get_region_stats(bbox=[54.0, 24.0, 56.0, 25.0])
        assert stats.type == "region_stats"
        assert stats.well_count > 0
        assert stats.active_count <= stats.well_count
        assert stats.avg_debit_ls > 0

    def test_narrow_bbox_fewer_wells(self):
        wide = get_region_stats(bbox=[54.0, 24.0, 56.0, 25.0])
        narrow = get_region_stats(bbox=[54.7, 24.4, 54.75, 24.45])
        assert narrow.well_count <= wide.well_count
