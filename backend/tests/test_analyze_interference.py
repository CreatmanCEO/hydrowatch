"""Tests for analyze_interference tool."""

import os
from pathlib import Path

DATA_DIR = str(Path(__file__).resolve().parent.parent.parent / "data")
os.environ["DATA_DIR"] = DATA_DIR

from tools.analyze_interference import _wgs84_distance_m, analyze_interference


class TestDistance:
    def test_distance_zero(self):
        assert _wgs84_distance_m(24.5, 54.7, 24.5, 54.7) < 1.0

    def test_known_distance(self):
        # 0.001 deg lat ≈ 111m
        d = _wgs84_distance_m(24.5, 54.7, 24.501, 54.7)
        assert 100 < d < 120


class TestAnalyzeInterference:
    def test_returns_result(self):
        result = analyze_interference(bbox=[54.0, 24.0, 56.0, 25.0])
        assert result.type == "interference_result"
        assert result.t_days == 30
        assert result.wells_analyzed > 0

    def test_filters_by_min_coefficient(self):
        all_result = analyze_interference(bbox=[54.0, 24.0, 56.0, 25.0], min_coefficient=0.0)
        filtered = analyze_interference(bbox=[54.0, 24.0, 56.0, 25.0], min_coefficient=0.5)
        assert len(filtered.pairs) <= len(all_result.pairs)

    def test_pair_coefficients_in_range(self):
        result = analyze_interference(bbox=[54.0, 24.0, 56.0, 25.0])
        for p in result.pairs:
            assert 0 <= p.coef_at_a <= 1
            assert 0 <= p.coef_at_b <= 1
            assert p.drawdown_midpoint_m >= 0

    def test_severity_assignment(self):
        result = analyze_interference(bbox=[54.0, 24.0, 56.0, 25.0])
        valid = {"low", "medium", "high", "critical"}
        for p in result.pairs:
            assert p.severity in valid

    def test_dominant_well_logic(self):
        result = analyze_interference(bbox=[54.0, 24.0, 56.0, 25.0])
        for p in result.pairs:
            assert p.dominant_well in (p.well_a, p.well_b)

    def test_t_days_param(self):
        r30 = analyze_interference(bbox=[54.0, 24.0, 56.0, 25.0], t_days=30)
        r90 = analyze_interference(bbox=[54.0, 24.0, 56.0, 25.0], t_days=90)
        assert r30.t_days == 30
        assert r90.t_days == 90
