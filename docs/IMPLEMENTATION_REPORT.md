# HydroWatch — Implementation Report

**Date:** 2026-04-19 — 2026-04-20
**Repository:** https://github.com/CreatmanCEO/hydrowatch
**Commits:** 48 total on `main`

---

## Project Summary

AI-powered groundwater monitoring system for Abu Dhabi aquifer management. Interactive MapLibre map with 25 monitoring wells, LLM-assisted anomaly detection, SSE streaming chat, structured output cards, CSV validation, and model evaluation pipeline.

---

## Architecture

```
Frontend (Next.js 15 + TypeScript)
├── MapLibre GL map (react-map-gl) — wells, depression cones, popups
├── Chat panel — SSE streaming, anomaly cards, line charts
├── Zustand stores — map state, chat state (devtools middleware)
└── Context Bridge — viewport/layers/selection → API

Backend (FastAPI + Python 3.12)
├── SSE chat endpoint — tool calling + follow-up
├── Prompt Engine — 3-level hierarchy (role + domain + adaptor + task + output)
├── LLM Router — Pool A/B via LiteLLM (Anthropic Haiku via OpenRouter + Gemini fallback)
├── Tool Executor — 5 MCP-style tools (validate_csv, query_wells, detect_anomalies, get_well_history, get_region_stats)
├── Anomaly Detector — debit decline, TDS spike, sensor fault
├── Data Generator — 25 wells + 365-day time series with anomaly injection
├── PostgreSQL + PostGIS — ORM models, spatial indexes, seed scripts
└── Eval Pipeline — 48 test cases, batch runner, metrics comparison
```

---

## Implementation Tasks Completed

| # | Task | Files | Tests |
|---|------|-------|-------|
| 1 | Project scaffolding | config.py, requirements.txt, .gitignore, CLAUDE.md | — |
| 2 | Theis equation + superposition | hydro_models.py | 7 |
| 3 | Well GeoJSON generator | generate_wells.py | 6 |
| 4 | Time series generator | generate_timeseries.py | 6 |
| 5 | PostgreSQL + PostGIS ORM | database.py, session.py, seed.py | 8 |
| 6 | Pydantic schemas | schemas.py | 13 |
| 7 | MCP-style tools (5) | validate_csv, query_wells, detect_anomalies, get_well_history, get_region_stats | 14 |
| 8 | Tool registry + executor | tool_schemas.py, tool_executor.py | 10 |
| 9 | LLM router + context bridge | llm_router.py, context_bridge.py | 8 |
| 9.5 | Prompt Engine | prompt_engine.py, 5 prompt modules | 16 |
| 10 | FastAPI main app (SSE) | main.py | 8 |
| 11 | Next.js scaffolding | frontend/ with MapLibre, Zustand, Tailwind | — |
| 12 | Zustand stores + types | mapStore.ts, chatStore.ts, types, contextBridge, api | — |
| 13 | Map component | WellsMap, WellPopup, DepressionConeLayer, LayerControls | — |
| 14 | Chat panel | ChatPanel, MessageBubble, AnomalyCard, CSVUpload, CommandBar | — |
| 15 | Main page layout | page.tsx, layout.tsx, mobile drawer | — |
| 16 | Eval pipeline | eval_dataset.jsonl (48 cases), batch_runner.py, metrics.py | 21 |
| 17 | Metrics dashboard | metrics_api.py, MetricsPanel.tsx | — |
| 18 | Docker + docs | Dockerfiles, docker-compose, README, ARCHITECTURE, 6 ADRs, CI, Makefile | — |
| 19 | Integration + fixes | Data path fix, audit fixes, LLM provider migration | — |
| E2E | Playwright tests | 5 test suites | 25 |

---

## Test Coverage

| Suite | Tests | Status |
|-------|-------|--------|
| Backend unit tests | 117 | All passing |
| Playwright E2E | 25 | All passing |
| **Total** | **142** | **All passing** |

### Backend test breakdown:
- test_hydro_models.py — 7 (Theis equation physics)
- test_generate_wells.py — 6 (GeoJSON structure, coordinates, properties)
- test_generate_timeseries.py — 6 (time series, anomaly injection)
- test_database.py — 8 (ORM models, indexes, cascades)
- test_schemas.py — 13 (Pydantic validation, defaults, errors)
- test_tools.py — 14 (all 5 tools with real data)
- test_tool_executor.py — 10 (registry, execution, error handling)
- test_context_bridge.py — 8 (prompt building, well selection)
- test_prompt_engine.py — 16 (levels, adaptors, tasks, domain knowledge)
- test_main.py — 8 (API endpoints, SSE, CSV upload)
- test_eval.py — 21 (dataset, schema validation, metrics, costs)

