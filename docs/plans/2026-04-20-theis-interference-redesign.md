# Theis-Based Interference & Depression Cone Redesign — Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace decorative InterferenceLayer (geometric lines) and DepressionConeLayer (cosmetic concentric rings) with real Theis-based hydrogeological analysis, exposed both visually on map AND through 2 new MCP tools the AI can call. Add 5 missing task types for CommandBar correctness and polish Run Eval status feedback.

**Architecture:** Single source of truth — Theis math lives only on backend in `hydro_models.py`. Two new MCP tools (`analyze_interference`, `compute_drawdown_grid`) wrap the math; both AI and frontend map render from same endpoints. Frontend never recomputes hydrogeology client-side. Gradient lines encode donor/victim per Theis coefficient. Isoline polygons (computed via scipy contour extraction) replace cosmetic rings.

**Tech Stack:** Backend: existing Python 3.12 + FastAPI + Pydantic v2 + scipy.special.exp1 + scipy contour generation. Frontend: existing Next.js 15 + react-map-gl/maplibre + Recharts. New: scikit-image for marching-squares contours (or scipy.ndimage). No new infra.

**Design doc:** `docs/plans/2026-04-20-theis-interference-redesign-design.md`

---

## CONTEXT FOR THE IMPLEMENTING ENGINEER

### What is this project?

HydroWatch — AI-powered groundwater monitoring system for Abu Dhabi aquifer. 25 synthetic wells in 4 clusters, MapLibre map, FastAPI backend, LiteLLM router (Anthropic Haiku via OpenRouter), MCP-style tool calling, SSE streaming chat.

### What's broken

Current `InterferenceLayer` draws lines between any pair <5km apart. No physics. Current `DepressionConeLayer` uses formula `0.3 + yield/30 * 1.5` km — pure cosmetic. The real Theis equation in `backend/data_generator/hydro_models.py` is unused for visualization. AI doesn't know either feature exists — no tools, no domain instructions.

### Key files

```
backend/
  data_generator/hydro_models.py     # Existing: theis_drawdown, superposition_drawdown
  models/schemas.py                  # Pydantic models — extend
  models/tool_schemas.py             # TOOL_DEFINITIONS for LLM — extend
  tools/                             # Add 2 new tools
  services/
    tool_executor.py                 # Register new tools
    llm_router.py                    # TASK_ROUTING — extend
    prompt_engine.py                 # No change
    context_bridge.py                # Extend with cone state
  prompts/
    domain_knowledge.py              # Add Theis interference section
    task_instructions.py             # Add 6 new task types
    output_formats.py                # Add interference_card, drawdown_card formats
  main.py                            # _classify_task — extend keywords
  eval/
    metrics_api.py                   # Add /run/status endpoint
    batch_runner.py                  # Write status JSON during run
  tests/                             # Add tests per new tool/schema

frontend/src/
  types/index.ts                     # Mirror new TS types
  stores/mapStore.ts                 # Add cone mode + time days state
  components/Map/
    InterferenceLayer.tsx            # Rewrite (gradient + popup)
    InterferencePopup.tsx            # New
    DepressionConeLayer.tsx          # Rewrite (isolines)
    TimeSlider.tsx                   # New
    DrawdownLegend.tsx               # New
    LayerControls.tsx                # Update
    WellsMap.tsx                     # Wire new components
  components/Chat/
    CommandBar.tsx                   # Rebind commands to new task types
    InterferenceCard.tsx             # New
    DrawdownCard.tsx                 # New
    MessageBubble.tsx                # Switch on new card types
  components/Metrics/
    MetricsPanel.tsx                 # Add progress polling

frontend/e2e/                        # Update for new layers
```

### Conventions

- TDD: write failing test → implement → green → commit. No exceptions.
- Pydantic v2 syntax (`model_config = {...}`, not nested `Config` class).
- All Pydantic schema imports go in `models/schemas.py` (do NOT scatter).
- Run tests with `cd backend && .venv/Scripts/python -m pytest tests/ -v` (Windows path).
- Frontend tests: `cd frontend && npx tsc --noEmit` for typecheck, `npx playwright test` for e2e.
- Commits: conventional format (feat:, fix:, test:, refactor:). End every commit with `Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>`.
- Frontend imports: `@/types`, `@/stores/...`, `@/components/...`, `@/lib/...`.
- After touching code: run all backend tests + tsc, must stay green.

---

## IMPLEMENTATION TASKS

### Phase A: Backend Foundation (Tasks 1–7)

---

### Task 1: Pydantic schemas for interference and drawdown

**Files:**
- Modify: `backend/models/schemas.py`
- Test: `backend/tests/test_schemas.py`

**Step 1: Add tests**

Append to `backend/tests/test_schemas.py`:

```python
from models.schemas import (
    InterferencePair, InterferenceResult, InterferenceCard,
    DrawdownIsoline, DrawdownGrid, DrawdownCard,
)


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
```

**Step 2: Run, verify FAIL**

```
cd backend && .venv/Scripts/python -m pytest tests/test_schemas.py -k "Interfer or Drawdown" -v
```
Expected: collection ERROR (`ImportError`).

**Step 3: Implement schemas**

Append to `backend/models/schemas.py`:

```python
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
```

Update `ChatResponse.cards` union to include new types:
```python
class ChatResponse(BaseModel):
    message: str
    cards: list[
        AnomalyCard | ValidationResult | RegionStats | WellHistory
        | InterferenceCard | DrawdownCard
    ] = Field(default_factory=list)
    tool_calls: list[ToolCall] = Field(default_factory=list)
    model_used: str = ""
    latency_ms: int = 0
    tokens_used: int = 0
```

**Step 4: Run tests**

```
cd backend && .venv/Scripts/python -m pytest tests/test_schemas.py -v
```
Expected: all PASS, no regressions.

**Step 5: Commit**

```bash
git add backend/models/schemas.py backend/tests/test_schemas.py
git commit -m "feat(schemas): add Theis interference and drawdown Pydantic models

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 2: `analyze_interference` tool

**Files:**
- Create: `backend/tools/analyze_interference.py`
- Test: `backend/tests/test_analyze_interference.py`

**Step 1: Write tests**

Create `backend/tests/test_analyze_interference.py`:

```python
"""Tests for analyze_interference tool."""
import os
from pathlib import Path

import pytest

DATA_DIR = str(Path(__file__).resolve().parent.parent.parent / "data")
os.environ["DATA_DIR"] = DATA_DIR

from tools.analyze_interference import analyze_interference, _wgs84_distance_m


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
            # Dominant well is the one whose coef on the OTHER side is higher
            # (i.e., the one whose drawdown dominates the other's well)
            assert p.dominant_well in (p.well_a, p.well_b)

    def test_t_days_param(self):
        r30 = analyze_interference(bbox=[54.0, 24.0, 56.0, 25.0], t_days=30)
        r90 = analyze_interference(bbox=[54.0, 24.0, 56.0, 25.0], t_days=90)
        # Longer pumping → more drawdown → potentially more pairs above threshold
        assert r90.t_days == 90
```

**Step 2: Verify FAIL**

```
cd backend && .venv/Scripts/python -m pytest tests/test_analyze_interference.py -v
```
Expected: ImportError on collection.

**Step 3: Implement tool**

Create `backend/tools/analyze_interference.py`:

```python
"""Tool: Theis-based interference analysis between well pairs."""
import json
import math
import os
from pathlib import Path

from data_generator.hydro_models import theis_drawdown
from models.schemas import InterferencePair, InterferenceResult


def _get_data_dir() -> str:
    return os.environ.get("DATA_DIR", "./data")


