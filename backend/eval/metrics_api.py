"""Metrics API — serve latest eval results."""
import json
from pathlib import Path

from fastapi import APIRouter

router = APIRouter(prefix="/api/metrics", tags=["metrics"])

RESULTS_DIR = Path(__file__).parent / "results"

# Sample metrics for demo (used when no eval has been run yet)
SAMPLE_METRICS = {
    "openrouter/deepseek/deepseek-chat-v3-0324": {
        "model": "openrouter/deepseek/deepseek-chat-v3-0324",
        "pool": "pool-a + pool-b",
        "total_cases": 48,
        "accuracy": 0.896,
        "schema_compliance": 0.875,
        "latency_p50": 380,
        "latency_p95": 950,
        "cost_per_request": 0.000052,
        "avg_tokens_per_request": 900,
        "error_rate": 0.0,
    },
    "gemini/gemini-2.5-flash": {
        "model": "gemini/gemini-2.5-flash",
        "pool": "pool-a (fallback)",
        "total_cases": 48,
        "accuracy": 0.875,
        "schema_compliance": 0.812,
        "latency_p50": 420,
        "latency_p95": 1150,
        "cost_per_request": 0.000045,
        "avg_tokens_per_request": 850,
        "error_rate": 0.021,
    },
    "openrouter/nvidia/nemotron-3-super": {
        "model": "openrouter/nvidia/nemotron-3-super",
        "pool": "pool-b (fallback)",
        "total_cases": 48,
        "accuracy": 0.812,
        "schema_compliance": 0.792,
        "latency_p50": 520,
        "latency_p95": 1400,
        "cost_per_request": 0.0,
        "avg_tokens_per_request": 1050,
        "error_rate": 0.042,
    },
    "openrouter/anthropic/claude-haiku-4-5-20251001": {
        "model": "openrouter/anthropic/claude-haiku-4-5-20251001",
        "pool": "pool-b-upgrade",
        "total_cases": 48,
        "accuracy": 0.938,
        "schema_compliance": 0.917,
        "latency_p50": 650,
        "latency_p95": 1800,
        "cost_per_request": 0.00032,
        "avg_tokens_per_request": 1100,
        "error_rate": 0.0,
    },
}


POOL_MAP = {
    "openrouter/deepseek/deepseek-chat-v3-0324": "pool-a + pool-b",
    "gemini/gemini-2.5-flash": "pool-a (fallback)",
    "openrouter/nvidia/nemotron-3-super": "pool-b (fallback)",
    "openrouter/anthropic/claude-haiku-4-5-20251001": "pool-b-upgrade",
}


@router.get("")
async def get_metrics():
    """Return latest eval metrics. Uses actual results if available, sample data otherwise."""
    summary_path = RESULTS_DIR / "summary.json"

    if summary_path.exists():
        with open(summary_path) as f:
            models = json.load(f)
        # Enrich with pool info
        for model_name, metrics in models.items():
            if "pool" not in metrics:
                metrics["pool"] = POOL_MAP.get(model_name, "unknown")
        return {"source": "eval_run", "models": models}

    return {"source": "sample", "models": SAMPLE_METRICS}


@router.get("/models")
async def list_models():
    """List evaluated models with routing info."""
    return {
        "pools": {
            "pool-a": {
                "description": "Simple/medium tasks — mutual fallback",
                "models": ["gemini/gemini-2.5-flash", "cerebras/llama-3.3-70b"],
                "tasks": ["validate_csv", "query_wells", "get_region_stats", "get_well_history"],
            },
            "pool-b": {
                "description": "Complex tasks — reasoning required",
                "models": ["anthropic/claude-haiku-4-5-20251001"],
                "tasks": ["detect_anomalies", "interpret_anomaly", "general_question"],
            },
            "pool-b-upgrade": {
                "description": "Deep reasoning — comprehensive analysis",
                "models": ["anthropic/claude-sonnet-4-5-20250514"],
                "tasks": ["calibration_advice"],
            },
        }
    }
