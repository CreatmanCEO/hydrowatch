# HydroWatch Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a web application that monitors groundwater wells on an interactive map with an AI assistant that understands the user's map context (viewport, layers, selected well) and detects hydrodynamic anomalies (depression cones, debit decline, well interference).

**Architecture:** FastAPI backend with MCP-style tool calling via LiteLLM/Instructor (Gemini 2.5 Flash), SSE streaming, Pydantic-validated structured output. Next.js 15 frontend with MapLibre map (react-map-gl), Zustand state management, and a chat panel consuming SSE. Synthetic data generator produces realistic Abu Dhabi groundwater well data with injected anomalies. Eval module uses Gemini Batch API to compare model quality with analytical metrics.

**Tech Stack:**
- Backend: Python 3.12, FastAPI, LiteLLM, Instructor, Langfuse, DeepEval, Pydantic v2, SQLAlchemy 2.0 (async), Alembic, asyncpg, numpy, scipy, pandas, geopandas, shapely, adtk
- Database: PostgreSQL 16 + PostGIS 3.4 (Docker) — wells geometry, observations, anomalies, chat history, eval metrics
- Frontend: Next.js 15, TypeScript, React, react-map-gl, MapLibre GL JS, Zustand, @turf/circle, @microsoft/fetch-event-source, Tailwind CSS
- LLM Pool A (simple/medium): Gemini 2.5 Flash ↔ Cerebras Llama 3.3 70B (mutual fallback via LiteLLM)
- LLM Pool B (complex): Anthropic Haiku 4.5 (default) → Sonnet 4.5 (upgrade for reasoning)
- Eval: Gemini Batch API (50% discount)
- Map tiles: OpenFreeMap (free, no API key)
- Deploy: Docker Compose (localhost demo)

**Repository:** https://github.com/CreatmanCEO/hydrowatch

---

## CONTEXT FOR THE IMPLEMENTING ENGINEER

### What is this project?

A demo/portfolio project for a job interview (LLM Engineer position at GetMeGit). The company builds an AI assistant for a hydrology/geospatial web platform for the UAE government (Environment Agency Abu Dhabi — Makhazin Al Khayr project: 315 groundwater wells, AI-powered monitoring).

This demo replicates the core functionality at small scale: 25-30 synthetic wells, AI assistant that understands map context, detects anomalies, validates CSV data.

### Why these specific technologies?

Every technology choice maps to a job vacancy requirement:
- FastAPI + Pydantic + asyncio → core backend requirement
- MCP-style tool calling → "design MCP tools or similar tool-calling interfaces"
- Context bridge (viewport → LLM) → "pass application state to LLM including region, zoom, layers"
- Structured JSON output → "strictly structured JSON responses for predictable frontend rendering"
- SSE streaming → "real-time interaction via WebSocket and/or SSE"
- React + TypeScript + Zustand → "React, TypeScript, state management patterns"
- MapLibre + GeoJSON → "GeoJSON, geospatial UI context, bounding boxes, layers, viewport"
- CSV + Pandas → "CSV file processing, validation, metadata-based processing"
- Gemini Batch API + metrics → interviewer specifically asked to study "OpenAI batches" and "analytical metrics for model downgrading"
- Langfuse + DeepEval → "observability, testing, production-readiness"

### Hydrogeological context

The project owner (Nikolay) has 14 years of professional hydrogeology experience. The data generator should produce REALISTIC parameters for Abu Dhabi aquifers:

- Well depths: 60-350m (Dammam limestone 80-200m, Umm Er Radhuma 150-350m)
- Static water levels: 20-80m below ground surface
- Flow rates (debit): 2-30 L/s (typical 5-15)
- TDS: 2,000-8,000 mg/L (brackish water, freshwater lenses mostly depleted)
- pH: 7.0-8.5, Chlorides: 300-5,000 mg/L, Temperature: 28-38°C
- Coordinates: WGS84, Abu Dhabi area (24.2-24.6°N, 54.3-55.8°E)
- Transmissivity: 50-2,000 m²/day, Storativity: 0.001-0.01

Depression cone calculation: Theis equation via `scipy.special.exp1`. Well interference: superposition principle.

### Project structure (target)

```
hydrowatch/
├── backend/
│   ├── main.py                   # FastAPI app, SSE endpoint, CORS
│   ├── config.py                 # Pydantic BaseSettings (.env)
│   ├── models/
│   │   ├── __init__.py
│   │   ├── schemas.py            # Pydantic: Well, Anomaly, MapContext, ToolResult, etc.
│   │   ├── tool_schemas.py       # Tool definitions (JSON Schema for LLM)
│   │   └── database.py           # SQLAlchemy ORM models (wells, observations, etc.)
│   ├── db/
│   │   ├── __init__.py
│   │   ├── session.py            # async engine + session factory
│   │   ├── seed.py               # seed DB from generated GeoJSON/CSV
│   │   └── migrations/
│   │       ├── env.py            # Alembic async config
│   │       └── versions/         # migration files
│   ├── services/
│   │   ├── __init__.py
│   │   ├── llm_router.py         # LiteLLM + Instructor, model routing
│   │   ├── context_bridge.py     # MapContext → system prompt
│   │   ├── tool_executor.py      # Execute tools safely (permissions, validation)
│   │   ├── csv_validator.py      # Pandas CSV validation
│   │   └── anomaly_detector.py   # Depression cones, debit decline, interference
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── validate_csv.py       # Tool: validate uploaded CSV
│   │   ├── query_wells.py        # Tool: query wells by bbox/filters
│   │   ├── detect_anomalies.py   # Tool: run anomaly detection
│   │   ├── get_well_history.py   # Tool: get time series for a well
│   │   └── get_region_stats.py   # Tool: aggregate stats for viewport
│   ├── eval/
│   │   ├── batch_runner.py       # Gemini Batch API pipeline
│   │   ├── metrics.py            # accuracy, schema_compliance, latency, cost
│   │   └── eval_dataset.jsonl    # Test cases
│   ├── data_generator/
│   │   ├── generate_wells.py     # Generate 25-30 wells as GeoJSON
│   │   ├── generate_timeseries.py# Generate time series with anomalies
│   │   └── hydro_models.py       # Theis equation, superposition
│   ├── tests/
│   │   ├── test_anomaly_detector.py
│   │   ├── test_csv_validator.py
│   │   ├── test_tool_executor.py
│   │   └── test_schemas.py
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx
│   │   │   ├── page.tsx
│   │   │   └── api/              # Next.js API routes (proxy to backend)
│   │   ├── components/
│   │   │   ├── Map/
│   │   │   │   ├── WellsMap.tsx        # Main map component
│   │   │   │   ├── WellPopup.tsx       # Well info popup
│   │   │   │   ├── DepressionConeLayer.tsx
│   │   │   │   ├── InterferenceLayer.tsx
│   │   │   │   └── LayerControls.tsx
│   │   │   ├── Chat/
│   │   │   │   ├── ChatPanel.tsx       # Chat with SSE streaming
│   │   │   │   ├── MessageBubble.tsx
│   │   │   │   ├── AnomalyCard.tsx     # Structured anomaly card
│   │   │   │   └── CSVUpload.tsx
│   │   │   └── Metrics/
│   │   │       └── MetricsPanel.tsx    # Eval metrics dashboard
│   │   ├── stores/
│   │   │   ├── mapStore.ts             # Zustand: viewport, layers, selection
│   │   │   └── chatStore.ts            # Zustand: messages, streaming state
│   │   ├── hooks/
│   │   │   └── useSSEChat.ts           # SSE streaming hook
│   │   ├── lib/
│   │   │   ├── contextBridge.ts        # Build map context for API
│   │   │   └── api.ts                  # API client
│   │   └── types/
│   │       └── index.ts                # Shared types
│   ├── public/
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   └── next.config.ts
├── data/                          # Generated data (gitignored except samples)
│   ├── wells.geojson
│   └── observations/
│       └── *.csv
├── docker-compose.yml
├── .env.example
├── .gitignore
├── CLAUDE.md                      # Instructions for Claude Code implementing this
└── README.md
```

