"""Tests for database ORM models (unit-level, no DB connection)."""

from models.database import Anomaly, Base, ChatMessage, LLMMetric, Observation, Well


class TestORMModels:
    """Verify ORM model structure without database."""

    def test_all_tables_registered(self):
        table_names = set(Base.metadata.tables.keys())
        expected = {
            "wells",
            "observations",
            "anomalies",
            "chat_messages",
            "eval_results",
            "llm_metrics",
        }
        assert expected == table_names

    def test_well_columns(self):
        cols = {c.name for c in Well.__table__.columns}
        required = {
            "id",
            "name",
            "cluster_id",
            "cluster_name",
            "geometry",
            "well_depth_m",
            "aquifer_type",
            "status",
            "current_yield_ls",
            "last_tds_mgl",
            "last_ph",
            "transmissivity_m2d",
            "storativity",
        }
        assert required.issubset(cols)

    def test_observation_columns(self):
        cols = {c.name for c in Observation.__table__.columns}
        required = {
            "id",
            "well_id",
            "timestamp",
            "debit_ls",
            "tds_mgl",
            "ph",
            "chloride_mgl",
            "water_level_m",
            "temperature_c",
        }
        assert required.issubset(cols)

    def test_anomaly_columns(self):
        cols = {c.name for c in Anomaly.__table__.columns}
        required = {
            "id",
            "well_id",
            "anomaly_type",
            "severity",
            "title",
            "value_current",
            "value_baseline",
            "change_pct",
        }
        assert required.issubset(cols)

    def test_well_has_spatial_index(self):
        indexes = {idx.name for idx in Well.__table__.indexes}
        assert "idx_wells_geometry" in indexes

    def test_observation_has_composite_index(self):
        indexes = {idx.name for idx in Observation.__table__.indexes}
        assert "idx_obs_well_time" in indexes

    def test_chat_message_columns(self):
        cols = {c.name for c in ChatMessage.__table__.columns}
        required = {
            "id",
            "conversation_id",
            "role",
            "content",
            "map_context",
            "model_used",
            "tokens_used",
            "latency_ms",
        }
        assert required.issubset(cols)

    def test_llm_metric_columns(self):
        cols = {c.name for c in LLMMetric.__table__.columns}
        required = {
            "id",
            "model",
            "task_type",
            "pool",
            "latency_ms",
            "tokens_in",
            "tokens_out",
            "cost_usd",
            "was_fallback",
        }
        assert required.issubset(cols)