def _wgs84_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Haversine distance in meters."""
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _severity_from_coef(c_max: float) -> str:
    if c_max >= 0.60:
        return "critical"
    if c_max >= 0.40:
        return "high"
    if c_max >= 0.20:
        return "medium"
    return "low"


def _recommendation(severity: str, dominant: str, victim: str, distance_km: float) -> str:
    if severity == "critical":
        return (
            f"URGENT: Reduce pumping at {dominant} or relocate {victim} "
            f"to >2km away. Current spacing {distance_km:.2f}km creates severe interference."
        )
    if severity == "high":
        return (
            f"Schedule pump test at {dominant} and {victim}. "
            f"Consider staggered pumping schedule to reduce simultaneous load."
        )
    if severity == "medium":
        return (
            f"Monitor combined drawdown at {dominant}-{victim} pair. "
            f"Acceptable but watch for further decline."
        )
    return f"Routine monitoring sufficient for {dominant}-{victim} pair."


def analyze_interference(
    bbox: list[float] | None = None,
    t_days: int = 30,
    min_coefficient: float = 0.10,
) -> InterferenceResult:
    """
    Compute Theis-based interference for all well pairs in bbox.

    Args:
        bbox: [west, south, east, north] WGS84. None = all wells.
        t_days: pumping time horizon (days).
        min_coefficient: filter out pairs with max coef below this threshold.

    Returns:
        InterferenceResult with significant pairs.
    """
    geojson_path = Path(_get_data_dir()) / "wells.geojson"
    with open(geojson_path, encoding="utf-8") as f:
        geojson = json.load(f)

    # Filter wells by bbox
    wells_in_bbox = []
    for feat in geojson["features"]:
        lon, lat = feat["geometry"]["coordinates"]
        if bbox is not None:
            west, south, east, north = bbox
            if not (west <= lon <= east and south <= lat <= north):
                continue
        wells_in_bbox.append(feat)

    pairs: list[InterferencePair] = []
    well_radius_m = 0.3  # standard well radius for self-drawdown calc

    for i in range(len(wells_in_bbox)):
        for j in range(i + 1, len(wells_in_bbox)):
            a, b = wells_in_bbox[i], wells_in_bbox[j]
            pa, pb = a["properties"], b["properties"]
            lon_a, lat_a = a["geometry"]["coordinates"]
            lon_b, lat_b = b["geometry"]["coordinates"]

            r = _wgs84_distance_m(lat_a, lon_a, lat_b, lon_b)
            if r < 1.0:
                continue

            # Pumping rate Q in m³/day = yield_ls * 86.4
            q_a = pa["current_yield_ls"] * 86.4
            q_b = pb["current_yield_ls"] * 86.4
            t_a = pa["transmissivity_m2d"]
            t_b = pb["transmissivity_m2d"]
            s_a = pa["storativity"]
            s_b = pb["storativity"]

            # Skip if either well not pumping
            if q_a <= 0 or q_b <= 0:
                continue

            # Self-drawdown at well radius
            s_self_a = theis_drawdown(q_a, t_a, s_a, well_radius_m, t_days)
            s_self_b = theis_drawdown(q_b, t_b, s_b, well_radius_m, t_days)

            # Cross-drawdown
            s_b_at_a = theis_drawdown(q_b, t_b, s_b, r, t_days)
            s_a_at_b = theis_drawdown(q_a, t_a, s_a, r, t_days)

            coef_at_a = s_b_at_a / s_self_a if s_self_a > 0 else 0
            coef_at_b = s_a_at_b / s_self_b if s_self_b > 0 else 0

            coef_max = max(coef_at_a, coef_at_b)
            if coef_max < min_coefficient:
                continue

            # Drawdown at midpoint
            r_mid = r / 2
            dm = theis_drawdown(q_a, t_a, s_a, r_mid, t_days) + theis_drawdown(
                q_b, t_b, s_b, r_mid, t_days
            )

            severity = _severity_from_coef(coef_max)
            # Dominant well = the one whose pumping causes higher coef on the other side
            # If coef_at_a is high → B is dominating A → dominant = B
            dominant = pb["id"] if coef_at_a >= coef_at_b else pa["id"]
            victim = pa["id"] if dominant == pb["id"] else pb["id"]

            pairs.append(
                InterferencePair(
                    well_a=pa["id"],
                    well_b=pb["id"],
                    distance_km=round(r / 1000, 3),
                    coef_at_a=round(coef_at_a, 3),
                    coef_at_b=round(coef_at_b, 3),
                    drawdown_midpoint_m=round(dm, 2),
                    severity=severity,
                    dominant_well=dominant,
                    recommendation=_recommendation(severity, dominant, victim, r / 1000),
                )
            )

    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    pairs.sort(key=lambda p: (severity_order[p.severity], -max(p.coef_at_a, p.coef_at_b)))

    return InterferenceResult(
        pairs=pairs,
        t_days=t_days,
        wells_analyzed=len(wells_in_bbox),
        pairs_significant=len(pairs),
    )
```

**Step 4: Run tests**

```
cd backend && .venv/Scripts/python -m pytest tests/test_analyze_interference.py -v
```
Expected: all 6 tests PASS.

**Step 5: Commit**

```bash
git add backend/tools/analyze_interference.py backend/tests/test_analyze_interference.py
git commit -m "feat(tools): add analyze_interference Theis-based tool

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 3: `compute_drawdown_grid` tool

**Files:**
- Create: `backend/tools/compute_drawdown_grid.py`
- Test: `backend/tests/test_compute_drawdown_grid.py`
- Modify: `backend/requirements.txt` (add `scikit-image==0.25.0`)

**Step 1: Add dep**

Append to `backend/requirements.txt`:
```
scikit-image==0.25.0
```

Install: `cd backend && .venv/Scripts/pip install scikit-image==0.25.0`.

**Step 2: Write tests**

Create `backend/tests/test_compute_drawdown_grid.py`:

```python
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
        # Some levels may be missing if max drawdown is small, but we expect at least one
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
        # Other Al Wathba wells are within 10km
        assert isinstance(g.interfering_wells, list)
```

**Step 3: Verify FAIL**

```
cd backend && .venv/Scripts/python -m pytest tests/test_compute_drawdown_grid.py -v
```
Expected: ImportError.

**Step 4: Implement tool**

Create `backend/tools/compute_drawdown_grid.py`:

```python
"""Tool: Theis-based drawdown grid with isoline polygons."""
import json
import math
import os
from pathlib import Path

import numpy as np
from skimage import measure

from data_generator.hydro_models import theis_drawdown
from models.schemas import DrawdownGrid, DrawdownIsoline


ISOLINE_LEVELS = [0.5, 1.0, 2.0, 5.0]
DEFAULT_RESOLUTION = 50
DEFAULT_EXTENT_KM = 5


def _get_data_dir() -> str:
    return os.environ.get("DATA_DIR", "./data")


def _load_wells() -> list[dict]:
    path = Path(_get_data_dir()) / "wells.geojson"
    with open(path, encoding="utf-8") as f:
        return json.load(f)["features"]


def _km_to_deg_lat(km: float) -> float:
    return km / 111.0


def _km_to_deg_lon(km: float, lat_deg: float) -> float:
    return km / (111.0 * math.cos(math.radians(lat_deg)))


def _meters_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6_371_000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lon2 - lon1)
    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    return 2 * R * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _contours_to_polygon(
    contours: list[np.ndarray],
    grid_lon: np.ndarray,
    grid_lat: np.ndarray,
) -> dict:
    """Convert scikit-image contour pixel coords to GeoJSON MultiPolygon."""
    multi_coords = []
    for c in contours:
        # c is array of (row, col) in grid coords
        if len(c) < 3:
            continue
        ring = []
        for row, col in c:
            ri = int(round(row))
            ci = int(round(col))
            ri = max(0, min(grid_lat.shape[0] - 1, ri))
            ci = max(0, min(grid_lon.shape[0] - 1, ci))
            ring.append([float(grid_lon[ci]), float(grid_lat[ri])])
        # Close ring
        if ring[0] != ring[-1]:
            ring.append(ring[0])
        multi_coords.append([ring])

    return {"type": "MultiPolygon", "coordinates": multi_coords}


def compute_drawdown_grid(
    well_id: str,
    t_days: int = 30,
    extent_km: float = DEFAULT_EXTENT_KM,
    resolution: int = DEFAULT_RESOLUTION,
) -> DrawdownGrid:
    """
    Compute Theis drawdown on a square grid centered on well_id and return isoline polygons.

    Includes superposition from any other well within `extent_km`.
    """
    wells = _load_wells()
    target = next((w for w in wells if w["properties"]["id"] == well_id), None)
    if target is None:
        raise ValueError(f"Well not found: {well_id}")

    target_lon, target_lat = target["geometry"]["coordinates"]
    target_props = target["properties"]

    # Find interfering wells within extent_km
    interfering = []
    relevant = [target]
    for w in wells:
        if w["properties"]["id"] == well_id:
            continue
        wlon, wlat = w["geometry"]["coordinates"]
        d = _meters_distance(target_lat, target_lon, wlat, wlon)
        if d <= extent_km * 1000 and w["properties"]["current_yield_ls"] > 0:
            interfering.append(w["properties"]["id"])
            relevant.append(w)

    # Build grid in lat/lon
    d_lat = _km_to_deg_lat(extent_km)
    d_lon = _km_to_deg_lon(extent_km, target_lat)
    lats = np.linspace(target_lat - d_lat, target_lat + d_lat, resolution)
    lons = np.linspace(target_lon - d_lon, target_lon + d_lon, resolution)

    drawdown = np.zeros((resolution, resolution), dtype=float)
    for ri, lat in enumerate(lats):
        for ci, lon in enumerate(lons):
            total = 0.0
            for w in relevant:
                wlon, wlat = w["geometry"]["coordinates"]
                wp = w["properties"]
                q = wp["current_yield_ls"] * 86.4
                if q <= 0:
                    continue
                r = _meters_distance(lat, lon, wlat, wlon)
                r = max(r, 0.3)
                total += theis_drawdown(q, wp["transmissivity_m2d"], wp["storativity"], r, t_days)
            drawdown[ri, ci] = total

    max_dd = float(drawdown.max())

    isolines: list[DrawdownIsoline] = []
    for level in ISOLINE_LEVELS:
        if level >= max_dd:
            continue
        contours = measure.find_contours(drawdown, level)
        polygon = _contours_to_polygon(contours, lons, lats)
        if polygon["coordinates"]:
            isolines.append(DrawdownIsoline(level_m=level, polygon=polygon))

    return DrawdownGrid(
        well_id=well_id,
        center=[target_lon, target_lat],
        t_days=t_days,
        isolines=isolines,
        max_drawdown_m=round(max_dd, 2),
        interfering_wells=interfering,
    )
```

**Step 5: Run tests**

```
cd backend && .venv/Scripts/python -m pytest tests/test_compute_drawdown_grid.py -v
```
Expected: 6 tests PASS.

**Step 6: Commit**

```bash
git add backend/tools/compute_drawdown_grid.py backend/tests/test_compute_drawdown_grid.py backend/requirements.txt
git commit -m "feat(tools): add compute_drawdown_grid tool with scikit-image isolines

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 4: Tool registry update

**Files:**
- Modify: `backend/models/tool_schemas.py`
- Modify: `backend/services/tool_executor.py`
- Modify: `backend/tests/test_tool_executor.py`

**Step 1: Update test**

Add to `backend/tests/test_tool_executor.py` `TestToolDefinitions`:

```python
def test_new_tools_present(self):
    names = {t["function"]["name"] for t in TOOL_DEFINITIONS}
    assert "analyze_interference" in names
    assert "compute_drawdown_grid" in names
```

Add to `TestToolExecutor`:

```python
def test_execute_analyze_interference(self, executor):
    result = executor.execute("analyze_interference", {"bbox": [54.0, 24.0, 56.0, 25.0]})
    assert result.success
    assert result.result["type"] == "interference_result"

def test_execute_compute_drawdown_grid(self, executor):
    result = executor.execute("compute_drawdown_grid", {"well_id": "AUH-01-001"})
    assert result.success
    assert result.result["type"] == "drawdown_grid"
```

**Step 2: Verify FAIL**

```
cd backend && .venv/Scripts/python -m pytest tests/test_tool_executor.py -v
```
Expected: 2 new tests fail.

**Step 3: Update TOOL_DEFINITIONS**

Append to `backend/models/tool_schemas.py` `TOOL_DEFINITIONS` list:

```python
{
    "type": "function",
    "function": {
        "name": "analyze_interference",
        "description": "Compute Theis-based interference between well pairs. Returns asymmetric coefficients (donor/victim relationships) and severity classification. Use for any question about well interference, depression cone overlap, mutual influence, or competing wells.",
        "parameters": {
            "type": "object",
            "properties": {
                "bbox": {
                    "type": "array",
                    "items": {"type": "number"},
                    "minItems": 4, "maxItems": 4,
                    "description": "[west, south, east, north] WGS84",
                },
                "t_days": {
                    "type": "integer",
                    "default": 30,
                    "description": "Pumping time horizon in days",
                },
                "min_coefficient": {
                    "type": "number",
                    "default": 0.10,
                    "description": "Filter out pairs below this coefficient",
                },
            },
        },
    },
},
{
    "type": "function",
    "function": {
        "name": "compute_drawdown_grid",
        "description": "Compute Theis depression cone (drawdown grid) around a single well, returning isoline polygons. Includes superposition from interfering wells. Use for depression cone analysis, drawdown questions, or operational risk assessment.",
        "parameters": {
            "type": "object",
            "properties": {
                "well_id": {"type": "string"},
                "t_days": {"type": "integer", "default": 30},
                "extent_km": {"type": "number", "default": 5},
                "resolution": {"type": "integer", "default": 50},
            },
            "required": ["well_id"],
        },
    },
},
```

**Step 4: Update ToolExecutor**

In `backend/services/tool_executor.py`:

```python
from tools.analyze_interference import analyze_interference
from tools.compute_drawdown_grid import compute_drawdown_grid
```

Add to `_registry` dict:
```python
"analyze_interference": self._exec_analyze_interference,
"compute_drawdown_grid": self._exec_compute_drawdown_grid,
```

Add method definitions:
```python
@staticmethod
def _exec_analyze_interference(args: dict) -> dict:
    result = analyze_interference(
        bbox=args.get("bbox"),
        t_days=args.get("t_days", 30),
        min_coefficient=args.get("min_coefficient", 0.10),
    )
    return result.model_dump()


@staticmethod
def _exec_compute_drawdown_grid(args: dict) -> dict:
    result = compute_drawdown_grid(
        well_id=args["well_id"],
        t_days=args.get("t_days", 30),
        extent_km=args.get("extent_km", 5),
        resolution=args.get("resolution", 50),
    )
    return result.model_dump()
```

**Step 5: Run tests**

```
cd backend && .venv/Scripts/python -m pytest tests/test_tool_executor.py -v
```
Expected: all PASS.

**Step 6: Commit**

```bash
git add backend/models/tool_schemas.py backend/services/tool_executor.py backend/tests/test_tool_executor.py
git commit -m "feat(tools): register analyze_interference and compute_drawdown_grid

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 5: Domain knowledge + task instructions + output formats

**Files:**
- Modify: `backend/prompts/domain_knowledge.py`
- Modify: `backend/prompts/task_instructions.py`
- Modify: `backend/prompts/output_formats.py`
- Test: `backend/tests/test_prompt_engine.py`

**Step 1: Update tests**

Add to `backend/tests/test_prompt_engine.py`:

```python
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
```

**Step 2: Verify FAIL**

```
cd backend && .venv/Scripts/python -m pytest tests/test_prompt_engine.py -v
```
Expected: new tests fail.

**Step 3: Append to `domain_knowledge.py`**

Append at end of `DOMAIN_KNOWLEDGE` string:

```markdown

## Interference & Depression Cones

### How to read interference lines on the map
- Lines connect well pairs with significant interference (>10% Theis coefficient).
- Color gradient encodes vulnerability:
  - RED end of line = "victim" — neighbor's drawdown dominates here (>60% of total)
  - GREEN end = "donor" — minimally affected by neighbor
  - YELLOW middle = balanced influence
- Annotation "X% / Ym" shows max coefficient + combined drawdown at midpoint
- Severity thresholds: 10-20% low, 20-40% medium, 40-60% high, >60% critical

### How to read depression cone isolines
- Concentric polygons from selected well: 0.5m, 1m, 2m, 5m drawdown levels
- Computed via Theis equation with superposition (includes interfering wells)
- Time slider: 1/7/30/90 days of pumping
- 5m+ red zone = severe drawdown, well at operational limit
- Cone radius >2km at 1m isoline = excessive pumping or low T aquifer

### Theis interference rules of thumb
- High coefficient (>40%) → wells too close OR pumping too hard OR low T aquifer
- Asymmetric coefficients (e.g., 60% vs 18%) → bigger pumper dominates
- Both >40% → mutual depletion, both wells at risk
- Distance < 1km + active pumping → almost always significant interference
```

**Step 4: Append to `task_instructions.py`**

Add to `TASK_INSTRUCTIONS` dict:

```python
"interference_analysis": """## Task: Well Interference Analysis
You are analyzing mutual hydraulic influence between groundwater wells.