---

## IMPLEMENTATION TASKS

### Phase 1: Project Setup & Data Generator (foundation)

---

### Task 1: Project scaffolding and configuration

**Files:**
- Create: `backend/config.py`
- Create: `backend/requirements.txt`
- Create: `backend/.env.example`
- Create: `.gitignore`
- Create: `CLAUDE.md`
- Create: `.env.example`

**Step 1: Create .gitignore**

```gitignore
# Python
__pycache__/
*.pyc
.venv/
venv/
*.egg-info/

# Node
node_modules/
.next/
out/

# Environment
.env
.env.local

# Data (keep samples)
data/observations/*.csv
!data/observations/.gitkeep

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db
```

**Step 2: Create backend/requirements.txt**

```
fastapi==0.115.12
uvicorn[standard]==0.34.2
pydantic==2.11.3
pydantic-settings==2.9.1
litellm==1.83.10
instructor[google-genai]==1.15.1
langfuse==4.3.1
deepeval==3.9.7
sqlalchemy[asyncio]==2.0.40
alembic==1.15.2
asyncpg==0.30.0
geoalchemy2==0.17.1
numpy==2.2.5
scipy==1.15.3
pandas==2.2.3
geopandas==1.0.1
shapely==2.1.0
pyproj==3.7.1
adtk==0.6.2
statsmodels==0.14.4
folium==0.19.5
python-multipart==0.0.20
```

**Step 3: Create backend/config.py**

```python
"""Application configuration via environment variables."""
from pydantic_settings import BaseSettings
from pydantic import SecretStr, Field


class Settings(BaseSettings):
    # LLM Provider Keys
    gemini_api_key: SecretStr
    cerebras_api_key: SecretStr
    anthropic_api_key: SecretStr

    # Model routing — Pool A (simple/medium, mutual fallback)
    model_pool_a_primary: str = "gemini/gemini-2.5-flash"
    model_pool_a_fallback: str = "cerebras/llama-3.3-70b"

    # Model routing — Pool B (complex tasks)
    model_pool_b_default: str = "anthropic/claude-haiku-4-5-20251001"
    model_pool_b_complex: str = "anthropic/claude-sonnet-4-5-20250514"

    llm_temperature: float = 0.1

    # Database
    database_url: str = "postgresql+asyncpg://hydrowatch:hydrowatch_dev@localhost:5432/hydrowatch"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: list[str] = ["http://localhost:3000"]

    # Data
    data_dir: str = "./data"
    max_csv_size_mb: int = 10

    # Langfuse (optional)
    langfuse_public_key: str = ""
    langfuse_secret_key: SecretStr = SecretStr("")
    langfuse_host: str = "http://localhost:3001"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


def get_settings() -> Settings:
    return Settings()
```

**Step 4: Create .env.example**

```bash
GEMINI_API_KEY=your-gemini-api-key-here
DEFAULT_MODEL=gemini/gemini-2.5-flash
FALLBACK_MODEL=gemini/gemini-2.5-pro
LLM_TEMPERATURE=0.1
CORS_ORIGINS=["http://localhost:3000"]
DATA_DIR=./data
```

**Step 5: Create CLAUDE.md**

```markdown
# HydroWatch — AI Groundwater Monitoring

## Project Overview
AI-powered groundwater well monitoring with LLM assistant.
FastAPI backend + Next.js frontend + MapLibre map.

## Architecture
- Backend: FastAPI + LiteLLM (Gemini) + Instructor + Pydantic
- Frontend: Next.js 15 + React + TypeScript + react-map-gl + Zustand
- Data: Synthetic wells (GeoJSON) + time series (CSV)

## Key Patterns
1. Context Bridge: frontend sends viewport/layers/selection → backend builds LLM prompt
2. Tool Calling: LLM chooses which tool to call (validate_csv, detect_anomalies, etc.)
3. Structured Output: all LLM responses → Pydantic models → JSON cards for frontend
4. SSE Streaming: /api/chat/stream endpoint streams LLM response tokens

## Commands
- Backend: `cd backend && uvicorn main:app --reload --port 8000`
- Frontend: `cd frontend && npm run dev`
- Generate data: `cd backend && python -m data_generator.generate_wells`
- Run tests: `cd backend && pytest tests/ -v`

## Implementation Plan
See: docs/plans/2026-04-19-hydrowatch-implementation.md
```

**Step 6: Commit**

```bash
git add -A
git commit -m "chore: project scaffolding — config, requirements, gitignore, CLAUDE.md"
git push -u origin main
```

---

### Task 2: Hydro models — Theis equation and superposition

**Files:**
- Create: `backend/data_generator/__init__.py`
- Create: `backend/data_generator/hydro_models.py`
- Create: `backend/tests/__init__.py`
- Create: `backend/tests/test_hydro_models.py`

**Step 1: Write tests for Theis drawdown**