### E2E test breakdown:
- map.spec.ts — 5 (canvas, nav, layers, checkbox, toggle)
- chat.spec.ts — 7 (welcome, suggestions, input, send, loading, SSE)
- layout.spec.ts — 6 (split view, panels, commands)
- metrics.spec.ts — 4 (panel, table, insights, Run Eval)
- commands.spec.ts — 3 (dropdown, execution, close)

---

## LLM Provider Configuration

| Pool | Primary | Fallback | Tasks |
|------|---------|----------|-------|
| Pool A | Claude Haiku 4.5 (OpenRouter) | Gemini 2.5 Flash | validate_csv, query_wells, get_region_stats, get_well_history |
| Pool B | Claude Haiku 4.5 (OpenRouter) | — | detect_anomalies, interpret_anomaly, depression_analysis, general_question |
| Pool B+ | Claude Sonnet 4.5 (OpenRouter) | Claude Haiku 4.5 | calibration_advice |

**Routing:** latency-based-routing via LiteLLM Router. Native tool calling via Anthropic API.

### Provider history:
1. Initial: Gemini Flash + Cerebras Llama + Anthropic direct → all failed (503, no credits, model not found)
2. Migration to DeepSeek V3.2 via OpenRouter → no streaming tool calling support
3. Final: Anthropic Haiku/Sonnet via OpenRouter → stable, native tool calling works

---

## Prompt Engine Architecture

```
Final prompt = Level 0: Base Role (~200 tokens)
             + Level 1: Domain Knowledge (~600 tokens)
             + Model Adaptor (per pool, ~100 tokens)
             + Task Instructions (per task type, ~200 tokens)
             + Output Format (per response type, ~80 tokens)
             + Level 2: Context Bridge (runtime, variable)
```

Level 1 domain knowledge includes:
- Abu Dhabi aquifer formations (Dammam, Umm Er Radhuma, Quaternary, Alluvial)
- UAE water quality standards and alert thresholds
- Monitoring network characteristics (25 wells, 4 clusters, 4x/day)
- Anomaly interpretation guidelines with severity thresholds

---

## Key Features Implemented

1. **Interactive Map** — MapLibre GL with data-driven well styling (color by TDS, size by debit, opacity by status), depression cone visualization (5 concentric rings with gradient opacity)
2. **AI Chat** — SSE streaming with tool calling, structured output cards (AnomalyCard, ValidationResult, RegionStats, WellHistory with Recharts line charts)
3. **Command Bar** — 9 quick commands in 4 categories (Analysis, Monitoring, Data, Reports)
4. **CSV Upload** — drag-and-drop validation + auto-triggers AI analysis
5. **Metrics Dashboard** — model comparison table with accuracy, schema compliance, latency, cost per model
6. **Anomaly Detection** — debit decline (Q1 vs Q4 regression), TDS spike (3σ z-score), sensor fault (zero runs)
7. **Theis Equation** — analytical drawdown calculation with superposition for multi-well interference
8. **Welcome Experience** — capabilities list, usage instructions, clickable suggestions

---

## Documentation

| Document | Content |
|----------|---------|
| README.md | Features, architecture diagram, quick start, API docs, tech stack |
| ARCHITECTURE.md | C4 diagrams (Level 1+2), data flow sequence, prompt engine, model routing |
| CHANGELOG.md | Keep a Changelog format |
| docs/adr/ | 6 Architecture Decision Records (MADR format) |
| .github/workflows/ci.yml | GitHub Actions: test + lint |
| Makefile | dev, test, lint, format, generate-data, docker, e2e |

---

## Known Limitations

1. Gemini Flash as fallback is unreliable (503 "high demand" during peak hours)
2. Task classifier is heuristic-based (keyword matching) — production should use LLM-based intent classification
3. Eval pipeline runs sequentially, not via Gemini Batch API (50% discount missed)
4. No real-time WebSocket for multi-user collaboration
5. Synthetic data — real aquifer heterogeneity not captured
6. Frontend path with Cyrillic characters breaks Turbopack — must run from ASCII path (C:\hydrowatch)

---

## Budget

OpenRouter balance: $5.00
- Claude Haiku 4.5: $0.80/$4.00 per 1M tokens → ~$0.003/request
- Claude Sonnet 4.5: $3.00/$15.00 per 1M tokens → ~$0.015/request
- Estimated capacity: ~1500 Haiku requests or ~300 Sonnet requests
