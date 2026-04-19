# ADR 0006: SSE over WebSocket for Chat Streaming

**Status:** Accepted
**Date:** 2026-04-19

## Context

LLM responses need to stream token-by-token to the frontend for responsive UX. Two options: Server-Sent Events (SSE) or WebSocket.

## Decision

Use **SSE** via FastAPI `StreamingResponse` for the chat endpoint. Frontend consumes via `@microsoft/fetch-event-source` (supports POST requests, unlike native `EventSource`).

## Consequences

**Positive:**
- Simpler than WebSocket — no connection state management, no heartbeats
- HTTP-native — works through proxies, load balancers, CDNs without special config
- Automatic reconnection built into the protocol
- POST support via `fetch-event-source` library — can send chat request body
- Structured event types (meta, token, tool_call, tool_result, error, done) map cleanly to SSE data fields
- Sufficient for LLM streaming which is inherently unidirectional (server → client)

**Negative:**
- Unidirectional: client cannot send messages during an active stream (must cancel and re-request)
- No binary data support — all payloads must be JSON text
- Browser limit of ~6 concurrent SSE connections per domain (not an issue for single-user demo)
- For production with collaborative features (multiple users viewing same map), WebSocket would be needed