MANDATORY first step: call `analyze_interference` with the user's current viewport bbox.
Do NOT estimate Theis coefficients yourself.

Interpret returned pairs:
- Critical (>60%) and high (40-60%) pairs: highlight by name in the response
- Use coef_at_a vs coef_at_b to identify donor/victim relationships
- Group findings by cluster if pattern is regional
- Reference Theis principles: high coefficient means wells too close, pumping too hard, or low transmissivity

Always recommend specific actions: reduce pumping at well X, relocate well Y, schedule field check.
""",

"drawdown_analysis": """## Task: Depression Cone & Drawdown Analysis
You are interpreting Theis-based drawdown isolines.

MANDATORY first step: call `compute_drawdown_grid` for the selected well (or specified well).
Do NOT compute Theis values manually.

Comment on:
- Maximum drawdown at the well (s_self) — operational concern if >5m
- Cone radius at 1m isoline — if >2km, excessive pumping
- Interfering wells listed in `interfering_wells` — explain superposition contribution
- Time horizon (t_days): if user wants longer-term impact, suggest re-running with t_days=90

Reference UAE pumping guidelines and aquifer sustainability for context.
""",

"water_quality_report": """## Task: Water Quality Report
Generate a water quality assessment for wells in the user's viewport.

Steps:
1. Call query_wells with the viewport bbox
2. Compare last_tds_mgl, last_chloride_mgl, last_ph against UAE drinking water standards:
   - TDS limit: 1,000 mg/L (drinking), 1,500 (emergency)
   - Chloride: 250 mg/L (drinking), 600 (emergency)
   - pH: 6.5-8.5 acceptable
