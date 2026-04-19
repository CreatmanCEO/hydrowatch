"""SQLAlchemy ORM models with PostGIS geometry."""
from datetime import datetime
from sqlalchemy import (
    String, Float, Integer, DateTime, Boolean, Text,
    ForeignKey, Index, func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from geoalchemy2 import Geometry


class Base(DeclarativeBase):
    pass


class Well(Base):
    """Monitoring well with PostGIS geometry."""
    __tablename__ = "wells"

    id: Mapped[str] = mapped_column(String(20), primary_key=True)  # e.g. "AUH-01-003"
    name: Mapped[str] = mapped_column(String(100))
    cluster_id: Mapped[str] = mapped_column(String(20), index=True)
    cluster_name: Mapped[str] = mapped_column(String(100))

    # PostGIS geometry (Point, SRID 4326 = WGS84)
    geometry: Mapped[str] = mapped_column(Geometry("POINT", srid=4326))

    # Well construction
    well_depth_m: Mapped[float] = mapped_column(Float)
    aquifer_type: Mapped[str] = mapped_column(String(50))
    casing_diameter_mm: Mapped[int] = mapped_column(Integer)
    ground_elevation_m: Mapped[float] = mapped_column(Float)

    # Hydraulic parameters
    transmissivity_m2d: Mapped[float] = mapped_column(Float)
    storativity: Mapped[float] = mapped_column(Float)

    # Current state
    status: Mapped[str] = mapped_column(String(20), index=True)
    current_yield_ls: Mapped[float] = mapped_column(Float)
    static_water_level_m: Mapped[float] = mapped_column(Float)

    # Latest quality (denormalized for quick access)
    last_tds_mgl: Mapped[float] = mapped_column(Float)
    last_ph: Mapped[float] = mapped_column(Float)
    last_chloride_mgl: Mapped[float] = mapped_column(Float)
    last_temperature_c: Mapped[float] = mapped_column(Float)

    # Metadata
    operator: Mapped[str] = mapped_column(String(50))
    installation_date: Mapped[str] = mapped_column(String(10))
    properties: Mapped[dict] = mapped_column(JSONB, default=dict)

    # Relationships
    observations: Mapped[list["Observation"]] = relationship(back_populates="well")
    anomalies: Mapped[list["Anomaly"]] = relationship(back_populates="well")

    # Spatial index
    __table_args__ = (
        Index("idx_wells_geometry", "geometry", postgresql_using="gist"),
    )


class Observation(Base):
    """Time series observation for a well."""
    __tablename__ = "observations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    well_id: Mapped[str] = mapped_column(ForeignKey("wells.id"), index=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, index=True)

    debit_ls: Mapped[float] = mapped_column(Float)
    tds_mgl: Mapped[float] = mapped_column(Float)
    ph: Mapped[float] = mapped_column(Float)
    chloride_mgl: Mapped[float] = mapped_column(Float)
    water_level_m: Mapped[float] = mapped_column(Float)
    temperature_c: Mapped[float] = mapped_column(Float)

    well: Mapped["Well"] = relationship(back_populates="observations")

    __table_args__ = (
        Index("idx_obs_well_time", "well_id", "timestamp"),
    )


class Anomaly(Base):
    """Detected anomaly record."""
    __tablename__ = "anomalies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    well_id: Mapped[str] = mapped_column(ForeignKey("wells.id"), index=True)
    detected_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())

    anomaly_type: Mapped[str] = mapped_column(String(30))
    severity: Mapped[str] = mapped_column(String(10))
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text)
    value_current: Mapped[float] = mapped_column(Float)
    value_baseline: Mapped[float] = mapped_column(Float)
    change_pct: Mapped[float] = mapped_column(Float)
    recommendation: Mapped[str] = mapped_column(Text)
    metadata_json: Mapped[dict] = mapped_column(JSONB, default=dict)

    well: Mapped["Well"] = relationship(back_populates="anomalies")


class ChatMessage(Base):
    """Chat history."""
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[str] = mapped_column(String(36), index=True)
    role: Mapped[str] = mapped_column(String(10))
    content: Mapped[str] = mapped_column(Text)
    map_context: Mapped[dict] = mapped_column(JSONB, default=dict)
    tool_calls: Mapped[dict] = mapped_column(JSONB, default=dict)
    model_used: Mapped[str] = mapped_column(String(50), default="")
    tokens_used: Mapped[int] = mapped_column(Integer, default=0)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class EvalResult(Base):
    """Batch evaluation results."""
    __tablename__ = "eval_results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(String(36), index=True)
    model: Mapped[str] = mapped_column(String(50))
    test_case_id: Mapped[str] = mapped_column(String(50))
    input_text: Mapped[str] = mapped_column(Text)
    expected_output: Mapped[str] = mapped_column(Text, default="")
    actual_output: Mapped[str] = mapped_column(Text)
    accuracy_score: Mapped[float] = mapped_column(Float, default=0.0)
    schema_valid: Mapped[bool] = mapped_column(Boolean, default=False)
    latency_ms: Mapped[int] = mapped_column(Integer, default=0)
    tokens_in: Mapped[int] = mapped_column(Integer, default=0)
    tokens_out: Mapped[int] = mapped_column(Integer, default=0)
    cost_usd: Mapped[float] = mapped_column(Float, default=0.0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())


class LLMMetric(Base):
    """Per-request LLM metrics for observability."""
    __tablename__ = "llm_metrics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=func.now(), index=True)
    model: Mapped[str] = mapped_column(String(50), index=True)
    task_type: Mapped[str] = mapped_column(String(30))
    pool: Mapped[str] = mapped_column(String(10))
    latency_ms: Mapped[int] = mapped_column(Integer)
    tokens_in: Mapped[int] = mapped_column(Integer)
    tokens_out: Mapped[int] = mapped_column(Integer)
    cost_usd: Mapped[float] = mapped_column(Float)
    schema_valid: Mapped[bool] = mapped_column(Boolean)
    was_fallback: Mapped[bool] = mapped_column(Boolean, default=False)