```python
# backend/tests/test_hydro_models.py
"""Tests for hydrogeological models."""
import numpy as np
import pytest
from data_generator.hydro_models import theis_drawdown, superposition_drawdown, PumpingWell


class TestTheisDrawdown:
    """Theis equation correctness tests."""

    def test_drawdown_decreases_with_distance(self):
        """Closer to well = more drawdown."""
        Q, T, S, t = 864.0, 500.0, 0.005, 1.0  # 10 L/s, 1 day
        s_near = theis_drawdown(Q, T, S, r=10, t=t)
        s_far = theis_drawdown(Q, T, S, r=500, t=t)
        assert s_near > s_far > 0

    def test_drawdown_increases_with_time(self):
        """Longer pumping = more drawdown."""
        Q, T, S, r = 864.0, 500.0, 0.005, 100.0
        s_1day = theis_drawdown(Q, T, S, r, t=1.0)
        s_30day = theis_drawdown(Q, T, S, r, t=30.0)
        assert s_30day > s_1day

    def test_drawdown_increases_with_rate(self):
        """Higher pumping rate = more drawdown."""
        T, S, r, t = 500.0, 0.005, 100.0, 1.0
        s_low = theis_drawdown(Q=432, T=T, S=S, r=r, t=t)   # 5 L/s
        s_high = theis_drawdown(Q=1728, T=T, S=S, r=r, t=t)  # 20 L/s
        assert s_high > s_low

    def test_zero_time_returns_zero(self):
        assert theis_drawdown(864, 500, 0.005, 100, t=0) == 0.0

    def test_realistic_abu_dhabi_values(self):
        """Drawdown should be in realistic range for Abu Dhabi wells."""
        Q = 10 * 86.4  # 10 L/s → m³/day
        T = 500         # m²/day (limestone)
        S = 0.005
        s = theis_drawdown(Q, T, S, r=50, t=30)
        assert 1.0 < s < 20.0  # realistic range


class TestSuperposition:
    """Superposition of multiple wells."""

    def test_two_wells_more_than_one(self):
        wells = [
            PumpingWell(id="W1", x=0, y=0, Q=864, T=500, S=0.005, start_time=0),
            PumpingWell(id="W2", x=200, y=0, Q=864, T=500, S=0.005, start_time=0),
        ]
        s_both = superposition_drawdown(wells, obs_x=100, obs_y=0, t=10)
        s_one = superposition_drawdown(wells[:1], obs_x=100, obs_y=0, t=10)
        assert s_both > s_one

    def test_distant_well_negligible_effect(self):
        wells = [
            PumpingWell(id="W1", x=0, y=0, Q=864, T=500, S=0.005, start_time=0),
            PumpingWell(id="W2", x=50000, y=0, Q=864, T=500, S=0.005, start_time=0),
        ]
        s = superposition_drawdown(wells, obs_x=0, obs_y=0, t=1)
        s_alone = superposition_drawdown(wells[:1], obs_x=0, obs_y=0, t=1)
        assert abs(s - s_alone) < 0.01  # distant well adds < 1cm
```

**Step 2: Run tests to verify they fail**

```bash
cd backend && python -m pytest tests/test_hydro_models.py -v
# Expected: ModuleNotFoundError: No module named 'data_generator'
```

**Step 3: Implement hydro_models.py**

```python
# backend/data_generator/hydro_models.py
"""Analytical groundwater models: Theis equation, superposition."""
from dataclasses import dataclass
import numpy as np
from scipy.special import exp1


@dataclass
class PumpingWell:
    """A pumping well with hydraulic parameters."""
    id: str
    x: float            # UTM easting, meters
    y: float            # UTM northing, meters
    Q: float            # pumping rate, m³/day
    T: float            # transmissivity, m²/day
    S: float            # storativity (dimensionless)
    start_time: float   # pumping start time, days


def theis_drawdown(Q: float, T: float, S: float, r: float, t: float) -> float:
    """
    Calculate drawdown using Theis equation.

    Args:
        Q: pumping rate (m³/day)
        T: transmissivity (m²/day)
        S: storativity
        r: distance from well (m)
        t: time since pumping started (days)

    Returns:
        Drawdown in meters.
    """
    if t <= 0 or r <= 0:
        return 0.0
    u = (r**2 * S) / (4 * T * t)
    W_u = float(exp1(u))
    return (Q / (4 * np.pi * T)) * W_u


def superposition_drawdown(
    wells: list[PumpingWell],
    obs_x: float,
    obs_y: float,
    t: float,
) -> float:
    """
    Total drawdown at observation point from multiple pumping wells.
    Uses superposition principle (sum of individual Theis drawdowns).
    """
    total = 0.0
    for w in wells:
        dt = t - w.start_time
        if dt <= 0:
            continue
        r = np.sqrt((obs_x - w.x) ** 2 + (obs_y - w.y) ** 2)
        r = max(r, 0.3)  # well radius
        total += theis_drawdown(w.Q, w.T, w.S, r, dt)
    return total


def generate_drawdown_grid(
    wells: list[PumpingWell],
    center_x: float,
    center_y: float,
    extent: float = 2000,
    grid_size: int = 50,
    t: float = 30,
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Generate 2D drawdown grid around wells for visualization."""
    x = np.linspace(center_x - extent, center_x + extent, grid_size)
    y = np.linspace(center_y - extent, center_y + extent, grid_size)
    X, Y = np.meshgrid(x, y)
    Z = np.zeros_like(X)

    for i in range(grid_size):
        for j in range(grid_size):
            Z[i, j] = superposition_drawdown(wells, X[i, j], Y[i, j], t)

    return X, Y, Z
```

**Step 4: Run tests**

```bash
cd backend && python -m pytest tests/test_hydro_models.py -v
# Expected: all PASS
```

**Step 5: Commit**

```bash
git add backend/data_generator/ backend/tests/
git commit -m "feat: Theis equation and superposition — core hydro models"
git push
```

---

### Task 3: Well GeoJSON generator

**Files:**
- Create: `backend/data_generator/generate_wells.py`
- Create: `backend/tests/test_generate_wells.py`

**Step 1: Write tests**

```python
# backend/tests/test_generate_wells.py
"""Tests for well GeoJSON generation."""
import json
import pytest
from data_generator.generate_wells import generate_wells_geojson


class TestWellGeneration:

    def test_generates_correct_count(self):
        geojson = generate_wells_geojson(n_wells=25)
        assert len(geojson["features"]) == 25

    def test_valid_geojson_structure(self):
        geojson = generate_wells_geojson(n_wells=5)
        assert geojson["type"] == "FeatureCollection"
        for f in geojson["features"]:
            assert f["type"] == "Feature"
            assert f["geometry"]["type"] == "Point"
            assert len(f["geometry"]["coordinates"]) == 2

    def test_coordinates_in_abu_dhabi_region(self):
        geojson = generate_wells_geojson(n_wells=10)
        for f in geojson["features"]:
            lon, lat = f["geometry"]["coordinates"]
            assert 54.0 < lon < 56.0, f"Longitude {lon} outside Abu Dhabi"
            assert 24.0 < lat < 25.0, f"Latitude {lat} outside Abu Dhabi"

    def test_realistic_well_properties(self):
        geojson = generate_wells_geojson(n_wells=10)
        for f in geojson["features"]:
            p = f["properties"]
            assert 20 < p["well_depth_m"] < 500
            assert 500 < p["last_tds_mgl"] < 15000
            assert 6.0 < p["last_ph"] < 9.5
            assert p["status"] in ("active", "inactive", "maintenance")
            assert "id" in p
            assert "cluster_id" in p

    def test_wells_grouped_in_clusters(self):
        geojson = generate_wells_geojson(n_wells=20, n_clusters=4)
        cluster_ids = {f["properties"]["cluster_id"] for f in geojson["features"]}
        assert len(cluster_ids) >= 3  # at least 3 clusters used

    def test_serializable_to_json(self):
        geojson = generate_wells_geojson(n_wells=5)
        json_str = json.dumps(geojson, ensure_ascii=False)
        assert len(json_str) > 100
```

**Step 2: Run tests — expected FAIL**

```bash
cd backend && python -m pytest tests/test_generate_wells.py -v
```

**Step 3: Implement generate_wells.py**

Implement well generator that creates a GeoJSON FeatureCollection with 25-30 wells clustered around Abu Dhabi locations (Al Wathba, Mussafah, Sweihan, Al Khatim). Each well has realistic properties: depth, aquifer type (Dammam/Umm Er Radhuma/sandstone/alluvial), TDS, pH, chlorides, flow rate, static water level, status, operator, installation date. Use numpy.random with seed for reproducibility.

