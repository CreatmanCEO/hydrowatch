"""Evaluation metrics for model comparison."""

import json
from dataclasses import asdict, dataclass, field

import numpy as np
from pydantic import ValidationError

from models.schemas import AnomalyCard, RegionStats, ValidationResult, WellHistory


@dataclass
class ModelMetrics:
    """Aggregated metrics for a single model."""

    model: str
    total_cases: int = 0
    # Accuracy
    correct_tool_calls: int = 0
    accuracy: float = 0.0
    # Schema compliance
    schema_valid_count: int = 0
    schema_compliance: float = 0.0
    # Latency
    latencies_ms: list[int] = field(default_factory=list)
    latency_p50: float = 0.0
    latency_p95: float = 0.0
    # Cost
    total_cost_usd: float = 0.0
    cost_per_request: float = 0.0
    # Tokens
    total_tokens_in: int = 0
    total_tokens_out: int = 0
    avg_tokens_per_request: float = 0.0
    # Errors
    error_count: int = 0
    error_rate: float = 0.0

    def finalize(self):
        """Calculate derived metrics."""
        if self.total_cases > 0:
            self.accuracy = self.correct_tool_calls / self.total_cases
            self.schema_compliance = self.schema_valid_count / self.total_cases
            self.cost_per_request = self.total_cost_usd / self.total_cases
            self.avg_tokens_per_request = (
                self.total_tokens_in + self.total_tokens_out
            ) / self.total_cases
            self.error_rate = self.error_count / self.total_cases

        if self.latencies_ms:
            arr = np.array(self.latencies_ms)
            self.latency_p50 = float(np.percentile(arr, 50))
            self.latency_p95 = float(np.percentile(arr, 95))

    def to_dict(self) -> dict:
        """Serialize for API response (exclude raw latencies)."""
        d = asdict(self)
        d.pop("latencies_ms")
        return d


SCHEMA_VALIDATORS = {
    "anomaly_card": AnomalyCard,
    "validation_result": ValidationResult,
    "region_stats": RegionStats,
    "well_history": WellHistory,
}


def validate_schema_compliance(output: dict) -> bool:
    """Check if output conforms to expected Pydantic schema."""
    output_type = output.get("type")
    if not output_type or output_type not in SCHEMA_VALIDATORS:
        return False

    try:
        SCHEMA_VALIDATORS[output_type](**output)
        return True
    except (ValidationError, TypeError):
        return False


def check_tool_call_accuracy(
    expected_tool: str | None,
    actual_tool_calls: list[dict],
) -> bool:
    """Check if the model called the correct tool."""
    if expected_tool is None:
        # Edge case: no tool expected, model should not call tools
        return len(actual_tool_calls) == 0

    actual_tools = {tc.get("name") for tc in actual_tool_calls}
    return expected_tool in actual_tools


def check_fields_present(
    expected_fields: list[str],
    output: dict | list,
) -> bool:
    """Check if expected fields are present in output."""
    if not expected_fields:
        return True

    if isinstance(output, list):
        if not output:
            return False
        # Check first item
        output = output[0]

    if not isinstance(output, dict):
        return False

    return all(f in output for f in expected_fields)


@dataclass
class EvalResult:
    """Single evaluation result."""

    case_id: str
    model: str
    input_text: str
    expected_tool: str | None
    actual_tool_calls: list[dict]
    output: dict | list | str
    correct_tool: bool
    schema_valid: bool
    fields_present: bool
    latency_ms: int
    tokens_in: int
    tokens_out: int
    cost_usd: float
    error: str | None = None


def aggregate_metrics(results: list[EvalResult]) -> dict[str, ModelMetrics]:
    """Aggregate individual results into per-model metrics."""
    models: dict[str, ModelMetrics] = {}

    for r in results:
        if r.model not in models:
            models[r.model] = ModelMetrics(model=r.model)

        m = models[r.model]
        m.total_cases += 1
        m.latencies_ms.append(r.latency_ms)
        m.total_tokens_in += r.tokens_in
        m.total_tokens_out += r.tokens_out
        m.total_cost_usd += r.cost_usd

        if r.correct_tool:
            m.correct_tool_calls += 1
        if r.schema_valid:
            m.schema_valid_count += 1
        if r.error:
            m.error_count += 1

    for m in models.values():
        m.finalize()

    return models


def save_results(results: list[EvalResult], output_path: str):
    """Save evaluation results to JSONL."""
    with open(output_path, "w") as f:
        for r in results:
            f.write(json.dumps(asdict(r), default=str) + "\n")


def load_results(input_path: str) -> list[EvalResult]:
    """Load evaluation results from JSONL."""
    results = []
    with open(input_path) as f:
        for line in f:
            data = json.loads(line)
            results.append(EvalResult(**data))
    return results
