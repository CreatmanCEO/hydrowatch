# ADR 0001: LiteLLM + Instructor over LangChain

**Status:** Accepted
**Date:** 2026-04-19

## Context

We need a framework for LLM integration that supports multiple providers (Gemini, Cerebras, Anthropic), structured output via Pydantic, and tool calling. LangChain is the most popular option but adds significant abstraction layers.

## Decision

Use **LiteLLM** for provider-agnostic API calls with built-in Router for fallback, and **Instructor** for Pydantic-validated structured output. No LangChain.

## Consequences

**Positive:**
- Direct control over prompts and tool calling — no hidden prompt templates
- LiteLLM Router handles fallback between providers transparently
- Instructor patches LiteLLM's completion to return Pydantic models directly
- Minimal dependencies, easier to debug
- Provider switching requires only changing model string, not code

**Negative:**
- No built-in RAG chains or agent loops — must implement tool calling loop manually
- Less community tooling compared to LangChain ecosystem
- Instructor's structured output depends on provider support for function calling
