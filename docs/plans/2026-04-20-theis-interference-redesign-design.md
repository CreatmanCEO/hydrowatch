# Theis-Based Interference & Depression Cone Redesign — Design

**Date:** 2026-04-20
**Status:** Approved, ready for implementation planning

## Problem

Current implementation has two "decorative" features that look meaningful but provide no analytical value:

1. **InterferenceLayer** — draws lines between any two wells <5km apart, regardless of whether they actually interfere hydraulically. No gradient, no annotations, no integration with AI. Just geometry.

2. **DepressionConeLayer** — concentric rings with cosmetic radius `0.3 + yield/30 * 1.5` km. Does not use Theis equation, transmissivity, storativity, or pumping time. The `hydro_models.py` with proper Theis is unused for visualization.

3. **AI assistant has no awareness** of either feature. Users cannot ask meaningful questions about cone overlap, well interference, or vulnerability — LLM has no tool and no domain context.

## Goal

Replace decoration with real Theis-based hydrogeological analysis, exposed both visually on the map AND through MCP-style tools the AI can call.

## Architecture Principle

**Single source of truth — Theis math lives only on backend.** Frontend never recomputes. Two new MCP tools wrap the math; AI and map render from the same endpoints. If formula changes, it changes in one place. No JS-side hydrogeology.

## Components

### Backend

#### Tool 1: `analyze_interference`

**Inputs:** `bbox`, `t_days=30`, `min_coefficient=0.10`

**Per pair (A, B) within bbox:**
- Distance via haversine + WGS84→metric
- `s_self_A` = Theis drawdown at well radius (0.3m) from A's own pumping
- `s_other_at_A` = Theis drawdown at A from B's pumping
- `coef_at_A = s_other_at_A / s_self_A` — fraction of A's drawdown caused by B
- Mirror for B
- Severity from max coefficient: low (10–20%), medium (20–40%), high (40–60%), critical (>60%)

**Output (Pydantic `InterferenceResult`):**
- List of pairs with `well_a`, `well_b`, `distance_km`, `coef_at_a`, `coef_at_b`, `drawdown_midpoint_m`, `severity`, `dominant_well`, `recommendation`
- Context: `t_days`, `wells_analyzed`, `pairs_significant`

#### Tool 2: `compute_drawdown_grid`

**Inputs:** `well_id` (string or list), `t_days=30`, `extent_km=5`, `resolution=50`

**Computes Theis drawdown on N×N grid via `superposition_drawdown` (includes nearby wells automatically). Generates isoline polygons for levels 0.5m, 1m, 2m, 5m using scipy contour extraction → MultiPolygon GeoJSON.**

**Output (Pydantic `DrawdownGrid`):**
- `well_id`, `center`, `t_days`
- `isolines`: list of `{level_m, polygon: GeoJSON}`
- `max_drawdown_m`, `interfering_wells: list[str]`

### Frontend

#### InterferenceLayer (rewritten)

**Render:** one `<Source>` with `lineMetrics: true`, two layers:
- **Gradient line** per pair, `line-gradient` interpolating `coef_at_a` (color at start) → balanced midpoint → `coef_at_b` (color at end). Color scale: green (0%) → yellow (30%) → red (60%+).
- **Symbol layer** at midpoint with `text-field` showing `"X% / Ym"` (max coefficient + drawdown). Visible at zoom ≥ 12.
- **Click handler** on line → `<InterferencePopup>` with full pair data, donor/victim explanation, severity-tagged recommendation.

`line-width: 2px` fixed. Accent through color, not thickness.

#### DepressionConeLayer (rewritten)

**Activation:** `selectedWellId !== null` AND layer toggle on. OR `coneMode === "all"` mode renders cones for all active wells.

**Render:** 4 fill layers from isoline polygons:
- 5m+ — fill `#dc2626` opacity 0.25
- 2m — `#f97316` opacity 0.15
- 1m — `#eab308` opacity 0.10
- 0.5m — `#84cc16` opacity 0.06

Stacked → visual gradient cone.

**TimeSlider component** above map: 1d / 7d / 30d / 90d. Debounced 300ms tool refetch.

**DrawdownLegend (bottom-left):** color swatches with isoline levels.

#### LayerControls

Three checkboxes:
- ☑ Wells
- ☐ Depression Cone (singular — one well or all per `coneMode`)
- ☐ Interference

#### Chat — new card components

- `<InterferenceCardComponent>` rendering pairs as ranked table with severity colors and donor/victim labels
- `<DrawdownCardComponent>` showing isoline summary + max drawdown + interfering wells list

Both render in `MessageBubble` switch on `card.type`.

### AI Integration

#### MapContext extension