Reference the comprehensive code from the research document at: `docs/plans/2026-04-19-hydrowatch-implementation.md` (this file), hydrodata agent results.

**Step 4: Run tests — expected PASS**

**Step 5: Generate sample data and commit**

```bash
cd backend && python -m data_generator.generate_wells
# Should create data/wells.geojson
git add backend/data_generator/generate_wells.py backend/tests/test_generate_wells.py data/wells.geojson
git commit -m "feat: synthetic well GeoJSON generator — 25 Abu Dhabi wells in 4 clusters"
git push
```

---

### Task 4: Time series generator with anomaly injection

**Files:**
- Create: `backend/data_generator/generate_timeseries.py`
- Create: `backend/tests/test_generate_timeseries.py`

**Step 1: Write tests**

```python
# backend/tests/test_generate_timeseries.py
"""Tests for time series generation with anomalies."""
import pandas as pd
import numpy as np
import pytest
from data_generator.generate_timeseries import (
    generate_well_timeseries,
    AnomalyInjector,
    generate_all_timeseries,
)


class TestTimeSeriesGeneration:

    def test_correct_columns(self):
        df, _ = generate_well_timeseries("W-001", days=30)
        expected_cols = {"timestamp", "well_id", "debit_ls", "tds_mgl",
                         "ph", "chloride_mgl", "water_level_m", "temperature_c"}
        assert expected_cols.issubset(set(df.columns))

    def test_correct_length(self):
        df, _ = generate_well_timeseries("W-001", days=365, measurements_per_day=4)
        assert len(df) == 365 * 4

    def test_values_in_realistic_ranges(self):
        df, _ = generate_well_timeseries("W-001", days=90)
        assert df["debit_ls"].min() >= 0
        assert 500 < df["tds_mgl"].mean() < 15000
        assert 6.0 < df["ph"].mean() < 9.5
        assert df["water_level_m"].min() > 0

    def test_anomaly_injection_debit_decline(self):
        ts = np.full(1000, 10.0)
        result = AnomalyInjector.gradual_decline(ts, start_idx=200, duration=300, decline_pct=0.4)
        assert result[100] == pytest.approx(10.0, abs=0.1)  # before anomaly
        assert result[800] == pytest.approx(6.0, abs=0.5)   # after: 40% decline

    def test_anomaly_log_populated(self):
        _, anomaly_log = generate_well_timeseries("W-001", days=365, inject_anomalies=True)
        assert len(anomaly_log) > 0
        assert all("type" in a for a in anomaly_log)


class TestBatchGeneration:

    def test_generates_for_all_wells(self):
        well_ids = ["W-001", "W-002", "W-003"]
        result = generate_all_timeseries(well_ids, days=30)
        assert len(result) == 3
        assert all(wid in result for wid in well_ids)
```

**Step 2: Run — FAIL**

**Step 3: Implement**

Create `generate_timeseries.py` with:
- `AnomalyInjector` class: gradual_decline, sudden_spike, sensor_fault methods
- `generate_well_timeseries()`: base values + seasonal + diurnal + AR(1) noise + anomalies
- `generate_all_timeseries()`: batch generation for all wells
- Anomaly log with timestamps and types (ground truth for detection)
- Export to CSV per well

Use the comprehensive code from research (hydro data generation agent results).

**Step 4: Run — PASS**

**Step 5: Generate data and commit**

```bash
cd backend && python -c "
from data_generator.generate_wells import generate_wells_geojson
from data_generator.generate_timeseries import generate_all_timeseries
import json

geojson = generate_wells_geojson(25)
well_ids = [f['properties']['id'] for f in geojson['features']]
data = generate_all_timeseries(well_ids, days=365)
print(f'Generated {len(data)} time series')
"
git add backend/data_generator/generate_timeseries.py backend/tests/test_generate_timeseries.py
git commit -m "feat: time series generator with anomaly injection — debit decline, TDS spike, sensor fault"
git push
```

---

### Phase 1.5: Database (PostgreSQL + PostGIS)

---

### Task 5: PostgreSQL + PostGIS + SQLAlchemy models + Alembic

**Files:**
- Create: `backend/models/database.py`
- Create: `backend/db/__init__.py`
- Create: `backend/db/session.py`
- Create: `backend/db/seed.py`
- Create: `backend/db/migrations/env.py`
- Create: `backend/tests/test_database.py`
- Modify: `backend/config.py` (add database_url)
- Modify: `docker-compose.yml` (add postgres service)

**Step 1: Add PostgreSQL + PostGIS to docker-compose.yml**

```yaml
services:
  postgres:
    image: postgis/postgis:16-3.4-alpine
    environment:
      POSTGRES_DB: hydrowatch
      POSTGRES_USER: hydrowatch
      POSTGRES_PASSWORD: hydrowatch_dev
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U hydrowatch"]
      interval: 5s
      timeout: 3s
      retries: 5

volumes:
  pgdata:
```

**Step 2: Create backend/db/session.py**

```python
"""Async SQLAlchemy session factory."""
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from config import get_settings

settings = get_settings()

engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncSession:
    """FastAPI dependency for database sessions."""
    async with async_session() as session:
        yield session
```

**Step 3: Create backend/models/database.py — SQLAlchemy ORM models**

```python
"""SQLAlchemy ORM models with PostGIS geometry."""
from datetime import datetime
from uuid import uuid4
from sqlalchemy import (
    String, Float, Integer, DateTime, Boolean, Text, JSON,
    ForeignKey, Index, func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
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
    status: Mapped[str] = mapped_column(String(20), index=True)  # active/inactive/maintenance
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
    properties: Mapped[dict] = mapped_column(JSONB, default=dict)  # extra properties

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

    anomaly_type: Mapped[str] = mapped_column(String(30))  # debit_decline, depression_cone, interference
    severity: Mapped[str] = mapped_column(String(10))       # low, medium, high, critical
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
    role: Mapped[str] = mapped_column(String(10))  # user, assistant
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
    pool: Mapped[str] = mapped_column(String(10))  # pool-a, pool-b
    latency_ms: Mapped[int] = mapped_column(Integer)
    tokens_in: Mapped[int] = mapped_column(Integer)
    tokens_out: Mapped[int] = mapped_column(Integer)
    cost_usd: Mapped[float] = mapped_column(Float)
    schema_valid: Mapped[bool] = mapped_column(Boolean)
    was_fallback: Mapped[bool] = mapped_column(Boolean, default=False)
```

**Step 4: Create backend/db/seed.py**

