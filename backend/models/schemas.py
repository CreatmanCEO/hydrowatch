"""Pydantic models for HydroWatch API."""
from pydantic import BaseModel, Field, field_validator
from typing import Literal, Any
from datetime import datetime


# --- Map Context (from frontend) ---

class MapContext(BaseModel):
    """Current map state sent from frontend for context bridge."""
    center_lat: float = Field(ge=-90, le=90)
    center_lng: float = Field(ge=-180, le=180)
    zoom: float = Field(ge=0, le=22)
    bbox: list[float] = Field(min_length=4, max_length=4, description="[west, south, east, north]")
    active_layers: list[str] = Field(default_factory=lambda: ["wells"])
    selected_well_id: str | None = None
    filters: dict[str, Any] = Field(default_factory=dict)
    depression_cone_t_days: int = 30
    depression_cone_mode: Literal["selected", "all"] = "selected"
    interference_visible: bool = False

    @field_validator("bbox")
    @classmethod
    def validate_bbox(cls, v):
        if len(v) != 4:
            raise ValueError("bbox must have exactly 4 elements: [west, south, east, north]")
        return v


# --- Well Data ---

class WellInfo(BaseModel):
    """Well information for display."""
    id: str
    name: str
    cluster_id: str
    latitude: float
    longitude: float
    well_depth_m: float
    aquifer_type: str
    status: Literal["active", "inactive", "maintenance"]
    current_yield_ls: float
    last_tds_mgl: float
    last_ph: float
    last_water_level_m: float


# --- Structured Output Cards (LLM -> Frontend) ---

class AnomalyCard(BaseModel):
    """Anomaly detection result card for frontend rendering."""
    type: Literal["anomaly_card"] = "anomaly_card"
    severity: Literal["low", "medium", "high", "critical"]
    well_id: str
    anomaly_type: Literal["debit_decline", "depression_cone", "interference", "tds_spike", "sensor_fault"]
    title: str
    description: str
    value_current: float
    value_baseline: float
    change_pct: float
    recommendation: str


class ValidationResult(BaseModel):
    """CSV validation result card."""
    type: Literal["validation_result"] = "validation_result"
    valid: bool
    total_rows: int
    valid_rows: int
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    column_stats: dict[str, dict[str, float]] = Field(default_factory=dict)


class RegionStats(BaseModel):
    """Aggregated statistics for the current viewport region."""
    type: Literal["region_stats"] = "region_stats"
    well_count: int
    active_count: int
    avg_debit_ls: float
    avg_tds_mgl: float
    anomaly_count: int
    wells_in_bbox: list[str]


class WellHistory(BaseModel):
    """Time series data for a single well."""
    type: Literal["well_history"] = "well_history"
    well_id: str
    parameter: str
    timestamps: list[str]
    values: list[float]
    trend: str  # "rising", "falling", "stable"
    anomalies_detected: list[dict[str, Any]] = Field(default_factory=list)


# --- Chat API ---

class ChatRequest(BaseModel):
    """Chat request from frontend."""
    message: str = Field(min_length=1, max_length=2000)
    map_context: MapContext
    conversation_id: str | None = None


class ToolCall(BaseModel):
    """A tool call made by LLM."""
    name: str
    arguments: dict[str, Any]


class ToolResult(BaseModel):
    """Result of a tool execution."""
    tool_name: str
    success: bool
    result: dict[str, Any] | list[Any]
    error: str | None = None


# --- Interference (Theis-based) ---

class InterferencePair(BaseModel):
    """Hydraulic interference between two wells (Theis-based)."""
    well_a: str
    well_b: str
    distance_km: float
    coef_at_a: float = Field(ge=0, le=1, description="Fraction of drawdown at A caused by B")
    coef_at_b: float = Field(ge=0, le=1, description="Fraction of drawdown at B caused by A")
    drawdown_midpoint_m: float = Field(ge=0)
    severity: Literal["low", "medium", "high", "critical"]
    dominant_well: str
    recommendation: str


class InterferenceResult(BaseModel):
    """Tool output: list of significant interference pairs."""
    type: Literal["interference_result"] = "interference_result"
    pairs: list[InterferencePair]
    t_days: int
    wells_analyzed: int
    pairs_significant: int


class InterferenceCard(BaseModel):
    """Frontend-rendered card summarizing interference analysis."""
    type: Literal["interference_card"] = "interference_card"
    pairs_summary: dict[str, int]
    top_concerns: list[dict[str, Any]]
    regional_pattern: str = ""


# --- Drawdown (Theis cone) ---

class DrawdownIsoline(BaseModel):
    """One contour level of the depression cone."""
    level_m: float = Field(gt=0)
    polygon: dict[str, Any]  # GeoJSON MultiPolygon


class DrawdownGrid(BaseModel):
    """Tool output: Theis drawdown grid as isoline polygons."""
    type: Literal["drawdown_grid"] = "drawdown_grid"
    well_id: str
    center: list[float] = Field(min_length=2, max_length=2)  # [lng, lat]
    t_days: int
    isolines: list[DrawdownIsoline]
    max_drawdown_m: float = Field(ge=0)
    interfering_wells: list[str] = Field(default_factory=list)


class DrawdownCard(BaseModel):
    """Frontend-rendered card summarizing depression cone analysis."""
    type: Literal["drawdown_card"] = "drawdown_card"
    well_id: str
    t_days: int
    max_drawdown_m: float
    cone_radius_1m_km: float
    interfering_wells: list[str]
    assessment: str
    recommendation: str


class ChatResponse(BaseModel):
    """Full chat response (non-streaming)."""
    message: str
    cards: list[
        AnomalyCard | ValidationResult | RegionStats | WellHistory
        | InterferenceCard | DrawdownCard
    ] = Field(default_factory=list)
    tool_calls: list[ToolCall] = Field(default_factory=list)
    model_used: str = ""
    latency_ms: int = 0
    tokens_used: int = 0