```python
depression_cone_t_days: int = 30
depression_cone_mode: Literal["selected", "all"] = "selected"
interference_visible: bool = False
```

`build_context_prompt` includes current map state — AI sees layers active, time slider position, cone mode.

#### TASK_ROUTING new entries

- `interference_analysis` → pool-b
- `drawdown_analysis` → pool-b
- `water_quality_report` → pool-a
- `cluster_comparison` → pool-a
- `trend_analysis` → pool-a
- `daily_report` → pool-b

#### `_classify_task` keyword extension

- `interference_analysis`: "interference", "competing wells", "cone overlap", "mutual influence"
- `drawdown_analysis`: "depression cone", "drawdown", "isoline", "voronka"
- `water_quality_report`: "water quality", "TDS", "chloride", "pH", "drinking water"
- `cluster_comparison`: "compare clusters", "cross-cluster"
- `trend_analysis`: "trend", "time series", "history"
- `daily_report`: "daily report", "summary report"

#### Prompts

- **domain_knowledge.py**: section "Interference & Depression Cones" — how to read gradient lines, what isolines mean, severity thresholds, Theis principles.
- **task_instructions.py**: 5 new entries with explicit tool-calling instructions and reasoning structure.
- **output_formats.py**: `interference_card`, `drawdown_card` formats.

#### Tool registry

`TOOL_DEFINITIONS` += 2 entries (analyze_interference, compute_drawdown_grid). `ToolExecutor._registry` += 2 handlers.

### CommandBar audit

Of 9 commands, 5 currently route incorrectly through `general_question`. Rebind to specific task types so LLM is guaranteed to call right tool — not dependent on prompt parsing luck.

### Run Eval polishing

Backend writes `results/_status.json` per case with `{state, progress_pct, current}`. New endpoint `GET /api/metrics/run/status`. Frontend polls every 2s during run, shows progress bar `12 / 48 cases`, autorefreshes metrics on completion.

## Data Flow

```
User clicks "Check well interference" command
  → Frontend sends ChatRequest with task_type=interference_analysis
  → Backend prompt_engine builds prompt with domain knowledge + task_instructions
  → LLM calls analyze_interference(bbox=user_viewport)
  → Backend computes Theis pairs → returns InterferenceResult
  → LLM formats InterferenceCard + text analysis
  → SSE streams to frontend
  → MessageBubble renders <InterferenceCardComponent>
  → Map InterferenceLayer ALSO calls analyze_interference on layer toggle
  → Same data, no client-side recompute
```

## What stays unchanged

- Welcome message (onboarding, not decoration)
- Well marker color/size/opacity (already data-driven)
- AnomalyCard + recommendations (already useful)
- WellHistoryChart (Recharts already in place)
- Map base style, navigation controls
- SSE streaming infrastructure
- Pydantic v2 patterns for schemas

## Non-goals

- Real groundwater table modeling (regional flow, recharge boundaries) — out of scope
- Multi-tenant or auth — demo only
- Real Abu Dhabi well data — synthetic, controlled

## Sub-stage breakdown

16 stages, ordered to keep main branch building at every commit:

1. **Pydantic schemas** (InterferenceResult/Pair, DrawdownGrid/Isoline, cards)
2. **analyze_interference tool** + tests
3. **compute_drawdown_grid tool** + tests
4. **Tool registry update** + tests
5. **Prompts update** (domain, instructions, formats)
6. **Task router update** (TASK_ROUTING + classifier)
7. **Context bridge extension**
8. **Frontend types** (TS mirrors)
9. **mapStore extension** (cone mode, time days)
10. **InterferenceLayer rewrite** (gradient + annotations + popup)
11. **DepressionConeLayer rewrite** (isolines + time slider + legend)
12. **LayerControls update**
13. **Chat cards** (Interference/Drawdown components)
14. **CommandBar rebind**
15. **Run Eval status polling**
16. **E2E tests update**

Stages 1–7 backend, 8–14 frontend, 15–16 polish.

## Testing

- Unit tests per backend tool: known-input → expected coefficient/grid
- Pydantic schema validation tests
- Existing 117 backend tests must remain green
- E2E (Playwright): click interference line → popup visible; toggle depression cone → isolines render; time slider change → grid refetch

## Risks & mitigations

- **Theis grid generation slow at 50×50 with multiple wells** → cache by (well_id, t_days) tuple; consider 30×30 default if perf issue.
- **MapLibre `line-gradient` requires `lineMetrics: true`** — easy miss. Document in component.
- **Click handler on thin lines is hard to hit** — add invisible 12px-wide hit-target line layer above gradient layer.
- **AI may still hallucinate Theis numbers** — task_instructions explicitly mandate "you MUST call the tool first, do not estimate".
