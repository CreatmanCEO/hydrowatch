"""Tests for context bridge — MapContext to LLM system prompt."""
import json
import os
from pathlib import Path

import pytest

DATA_DIR = str(Path(__file__).resolve().parent.parent.parent / "data")
os.environ["DATA_DIR"] = DATA_DIR

from models.schemas import MapContext
from services.context_bridge import build_context_prompt, load_wells_data


class TestLoadWellsData:

    def test_loads_wells_dict(self):
        wells = load_wells_data()
        assert isinstance(wells, dict)
        assert len(wells) > 0
        first_key = next(iter(wells))
        assert "name_en" in wells[first_key]

    def test_keyed_by_well_id(self):
        wells = load_wells_data()
        for wid, data in wells.items():
            assert wid.startswith("AUH-")
            assert "well_depth_m" in data


class TestBuildContextPrompt:

    @pytest.fixture
    def wells_data(self):
        return load_wells_data()

    @pytest.fixture
    def sample_well_id(self, wells_data):
        return next(iter(wells_data))

    def test_basic_prompt(self, wells_data):
        ctx = MapContext(
            center_lat=24.45, center_lng=54.65, zoom=12,
            bbox=[54.61, 24.42, 54.69, 24.48],
            active_layers=["wells"],
        )
        prompt = build_context_prompt(ctx, wells_data)
        assert "Map State" in prompt
        assert "24.45" in prompt
        assert "54.65" in prompt
        assert "zoom" in prompt.lower() or "12" in prompt

    def test_prompt_includes_layers(self, wells_data):
        ctx = MapContext(
            center_lat=24.45, center_lng=54.65, zoom=12,
            bbox=[54.61, 24.42, 54.69, 24.48],
            active_layers=["wells", "depression_cone"],
        )
        prompt = build_context_prompt(ctx, wells_data)
        assert "wells" in prompt
        assert "depression_cone" in prompt

    def test_prompt_with_selected_well(self, wells_data, sample_well_id):
        ctx = MapContext(
            center_lat=24.45, center_lng=54.65, zoom=14,
            bbox=[54.61, 24.42, 54.69, 24.48],
            active_layers=["wells"],
            selected_well_id=sample_well_id,
        )
        prompt = build_context_prompt(ctx, wells_data)
        assert "Selected Well" in prompt
        assert sample_well_id in prompt

    def test_prompt_without_selected_well(self, wells_data):
        ctx = MapContext(
            center_lat=24.45, center_lng=54.65, zoom=10,
            bbox=[54.0, 24.0, 55.0, 25.0],
        )
        prompt = build_context_prompt(ctx, wells_data)
        assert "Selected Well" not in prompt

    def test_prompt_with_unknown_well_id(self, wells_data):
        ctx = MapContext(
            center_lat=24.45, center_lng=54.65, zoom=10,
            bbox=[54.0, 24.0, 55.0, 25.0],
            selected_well_id="NONEXISTENT-999",
        )
        prompt = build_context_prompt(ctx, wells_data)
        assert "Selected Well" not in prompt

    def test_prompt_includes_visible_wells_count(self, wells_data):
        ctx = MapContext(
            center_lat=24.45, center_lng=54.65, zoom=10,
            bbox=[54.0, 24.0, 56.0, 25.0],
        )
        prompt = build_context_prompt(ctx, wells_data)
        assert "visible" in prompt.lower() or "wells in view" in prompt.lower()


class TestExtendedMapContext:
    @pytest.fixture
    def wells_data(self):
        return load_wells_data()

    def test_cone_state_in_prompt(self, wells_data):
        ctx = MapContext(
            center_lat=24.45, center_lng=54.65, zoom=14,
            bbox=[54.6, 24.4, 54.7, 24.5],
            active_layers=["wells", "depression_cone"],
            selected_well_id=next(iter(wells_data)),
            depression_cone_t_days=90,
            depression_cone_mode="selected",
            interference_visible=True,
        )
        prompt = build_context_prompt(ctx, wells_data)
        assert "depression_cone" in prompt.lower() or "cone" in prompt.lower()
        assert "90" in prompt
        assert "interference" in prompt.lower()
