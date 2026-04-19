"""Metrics API — serve latest eval results."""
import json
from pathlib import Path

from fastapi import APIRouter

router = APIRouter(prefix="/api/metrics", tags=["metrics"])

RESULTS_DIR = Path(__file__).parent / "results"

# Sample metrics for demo (used when no eval has been run yet)
SAMPLE_METRICS = {
    "gemini/gemini-2.5-flash": {
        "model": "gemini/gemini-2.5-flash",
        "pool": "pool-a",
        "total_cases": 48,
        "accuracy": 0.875,
        "schema_compliance": 0.812,
        "latency_p50": 420,
        "latency_p95": 1150,
        "cost_per_request": 0.000045,
        "avg_tokens_per_request": 850,
        "error_rate": 0.021,
    },
    "cerebras/llama-3.3-70b": {
        "model": "cerebras/llama-3.3-70b",
        "pool": "pool-a (fallback)",
        "total_cases": 48,
        "accuracy": 0.833,
        "schema_compliance": 0.854,
        "latency_p50": 280,
        "latency_p95": 680,
        "cost_per_request": 0.000062,
        "avg_tokens_per_request": 920,
        "error_rate": 0.042,
    },
    "anthropic/claude-haiku-4-5-20251001": {
        "model": "anthropic/claude-haiku-4-5-20251001",
        "pool": "pool-b",
        "total_cases": 48,
        "accuracy": 0.938,
        "schema_compliance": 0.917,
        "latency_p50": 650,
        "latency_p95": 1800,
        "cost_per_request": 0.00032,
        "avg_tokens_per_request": 1100,
        "error_rate": 0.0,
    },
    "anthropic/claude-sonnet-4-5-20250514": {
        "model": "anthropic/claude-sonnet-4-5-20250514",
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
    "gemini/gemini-2.5-flash": "pool-a",
    "cerebras/llama-3.3-70b": "pool-a (fallback)",
    "anthropic/claude-haiku-4-5-20251001": "pool-b",
    "anthropic/claude-sonnet-4-5-20250514": "pool-b-upgrade",
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
