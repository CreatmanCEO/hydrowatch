# HydroWatch — AI Groundwater Monitoring

## Project Overview
AI-powered groundwater well monitoring with LLM assistant.
FastAPI backend + Next.js frontend + MapLibre map.

## Architecture
- Backend: FastAPI + LiteLLM (Gemini) + Instructor + Pydantic
- Frontend: Next.js 15 + React + TypeScript + react-map-gl + Zustand
- Data: Synthetic wells (GeoJSON) + time series (CSV)

## Key Patterns
1. Context Bridge: frontend sends viewport/layers/selection -> backend builds LLM prompt
2. Tool Calling: LLM chooses which tool to call (validate_csv, detect_anomalies, etc.)
3. Structured Output: all LLM responses -> Pydantic models -> JSON cards for frontend
4. SSE Streaming: /api/chat/stream endpoint streams LLM response tokens

## Commands
- Backend: `cd backend && uvicorn main:app --reload --port 8000`
- Frontend: `cd frontend && npm run dev`
- Generate data: `cd backend && python -m data_generator.generate_wells`
- Run tests: `cd backend && pytest tests/ -v`

## Implementation Plan
See: docs/plans/2026-04-19-hydrowatch-implementation.md
