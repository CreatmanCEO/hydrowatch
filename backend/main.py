"""FastAPI application — SSE chat, wells API, CSV upload, healthcheck."""
import json
import time
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel as _BaseModel

from config import get_settings
from models.schemas import ChatRequest, ChatResponse, MapContext
from services.context_bridge import build_context_prompt, load_wells_data
from services.llm_router import (
    create_router,
    get_model_for_task,
    build_system_prompt,
    TASK_ROUTING,
)
from services.tool_executor import ToolExecutor
from models.tool_schemas import TOOL_DEFINITIONS
from eval.metrics_api import router as metrics_router

settings = get_settings()

# Sync DATA_DIR env var so tools use the same path as config
os.environ["DATA_DIR"] = settings.data_dir

# Singletons
tool_executor = ToolExecutor()
wells_data: dict = {}
llm_router = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global wells_data, llm_router
    wells_data = load_wells_data()
    try:
        llm_router = create_router()
    except Exception:
        # LLM router may fail without API keys — app still serves data endpoints
        llm_router = None
    yield


def _ensure_wells_loaded():
    """Lazy-load wells data if not loaded yet (e.g., in tests without lifespan)."""
    global wells_data
    if not wells_data:
        wells_data = load_wells_data()


app = FastAPI(
    title="HydroWatch API",
    description="AI-powered groundwater monitoring system for Abu Dhabi aquifer management. "
                "Provides well monitoring, anomaly detection, and LLM-assisted analysis.",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Metrics router
app.include_router(metrics_router)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@app.get("/api/health", tags=["health"])
async def health():
    _ensure_wells_loaded()
    return {
        "status": "ok",
        "wells_loaded": len(wells_data),
        "llm_available": llm_router is not None,
    }


# ---------------------------------------------------------------------------
# Wells API
# ---------------------------------------------------------------------------

@app.get("/api/wells", tags=["wells"])
async def get_wells():
    """Return wells GeoJSON."""
    geojson_path = Path(settings.data_dir) / "wells.geojson"
    with open(geojson_path) as f:
        return json.load(f)


# ---------------------------------------------------------------------------
# Theis tools (direct HTTP for frontend map layers)
# ---------------------------------------------------------------------------

class _InterferenceRequest(_BaseModel):
    bbox: list[float] | None = None
    t_days: int = 30
    min_coefficient: float = 0.10


@app.post("/api/tools/analyze_interference", tags=["tools"])
async def api_analyze_interference(req: _InterferenceRequest):
    from tools.analyze_interference import analyze_interference
    result = analyze_interference(
        bbox=req.bbox, t_days=req.t_days, min_coefficient=req.min_coefficient
    )
    return result.model_dump()


class _DrawdownRequest(_BaseModel):
    well_id: str
    t_days: int = 30
    extent_km: float = 5
    resolution: int = 50


@app.post("/api/tools/compute_drawdown_grid", tags=["tools"])
async def api_compute_drawdown_grid(req: _DrawdownRequest):
    from tools.compute_drawdown_grid import compute_drawdown_grid
    result = compute_drawdown_grid(
        well_id=req.well_id,
        t_days=req.t_days,
        extent_km=req.extent_km,
        resolution=req.resolution,
    )
    return result.model_dump()


@app.get("/api/wells/{well_id}/history", tags=["wells"])
async def get_well_history_endpoint(
    well_id: str,
    parameter: str = "debit_ls",
    last_n_days: int | None = None,
):
    """Return time series for a well."""
    result = tool_executor.execute("get_well_history", {
        "well_id": well_id,
        "parameter": parameter,
        "last_n_days": last_n_days,
    })
    if not result.success:
        raise HTTPException(status_code=404, detail=result.error)
    return result.result


# ---------------------------------------------------------------------------
# CSV Upload
# ---------------------------------------------------------------------------

@app.post("/api/upload/csv", tags=["upload"])
async def upload_csv(file: UploadFile = File(...)):
    """Upload and validate a CSV file."""
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a .csv")

    max_size = settings.max_csv_size_mb * 1024 * 1024
    contents = await file.read()
    if len(contents) > max_size:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Max: {settings.max_csv_size_mb}MB",
        )

    # Save to temp file for validation
    upload_dir = Path(settings.data_dir) / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    temp_path = upload_dir / Path(file.filename).name
    temp_path.write_bytes(contents)

    try:
        result = tool_executor.execute("validate_csv", {"file_path": str(temp_path)})
        return result.result
    finally:
        temp_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Chat SSE Streaming
