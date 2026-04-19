"""LLM router with two model pools via LiteLLM."""
from litellm import Router
from config import get_settings
from services.prompt_engine import PromptEngine

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

# Prompt engine singleton
prompt_engine = PromptEngine()


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


def build_system_prompt(
    model_pool: str,
    task_type: str,
    context_section: str,
    output_type: str = "text_response",
) -> str:
    """Build full system prompt via PromptEngine."""
    return prompt_engine.build(
        model_pool=model_pool,
        task_type=task_type,
        context_section=context_section,
        output_type=output_type,
    )
