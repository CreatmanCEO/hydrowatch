"""LLM router with two model pools via LiteLLM."""
from litellm import Router
from config import get_settings
from services.prompt_engine import PromptEngine

# Task → model pool routing
TASK_ROUTING = {
    "validate_csv":         "pool-a",
    "query_wells":          "pool-a",
    "get_region_stats":     "pool-a",
    "get_well_history":     "pool-a",
    "detect_anomalies":     "pool-b",
    "interpret_anomaly":    "pool-b",
    "depression_analysis":  "pool-b",
    "calibration_advice":   "pool-b-upgrade",
    "general_question":     "pool-b",
}

# Prompt engine singleton
prompt_engine = PromptEngine()


def create_router() -> Router:
    """Create LiteLLM router with two model pools."""
    settings = get_settings()

    or_key = settings.openrouter_api_key.get_secret_value()
    gemini_key = settings.gemini_api_key.get_secret_value()

    model_list = [
        # Pool A — simple/medium tasks
        {"model_name": "pool-a", "litellm_params": {
            "model": "openrouter/anthropic/claude-haiku-4.5",
            "api_key": or_key,
        }},
        {"model_name": "pool-a", "litellm_params": {
            "model": "gemini/gemini-2.5-flash",
            "api_key": gemini_key,
        }},

        # Pool B — complex tasks
        {"model_name": "pool-b", "litellm_params": {
            "model": "openrouter/anthropic/claude-haiku-4.5",
            "api_key": or_key,
        }},
        {"model_name": "pool-b", "litellm_params": {
            "model": "gemini/gemini-2.5-flash",
            "api_key": gemini_key,
        }},

        # Pool B upgrade — deep reasoning
        {"model_name": "pool-b-upgrade", "litellm_params": {
            "model": "openrouter/anthropic/claude-sonnet-4.5",
            "api_key": or_key,
        }},
        {"model_name": "pool-b-upgrade", "litellm_params": {
            "model": "openrouter/anthropic/claude-haiku-4.5",
            "api_key": or_key,
        }},
    ]

    return Router(
        model_list=model_list,
        routing_strategy="latency-based-routing",
        num_retries=3,
        timeout=45,
        allowed_fails=1,
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