```python
"""Seed database from generated GeoJSON and CSV files."""
import json
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from geoalchemy2.shape import from_shape
from shapely.geometry import shape
from models.database import Well, Observation


async def seed_wells(session: AsyncSession, geojson_path: str):
    """Load wells from GeoJSON into database."""
    with open(geojson_path) as f:
        geojson = json.load(f)

    for feature in geojson["features"]:
        props = feature["properties"]
        geom = shape(feature["geometry"])

        well = Well(
            id=props["id"],
            name=props["name_en"],
            cluster_id=props["cluster_id"],
            cluster_name=props["cluster_name"],
            geometry=from_shape(geom, srid=4326),
            well_depth_m=props["well_depth_m"],
            aquifer_type=props["aquifer_type"],
            casing_diameter_mm=props["casing_diameter_mm"],
            ground_elevation_m=props["ground_elevation_m"],
            transmissivity_m2d=props["transmissivity_m2d"],
            storativity=props["storativity"],
            status=props["status"],
            current_yield_ls=props["current_yield_ls"],
            static_water_level_m=props["static_water_level_m"],
            last_tds_mgl=props["last_tds_mgl"],
            last_ph=props["last_ph"],
            last_chloride_mgl=props["last_chloride_mgl"],
            last_temperature_c=props["last_temperature_c"],
            operator=props["operator"],
            installation_date=props["installation_date"],
            properties=props,
        )
        session.add(well)

    await session.commit()


async def seed_observations(session: AsyncSession, csv_dir: str, well_ids: list[str]):
    """Load time series CSV files into database."""
    for well_id in well_ids:
        csv_path = f"{csv_dir}/{well_id}.csv"
        df = pd.read_csv(csv_path, parse_dates=["timestamp"])

        observations = [
            Observation(
                well_id=row["well_id"],
                timestamp=row["timestamp"],
                debit_ls=row["debit_ls"],
                tds_mgl=row["tds_mgl"],
                ph=row["ph"],
                chloride_mgl=row["chloride_mgl"],
                water_level_m=row["water_level_m"],
                temperature_c=row["temperature_c"],
            )
            for _, row in df.iterrows()
        ]
        session.add_all(observations)

    await session.commit()
```

**Step 5: Initialize Alembic**

```bash
cd backend
alembic init db/migrations
# Edit db/migrations/env.py for async support
# Edit alembic.ini: sqlalchemy.url = postgresql+asyncpg://hydrowatch:hydrowatch_dev@localhost:5432/hydrowatch
alembic revision --autogenerate -m "initial schema — wells, observations, anomalies, chat, eval"
alembic upgrade head
```

**Step 6: Write tests**

Test that Well model can be created, queried by bbox (PostGIS ST_Within), and that seed populates data correctly.

**Step 7: Seed database**

```bash
docker compose up -d postgres          # start PostgreSQL
alembic upgrade head                    # create tables
python -m db.seed                       # load generated data
```

**Step 8: Commit**

```bash
git add backend/models/database.py backend/db/ docker-compose.yml
git commit -m "feat: PostgreSQL + PostGIS — ORM models, async session, Alembic migrations, seed script"
git push
```

---

### Phase 2: Backend — Pydantic Schemas, Tools, LLM Integration

---

### Task 5: Pydantic schemas — all data models

**Files:**
- Create: `backend/models/__init__.py`
- Create: `backend/models/schemas.py`
- Create: `backend/tests/test_schemas.py`

**Step 1: Write tests**

```python
# backend/tests/test_schemas.py
"""Tests for Pydantic schemas."""
import pytest
from models.schemas import (
    MapContext, WellInfo, AnomalyCard, ValidationResult,
    ChatRequest, ChatResponse, ToolCall, ToolResult,
)


class TestMapContext:
    def test_valid_context(self):
        ctx = MapContext(
            center_lat=24.45, center_lng=54.65, zoom=12,
            bbox=[54.61, 24.42, 54.69, 24.48],
            active_layers=["wells", "depression_cones"],
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


class TestAnomalyCard:
    def test_anomaly_card_structure(self):
        card = AnomalyCard(
            type="anomaly_card",
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
```

**Step 2: Run — FAIL**

**Step 3: Implement schemas.py**

```python
# backend/models/schemas.py
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


# --- Structured Output Cards (LLM → Frontend) ---

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


class ChatResponse(BaseModel):
    """Full chat response (non-streaming)."""
    message: str
    cards: list[AnomalyCard | ValidationResult | RegionStats | WellHistory] = Field(default_factory=list)
    tool_calls: list[ToolCall] = Field(default_factory=list)
    model_used: str = ""
    latency_ms: int = 0
    tokens_used: int = 0
```

**Step 4: Run — PASS**

**Step 5: Commit**

```bash
git add backend/models/
git commit -m "feat: Pydantic schemas — MapContext, AnomalyCard, ValidationResult, ChatRequest/Response"
git push
```

---

### Task 6: Tool implementations (validate_csv, query_wells, detect_anomalies, get_well_history, get_region_stats)

**Files:**
- Create: `backend/tools/__init__.py`
- Create: `backend/tools/validate_csv.py`
- Create: `backend/tools/query_wells.py`
- Create: `backend/tools/detect_anomalies.py`
- Create: `backend/tools/get_well_history.py`
- Create: `backend/tools/get_region_stats.py`
- Create: `backend/tests/test_tools.py`

Each tool should:
1. Accept typed parameters (Pydantic)
2. Load data from `data/` directory (GeoJSON + CSV files)
3. Return a structured result (Pydantic model from schemas.py)
4. Be READ-ONLY (no writes, no deletions — safe execution)

Key implementations:
- `validate_csv`: load CSV with pandas, check columns, types, ranges, return ValidationResult
- `query_wells`: load wells.geojson, filter by bbox/status/cluster, return list[WellInfo]
- `detect_anomalies`: load time series, use adtk LevelShiftAD + custom debit decline detector, return list[AnomalyCard]
- `get_well_history`: load CSV for well, return WellHistory with trend analysis (scipy linregress)
- `get_region_stats`: aggregate stats for wells in bbox, return RegionStats

Write tests first (TDD), then implement.

**Commit:** `"feat: MCP-style tools — validate_csv, query_wells, detect_anomalies, get_history, region_stats"`

---

### Task 7: Tool registry and safe executor

**Files:**
- Create: `backend/models/tool_schemas.py`
- Create: `backend/services/tool_executor.py`
- Create: `backend/tests/test_tool_executor.py`

`tool_schemas.py` defines JSON Schema for each tool (what LLM sees):

```python
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "validate_csv",
            "description": "Validate an uploaded CSV file with groundwater observations. Checks columns, data types, value ranges, and metadata consistency.",
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Path to the CSV file"},
                    "expected_columns": {
                        "type": "array", "items": {"type": "string"},
                        "description": "Expected column names",
                        "default": ["timestamp", "well_id", "debit_ls", "tds_mgl", "ph", "water_level_m"]
                    },
                },
                "required": ["file_path"],
            },
        },
    },
    # ... same structure for query_wells, detect_anomalies, get_well_history, get_region_stats
]
```

`tool_executor.py` — safe execution layer:
- Maps tool name → function
- Validates parameters with Pydantic before execution
- Catches exceptions, returns ToolResult with error
- Enforces READ-ONLY (no file writes allowed)
- Logs execution to Langfuse

**Commit:** `"feat: tool registry with JSON Schema + safe executor with permissions and validation"`

---

### Task 8: LLM router and context bridge

**Files:**
- Create: `backend/services/llm_router.py`
- Create: `backend/services/context_bridge.py`
- Create: `backend/tests/test_context_bridge.py`

