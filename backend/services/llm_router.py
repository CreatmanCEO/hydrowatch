"""LLM router with two model pools via LiteLLM."""
import os
from typing import AsyncIterator

from litellm import Router
from config import get_settings

# Task → model pool routing
TASK_ROUTING = {
    "validate_csv":       "pool-a",
    "query_wells":        "pool-a",
    "get_region_stats":   "pool-a",
    "get_well_history":   "pool-a",
    "detect_anomalies":   "pool-b",
    "interpret_anomaly":  "pool-b",
    "calibration_advice": "pool-b-upgrade",
    "general_question":   "pool-b",
}

SYSTEM_PROMPT = """You are HydroWatch AI — an expert groundwater monitoring assistant for Abu Dhabi wells.

You help hydrogeologists analyze well data, detect anomalies, and make decisions.

Your capabilities (via tools):
- **query_wells**: Find wells by location, status, or cluster
- **get_well_history**: Get time series data with trend analysis
- **detect_anomalies**: Detect debit decline, TDS spikes, sensor faults
- **get_region_stats**: Aggregate statistics for a map viewport
- **validate_csv**: Validate uploaded CSV observation files

Guidelines:
1. Always use tools when the user asks about specific data — don't guess
2. Respond in the same language as the user's message
3. When showing anomalies, include severity and recommendations
4. Reference well IDs (e.g., AUH-01-003) when discussing specific wells
5. Use hydrogeological terminology appropriate for professionals

{context}
"""


def create_router() -> Router:
    """Create LiteLLM router with two model pools."""
    settings = get_settings()

    model_list = [
        # Pool A — simple/medium tasks (mutual fallback)
        {
            "model_name": "pool-a",
            "litellm_params": {
                "model": settings.model_pool_a_primary,
                "api_key": settings.gemini_api_key.get_secret_value(),
            },
        },
        {
            "model_name": "pool-a",
            "litellm_params": {
                "model": settings.model_pool_a_fallback,
                "api_key": settings.cerebras_api_key.get_secret_value(),
            },
        },
        # Pool B — complex tasks
        {
            "model_name": "pool-b",
            "litellm_params": {
                "model": settings.model_pool_b_default,
                "api_key": settings.anthropic_api_key.get_secret_value(),
            },
        },
        {
            "model_name": "pool-b-upgrade",
            "litellm_params": {
                "model": settings.model_pool_b_complex,
                "api_key": settings.anthropic_api_key.get_secret_value(),
            },
        },
    ]

    return Router(
        model_list=model_list,
        routing_strategy="simple-shuffle",
        num_retries=2,
        timeout=30,
    )


def get_model_for_task(task_type: str) -> str:
    """Determine which model pool to use for a given task type."""
    return TASK_ROUTING.get(task_type, "pool-b")


def build_system_prompt(context_section: str) -> str:
    """Build full system prompt with context bridge section."""
    return SYSTEM_PROMPT.format(context=context_section)
