# Changelog

All notable changes to this project will be documented in this file.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.1.0/)

## [0.1.0] - 2026-04-19

### Added
- Synthetic data generator: 25 wells in 4 Abu Dhabi clusters with Theis-based depression cones
- Time series generator with anomaly injection (debit decline, TDS spike, sensor fault)
- FastAPI backend with SSE streaming, MCP-style tool calling, 3-level prompt engine
- Multi-provider LLM routing: Gemini Flash / Cerebras Llama (Pool A) + Anthropic Haiku / Sonnet (Pool B)
- 5 read-only tools: validate_csv, query_wells, detect_anomalies, get_well_history, get_region_stats
- Next.js 15 frontend with MapLibre map, data-driven well styling, depression cone visualization
- Chat panel with SSE streaming and structured cards: AnomalyCard, ValidationResult, RegionStats, WellHistory
- CSV upload with validation (columns, ranges, metadata consistency)
- Eval pipeline: 48 test cases across 5 categories, accuracy/schema compliance/latency/cost metrics
- Metrics dashboard with model comparison table and key insights
- PostgreSQL + PostGIS with spatial indexes, async SQLAlchemy ORM, seed scripts
- Pydantic v2 schemas for all API contracts
- Domain knowledge injection simulating fine-tuned model behavior
- 117 backend tests passing