# ---------------------------------------------------------------------------

def _classify_task(message: str) -> str:
    """Heuristic classifier — order matters: most specific first."""
    msg = message.lower()

    if any(w in msg for w in ["depression cone", "drawdown", "isoline", "voronka", "влияние на уровень"]):
        return "drawdown_analysis"
    if any(w in msg for w in ["interference", "competing wells", "cone overlap", "mutual influence", "wells competing"]):
        return "interference_analysis"
    if any(w in msg for w in ["water quality", "drinking water", "salinity"]) or (
        "tds" in msg or "chloride" in msg or "ph levels" in msg
    ):
        return "water_quality_report"
    if any(w in msg for w in ["compare cluster", "cross-cluster", "between cluster"]):
        return "cluster_comparison"
    if any(w in msg for w in ["daily report", "daily monitoring", "daily summary"]):
        return "daily_report"
    if any(w in msg for w in ["trend", "time series", "history of"]):
        return "trend_analysis"
    if any(w in msg for w in ["csv", "upload", "validate", "file"]):
        return "validate_csv"
    if any(w in msg for w in ["anomal", "decline", "spike", "fault", "problem", "scan"]):
        return "detect_anomalies"
    if any(w in msg for w in ["calibrat", "optimi", "theis", "pumping schedule"]):
        return "calibration_advice"
    if any(w in msg for w in ["interpret", "why", "cause", "explain", "reason", "root cause"]):
        return "interpret_anomaly"
    if any(w in msg for w in ["region", "area", "viewport", "overview", "stats", "summary", "report"]):
        return "get_region_stats"
    if any(w in msg for w in ["find", "search", "list", "wells", "query", "status", "active", "inactive"]):
        return "query_wells"
    return "general_question"


