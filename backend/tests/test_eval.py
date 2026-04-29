"""Tests for eval pipeline — metrics, dataset, schema validation."""

import os
from pathlib import Path

DATA_DIR = str(Path(__file__).resolve().parent.parent.parent / "data")
os.environ["DATA_DIR"] = DATA_DIR
os.environ.setdefault("GEMINI_API_KEY", "test-key")
os.environ.setdefault("CEREBRAS_API_KEY", "test-key")
os.environ.setdefault("ANTHROPIC_API_KEY", "test-key")

from eval.batch_runner import estimate_cost, load_eval_dataset
from eval.metrics import (
    EvalResult,
    aggregate_metrics,
    check_fields_present,
    check_tool_call_accuracy,
    validate_schema_compliance,
)


class TestEvalDataset:
    def test_dataset_loads(self):
        cases = load_eval_dataset()
        assert len(cases) >= 40

    def test_all_cases_have_required_fields(self):
        cases = load_eval_dataset()
        for case in cases:
            assert "id" in case
            assert "category" in case
            assert "input" in case
            assert "difficulty" in case

    def test_categories_covered(self):
        cases = load_eval_dataset()
        categories = {c["category"] for c in cases}
        expected = {
            "csv_validation",
            "anomaly_detection",
            "well_query",
            "region_analysis",
            "edge_case",
        }
        assert expected == categories

    def test_difficulty_levels(self):
        cases = load_eval_dataset()
        difficulties = {c["difficulty"] for c in cases}
        assert "simple" in difficulties
        assert "medium" in difficulties
        assert "complex" in difficulties


class TestSchemaValidation:
    def test_valid_anomaly_card(self):
        output = {
            "type": "anomaly_card",
            "severity": "high",
            "well_id": "AUH-01-003",
            "anomaly_type": "debit_decline",
            "title": "Debit decline",
            "description": "Flow rate dropped",
            "value_current": 8.2,
            "value_baseline": 12.6,
            "change_pct": -34.9,
            "recommendation": "Inspect pump",
        }
        assert validate_schema_compliance(output)

    def test_invalid_anomaly_card(self):
        output = {"type": "anomaly_card", "severity": "unknown_level"}
        assert not validate_schema_compliance(output)

    def test_valid_validation_result(self):
        output = {
            "type": "validation_result",
            "valid": True,
            "total_rows": 100,
            "valid_rows": 100,
        }
        assert validate_schema_compliance(output)

    def test_unknown_type(self):
        output = {"type": "unknown_type", "data": "test"}
        assert not validate_schema_compliance(output)

    def test_no_type_field(self):
        output = {"data": "test"}
        assert not validate_schema_compliance(output)


class TestToolCallAccuracy:
    def test_correct_tool(self):
        assert check_tool_call_accuracy(
            "detect_anomalies", [{"name": "detect_anomalies", "arguments": "{}"}]
        )

    def test_wrong_tool(self):
        assert not check_tool_call_accuracy(
            "detect_anomalies", [{"name": "query_wells", "arguments": "{}"}]
        )

    def test_no_tool_expected_none_called(self):
        assert check_tool_call_accuracy(None, [])

    def test_no_tool_expected_but_called(self):
        assert not check_tool_call_accuracy(None, [{"name": "query_wells", "arguments": "{}"}])

    def test_expected_tool_none_called(self):
        assert not check_tool_call_accuracy("detect_anomalies", [])


class TestFieldsPresent:
    def test_fields_in_dict(self):
        assert check_fields_present(
            ["severity", "well_id"],
            {"severity": "high", "well_id": "AUH-01-003", "extra": "data"},
        )

    def test_missing_field(self):
        assert not check_fields_present(["severity", "missing_field"], {"severity": "high"})

    def test_empty_expected(self):
        assert check_fields_present([], {"any": "data"})

    def test_list_output(self):
        assert check_fields_present(
            ["severity"], [{"severity": "high", "well_id": "X"}, {"severity": "low"}]
        )


class TestAggregateMetrics:
    def test_aggregate(self):
        results = [
            EvalResult(
                "c1",
                "model-a",
                "input1",
                "detect_anomalies",
                [{"name": "detect_anomalies"}],
                {},
                True,
                True,
                True,
                150,
                100,
                50,
                0.001,
            ),
            EvalResult(
                "c2",
                "model-a",
                "input2",
                "query_wells",
                [{"name": "query_wells"}],
                {},
                True,
                False,
                True,
                200,
                120,
                60,
                0.002,
            ),
            EvalResult(
                "c3",
                "model-b",
                "input3",
                "detect_anomalies",
                [{"name": "detect_anomalies"}],
                {},
                True,
                True,
                True,
                300,
                200,
                100,
                0.01,
            ),
        ]
        metrics = aggregate_metrics(results)

        assert "model-a" in metrics
        assert "model-b" in metrics
        assert metrics["model-a"].total_cases == 2
        assert metrics["model-a"].accuracy == 1.0
        assert metrics["model-a"].schema_compliance == 0.5
        assert metrics["model-b"].total_cases == 1


class TestCostEstimation:
    def test_gemini_flash_cost(self):
        cost = estimate_cost("gemini/gemini-2.5-flash", 1000, 500)
        assert cost > 0
        assert cost < 0.01  # should be very cheap

    def test_sonnet_more_expensive(self):
        flash_cost = estimate_cost("gemini/gemini-2.5-flash", 1000, 500)
        sonnet_cost = estimate_cost("anthropic/claude-sonnet-4.5", 1000, 500)
        assert sonnet_cost > flash_cost