3. Flag wells exceeding standards and explain operational implications
4. Note that Abu Dhabi monitoring wells produce mostly brackish water (2,000-8,000 mg/L)
   used for agriculture/landscaping, not drinking water — context-dependent severity
""",

"cluster_comparison": """## Task: Cross-Cluster Comparison
Compare well clusters visible in the viewport.

Steps:
1. For each cluster (Al Wathba, Mussafah, Sweihan, Al Khatim) call query_wells with cluster_id
2. Compare metrics: avg yield, avg TDS, anomaly count, active percentage
3. Identify best/worst cluster on each axis
4. Suggest operational priorities (which cluster needs more attention)
""",

"trend_analysis": """## Task: Trend Analysis for Well Time Series
Analyze debit and water level trends over the observation period.

Steps:
1. If selectedWellId is set, call get_well_history for that well
2. If no well selected, ask the user to click a well on the map first — do NOT pick arbitrarily
3. Comment on: trend direction (rising/falling/stable), magnitude of change, seasonal patterns
4. If trend is falling >25%, flag for inspection
""",

"daily_report": """## Task: Generate Daily Monitoring Report
Produce a structured daily summary for the visible region.

Steps:
1. Call get_region_stats with the viewport bbox
2. Call detect_anomalies (bbox-scoped) for current issues
3. Call analyze_interference if any active wells are <2km apart
4. Format report sections: Operational Status, Water Quality, Anomalies, Interference, Recommendations

