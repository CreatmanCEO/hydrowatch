# ADR 0004: Context Bridge Pattern for Map-Aware LLM

**Status:** Accepted
**Date:** 2026-04-19

## Context

The LLM assistant needs to understand what the user is looking at on the map — current viewport, active layers, selected well, applied filters. Without this context, the LLM cannot provide spatially relevant answers.

## Decision

Implement a **Context Bridge** that serializes frontend map state (viewport, bbox, zoom, layers, selected well) into a structured `MapContext` object, included in every chat request. Backend builds a text section from this context and injects it into the LLM system prompt.

## Consequences

**Positive:**
- LLM responses are contextually relevant to what the user sees
- "Show anomalies in viewport" works because LLM knows the bbox
- Selected well details are pre-loaded — LLM can reference specific parameters
- Zustand store provides reactive state — context updates on every map interaction
- Pattern is generalizable to any geospatial + LLM application

**Negative:**
- Every chat request includes full map context — adds ~200-400 tokens to each prompt
- Context is a snapshot — if user pans during LLM response, context may be stale
- Frontend must keep Zustand store in sync with map events (onMoveEnd)
