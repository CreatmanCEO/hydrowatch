"""Safe tool execution layer with validation and error handling."""

from typing import Any

from models.schemas import ToolResult
from models.tool_schemas import TOOL_DEFINITIONS
from tools.analyze_interference import analyze_interference
from tools.compute_drawdown_grid import compute_drawdown_grid
from tools.detect_anomalies import detect_anomalies
from tools.get_region_stats import get_region_stats
from tools.get_well_history import get_well_history
from tools.query_wells import query_wells
from tools.validate_csv import validate_csv


class ToolExecutor:
    """Execute tools safely with validation and error handling."""

    def __init__(self):
        self._registry: dict[str, callable] = {
            "validate_csv": self._exec_validate_csv,
            "query_wells": self._exec_query_wells,
            "detect_anomalies": self._exec_detect_anomalies,
            "get_well_history": self._exec_get_well_history,
            "get_region_stats": self._exec_get_region_stats,
            "analyze_interference": self._exec_analyze_interference,
            "compute_drawdown_grid": self._exec_compute_drawdown_grid,
        }

    def execute(self, tool_name: str, arguments: dict[str, Any]) -> ToolResult:
        """Execute a tool by name with given arguments."""
        if tool_name not in self._registry:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                result={},
                error=f"Unknown tool: {tool_name}. Available: {', '.join(self._registry.keys())}",
            )

        try:
            result = self._registry[tool_name](arguments)
            return ToolResult(
                tool_name=tool_name,
                success=True,
                result=result,
            )
        except Exception as e:
            return ToolResult(
                tool_name=tool_name,
                success=False,
                result={},
                error=f"{type(e).__name__}: {str(e)}",
            )

    def get_tool_definitions(self) -> list[dict]:
        """Return JSON Schema tool definitions for LLM."""
        return TOOL_DEFINITIONS

    # --- Tool wrappers (serialize Pydantic to dict/list) ---

    @staticmethod
    def _exec_validate_csv(args: dict) -> dict:
        result = validate_csv(
            file_path=args["file_path"],
            expected_columns=args.get("expected_columns"),
        )
        return result.model_dump()

    @staticmethod
    def _exec_query_wells(args: dict) -> list:
        wells = query_wells(
            bbox=args.get("bbox"),
            status=args.get("status"),
            cluster_id=args.get("cluster_id"),
        )
        return [w.model_dump() for w in wells]

    @staticmethod
    def _exec_detect_anomalies(args: dict) -> list:
        cards = detect_anomalies(well_id=args.get("well_id"))
        return [c.model_dump() for c in cards]

    @staticmethod
    def _exec_get_well_history(args: dict) -> dict:
        history = get_well_history(
            well_id=args["well_id"],
            parameter=args.get("parameter", "debit_ls"),
            last_n_days=args.get("last_n_days"),
        )
        return history.model_dump()

    @staticmethod
    def _exec_get_region_stats(args: dict) -> dict:
        stats = get_region_stats(bbox=args["bbox"])
        return stats.model_dump()

    @staticmethod
    def _exec_analyze_interference(args: dict) -> dict:
        result = analyze_interference(
            bbox=args.get("bbox"),
            t_days=args.get("t_days", 30),
            min_coefficient=args.get("min_coefficient", 0.10),
        )
        return result.model_dump()

    @staticmethod
    def _exec_compute_drawdown_grid(args: dict) -> dict:
        result = compute_drawdown_grid(
            well_id=args["well_id"],
            t_days=args.get("t_days", 30),
            extent_km=args.get("extent_km", 5),
            resolution=args.get("resolution", 50),
        )
        return result.model_dump()