@app.post("/api/chat/stream", tags=["chat"])
async def chat_stream(request: ChatRequest):
    """SSE streaming chat endpoint with tool calling."""

    async def generate() -> AsyncIterator[str]:
        start_time = time.time()
        _ensure_wells_loaded()

        # 1. Build context from map state
        context_section = build_context_prompt(request.map_context, wells_data)

        # 2. Classify task and route to model pool
        task_type = _classify_task(request.message)
        model_pool = get_model_for_task(task_type)

        # 3. Determine output type
        output_type = "text_response"
        if task_type == "detect_anomalies":
            output_type = "anomaly_card"
        elif task_type == "validate_csv":
            output_type = "validation_card"

        # 4. Build system prompt via PromptEngine
        system_prompt = build_system_prompt(
            model_pool=model_pool,
            task_type=task_type,
            context_section=context_section,
            output_type=output_type,
        )

        # 5. Send metadata event
        yield f"data: {json.dumps({'type': 'meta', 'model_pool': model_pool, 'task_type': task_type})}\n\n"

        if llm_router is None:
            # Fallback: no LLM available, use tools directly
            yield f"data: {json.dumps({'type': 'token', 'content': 'LLM not configured. Running tool directly...'})}\n\n"

            # Map non-tool task types to nearest real tool for fallback
            fallback_task = task_type
            if task_type in ("interpret_anomaly", "calibration_advice", "general_question"):
                fallback_task = "detect_anomalies" if task_type == "interpret_anomaly" else "query_wells"

            tool_result = tool_executor.execute(fallback_task, _build_tool_args(fallback_task, request))
            yield f"data: {json.dumps({'type': 'tool_result', 'tool': fallback_task, 'success': tool_result.success, 'result': tool_result.result})}\n\n"
            if not tool_result.success:
                yield f"data: {json.dumps({'type': 'error', 'message': tool_result.error})}\n\n"

            yield "data: [DONE]\n\n"
            return

        # 6. Call LLM with tools via streaming
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": request.message},
        ]

        try:
            response = await llm_router.acompletion(
                model=model_pool,
                messages=messages,
                tools=TOOL_DEFINITIONS,
                stream=True,
                temperature=settings.llm_temperature,
            )

            collected_content = ""
            tool_calls_buffer = []

            async for chunk in response:
                delta = chunk.choices[0].delta if chunk.choices else None
                if delta is None:
                    continue

                # Stream text content
                if delta.content:
                    collected_content += delta.content
                    yield f"data: {json.dumps({'type': 'token', 'content': delta.content})}\n\n"

                # Collect tool calls (arguments arrive in chunks during streaming)
                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        if tc.index is not None:
                            while len(tool_calls_buffer) <= tc.index:
                                tool_calls_buffer.append({"name": "", "arguments": ""})
                            if tc.function and tc.function.name:
                                tool_calls_buffer[tc.index]["name"] = tc.function.name
                            if tc.function and tc.function.arguments:
                                tool_calls_buffer[tc.index]["arguments"] += tc.function.arguments

            # 7. Execute ALL tool calls, then ONE follow-up
            if tool_calls_buffer:
                # Parse all tool call arguments
                parsed_calls = []
                for tc in tool_calls_buffer:
                    try:
                        args = json.loads(tc["arguments"]) if isinstance(tc["arguments"], str) else tc["arguments"]
                    except json.JSONDecodeError:
                        args = {}
                    parsed_calls.append((tc, args))

                # Build single assistant message with all tool calls
                assistant_tool_calls = [
                    {"id": f"call_{tc['name']}_{i}", "type": "function",
                     "function": {"name": tc["name"], "arguments": json.dumps(args)}}
                    for i, (tc, args) in enumerate(parsed_calls)
                ]
                messages.append({"role": "assistant", "content": collected_content or None, "tool_calls": assistant_tool_calls})

                # Execute all tools and add results
                for i, (tc, args) in enumerate(parsed_calls):
                    yield f"data: {json.dumps({'type': 'tool_call', 'tool': tc['name'], 'args': args})}\n\n"
                    tool_result = tool_executor.execute(tc["name"], args)
                    yield f"data: {json.dumps({'type': 'tool_result', 'tool': tc['name'], 'success': tool_result.success, 'result': tool_result.result})}\n\n"
                    messages.append({"role": "tool", "tool_call_id": f"call_{tc['name']}_{i}", "content": json.dumps(tool_result.result)})

                # ONE follow-up call with all tool results
                # No tools param — force text response, prevent LLM from attempting more tool calls as text
                followup = await llm_router.acompletion(
                    model=model_pool,
                    messages=messages,
                    stream=True,
                    temperature=settings.llm_temperature,
                )
                async for chunk in followup:
                    delta = chunk.choices[0].delta if chunk.choices else None
                    if delta and delta.content:
                        yield f"data: {json.dumps({'type': 'token', 'content': delta.content})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

        # 8. Done
        elapsed = int((time.time() - start_time) * 1000)
        yield f"data: {json.dumps({'type': 'done', 'latency_ms': elapsed})}\n\n"
        yield "data: [DONE]\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


def _build_tool_args(task_type: str, request: ChatRequest) -> dict:
    """Build tool arguments from request context (fallback when no LLM)."""
    ctx = request.map_context
    if task_type in ("query_wells", "get_region_stats"):
        return {"bbox": ctx.bbox}
    if task_type == "detect_anomalies":
        return {"well_id": ctx.selected_well_id} if ctx.selected_well_id else {}
    if task_type == "get_well_history" and ctx.selected_well_id:
        return {"well_id": ctx.selected_well_id}
    return {}