`llm_router.py`:
- Two model pools via LiteLLM Router:
  - **Pool A** (simple/medium tasks): Gemini 2.5 Flash (primary) ↔ Cerebras Llama 3.3 70B (fallback). Mutual fallback — if one is down, the other takes over.
  - **Pool B** (complex tasks): Anthropic Haiku 4.5 (default) → Sonnet 4.5 (upgrade for deep reasoning/interpretation).
- Task complexity classifier: determines which pool to use based on task type
- Instructor client for structured output (works with all providers via LiteLLM)
- Async streaming via `litellm.acompletion(stream=True)`
- LiteLLM Router config:

```python
from litellm import Router

router = Router(model_list=[
    # Pool A — simple/medium (mutual fallback)
    {"model_name": "pool-a", "litellm_params": {"model": "gemini/gemini-2.5-flash", "api_key": settings.gemini_api_key}},
    {"model_name": "pool-a", "litellm_params": {"model": "cerebras/llama-3.3-70b", "api_key": settings.cerebras_api_key}},
    # Pool B — complex
    {"model_name": "pool-b", "litellm_params": {"model": "anthropic/claude-haiku-4-5-20251001", "api_key": settings.anthropic_api_key}},
    {"model_name": "pool-b-upgrade", "litellm_params": {"model": "anthropic/claude-sonnet-4-5-20250514", "api_key": settings.anthropic_api_key}},
])

# Usage:
# Simple task → router.acompletion(model="pool-a", ...)
# Complex task → router.acompletion(model="pool-b", ...)
# Deep reasoning → router.acompletion(model="pool-b-upgrade", ...)
```

- Task routing logic:

```python
TASK_ROUTING = {
    "validate_csv":       "pool-a",   # structured, rule-based
    "query_wells":        "pool-a",   # data retrieval
    "get_region_stats":   "pool-a",   # aggregation
    "get_well_history":   "pool-a",   # data + simple trend
    "detect_anomalies":   "pool-b",   # needs reasoning
    "interpret_anomaly":  "pool-b",   # domain knowledge
    "calibration_advice": "pool-b-upgrade",  # complex reasoning
    "general_question":   "pool-b",   # default for unknown
}
```

`context_bridge.py`:
- Takes MapContext from frontend
- Builds system prompt section with current viewport, layers, selected well data
- If well selected → loads its properties and recent data
- Returns formatted string to inject into system prompt

```python
def build_context_prompt(map_context: MapContext, wells_data: dict) -> str:
    """Build context section for LLM system prompt."""
    lines = ["## Current Map State"]
    lines.append(f"- Region: center ({map_context.center_lat:.4f}, {map_context.center_lng:.4f}), zoom {map_context.zoom}")
    lines.append(f"- Visible area (bbox): {map_context.bbox}")
    lines.append(f"- Active layers: {', '.join(map_context.active_layers)}")

    if map_context.selected_well_id:
        well = wells_data.get(map_context.selected_well_id)
        if well:
            lines.append(f"\n## Selected Well: {well['name']}")
            lines.append(f"- Depth: {well['well_depth_m']}m, Aquifer: {well['aquifer_type']}")
            lines.append(f"- Current yield: {well['current_yield_ls']} L/s")
            lines.append(f"- TDS: {well['last_tds_mgl']} mg/L, pH: {well['last_ph']}")
    return "\n".join(lines)
```

**Commit:** `"feat: LLM router (2 pools: Gemini↔Cerebras + Anthropic Haiku/Sonnet) + context bridge"`

---

### Task 9.5: Prompt Engine — multi-level prompt architecture

**IMPORTANT: This task REPLACES the simple SYSTEM_PROMPT in llm_router.py with a proper prompt engineering system.**

**Problem with current approach:**
1. Single flat prompt "You are HydroWatch AI..." — no domain depth, LLM doesn't truly understand the project
2. Same prompt for all models — Gemini Flash, Cerebras Llama, and Anthropic Haiku/Sonnet have different strengths and need different instruction styles
3. No hierarchical context — LLM has no "memory" about the project, region, norms, history

**Solution: 3-level prompt hierarchy + model-specific adaptors + task-specific instructions**

**Files:**
- Create: `backend/services/prompt_engine.py`
- Create: `backend/prompts/` directory with prompt modules
- Create: `backend/prompts/base_role.py`
- Create: `backend/prompts/domain_knowledge.py`
- Create: `backend/prompts/model_adaptors.py`
- Create: `backend/prompts/task_instructions.py`
- Create: `backend/prompts/output_formats.py`
- Modify: `backend/services/llm_router.py` — use PromptEngine instead of flat SYSTEM_PROMPT
- Create: `backend/tests/test_prompt_engine.py`

**Architecture:**