Keep sections concise: each 2-3 bullet points max.
""",
```

**Step 5: Append to `output_formats.py`**

Add to `OUTPUT_FORMATS`:

```python
"interference_card": """## Output Format: Interference Card (JSON)
Return JSON matching InterferenceCard schema:
```json
{
  "type": "interference_card",
  "pairs_summary": {"critical": 2, "high": 4, "medium": 6, "low": 0},
  "top_concerns": [
    {"well_a": "AUH-01-001", "well_b": "AUH-01-002", "coef_max": 0.61,
     "action": "Reduce pumping at AUH-01-002"}
  ],
  "regional_pattern": "Mussafah cluster shows correlated drawdown patterns"
}
```
""",

"drawdown_card": """## Output Format: Drawdown Card (JSON)
Return JSON matching DrawdownCard schema:
```json
{
  "type": "drawdown_card",
  "well_id": "AUH-01-001",
  "t_days": 30,
  "max_drawdown_m": 6.8,
  "cone_radius_1m_km": 2.3,
  "interfering_wells": ["AUH-01-002", "AUH-01-007"],
  "assessment": "Cone radius >2km at 1m isoline indicates excessive pumping.",
  "recommendation": "Consider reducing pumping rate by 20% to limit aquifer depletion."
}
```
""",
```

**Step 6: Run tests**

```
cd backend && .venv/Scripts/python -m pytest tests/test_prompt_engine.py -v
```
Expected: all PASS.

**Step 7: Commit**

```bash
git add backend/prompts/
git commit -m "feat(prompts): add Theis interference domain knowledge and 6 task types

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 6: Task router and `_classify_task` extension

**Files:**
- Modify: `backend/services/llm_router.py`
- Modify: `backend/main.py`
- Test: `backend/tests/test_main.py`

**Step 1: Update test**

Add to `backend/tests/test_main.py`:

```python
class TestTaskClassifier:
    def test_classifies_interference(self):
        from main import _classify_task
        assert _classify_task("Check well interference patterns") == "interference_analysis"
        assert _classify_task("Wells competing for water") == "interference_analysis"
        assert _classify_task("Mutual influence between wells") == "interference_analysis"

    def test_classifies_drawdown(self):
        from main import _classify_task
        assert _classify_task("Show depression cone for well X") == "drawdown_analysis"
        assert _classify_task("What is the drawdown at this well?") == "drawdown_analysis"
        assert _classify_task("Generate isolines for AUH-01-001") == "drawdown_analysis"

    def test_classifies_water_quality(self):
        from main import _classify_task
        assert _classify_task("Generate a water quality report") == "water_quality_report"
        assert _classify_task("Check TDS levels in viewport") == "water_quality_report"

    def test_classifies_cluster_comparison(self):
        from main import _classify_task
        assert _classify_task("Compare clusters") == "cluster_comparison"
        assert _classify_task("Cross-cluster comparison") == "cluster_comparison"

    def test_classifies_daily_report(self):
        from main import _classify_task
        assert _classify_task("Generate daily report") == "daily_report"
        assert _classify_task("Daily monitoring summary") == "daily_report"
```

**Step 2: Verify FAIL**

```
cd backend && .venv/Scripts/python -m pytest tests/test_main.py -v
```
Expected: 5 new tests fail.

**Step 3: Update `TASK_ROUTING`**

In `backend/services/llm_router.py` extend dict:

```python
TASK_ROUTING = {
    "validate_csv":         "pool-a",
    "query_wells":          "pool-a",
    "get_region_stats":     "pool-a",
    "get_well_history":     "pool-a",
    "trend_analysis":       "pool-a",  # NEW
    "water_quality_report": "pool-a",  # NEW
    "cluster_comparison":   "pool-a",  # NEW
    "detect_anomalies":     "pool-b",
    "interpret_anomaly":    "pool-b",
    "interference_analysis":"pool-b",  # NEW
    "drawdown_analysis":    "pool-b",  # NEW
    "depression_analysis":  "pool-b",  # legacy alias, keep
    "daily_report":         "pool-b",  # NEW
    "calibration_advice":   "pool-b-upgrade",
    "general_question":     "pool-b",
}
```

**Step 4: Rewrite `_classify_task` in `main.py`**

Replace existing function:

```python
def _classify_task(message: str) -> str:
    """Heuristic classifier — order matters: most specific first."""
    msg = message.lower()

    # Most specific first
    if any(w in msg for w in ["depression cone", "drawdown", "isoline", "voronka", "влияние на уровень"]):
        return "drawdown_analysis"
    if any(w in msg for w in ["interference", "competing wells", "cone overlap", "mutual influence", "wells competing"]):
        return "interference_analysis"
    if any(w in msg for w in ["water quality", "drinking water", "salinity"]) or (
        "tds" in msg or "chloride" in msg or "ph levels" in msg
    ):
        return "water_quality_report"
    if any(w in msg for w in ["compare cluster", "cross-cluster", "between cluster"]):
        return "cluster_comparison"
    if any(w in msg for w in ["daily report", "daily monitoring", "daily summary"]):
        return "daily_report"
    if any(w in msg for w in ["trend", "time series", "history of"]):
        return "trend_analysis"
    if any(w in msg for w in ["csv", "upload", "validate", "file"]):
        return "validate_csv"
    if any(w in msg for w in ["anomal", "decline", "spike", "fault", "problem", "scan"]):
        return "detect_anomalies"
    if any(w in msg for w in ["calibrat", "optimi", "theis", "pumping schedule"]):
        return "calibration_advice"
    if any(w in msg for w in ["interpret", "why", "cause", "explain", "reason", "root cause"]):
        return "interpret_anomaly"
    if any(w in msg for w in ["region", "area", "viewport", "overview", "stats", "summary", "report"]):
        return "get_region_stats"
    if any(w in msg for w in ["find", "search", "list", "wells", "query", "status", "active", "inactive"]):
        return "query_wells"
    return "general_question"
```

**Step 5: Run tests**

```
cd backend && .venv/Scripts/python -m pytest tests/test_main.py -v
```
Expected: all PASS.

**Step 6: Commit**

```bash
git add backend/services/llm_router.py backend/main.py backend/tests/test_main.py
git commit -m "feat(router): add 6 new task types with classifier keywords

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 7: Context bridge extension

**Files:**
- Modify: `backend/models/schemas.py`
- Modify: `backend/services/context_bridge.py`
- Test: `backend/tests/test_context_bridge.py`

**Step 1: Update test**

Add to `backend/tests/test_context_bridge.py`:

```python
class TestExtendedMapContext:
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
```

**Step 2: Verify FAIL**

```
cd backend && .venv/Scripts/python -m pytest tests/test_context_bridge.py -v
```
Expected: ValidationError (new fields don't exist).

**Step 3: Extend `MapContext`**

In `backend/models/schemas.py` `MapContext` class, add fields:

```python
class MapContext(BaseModel):
    # existing fields...
    depression_cone_t_days: int = 30
    depression_cone_mode: Literal["selected", "all"] = "selected"
    interference_visible: bool = False
```

**Step 4: Update `build_context_prompt`**

In `backend/services/context_bridge.py`, after the existing well-selected block, add:

```python
    # Theis layer state
    if "depression_cone" in map_context.active_layers:
        lines.append(
            f"- Depression cone layer: ON, t={map_context.depression_cone_t_days}d, "
            f"mode={map_context.depression_cone_mode}"
        )
    if map_context.interference_visible or "interference" in map_context.active_layers:
        lines.append("- Interference layer: ON (showing significant pairs from analyze_interference)")
```

**Step 5: Run tests**

```
cd backend && .venv/Scripts/python -m pytest tests/test_context_bridge.py tests/test_schemas.py -v
```
Expected: all PASS.

**Step 6: Commit**

```bash
git add backend/models/schemas.py backend/services/context_bridge.py backend/tests/test_context_bridge.py
git commit -m "feat(context): pass cone time, mode, interference visibility to LLM

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Phase B: Frontend (Tasks 8–14)

---

### Task 8: Frontend TypeScript types

**Files:**
- Modify: `frontend/src/types/index.ts`

**Step 1: Add types**

Append to `frontend/src/types/index.ts`:

```typescript
// --- Theis Interference ---

export type Severity = "low" | "medium" | "high" | "critical";

export interface InterferencePair {
  well_a: string;
  well_b: string;
  distance_km: number;
  coef_at_a: number;
  coef_at_b: number;
  drawdown_midpoint_m: number;
  severity: Severity;
  dominant_well: string;
  recommendation: string;
}

export interface InterferenceResult {
  type: "interference_result";
  pairs: InterferencePair[];
  t_days: number;
  wells_analyzed: number;
  pairs_significant: number;
}

export interface InterferenceCard {
  type: "interference_card";
  pairs_summary: Record<string, number>;
  top_concerns: Array<{
    well_a: string;
    well_b: string;
    coef_max: number;
    action: string;
  }>;
  regional_pattern: string;
}

// --- Theis Drawdown ---

export interface DrawdownIsoline {
  level_m: number;
  polygon: GeoJSON.MultiPolygon | GeoJSON.Polygon;
}

export interface DrawdownGrid {
  type: "drawdown_grid";
  well_id: string;
  center: [number, number];
  t_days: number;
  isolines: DrawdownIsoline[];
  max_drawdown_m: number;
  interfering_wells: string[];
}

export interface DrawdownCard {
  type: "drawdown_card";
  well_id: string;
  t_days: number;
  max_drawdown_m: number;
  cone_radius_1m_km: number;
  interfering_wells: string[];
  assessment: string;
  recommendation: string;
}
```

Update `StructuredCard` union:

```typescript
export type StructuredCard =
  | AnomalyCard
  | ValidationResult
  | RegionStats
  | WellHistory
  | InterferenceCard
  | DrawdownCard;
```

Update `MapContext`:

```typescript
export interface MapContext {
  // existing...
  depression_cone_t_days?: number;
  depression_cone_mode?: "selected" | "all";
  interference_visible?: boolean;
}
```

**Step 2: Typecheck**

```
cd frontend && npx tsc --noEmit
```
Expected: clean.

**Step 3: Commit**

```bash
git add frontend/src/types/index.ts
git commit -m "feat(types): add Theis interference and drawdown TS types

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 9: mapStore extension

**Files:**
- Modify: `frontend/src/stores/mapStore.ts`
- Modify: `frontend/src/lib/contextBridge.ts`

**Step 1: Extend store**

Add to `MapState` interface and store implementation:

```typescript
interface MapState {
  // existing...
  coneTimeDays: number;            // 1, 7, 30, 90
  coneMode: "selected" | "all";

  setConeTimeDays: (days: number) => void;
  setConeMode: (mode: "selected" | "all") => void;
}
```

In store:

```typescript
coneTimeDays: 30,
coneMode: "selected",

setConeTimeDays: (days) => set({ coneTimeDays: days }),
setConeMode: (mode) => set({ coneMode: mode }),
```

In `getApiContext`:

```typescript
getApiContext: () => {
  const s = get();
  return {
    ...buildMapContext(s),
    depression_cone_t_days: s.coneTimeDays,
    depression_cone_mode: s.coneMode,
    interference_visible: s.activeLayers.includes("interference"),
  };
},
```

**Step 2: Typecheck**

```
cd frontend && npx tsc --noEmit
```
Expected: clean.

**Step 3: Commit**

```bash
git add frontend/src/stores/mapStore.ts frontend/src/lib/contextBridge.ts
git commit -m "feat(store): add cone time, cone mode state to mapStore

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 10: InterferenceLayer rewrite

**Files:**
- Rewrite: `frontend/src/components/Map/InterferenceLayer.tsx`
- Create: `frontend/src/components/Map/InterferencePopup.tsx`

**Step 1: Rewrite InterferenceLayer**

Full file `frontend/src/components/Map/InterferenceLayer.tsx`:

```typescript
'use client';

import { useEffect, useState, useCallback } from "react";
import { Source, Layer, Popup } from "react-map-gl/maplibre";
import type { InterferencePair, InterferenceResult, WellsGeoJSON } from "@/types";
import type { FeatureCollection, LineString, Point } from "geojson";
import { InterferencePopup } from "./InterferencePopup";

interface Props {
  wellsGeoJSON: WellsGeoJSON;
  bbox: [number, number, number, number];
}

const COLOR_LOW = "#16a34a";
const COLOR_MID = "#eab308";
const COLOR_HIGH = "#dc2626";

function colorForCoef(c: number): string {
  if (c >= 0.6) return COLOR_HIGH;
  if (c >= 0.3) return COLOR_MID;
  return COLOR_LOW;
}

export function InterferenceLayer({ wellsGeoJSON, bbox }: Props) {
  const [data, setData] = useState<InterferenceResult | null>(null);
  const [popup, setPopup] = useState<{ pair: InterferencePair; lng: number; lat: number } | null>(
    null
  );

  useEffect(() => {
    const ctrl = new AbortController();
    fetch("/api/tools/analyze_interference", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ bbox, t_days: 30, min_coefficient: 0.1 }),
      signal: ctrl.signal,
    })
      .then((r) => r.json())
      .then((d: InterferenceResult) => setData(d))
      .catch(() => {});
    return () => ctrl.abort();
  }, [bbox]);

  if (!data || data.pairs.length === 0) return null;

  // Build coord lookup from wellsGeoJSON
  const coords: Record<string, [number, number]> = {};
  for (const f of wellsGeoJSON.features) {
    coords[f.properties.id] = f.geometry.coordinates as [number, number];
  }

  const lines: FeatureCollection<LineString> = {
    type: "FeatureCollection",
    features: data.pairs
      .filter((p) => coords[p.well_a] && coords[p.well_b])
      .map((p, idx) => ({
        type: "Feature",
        id: idx,
        geometry: {
          type: "LineString",
          coordinates: [coords[p.well_a], coords[p.well_b]],
        },
        properties: {
          color_a: colorForCoef(p.coef_at_a),
          color_b: colorForCoef(p.coef_at_b),
          severity: p.severity,
          pair_idx: idx,
        },
      })),
  };

  const labels: FeatureCollection<Point> = {
    type: "FeatureCollection",
    features: data.pairs
      .filter((p) => coords[p.well_a] && coords[p.well_b])
      .map((p) => {
        const [lon_a, lat_a] = coords[p.well_a];
        const [lon_b, lat_b] = coords[p.well_b];
        const coefMax = Math.max(p.coef_at_a, p.coef_at_b);
        return {
          type: "Feature" as const,
          geometry: {
            type: "Point" as const,
            coordinates: [(lon_a + lon_b) / 2, (lat_a + lat_b) / 2],
          },
          properties: {
            label: `${Math.round(coefMax * 100)}% / ${p.drawdown_midpoint_m}m`,
            severity: p.severity,
          },
        };
      }),
  };

  const onLineClick = useCallback(
    (e: maplibregl.MapMouseEvent & { features?: maplibregl.MapGeoJSONFeature[] }) => {
      const f = e.features?.[0];
      if (!f) return;
      const idx = f.properties?.pair_idx;
      const pair = data.pairs[idx];
      if (!pair) return;
      const { lng, lat } = e.lngLat;
      setPopup({ pair, lng, lat });
    },
    [data]
  );

  return (
    <>
      <Source id="interference-lines" type="geojson" data={lines} lineMetrics={true}>
        {/* Wide invisible hit-target above gradient */}
        <Layer
          id="interference-lines-hit"
          type="line"
          paint={{ "line-width": 14, "line-color": "#000", "line-opacity": 0 }}
          onClick={onLineClick as never}
        />
        <Layer
          id="interference-lines-gradient"
          type="line"
          paint={{
            "line-width": 2,
            "line-gradient": [
              "interpolate",
              ["linear"],
              ["line-progress"],
              0, ["get", "color_a"],
              0.5, COLOR_MID,
              1, ["get", "color_b"],
            ],
          }}
        />
      </Source>

      <Source id="interference-labels" type="geojson" data={labels}>
        <Layer
          id="interference-labels-symbol"
          type="symbol"
          minzoom={11}
          layout={{
            "text-field": ["get", "label"],
            "text-size": 10,
            "text-offset": [0, 0],
            "text-anchor": "center",
            "text-allow-overlap": true,
          }}
          paint={{
            "text-color": "#1f2937",
            "text-halo-color": "#ffffff",
            "text-halo-width": 1.5,
          }}
        />
      </Source>

      {popup && (
        <Popup
          longitude={popup.lng}
          latitude={popup.lat}
          anchor="bottom"
          onClose={() => setPopup(null)}
          closeOnClick={false}
          maxWidth="360px"
        >
          <InterferencePopup pair={popup.pair} />
        </Popup>
      )}
    </>
  );
}
```

**Step 2: Create InterferencePopup**

```typescript
'use client';

import type { InterferencePair } from "@/types";

const SEVERITY_BG: Record<string, string> = {
  critical: "bg-red-100 text-red-800",
  high: "bg-orange-100 text-orange-800",
  medium: "bg-yellow-100 text-yellow-800",
  low: "bg-green-100 text-green-800",
};

export function InterferencePopup({ pair }: { pair: InterferencePair }) {
  const dominantIsA = pair.dominant_well === pair.well_a;

  return (
    <div className="p-2 text-sm">
      <div className="flex items-center gap-2 mb-2">
        <span className="font-mono">{pair.well_a}</span>
        <span>↔</span>
        <span className="font-mono">{pair.well_b}</span>
        <span className={`ml-auto px-2 py-0.5 rounded-full text-xs font-semibold ${SEVERITY_BG[pair.severity]}`}>
          {pair.severity}
        </span>
      </div>

      <div className="text-xs text-gray-600 mb-2">Distance: {pair.distance_km} km</div>

      <div className="space-y-1 text-xs mb-2">
        <div>
          Drawdown at <span className="font-mono">{pair.well_a}</span>:{" "}
          <span className="font-medium">{Math.round(pair.coef_at_a * 100)}%</span> from B
          {!dominantIsA && pair.coef_at_a > 0.4 ? <span className="text-red-600"> (vulnerable)</span> : null}
        </div>
        <div>
          Drawdown at <span className="font-mono">{pair.well_b}</span>:{" "}
          <span className="font-medium">{Math.round(pair.coef_at_b * 100)}%</span> from A
          {dominantIsA && pair.coef_at_b > 0.4 ? <span className="text-red-600"> (vulnerable)</span> : null}
        </div>
        <div className="text-gray-600">
          Combined drawdown midpoint: <span className="font-medium">{pair.drawdown_midpoint_m} m</span>
        </div>
      </div>

      <div className="text-xs text-gray-700 border-t pt-2">
        <span className="font-semibold">Recommendation:</span> {pair.recommendation}
      </div>
    </div>
  );
}
```

**Step 3: Add backend `/api/tools/analyze_interference` endpoint**

In `backend/main.py` add:

```python
from pydantic import BaseModel as _BaseModel

class _InterferenceRequest(_BaseModel):
    bbox: list[float] | None = None
    t_days: int = 30
    min_coefficient: float = 0.10


@app.post("/api/tools/analyze_interference", tags=["tools"])
async def api_analyze_interference(req: _InterferenceRequest):
    from tools.analyze_interference import analyze_interference
    result = analyze_interference(
        bbox=req.bbox, t_days=req.t_days, min_coefficient=req.min_coefficient
    )
    return result.model_dump()
```

Add similar for compute_drawdown_grid (used by Task 11).

**Step 4: Typecheck + manual smoke test**

```
cd frontend && npx tsc --noEmit
```

Restart backend. Open localhost:3000, toggle Interference. Lines should appear with gradient.

**Step 5: Commit**

```bash
git add frontend/src/components/Map/InterferenceLayer.tsx frontend/src/components/Map/InterferencePopup.tsx backend/main.py
git commit -m "feat(map): InterferenceLayer rewrite — gradient lines, click popup, Theis-driven

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 11: DepressionConeLayer rewrite + TimeSlider + Legend

**Files:**
- Rewrite: `frontend/src/components/Map/DepressionConeLayer.tsx`
- Create: `frontend/src/components/Map/TimeSlider.tsx`
- Create: `frontend/src/components/Map/DrawdownLegend.tsx`
- Modify: `frontend/src/components/Map/WellsMap.tsx`
- Modify: `backend/main.py` (add `/api/tools/compute_drawdown_grid` endpoint)

**Step 1: Add backend endpoint**

In `backend/main.py`:

```python
class _DrawdownRequest(_BaseModel):
    well_id: str
    t_days: int = 30
    extent_km: float = 5
    resolution: int = 50


@app.post("/api/tools/compute_drawdown_grid", tags=["tools"])
async def api_compute_drawdown_grid(req: _DrawdownRequest):
    from tools.compute_drawdown_grid import compute_drawdown_grid
    result = compute_drawdown_grid(
        well_id=req.well_id,
        t_days=req.t_days,
        extent_km=req.extent_km,
        resolution=req.resolution,
    )
    return result.model_dump()
```

**Step 2: Create TimeSlider**

```typescript
// frontend/src/components/Map/TimeSlider.tsx
'use client';

const PRESETS = [1, 7, 30, 90];

interface Props {
  value: number;
  onChange: (days: number) => void;
}

export function TimeSlider({ value, onChange }: Props) {
  return (
    <div className="flex items-center gap-2 bg-white/95 backdrop-blur-sm rounded-lg shadow-md px-3 py-2 text-xs">
      <span className="text-gray-500 font-medium">Pumping time:</span>
      {PRESETS.map((d) => (
        <button
          key={d}
          onClick={() => onChange(d)}
          className={`px-2.5 py-1 rounded ${
            value === d ? "bg-blue-600 text-white" : "bg-gray-100 text-gray-700 hover:bg-gray-200"
          }`}
        >
          {d}d
        </button>
      ))}
    </div>
  );
}
```

**Step 3: Create DrawdownLegend**

```typescript
// frontend/src/components/Map/DrawdownLegend.tsx
'use client';

const LEVELS = [
  { color: "#dc2626", label: "5m+ severe" },
  { color: "#f97316", label: "2m" },
  { color: "#eab308", label: "1m" },
  { color: "#84cc16", label: "0.5m" },
];

export function DrawdownLegend({ tDays }: { tDays: number }) {
  return (
    <div className="bg-white/95 backdrop-blur-sm rounded-lg shadow-md px-3 py-2 text-xs">
      <div className="text-gray-500 font-medium mb-1">Drawdown after {tDays}d:</div>
      <div className="flex gap-2">
        {LEVELS.map(({ color, label }) => (
          <div key={label} className="flex items-center gap-1">
            <span className="w-3 h-3 rounded-sm" style={{ backgroundColor: color }} />
            <span className="text-gray-700">{label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
```

**Step 4: Rewrite DepressionConeLayer**

```typescript
'use client';

import { useEffect, useState } from "react";
import { Source, Layer } from "react-map-gl/maplibre";
import type { DrawdownGrid, WellsGeoJSON } from "@/types";

const ISOLINE_PAINT = [
  { level: 0.5, color: "#84cc16", opacity: 0.06 },
  { level: 1.0, color: "#eab308", opacity: 0.10 },
  { level: 2.0, color: "#f97316", opacity: 0.15 },
  { level: 5.0, color: "#dc2626", opacity: 0.25 },
];

interface Props {
  wellsGeoJSON: WellsGeoJSON;
  selectedWellId: string | null;
  mode: "selected" | "all";
  tDays: number;
}

export function DepressionConeLayer({ wellsGeoJSON, selectedWellId, mode, tDays }: Props) {
  const [grids, setGrids] = useState<DrawdownGrid[]>([]);

  useEffect(() => {
    const ctrl = new AbortController();
    const targets =
      mode === "selected"
        ? selectedWellId
          ? [selectedWellId]
          : []
        : wellsGeoJSON.features
            .filter((f) => f.properties.status === "active")
            .map((f) => f.properties.id);

    if (targets.length === 0) {
      setGrids([]);
      return;
    }

    Promise.all(
      targets.map((wid) =>
        fetch("/api/tools/compute_drawdown_grid", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ well_id: wid, t_days: tDays, extent_km: 5, resolution: 40 }),
          signal: ctrl.signal,
        }).then((r) => r.json() as Promise<DrawdownGrid>)
      )
    )
      .then(setGrids)
      .catch(() => {});

    return () => ctrl.abort();
  }, [selectedWellId, mode, tDays, wellsGeoJSON]);

  if (grids.length === 0) return null;

  return (
    <>
      {ISOLINE_PAINT.map(({ level, color, opacity }) => {
        const features = grids.flatMap((g) => {
          const iso = g.isolines.find((i) => i.level_m === level);
          if (!iso) return [];
          return [
            {
              type: "Feature" as const,
              geometry: iso.polygon,
              properties: { well_id: g.well_id, level_m: level },
            },
          ];
        });
        if (features.length === 0) return null;

        return (
          <Source
            key={level}
            id={`drawdown-iso-${level}`}
            type="geojson"
            data={{ type: "FeatureCollection", features }}
          >
            <Layer
              id={`drawdown-iso-${level}-fill`}
              type="fill"
              paint={{ "fill-color": color, "fill-opacity": opacity }}
            />
          </Source>
        );
      })}
    </>
  );
}
```

**Step 5: Wire into WellsMap**

In `frontend/src/components/Map/WellsMap.tsx`:

- Replace existing DepressionConeLayer usage with new props (`selectedWellId`, `mode`, `tDays`).
- Pass `bbox` to InterferenceLayer.
- Add `<TimeSlider>` and `<DrawdownLegend>` overlays when `activeLayers.includes("depression_cone")`.

Concrete diff (around existing `<DepressionConeLayer>` block):

```typescript
// Imports: also import TimeSlider, DrawdownLegend
import { TimeSlider } from "./TimeSlider";
import { DrawdownLegend } from "./DrawdownLegend";

// Inside component, get coneTimeDays + setConeTimeDays + coneMode from store
const { coneTimeDays, setConeTimeDays, coneMode } = useMapStore();

// Inside Map JSX, replace DepressionConeLayer:
{activeLayers.includes("depression_cone") && wellsGeoJSON && (
  <DepressionConeLayer
    wellsGeoJSON={wellsGeoJSON}
    selectedWellId={selectedWellId}
    mode={coneMode}
    tDays={coneTimeDays}
  />
)}

{activeLayers.includes("interference") && wellsGeoJSON && bounds && (
  <InterferenceLayer wellsGeoJSON={wellsGeoJSON} bbox={bounds} />
)}

// Outside Map (overlays):
{activeLayers.includes("depression_cone") && (
  <>
    <div className="absolute top-3 left-1/2 -translate-x-1/2 z-10">
      <TimeSlider value={coneTimeDays} onChange={setConeTimeDays} />
    </div>
    <div className="absolute bottom-3 left-3 z-10">
      <DrawdownLegend tDays={coneTimeDays} />
    </div>
  </>
)}
```

**Step 6: Typecheck**

```
cd frontend && npx tsc --noEmit
```
Expected: clean.

**Step 7: Manual smoke test**

Restart backend. Open localhost:3000. Click a well. Toggle Depression Cone. Isoline polygons should appear. Move slider 1d/7d/30d/90d — cone size changes.

**Step 8: Commit**

```bash
git add frontend/src/components/Map/ backend/main.py
git commit -m "feat(map): DepressionConeLayer rewrite — Theis isolines, time slider, legend

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 12: LayerControls update

**Files:**
- Modify: `frontend/src/components/Map/LayerControls.tsx`

**Step 1: Update layer list**

```typescript
const LAYERS = [
  { id: "wells", label: "Wells", icon: "⬤" },
  { id: "depression_cone", label: "Depression Cone", icon: "◎" },
  { id: "interference", label: "Interference", icon: "⟷" },
];
```

(Note: `depression_cone` singular — old `depression_cones` plural removed everywhere it's referenced.)

**Step 2: Find and update old "depression_cones" references**

```
cd frontend && grep -r "depression_cones" src/
```

Update each match to `depression_cone`.

**Step 3: Typecheck + smoke**

```
cd frontend && npx tsc --noEmit
```

**Step 4: Commit**

```bash
git add frontend/src/components/Map/LayerControls.tsx frontend/src/
git commit -m "refactor(layers): rename depression_cones → depression_cone (singular)

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 13: Chat InterferenceCard + DrawdownCard components

**Files:**
- Create: `frontend/src/components/Chat/InterferenceCardView.tsx`
- Create: `frontend/src/components/Chat/DrawdownCardView.tsx`
- Modify: `frontend/src/components/Chat/MessageBubble.tsx`

**Step 1: InterferenceCardView**

```typescript
'use client';

import type { InterferenceCard } from "@/types";

const SEVERITY_COLOR: Record<string, string> = {
  critical: "bg-red-100 text-red-800",
  high: "bg-orange-100 text-orange-800",
  medium: "bg-yellow-100 text-yellow-800",
  low: "bg-green-100 text-green-800",
};

export function InterferenceCardView({ card }: { card: InterferenceCard }) {
  return (
    <div className="mt-2 p-3 bg-white rounded border text-xs">
      <div className="font-medium mb-2">Interference Analysis</div>

      <div className="flex gap-2 mb-2 flex-wrap">
        {Object.entries(card.pairs_summary).map(([sev, count]) => (
          count > 0 ? (
            <span key={sev} className={`px-2 py-0.5 rounded-full ${SEVERITY_COLOR[sev]}`}>
              {count} {sev}
            </span>
          ) : null
        ))}
      </div>

      {card.top_concerns.length > 0 && (
        <div className="mb-2">
          <div className="text-gray-500 uppercase text-[10px] mb-1">Top concerns</div>
          <ul className="space-y-1">
            {card.top_concerns.map((c, i) => (
              <li key={i} className="border-l-2 border-orange-400 pl-2">
                <span className="font-mono">{c.well_a}</span> ↔{" "}
                <span className="font-mono">{c.well_b}</span>{" "}
                <span className="font-medium">{Math.round(c.coef_max * 100)}%</span>
                <div className="text-gray-600">{c.action}</div>
              </li>
            ))}
          </ul>
        </div>
      )}

      {card.regional_pattern && (
        <div className="text-gray-700 border-t pt-2 mt-2">
          <span className="font-semibold">Pattern:</span> {card.regional_pattern}
        </div>
      )}
    </div>
  );
}
```

**Step 2: DrawdownCardView**

```typescript
'use client';

import type { DrawdownCard } from "@/types";

export function DrawdownCardView({ card }: { card: DrawdownCard }) {
  const severeCone = card.cone_radius_1m_km > 2;
  return (
    <div className="mt-2 p-3 bg-white rounded border text-xs">
      <div className="font-medium mb-2">
        Depression Cone — <span className="font-mono">{card.well_id}</span>{" "}
        <span className="text-gray-500">({card.t_days}d)</span>
      </div>

      <div className="grid grid-cols-2 gap-2 mb-2">
        <div>
          <div className="text-gray-500 text-[10px] uppercase">Max drawdown</div>
          <div className={`font-medium ${card.max_drawdown_m > 5 ? "text-red-600" : "text-gray-800"}`}>
            {card.max_drawdown_m} m
          </div>
        </div>
        <div>
          <div className="text-gray-500 text-[10px] uppercase">1m isoline radius</div>
          <div className={`font-medium ${severeCone ? "text-orange-600" : "text-gray-800"}`}>
            {card.cone_radius_1m_km} km
          </div>
        </div>
      </div>

      {card.interfering_wells.length > 0 && (
        <div className="mb-2">
          <div className="text-gray-500 text-[10px] uppercase mb-1">Interfering wells</div>
          <div className="flex flex-wrap gap-1">
            {card.interfering_wells.map((w) => (
              <span key={w} className="font-mono px-1.5 py-0.5 bg-gray-100 rounded">{w}</span>
            ))}
          </div>
        </div>
      )}

      <div className="text-gray-700 border-t pt-2 mt-2 space-y-1">
        <div><span className="font-semibold">Assessment:</span> {card.assessment}</div>
        <div><span className="font-semibold">Recommendation:</span> {card.recommendation}</div>
      </div>
    </div>
  );
}
```

**Step 3: Wire into MessageBubble**

Add imports and switch cases for `interference_card` and `drawdown_card` in MessageBubble's card-rendering block.

**Step 4: Typecheck + smoke**

```
cd frontend && npx tsc --noEmit
```

**Step 5: Commit**

```bash
git add frontend/src/components/Chat/
git commit -m "feat(chat): add InterferenceCardView and DrawdownCardView

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 14: CommandBar rebind + Run Eval polishing (combined)

**Files:**
- Modify: `frontend/src/components/Chat/CommandBar.tsx`
- Modify: `backend/eval/metrics_api.py`
- Modify: `backend/eval/batch_runner.py`
- Modify: `frontend/src/components/Metrics/MetricsPanel.tsx`

**Step 1: CommandBar — verify each command's prompt routes correctly**

After Task 6, the classifier handles all keywords. Verify by reading CommandBar.tsx — no code change needed unless a command's prompt does not contain keywords matching its intended task type. If any does, edit the prompt text to include trigger keywords (e.g., "Generate a daily monitoring report" already contains "daily report" — OK).

If a command needs explicit override, change CommandBar to pass `task_type` directly via a new prop on `sendMessage`. (Out of scope unless verified necessary — defer.)

**Step 2: Run Eval status — backend**

In `backend/eval/batch_runner.py`, add status writing per case:

```python
import json
from pathlib import Path

def _write_status(state: str, current: int, total: int, output_dir: Path):
    status_path = output_dir / "_status.json"
    with open(status_path, "w") as f:
        json.dump({
            "state": state,
            "current": current,
            "total": total,
            "progress_pct": round(100 * current / total, 1) if total else 0,
        }, f)
```

In `run_eval`:
```python
output_dir_path = Path(output_dir)
output_dir_path.mkdir(parents=True, exist_ok=True)
total = len(cases) * len(models)
counter = 0
_write_status("running", 0, total, output_dir_path)

for model in models:
    for case in cases:
        # existing per-case code
        counter += 1
        _write_status("running", counter, total, output_dir_path)

_write_status("done", total, total, output_dir_path)
```

In `metrics_api.py` add endpoint:

```python
@router.get("/run/status", tags=["metrics"])
async def get_run_status():
    status_path = RESULTS_DIR / "_status.json"
    if not status_path.exists():
        return {"state": "idle"}
    with open(status_path) as f:
        return json.load(f)
```

**Step 3: Run Eval status — frontend**

In `MetricsPanel.tsx` `handleRunEval`:

```typescript
const handleRunEval = async () => {
  setIsRunning(true);
  await fetch("/api/metrics/run", { method: "POST" });
  const poll = setInterval(async () => {
    const r = await fetch("/api/metrics/run/status").then((x) => x.json());
    setProgress(r);
    if (r.state === "done") {
      clearInterval(poll);
      setIsRunning(false);
      fetchMetrics();
    }
  }, 2000);
};
```

Add `progress` state and render:
```tsx
{progress && progress.state === "running" && (
  <div className="w-full bg-gray-200 rounded h-2 mt-2">
    <div
      className="bg-blue-600 h-2 rounded"
      style={{ width: `${progress.progress_pct}%` }}
    />
    <div className="text-xs text-gray-500 mt-1">
      {progress.current} / {progress.total} cases
    </div>
  </div>
)}
```

**Step 4: Typecheck + run all backend tests**

```
cd frontend && npx tsc --noEmit
cd backend && .venv/Scripts/python -m pytest tests/ -v
```
Expected: all green.

**Step 5: Commit**

```bash
git add backend/eval/ frontend/src/components/Metrics/MetricsPanel.tsx frontend/src/components/Chat/CommandBar.tsx
git commit -m "feat(eval): Run Eval progress polling + status endpoint

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

### Task 15: E2E tests update

**Files:**
- Modify: `frontend/e2e/map.spec.ts`
- Create: `frontend/e2e/interference.spec.ts`
- Create: `frontend/e2e/depression-cone.spec.ts`

**Step 1: Update map.spec.ts**

Replace `depression_cones` plural references with `depression_cone`.

**Step 2: interference.spec.ts**

```typescript
import { test, expect } from "@playwright/test";

test.describe("Interference layer", () => {
  test("toggle interference layer", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto("/");
    await page.waitForTimeout(2000);
    await page.locator("label", { hasText: "Interference" }).click();
    // wait for layer to load
    await page.waitForTimeout(2000);
    // verify map still rendered (no crash)
    await expect(page.locator(".maplibregl-canvas")).toBeVisible();
  });
});
```

**Step 3: depression-cone.spec.ts**

```typescript
import { test, expect } from "@playwright/test";

test.describe("Depression cone layer", () => {
  test("time slider visible when layer enabled", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto("/");
    await page.waitForTimeout(2000);
    await page.locator("label", { hasText: "Depression Cone" }).click();
    await page.waitForTimeout(500);
    await expect(page.getByText("Pumping time:").first()).toBeVisible();
    await expect(page.getByRole("button", { name: "30d" }).first()).toBeVisible();
  });

  test("legend visible when layer enabled", async ({ page }) => {
    await page.setViewportSize({ width: 1280, height: 720 });
    await page.goto("/");
    await page.waitForTimeout(2000);
    await page.locator("label", { hasText: "Depression Cone" }).click();
    await page.waitForTimeout(500);
    await expect(page.getByText(/Drawdown after.*d/).first()).toBeVisible();
  });
});
```

**Step 4: Run e2e**

```
cd frontend && npx playwright test --reporter=list
```
Expected: all PASS.

**Step 5: Commit**

```bash
git add frontend/e2e/
git commit -m "test(e2e): add interference and depression cone layer specs

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Final verification

After Task 15, run:

```bash
cd backend && .venv/Scripts/python -m pytest tests/ -v
cd frontend && npx tsc --noEmit && npx playwright test
```

All must be green. Then push:

```bash
git push origin main
```

---

## EXECUTION NOTES

1. Tasks 1–7 are backend; tasks 8–15 are frontend. Backend first means the API contracts exist before the UI consumes them.
2. Do not skip the failing-test step — it confirms tests actually exercise new code.
3. After tasks involving prompt/router changes, restart the backend (`uvicorn` doesn't reload prompt module).
4. The browser must run from `C:\hydrowatch\` (not OneDrive) due to Turbopack Cyrillic-path bug.
5. If a task says "smoke test in browser" — do it via Chrome MCP and screenshot. Don't claim "should work".
