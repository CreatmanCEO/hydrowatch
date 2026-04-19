# ADR 0002: Multi-Provider Model Routing with Two Pools

**Status:** Accepted
**Date:** 2026-04-19

## Context

Different tasks have different complexity levels. CSV validation is straightforward; anomaly interpretation requires reasoning. Using the same expensive model for everything wastes budget. Using only cheap models misses quality on complex tasks.

## Decision

Two model pools with task-based routing:
- **Pool A** (simple/medium): Gemini 2.5 Flash and Cerebras Llama 3.3 70B as mutual fallback. Used for data queries, validation, statistics.
- **Pool B** (complex): Anthropic Haiku 4.5 (default) with Sonnet 4.5 upgrade for deep reasoning. Used for anomaly detection, interpretation, calibration advice.

## Consequences

**Positive:**
- Cost optimization: simple tasks use ~$0.00004/request, complex tasks ~$0.0003/request
- Resilience: if one provider is down, fallback kicks in automatically
- Quality: complex tasks get reasoning-capable models
- Task classifier routes automatically based on user message keywords

**Negative:**
- Task classification is heuristic-based (keyword matching) — could misroute edge cases
- More configuration complexity (4 API keys, routing table)
- Model adaptors needed for each provider's prompt style differences
