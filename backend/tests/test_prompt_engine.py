"""Tests for Prompt Engine — multi-level prompt assembly."""

import os
from pathlib import Path

import pytest

DATA_DIR = str(Path(__file__).resolve().parent.parent.parent / "data")
os.environ["DATA_DIR"] = DATA_DIR

from models.schemas import MapContext
from services.context_bridge import build_context_prompt, load_wells_data
from services.prompt_engine import PromptEngine


@pytest.fixture
def engine():
    return PromptEngine()


@pytest.fixture
def sample_context():
    wells = load_wells_data()
    ctx = MapContext(
        center_lat=24.45,
        center_lng=54.65,
        zoom=12,
        bbox=[54.61, 24.42, 54.69, 24.48],
        active_layers=["wells", "depression_cone"],
        selected_well_id=next(iter(wells)),
    )
    return build_context_prompt(ctx, wells)


class TestPromptLevels:
    def test_base_role_always_present(self, engine, sample_context):
        prompt = engine.build("pool-a", "general_question", sample_context)
        assert "HydroWatch AI" in prompt
        assert "groundwater" in prompt.lower()

    def test_domain_knowledge_always_present(self, engine, sample_context):
        prompt = engine.build("pool-a", "general_question", sample_context)
        assert "Dammam" in prompt
        assert "Umm Er Radhuma" in prompt
        assert "TDS" in prompt
        assert "mg/L" in prompt

    def test_context_bridge_at_end(self, engine, sample_context):
        prompt = engine.build("pool-a", "general_question", sample_context)
        assert "Current Map State" in prompt
        # Context bridge should be the last major section
        last_section_idx = prompt.rfind("## Current Map State")
        assert last_section_idx > len(prompt) // 2


class TestModelAdaptors:
    def test_pool_a_vs_pool_b_different(self, engine, sample_context):
        prompt_a = engine.build("pool-a", "general_question", sample_context)
        prompt_b = engine.build("pool-b", "general_question", sample_context)
        # They should differ in the model adaptor section
        assert prompt_a != prompt_b

    def test_pool_a_concise_style(self, engine, sample_context):
        prompt = engine.build("pool-a", "general_question", sample_context)
        assert (
            "concise" in prompt.lower()
            or "under 150 words" in prompt.lower()
            or "simple" in prompt.lower()
        )

    def test_pool_b_analytical_style(self, engine, sample_context):
        prompt = engine.build("pool-b", "general_question", sample_context)
        assert "step by step" in prompt.lower() or "chain-of-thought" in prompt.lower()

    def test_pool_b_upgrade_comprehensive(self, engine, sample_context):
        prompt = engine.build("pool-b-upgrade", "general_question", sample_context)
        assert "comprehensive" in prompt.lower() or "full freedom" in prompt.lower()


class TestTaskInstructions:
    def test_validate_csv_instructions(self, engine, sample_context):
        prompt = engine.build("pool-a", "validate_csv", sample_context)
        assert "validation" in prompt.lower() or "data quality" in prompt.lower()

    def test_detect_anomalies_instructions(self, engine, sample_context):
        prompt = engine.build("pool-b", "detect_anomalies", sample_context)
        assert "anomaly" in prompt.lower()
        assert "seasonal" in prompt.lower()

    def test_different_tasks_different_prompts(self, engine, sample_context):
        prompt_csv = engine.build("pool-a", "validate_csv", sample_context)
        prompt_anomaly = engine.build("pool-a", "detect_anomalies", sample_context)
        assert prompt_csv != prompt_anomaly

    def test_unknown_task_falls_back_to_general(self, engine, sample_context):
        prompt = engine.build("pool-a", "unknown_task_xyz", sample_context)
        assert "General" in prompt or "available data" in prompt.lower()


class TestOutputFormats:
    def test_anomaly_card_format(self, engine, sample_context):
        prompt = engine.build(
            "pool-b", "detect_anomalies", sample_context, output_type="anomaly_card"
        )
        assert "anomaly_card" in prompt
        assert "severity" in prompt

    def test_validation_card_format(self, engine, sample_context):
        prompt = engine.build(
            "pool-a", "validate_csv", sample_context, output_type="validation_card"
        )
        assert "validation_result" in prompt
        assert "total_rows" in prompt

    def test_text_response_default(self, engine, sample_context):
        prompt = engine.build("pool-a", "general_question", sample_context)
        assert "markdown" in prompt.lower()


class TestWaterQualityNorms:
    def test_uae_standards_present(self, engine, sample_context):
        prompt = engine.build("pool-b", "detect_anomalies", sample_context)
        assert "1,000" in prompt or "1000" in prompt  # TDS drinking limit
        assert "250" in prompt  # Chloride limit
        assert "6.5" in prompt or "6.5-8.5" in prompt  # pH range

    def test_alert_thresholds_present(self, engine, sample_context):
        prompt = engine.build("pool-b", "detect_anomalies", sample_context)
        assert "5,000" in prompt or "5000" in prompt  # TDS alert
        assert "15%" in prompt  # debit decline threshold


class TestNewTaskTypes:
    def test_interference_analysis_task(self, engine, sample_context):
        prompt = engine.build("pool-b", "interference_analysis", sample_context)
        assert "analyze_interference" in prompt
        assert "donor" in prompt.lower() or "victim" in prompt.lower()

    def test_drawdown_analysis_task(self, engine, sample_context):
        prompt = engine.build("pool-b", "drawdown_analysis", sample_context)
        assert "compute_drawdown_grid" in prompt

    def test_water_quality_task(self, engine, sample_context):
        prompt = engine.build("pool-a", "water_quality_report", sample_context)
        assert "TDS" in prompt and "UAE" in prompt

    def test_cluster_comparison_task(self, engine, sample_context):
        prompt = engine.build("pool-a", "cluster_comparison", sample_context)
        assert "cluster" in prompt.lower()

    def test_trend_analysis_task(self, engine, sample_context):
        prompt = engine.build("pool-a", "trend_analysis", sample_context)
        assert "trend" in prompt.lower()

    def test_daily_report_task(self, engine, sample_context):
        prompt = engine.build("pool-b", "daily_report", sample_context)
        assert "report" in prompt.lower()


class TestInterferenceDomain:
    def test_interference_in_domain(self, engine, sample_context):
        prompt = engine.build("pool-b", "interference_analysis", sample_context)
        assert "Theis" in prompt
        assert "gradient" in prompt.lower()
