"""Tests for Pydantic schemas."""
import pytest
from models.schemas import (
    MapContext, WellInfo, AnomalyCard, ValidationResult,
    ChatRequest, ChatResponse, ToolCall, ToolResult,
    RegionStats, WellHistory,
    InterferencePair, InterferenceResult, InterferenceCard,
    DrawdownIsoline, DrawdownGrid, DrawdownCard,
)


class TestMapContext:
    def test_valid_context(self):
        ctx = MapContext(
            center_lat=24.45, center_lng=54.65, zoom=12,
            bbox=[54.61, 24.42, 54.69, 24.48],
            active_layers=["wells", "depression_cone"],
            selected_well_id="AUH-01-003",
            filters={"status": ["active"]},
        )
        assert ctx.zoom == 12
        assert len(ctx.bbox) == 4

    def test_bbox_validation(self):
        with pytest.raises(ValueError):
            MapContext(center_lat=24.45, center_lng=54.65, zoom=12,
                       bbox=[1, 2, 3],  # must be 4 elements
                       active_layers=["wells"])

    def test_defaults(self):
        ctx = MapContext(
            center_lat=24.45, center_lng=54.65, zoom=10,
            bbox=[54.0, 24.0, 55.0, 25.0],
        )
        assert ctx.active_layers == ["wells"]
        assert ctx.selected_well_id is None
        assert ctx.filters == {}


class TestAnomalyCard:
    def test_anomaly_card_structure(self):
        card = AnomalyCard(
            severity="high",
            well_id="AUH-02-003",
            anomaly_type="debit_decline",
            title="Debit decline detected",
            description="Flow rate dropped 35% over 3 months",
            value_current=8.2,
            value_baseline=12.6,
            change_pct=-34.9,
            recommendation="Schedule well maintenance inspection",
        )
        assert card.severity in ("low", "medium", "high", "critical")
        assert card.type == "anomaly_card"

    def test_invalid_severity_rejected(self):
        with pytest.raises(ValueError):
            AnomalyCard(
                severity="unknown",
                well_id="X", anomaly_type="debit_decline",
                title="t", description="d",
                value_current=1, value_baseline=2,
                change_pct=-50, recommendation="r",
            )


class TestValidationResult:
    def test_valid_result(self):
        result = ValidationResult(
            valid=False,
            total_rows=500,
            valid_rows=487,
            errors=["Row 45: negative flow rate"],
            warnings=["12 rows with missing depth"],
            column_stats={"debit_ls": {"min": -2.1, "max": 25.3, "mean": 12.1}},
        )
        assert not result.valid
        assert len(result.errors) == 1
        assert result.type == "validation_result"


class TestWellInfo:
    def test_well_info(self):
        w = WellInfo(
            id="AUH-01-001", name="Al Wathba Well 1",
            cluster_id="AL_WATHBA", latitude=24.42, longitude=54.72,
            well_depth_m=150.0, aquifer_type="Dammam Limestone",
            status="active", current_yield_ls=12.5,
            last_tds_mgl=4500.0, last_ph=7.8, last_water_level_m=45.0,
        )
        assert w.status == "active"


class TestRegionStats:
    def test_region_stats(self):
        rs = RegionStats(
            well_count=10, active_count=8,
            avg_debit_ls=11.2, avg_tds_mgl=4200.0,
            anomaly_count=2, wells_in_bbox=["AUH-01-001", "AUH-01-002"],
        )
        assert rs.type == "region_stats"
        assert rs.well_count == 10


class TestChatModels:
    def test_chat_request(self):
        req = ChatRequest(
            message="Show anomalies in viewport",
            map_context=MapContext(
                center_lat=24.45, center_lng=54.65, zoom=12,
                bbox=[54.61, 24.42, 54.69, 24.48],
            ),
        )
        assert len(req.message) > 0

    def test_chat_request_empty_message_rejected(self):
        with pytest.raises(ValueError):
            ChatRequest(
                message="",
                map_context=MapContext(
                    center_lat=24.45, center_lng=54.65, zoom=12,
                    bbox=[54.0, 24.0, 55.0, 25.0],
                ),
            )

    def test_tool_call(self):
        tc = ToolCall(name="detect_anomalies", arguments={"well_id": "AUH-01-001"})
        assert tc.name == "detect_anomalies"

    def test_tool_result(self):
        tr = ToolResult(tool_name="query_wells", success=True, result={"count": 5})
        assert tr.success

    def test_chat_response(self):
        resp = ChatResponse(message="Found 2 anomalies", model_used="gemini-2.5-flash")
        assert resp.cards == []
        assert resp.tool_calls == []


class TestInterferencePair:
    def test_valid_pair(self):
        p = InterferencePair(
            well_a="AUH-01-001", well_b="AUH-01-002",
            distance_km=0.22,
            coef_at_a=0.61, coef_at_b=0.18,
            drawdown_midpoint_m=4.2,
            severity="critical",
            dominant_well="AUH-01-002",
            recommendation="Reduce pumping at AUH-01-002.",
        )
        assert p.severity == "critical"

    def test_invalid_severity_rejected(self):
        with pytest.raises(ValueError):
            InterferencePair(
                well_a="A", well_b="B", distance_km=1,
                coef_at_a=0.1, coef_at_b=0.1,
                drawdown_midpoint_m=1, severity="invalid",
                dominant_well="A", recommendation="x",
            )


class TestInterferenceResult:
    def test_full_result(self):
        r = InterferenceResult(
            pairs=[],
            t_days=30,
            wells_analyzed=25,
            pairs_significant=0,
        )
        assert r.type == "interference_result"


class TestInterferenceCard:
    def test_summary_card(self):
        c = InterferenceCard(
            pairs_summary={"critical": 2, "high": 4, "medium": 6, "low": 0},
            top_concerns=[
                {"well_a": "A", "well_b": "B", "coef_max": 0.61, "action": "Reduce pumping at B"}
            ],
            regional_pattern="Mussafah cluster shows correlated drawdown",
        )
        assert c.type == "interference_card"


class TestDrawdownIsoline:
    def test_isoline(self):
        iso = DrawdownIsoline(
            level_m=1.0,
            polygon={"type": "MultiPolygon", "coordinates": []},
        )
        assert iso.level_m == 1.0


class TestDrawdownGrid:
    def test_grid(self):
        g = DrawdownGrid(
            well_id="AUH-01-001",
            center=[54.7, 24.4],
            t_days=30,
            isolines=[],
            max_drawdown_m=6.8,
            interfering_wells=["AUH-01-002"],
        )
        assert g.type == "drawdown_grid"


class TestDrawdownCard:
    def test_card(self):
        c = DrawdownCard(
            well_id="AUH-01-001",
            t_days=30,
            max_drawdown_m=6.8,
            cone_radius_1m_km=2.3,
            interfering_wells=["AUH-01-002"],
            assessment="Cone radius >2km indicates excessive pumping.",
            recommendation="Consider reducing pumping rate by 20%.",
        )
        assert c.type == "drawdown_card"