```
┌─────────────────────────────────────────────────────────────┐
│                    PROMPT ENGINE                             │
│                                                              │
│  Final prompt = Level 0 (base role)                         │
│               + Level 1 (domain knowledge)                  │
│               + Model adaptor (per provider)                │
│               + Task instructions (per task type)           │
│               + Output format (per response type)           │
│               + Level 2 (context bridge — runtime)          │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Level 0: BASE ROLE (always present, ~200 tokens)     │   │
│  │                                                      │   │
│  │ Identity, mission, core rules, safety constraints    │   │
│  │ "You are HydroWatch AI, a specialized groundwater    │   │
│  │  monitoring system for strategic water reserves..."   │   │
│  └──────────────────────────────────────────────────────┘   │
│                         │                                    │
│  ┌──────────────────────▼──────────────────────────────┐   │
│  │ Level 1: DOMAIN KNOWLEDGE (~500-800 tokens)         │   │
│  │                                                      │   │
│  │ Regional context:                                    │   │
│  │ - Abu Dhabi aquifer system (Dammam, Umm Er Radhuma) │   │
│  │ - Water quality norms (UAE drinking water standards) │   │
│  │ - Typical parameters and realistic ranges           │   │
│  │ - Known cluster locations and characteristics       │   │
│  │                                                      │   │
│  │ Operational context:                                 │   │
│  │ - Current well inventory (25 wells, 4 clusters)     │   │
│  │ - Known anomalies count and types                   │   │
│  │ - Monitoring frequency (4x/day)                     │   │
│  │                                                      │   │
│  │ This simulates what a fine-tuned model would "know" │   │
│  │ natively — we provide it as context instead          │   │
│  └──────────────────────────────────────────────────────┘   │
│                         │                                    │
│  ┌──────────────────────▼──────────────────────────────┐   │
│  │ MODEL ADAPTOR (per provider, ~100-200 tokens)       │   │
│  │                                                      │   │
│  │ gemini_flash:                                        │   │
│  │   - Concise instructions, explicit JSON examples     │   │
│  │   - "Respond in under 150 words unless detailed      │   │
│  │     analysis is requested"                           │   │
│  │                                                      │   │
│  │ cerebras_llama:                                      │   │
│  │   - Very explicit format instructions                │   │
│  │   - Simpler vocabulary in system prompt              │   │
│  │   - More few-shot examples for structured output     │   │
│  │                                                      │   │
│  │ anthropic_haiku:                                     │   │
│  │   - Permission for chain-of-thought reasoning        │   │
│  │   - "Think step by step before concluding"           │   │
│  │   - Domain-expert tone                               │   │
│  │                                                      │   │
│  │ anthropic_sonnet:                                    │   │
│  │   - Full reasoning freedom                           │   │
│  │   - "Provide comprehensive analysis with evidence"   │   │
│  │   - Permission for longer responses                  │   │
│  └──────────────────────────────────────────────────────┘   │
│                         │                                    │
│  ┌──────────────────────▼──────────────────────────────┐   │
│  │ TASK INSTRUCTIONS (per task type, ~100-300 tokens)   │   │
│  │                                                      │   │
│  │ validate_csv:                                        │   │
│  │   "Focus on data quality. Check units, ranges,       │   │
│  │    missing values. Flag but don't interpret."        │   │
│  │                                                      │   │
│  │ detect_anomalies:                                    │   │
│  │   "Analyze results critically. Consider: is this a   │   │
│  │    real anomaly or seasonal variation? Check          │   │
│  │    neighboring wells for corroboration."             │   │
│  │                                                      │   │
│  │ interpret_anomaly:                                   │   │
│  │   "Provide root cause analysis. Consider geological  │   │
│  │    factors, pumping history, interference. Give       │   │
│  │    actionable recommendations with priority."        │   │
│  │                                                      │   │
│  │ general_question:                                    │   │
│  │   "Answer based on available data and tools.         │   │
│  │    Always cite well IDs and specific values."        │   │
│  └──────────────────────────────────────────────────────┘   │
│                         │                                    │
│  ┌──────────────────────▼──────────────────────────────┐   │
│  │ OUTPUT FORMAT (per response type, ~50-100 tokens)    │   │
│  │                                                      │   │
│  │ text_response:                                       │   │
│  │   "Respond in markdown. Use well IDs. Include        │   │
│  │    specific values with units."                      │   │
│  │                                                      │   │
│  │ anomaly_card:                                        │   │
│  │   "Return JSON matching AnomalyCard schema:          │   │
│  │    {severity, well_id, anomaly_type, title, ...}"    │   │
│  │                                                      │   │
│  │ validation_card:                                     │   │
│  │   "Return JSON matching ValidationResult schema"     │   │
│  └──────────────────────────────────────────────────────┘   │
│                         │                                    │
│  ┌──────────────────────▼──────────────────────────────┐   │
│  │ Level 2: CONTEXT BRIDGE (runtime, variable tokens)  │   │
│  │                                                      │   │
│  │ ## Current Map State                                 │   │
│  │ - Center, zoom, bbox, layers, selected well          │   │
│  │ - (from context_bridge.py — already implemented)     │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

**Implementation:**

```python
# backend/services/prompt_engine.py

class PromptEngine:
    """Multi-level prompt assembly with model-specific adaptors."""

    def build(
        self,
        model_pool: str,          # "pool-a" | "pool-b" | "pool-b-upgrade"
        task_type: str,           # "validate_csv" | "detect_anomalies" | ...
        context_section: str,     # from context_bridge.py
        output_type: str = "text_response",
    ) -> str:
        """Assemble final system prompt from components."""
        parts = [
            self._get_base_role(),
            self._get_domain_knowledge(),
            self._get_model_adaptor(model_pool),
            self._get_task_instructions(task_type),
            self._get_output_format(output_type),
            context_section,
        ]
        return "\n\n".join(part for part in parts if part)
```

**Key design decisions:**

1. **Domain knowledge simulates fine-tuning.** In production they have custom fine-tuned models. We simulate this by injecting domain knowledge as context. On the interview say: "In production you'd fine-tune the model on this domain knowledge. For the demo I inject it as Level 1 context — same effect, faster iteration."

2. **Model adaptors account for provider differences.** Gemini Flash works best with concise, structured prompts. Anthropic Sonnet benefits from chain-of-thought permission. Llama needs more explicit format examples. Each gets tailored instructions.

3. **Task instructions prevent "general assistant" behavior.** When detecting anomalies, the model should think like a hydrogeologist. When validating CSV, it should think like a data engineer. Different mindsets for different tasks.

4. **Output formats ensure schema compliance.** Each response type has explicit JSON schema examples in the prompt, reducing structured output failures.

**Domain knowledge content (Level 1) should include:**

```markdown
## Abu Dhabi Aquifer System
- Dammam Formation: limestone, 80-200m depth, T=200-1200 m²/day, good water quality
- Umm Er Radhuma: deep limestone, 150-350m, T=100-800, often brackish
- Quaternary Sand: shallow, 30-80m, variable quality
- Alluvial: very shallow, 20-60m, limited yield

## Water Quality Standards (UAE)
- Drinking water TDS limit: 1,000 mg/L (most wells exceed this — brackish)
- Emergency supply TDS limit: 1,500 mg/L
- Chloride limit: 250 mg/L (drinking), 600 mg/L (emergency)
- pH acceptable range: 6.5-8.5
- Alert thresholds: TDS > 5,000, pH outside 7.0-8.5, debit decline > 15%

## Monitoring Network
- 25 wells in 4 clusters: Al Wathba, Mussafah, Sweihan, Al Khatim
- Measurement frequency: every 6 hours (4/day)
- Parameters: debit, TDS, pH, chlorides, water level, temperature
- Known issues: general aquifer depletion trend, seasonal TDS variation

## Anomaly Interpretation Guidelines
- Debit decline > 15%: possible clogging, aquifer depletion, or casing damage
- TDS spike > 50% above baseline: possible contamination or saltwater intrusion
- Sensor reading = 0 for > 5 consecutive readings: likely sensor malfunction
- Correlated drawdown in neighboring wells: interference — adjust pumping schedule
- Depression cone radius > 2km: excessive pumping, consider reducing rates
```

**Test: verify prompt assembly produces different prompts for different models/tasks.**

**Commit:** `"feat: prompt engine — 3-level hierarchy, model adaptors, task-specific instructions, domain knowledge"`

---

### Task 10: FastAPI main app with SSE streaming (was Task 9)

**Files:**
- Create: `backend/main.py`
- Modify: `backend/config.py` (if needed)

Main endpoints:
- `POST /api/chat/stream` — SSE streaming (main chat endpoint)
- `POST /api/upload/csv` — CSV file upload → validate → return result
- `GET /api/wells` — return wells GeoJSON
- `GET /api/wells/{well_id}/history` — return time series
- `GET /api/health` — healthcheck

SSE implementation:
```python
from fastapi.responses import StreamingResponse

@app.post("/api/chat/stream")
async def chat_stream(request: ChatRequest):
    async def generate():
        # 1. Build context from map state
        context = build_context_prompt(request.map_context, wells_data)
        # 2. Call LLM with tools
        # 3. If tool call → execute → feed result back to LLM
        # 4. Stream final response token by token
        async for chunk in llm_stream(context, request.message):
            yield f"data: {json.dumps({'token': chunk})}\n\n"
        yield "data: [DONE]\n\n"
    return StreamingResponse(generate(), media_type="text/event-stream")
