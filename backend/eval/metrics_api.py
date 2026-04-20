"""Metrics API — serve latest eval results."""
import json
from pathlib import Path

from fastapi import APIRouter

router = APIRouter(prefix="/api/metrics", tags=["metrics"])

RESULTS_DIR = Path(__file__).parent / "results"

# Sample metrics for demo (used when no eval has been run yet)
SAMPLE_METRICS = {
    "openrouter/anthropic/claude-haiku-4.5": {
        "model": "openrouter/anthropic/claude-haiku-4.5",
        "pool": "pool-a + pool-b",
        "total_cases": 48,
        "accuracy": 0.938,
        "schema_compliance": 0.917,
        "latency_p50": 650,
        "latency_p95": 1800,
        "cost_per_request": 0.00032,
        "avg_tokens_per_request": 1100,
        "error_rate": 0.0,
    },
    "gemini/gemini-2.5-flash": {
        "model": "gemini/gemini-2.5-flash",
        "pool": "fallback",
        "total_cases": 48,
        "accuracy": 0.875,
        "schema_compliance": 0.812,
        "latency_p50": 420,
        "latency_p95": 1150,
        "cost_per_request": 0.000045,
        "avg_tokens_per_request": 850,
        "error_rate": 0.021,
    },
    "openrouter/anthropic/claude-sonnet-4.5": {
        "model": "openrouter/anthropic/claude-sonnet-4.5",
        "pool": "pool-b-upgrade",
        "total_cases": 48,
        "accuracy": 0.958,
        "schema_compliance": 0.938,
        "latency_p50": 1200,
        "latency_p95": 3500,
        "cost_per_request": 0.00145,
        "avg_tokens_per_request": 1450,
        "error_rate": 0.0,
    },
}


POOL_MAP = {
    "openrouter/anthropic/claude-haiku-4.5": "pool-a + pool-b",
    "gemini/gemini-2.5-flash": "fallback",
    "openrouter/anthropic/claude-sonnet-4.5": "pool-b-upgrade",
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


@router.post("/run", tags=["metrics"])
async def trigger_eval():
    """Trigger eval pipeline. Runs in background."""
    import asyncio
    from eval.batch_runner import run_eval as _run_eval

    asyncio.create_task(_run_eval())
    return {"status": "started", "message": "Eval pipeline started. Check /api/metrics for results."}


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
                "models": ["anthropic/claude-haiku-4.5"],
                "tasks": ["detect_anomalies", "interpret_anomaly", "general_question"],
            },
            "pool-b-upgrade": {
                "description": "Deep reasoning — comprehensive analysis",
                "models": ["anthropic/claude-sonnet-4.5"],
                "tasks": ["calibration_advice"],
            },
        }
    }
