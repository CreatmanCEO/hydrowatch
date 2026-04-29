"""Tests for compute_drawdown_grid tool."""
import os
from pathlib import Path

DATA_DIR = str(Path(__file__).resolve().parent.parent.parent / "data")
os.environ["DATA_DIR"] = DATA_DIR

from tools.compute_drawdown_grid import compute_drawdown_grid


class TestComputeDrawdownGrid:
    def test_returns_grid(self):
        g = compute_drawdown_grid(well_id="AUH-01-001")
        assert g.type == "drawdown_grid"
        assert g.well_id == "AUH-01-001"
        assert g.t_days == 30

    def test_isolines_present(self):
        g = compute_drawdown_grid(well_id="AUH-01-001")
        levels = {iso.level_m for iso in g.isolines}
        assert len(levels) >= 1
        for iso in g.isolines:
            assert iso.polygon["type"] in ("MultiPolygon", "Polygon")

    def test_max_drawdown_positive(self):
        g = compute_drawdown_grid(well_id="AUH-01-001")
        assert g.max_drawdown_m > 0

    def test_t_days_increases_drawdown(self):
        g30 = compute_drawdown_grid(well_id="AUH-01-001", t_days=30)
        g90 = compute_drawdown_grid(well_id="AUH-01-001", t_days=90)
        assert g90.max_drawdown_m >= g30.max_drawdown_m

    def test_unknown_well_raises(self):
        import pytest
        with pytest.raises((FileNotFoundError, ValueError, KeyError)):
            compute_drawdown_grid(well_id="NONEXISTENT-999")

    def test_interfering_wells_listed(self):
        g = compute_drawdown_grid(well_id="AUH-01-001", extent_km=10)
        assert isinstance(g.interfering_wells, list)