```

**Commit:** `"feat: FastAPI app — SSE chat endpoint, CSV upload, wells API, healthcheck"`

---

### Phase 3: Frontend

---

### Task 10: Next.js project setup

**Files:**
- Create entire `frontend/` directory via `npx create-next-app@latest`
- Install: `react-map-gl maplibre-gl @turf/circle zustand @microsoft/fetch-event-source`
- Configure: Tailwind CSS, TypeScript paths

```bash
cd ~/hydrowatch
npx create-next-app@latest frontend --typescript --tailwind --eslint --app --src-dir
cd frontend
npm install react-map-gl maplibre-gl @turf/circle zustand @microsoft/fetch-event-source
npm install -D @types/geojson
```

**Commit:** `"chore: Next.js 15 frontend scaffolding with MapLibre, Zustand, Tailwind"`

---

### Task 11: Zustand stores — map state and chat state

**Files:**
- Create: `frontend/src/stores/mapStore.ts`
- Create: `frontend/src/stores/chatStore.ts`
- Create: `frontend/src/types/index.ts`
- Create: `frontend/src/lib/contextBridge.ts`

`mapStore.ts`: viewport, activeLayers, selectedWell, filters, getApiContext()
`chatStore.ts`: messages, streamingText, isLoading, sendMessage(), cancel()
`contextBridge.ts`: serialize store state for API requests

Refer to research (SSE+Zustand agent) for complete implementation.

**Commit:** `"feat: Zustand stores — map state with getApiContext(), chat state with SSE"`

---

### Task 12: Map component with wells, popups, layers

**Files:**
- Create: `frontend/src/components/Map/WellsMap.tsx`
- Create: `frontend/src/components/Map/WellPopup.tsx`
- Create: `frontend/src/components/Map/DepressionConeLayer.tsx`
- Create: `frontend/src/components/Map/InterferenceLayer.tsx`
- Create: `frontend/src/components/Map/LayerControls.tsx`

Use `react-map-gl/maplibre` with OpenFreeMap tiles (`https://tiles.openfreemap.org/styles/positron`).

Wells as circle layer with data-driven styling (color by TDS, size by debit).
Click → popup with well details.
onMoveEnd → update Zustand viewport → triggers context bridge.

Refer to research (MapLibre agent) for complete code with GeoJSON layers, viewport events, depression cone rings via @turf/circle.

**Commit:** `"feat: MapLibre map — wells layer, popups, depression cones, interference lines, layer controls"`

---

### Task 13: Chat panel with SSE streaming

**Files:**
- Create: `frontend/src/hooks/useSSEChat.ts`
- Create: `frontend/src/components/Chat/ChatPanel.tsx`
- Create: `frontend/src/components/Chat/MessageBubble.tsx`
- Create: `frontend/src/components/Chat/AnomalyCard.tsx`
- Create: `frontend/src/components/Chat/CSVUpload.tsx`

SSE hook using `@microsoft/fetch-event-source` for POST requests.
Chat panel: input field, message list, streaming text with cursor animation.
AnomalyCard: renders structured AnomalyCard JSON from LLM as a styled card.
CSVUpload: drag-and-drop CSV upload → POST to /api/upload/csv → show ValidationResult.

Refer to research (SSE agent) for useSSEChat hook implementation.

**Commit:** `"feat: chat panel — SSE streaming, anomaly cards, CSV upload"`

---

### Task 14: Main page layout — map + chat + controls

**Files:**
- Modify: `frontend/src/app/page.tsx`
- Modify: `frontend/src/app/layout.tsx`

Layout: split view — map (left 60%) + chat panel (right 40%), layer controls overlay on map.
Responsive: on mobile, chat as bottom drawer.

**Commit:** `"feat: main page layout — map + chat split view with layer controls"`

---

### Phase 4: Eval & Metrics

---

### Task 15: Eval dataset and batch pipeline

**Files:**
- Create: `backend/eval/eval_dataset.jsonl`
- Create: `backend/eval/batch_runner.py`
- Create: `backend/eval/metrics.py`

`eval_dataset.jsonl`: 30-50 test cases covering:
- CSV validation questions (10)
- Anomaly detection questions (10)
- Well data queries (10)
- Region analysis questions (10)
- Edge cases (5-10)

`batch_runner.py`: Gemini Batch API pipeline
- Create JSONL with test prompts for Flash and Pro
- Submit batch, poll status, download results
- Compare outputs side-by-side

`metrics.py`: Calculate per-model:
- accuracy (LLM-as-Judge)
- schema_compliance (Pydantic validation pass rate)
- latency_p50, latency_p95
- cost_per_request
- token_usage
- hallucination_rate (DeepEval FaithfulnessMetric)

**Commit:** `"feat: eval pipeline — Gemini Batch API, metrics dashboard, Flash vs Pro comparison"`

---

### Task 16: Metrics API endpoint and frontend panel

**Files:**
- Create: `backend/eval/metrics_api.py`
- Create: `frontend/src/components/Metrics/MetricsPanel.tsx`
- Modify: `backend/main.py` (add /api/metrics endpoint)

`GET /api/metrics` returns latest eval results.
MetricsPanel: simple dashboard showing accuracy, latency, cost per model.

**Commit:** `"feat: metrics dashboard — accuracy, latency, cost comparison between models"`

---

### Phase 5: Docker & Polish

---

### Task 17: Docker Compose and README

**Files:**
- Create: `backend/Dockerfile`
- Create: `docker-compose.yml`
- Create: `README.md`

```yaml
# docker-compose.yml
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    env_file: .env
    volumes:
      - ./data:/app/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s

  frontend:
    build: ./frontend
    ports: ["3000:3000"]
    environment:
      - NEXT_PUBLIC_API_URL=http://localhost:8000
    depends_on:
      backend:
        condition: service_healthy
```

README with: project description, screenshots, setup instructions, architecture diagram, link to vacancy requirements mapping.

**Commit:** `"chore: Docker Compose + README with architecture diagram and setup instructions"`

---

### Task 18: Final integration test and cleanup

- Run full flow: generate data → start backend → start frontend → open map → ask questions → verify anomaly detection → upload CSV → verify validation
- Fix any integration issues
- Clean up code, remove debug prints
- Final commit and push

**Commit:** `"chore: integration test pass, cleanup, ready for demo"`

---

## EXECUTION NOTES

### For the implementing Claude Code session:

1. **Read CLAUDE.md first** — it has project overview and commands
2. **Read this plan fully** before starting any task
3. **Follow TDD**: write test → run (fail) → implement → run (pass) → commit
4. **Commit after every task** — push to GitHub
5. **Do NOT skip tests** — they demonstrate testing skills for the interview
6. **Use exact file paths** from this plan
7. **Research docs are at:** `~/OneDrive/Рабочий стол/CREATMAN/Собес GetMeGit 1/hydrowatch_research_summary.md`

### Environment setup:

```bash
cd ~/hydrowatch/backend
python -m venv .venv
source .venv/bin/activate  # or .venv/Scripts/activate on Windows
pip install -r requirements.txt

# Set Gemini API key
cp .env.example .env
# Edit .env with your GEMINI_API_KEY
```

### Key API keys needed:
- `GEMINI_API_KEY` — get from https://aistudio.google.com/app/apikey (free)
