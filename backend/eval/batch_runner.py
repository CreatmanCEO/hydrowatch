"""Model evaluation pipeline.

Runs eval_dataset.jsonl against multiple models, collects responses,
and computes comparison metrics.

NOTE: Current implementation uses sequential API calls for simplicity.
Production optimization: use Gemini Batch API (google.genai.Client.batches.create)
for 50% cost reduction and parallel processing.
See: https://ai.google.dev/gemini-api/docs/batch-api
"""
import asyncio
import json
import time
from pathlib import Path

import litellm

from eval.metrics import (
    EvalResult,
    aggregate_metrics,
    check_tool_call_accuracy,
    validate_schema_compliance,
    check_fields_present,
    save_results,
)
from models.tool_schemas import TOOL_DEFINITIONS
from services.prompt_engine import PromptEngine
from services.context_bridge import load_wells_data, build_context_prompt
from services.tool_executor import ToolExecutor
from services.llm_router import get_model_for_task, TASK_ROUTING
from models.schemas import MapContext
from config import get_settings

# Default map context for eval
DEFAULT_CONTEXT = MapContext(
    center_lat=24.42,
    center_lng=54.85,
    zoom=10,
    bbox=[54.0, 24.0, 56.0, 25.0],
    active_layers=["wells"],
)


def load_eval_dataset(path: str | None = None) -> list[dict]:
    """Load evaluation test cases from JSONL."""
    if path is None:
        path = str(Path(__file__).parent / "eval_dataset.jsonl")

    cases = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                cases.append(json.loads(line))
    return cases


async def run_single_case(
    case: dict,
    model: str,
    prompt_engine: PromptEngine,
    wells_data: dict,
    tool_executor: ToolExecutor,
    settings,
) -> EvalResult:
    """Run a single eval case against a model."""
    # Classify task
    task_type = case.get("expected_tool") or "general_question"
    model_pool = get_model_for_task(task_type)

    # Build prompt
    context_section = build_context_prompt(DEFAULT_CONTEXT, wells_data)
    system_prompt = prompt_engine.build(
        model_pool=model_pool,
        task_type=task_type,
        context_section=context_section,
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": case["input"]},
    ]

    start_time = time.time()
    tool_calls_made = []
    output = {}
    error = None
    tokens_in = 0
    tokens_out = 0
    llm_response = None

    try:
        # Direct call (not via Router) — eval targets specific model, not pool
        llm_response = await litellm.acompletion(
            model=model,
            messages=messages,
            tools=TOOL_DEFINITIONS,
            temperature=0.1,
            timeout=30,
        )

        latency_ms = int((time.time() - start_time) * 1000)

        # Extract usage
        if llm_response.usage:
            tokens_in = llm_response.usage.prompt_tokens or 0
            tokens_out = llm_response.usage.completion_tokens or 0

        # Extract tool calls
        choice = llm_response.choices[0]
        if choice.message.tool_calls:
            for tc in choice.message.tool_calls:
                tool_call_info = {
                    "name": tc.function.name,
                    "arguments": tc.function.arguments,
                }
                tool_calls_made.append(tool_call_info)

                # Execute tool
                try:
                    args = json.loads(tc.function.arguments)
                except json.JSONDecodeError:
                    args = {}
                result = tool_executor.execute(tc.function.name, args)
                if result.success:
                    output = result.result
        else:
            # Text response
            output = {"text": choice.message.content or ""}

    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        error = str(e)
        output = {"error": str(e)}

    # Evaluate
    correct_tool = check_tool_call_accuracy(case.get("expected_tool"), tool_calls_made)

    schema_valid = False
    if isinstance(output, dict):
        schema_valid = validate_schema_compliance(output)
    elif isinstance(output, list) and output:
        schema_valid = all(validate_schema_compliance(item) for item in output if isinstance(item, dict))

    fields_present = check_fields_present(case.get("expected_fields", []), output)

    # Estimate cost (LiteLLM first, manual fallback)
    cost_usd = estimate_cost(model, tokens_in, tokens_out, response=llm_response)

    return EvalResult(
        case_id=case["id"],
        model=model,
        input_text=case["input"],
        expected_tool=case.get("expected_tool"),
        actual_tool_calls=tool_calls_made,
        output=output,
        correct_tool=correct_tool,
        schema_valid=schema_valid,
        fields_present=fields_present,
        latency_ms=latency_ms,
        tokens_in=tokens_in,
        tokens_out=tokens_out,
        cost_usd=cost_usd,
        error=error,
    )


def estimate_cost(model: str, tokens_in: int, tokens_out: int, response=None) -> float:
    """Estimate cost per request. Uses LiteLLM cost estimation if available, falls back to manual pricing."""
    if response:
        try:
            cost = litellm.completion_cost(completion_response=response)
            if cost and cost > 0:
                return round(cost, 6)
        except Exception:
            pass

    # Fallback: manual approximate pricing (USD per 1M tokens)
    pricing = {
        "openrouter/anthropic/claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.00},
        "openrouter/anthropic/claude-sonnet-4-5-20250514": {"input": 3.00, "output": 15.00},
        "gemini/gemini-2.5-flash": {"input": 0.15, "output": 0.60},
    }

    rates = pricing.get(model, {"input": 1.0, "output": 3.0})
    cost = (tokens_in * rates["input"] + tokens_out * rates["output"]) / 1_000_000
    return round(cost, 6)


async def run_eval(
    models: list[str] | None = None,
    dataset_path: str | None = None,
    output_dir: str | None = None,
) -> dict:
    """Run full evaluation pipeline."""
    if models is None:
        settings = get_settings()
        models = [
            settings.model_pool_a_primary,
            settings.model_pool_b_default,
        ]

    if output_dir is None:
        output_dir = str(Path(__file__).parent / "results")
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    cases = load_eval_dataset(dataset_path)
    wells_data = load_wells_data()
    prompt_engine = PromptEngine()
    tool_executor = ToolExecutor()
    settings = get_settings()

    all_results: list[EvalResult] = []

    for model in models:
        print(f"\n=== Evaluating: {model} ===")
        model_results = []

        for i, case in enumerate(cases):
            print(f"  [{i+1}/{len(cases)}] {case['id']}: {case['input'][:50]}...")
            result = await run_single_case(
                case, model, prompt_engine, wells_data, tool_executor, settings
            )
            model_results.append(result)
            all_results.append(result)

        # Save per-model results
        save_results(model_results, f"{output_dir}/{model.replace('/', '_')}_results.jsonl")

    # Aggregate metrics
    metrics = aggregate_metrics(all_results)

    # Save summary
    summary = {m: v.to_dict() for m, v in metrics.items()}
    with open(f"{output_dir}/summary.json", "w") as f:
        json.dump(summary, f, indent=2)

    print("\n=== Summary ===")
    for model_name, m in metrics.items():
        print(f"\n{model_name}:")
        print(f"  Accuracy: {m.accuracy:.1%}")
        print(f"  Schema compliance: {m.schema_compliance:.1%}")
        print(f"  Latency p50/p95: {m.latency_p50:.0f}ms / {m.latency_p95:.0f}ms")
        print(f"  Cost/request: ${m.cost_per_request:.6f}")
        print(f"  Error rate: {m.error_rate:.1%}")

    return summary


if __name__ == "__main__":
    asyncio.run(run_eval())
