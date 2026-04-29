"""Tests for tool registry and safe executor."""

import os
from pathlib import Path

import pytest

DATA_DIR = str(Path(__file__).resolve().parent.parent.parent / "data")
os.environ["DATA_DIR"] = DATA_DIR

from models.tool_schemas import TOOL_DEFINITIONS
from services.tool_executor import ToolExecutor


class TestToolDefinitions:
    def test_all_tools_defined(self):
        names = {t["function"]["name"] for t in TOOL_DEFINITIONS}
        expected = {
            "validate_csv",
            "query_wells",
            "detect_anomalies",
            "get_well_history",
            "get_region_stats",
            "analyze_interference",
            "compute_drawdown_grid",
        }
        assert expected == names

    def test_new_tools_present(self):
        names = {t["function"]["name"] for t in TOOL_DEFINITIONS}
        assert "analyze_interference" in names
        assert "compute_drawdown_grid" in names

    def test_valid_json_schema_structure(self):
        for tool in TOOL_DEFINITIONS:
            assert tool["type"] == "function"
            fn = tool["function"]
            assert "name" in fn
            assert "description" in fn
            assert "parameters" in fn
            assert fn["parameters"]["type"] == "object"
            assert "properties" in fn["parameters"]

    def test_required_fields_present(self):
        for tool in TOOL_DEFINITIONS:
            fn = tool["function"]
            if "required" in fn["parameters"]:
                required = fn["parameters"]["required"]
                props = fn["parameters"]["properties"]
                for r in required:
                    assert r in props, f"{fn['name']}: required field '{r}' not in properties"


class TestToolExecutor:
    @pytest.fixture
    def executor(self):
        return ToolExecutor()

    def test_execute_query_wells(self, executor):
        result = executor.execute("query_wells", {})
        assert result.success
        assert isinstance(result.result, (dict, list))

    def test_execute_query_wells_with_bbox(self, executor):
        result = executor.execute("query_wells", {"bbox": [54.0, 24.0, 56.0, 25.0]})
        assert result.success

    def test_execute_get_region_stats(self, executor):
        result = executor.execute("get_region_stats", {"bbox": [54.0, 24.0, 56.0, 25.0]})
        assert result.success
        assert "well_count" in result.result

    def test_execute_detect_anomalies(self, executor):
        result = executor.execute("detect_anomalies", {})
        assert result.success

    def test_execute_unknown_tool_fails(self, executor):
        result = executor.execute("nonexistent_tool", {})
        assert not result.success
        assert result.error is not None

    def test_execute_catches_exceptions(self, executor):
        result = executor.execute("get_well_history", {"well_id": "NONEXISTENT-WELL-999"})
        assert not result.success
        assert result.error is not None

    def test_get_tool_definitions(self, executor):
        defs = executor.get_tool_definitions()
        assert len(defs) == 7
        assert all(d["type"] == "function" for d in defs)

    def test_execute_analyze_interference(self, executor):
        result = executor.execute("analyze_interference", {"bbox": [54.0, 24.0, 56.0, 25.0]})
        assert result.success
        assert result.result["type"] == "interference_result"

    def test_execute_compute_drawdown_grid(self, executor):
        result = executor.execute("compute_drawdown_grid", {"well_id": "AUH-01-001"})
        assert result.success
        assert result.result["type"] == "drawdown_grid"
