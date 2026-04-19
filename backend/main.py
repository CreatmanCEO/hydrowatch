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

settings = get_settings()

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
    description="AI-powered groundwater monitoring assistant",
    version="0.1.0",
    lifespan=lifespan,
)

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

@app.get("/api/health")
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

@app.get("/api/wells")
async def get_wells():
    """Return wells GeoJSON."""
    geojson_path = Path(settings.data_dir) / "wells.geojson"
    with open(geojson_path) as f:
        return json.load(f)


@app.get("/api/wells/{well_id}/history")
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

@app.post("/api/upload/csv")
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
    temp_path = upload_dir / file.filename
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
    """Simple heuristic to classify user message into task type."""
    msg = message.lower()
    if any(w in msg for w in ["csv", "upload", "validate", "file"]):
        return "validate_csv"
    if any(w in msg for w in ["anomal", "decline", "spike", "fault", "problem"]):
        return "detect_anomalies"
    if any(w in msg for w in ["history", "trend", "time series", "chart"]):
        return "get_well_history"
    if any(w in msg for w in ["region", "area", "viewport", "overview", "stats"]):
        return "get_region_stats"
    if any(w in msg for w in ["find", "search", "list", "wells", "query"]):
        return "query_wells"
    if any(w in msg for w in ["interpret", "why", "cause", "explain", "reason"]):
        return "interpret_anomaly"
    if any(w in msg for w in ["calibrat", "optimi", "theis", "pumping schedule"]):
        return "calibration_advice"
    return "general_question"


@app.post("/api/chat/stream")
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

            tool_result = tool_executor.execute(task_type, _build_tool_args(task_type, request))
            if tool_result.success:
                yield f"data: {json.dumps({'type': 'tool_result', 'tool': task_type, 'result': tool_result.result})}\n\n"
            else:
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

                # Collect tool calls
                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        if tc.function:
                            tool_calls_buffer.append({
                                "name": tc.function.name,
                                "arguments": tc.function.arguments,
                            })

            # 7. Execute tool calls if any
            for tc in tool_calls_buffer:
                try:
                    args = json.loads(tc["arguments"]) if isinstance(tc["arguments"], str) else tc["arguments"]
                except json.JSONDecodeError:
                    args = {}

                yield f"data: {json.dumps({'type': 'tool_call', 'tool': tc['name'], 'args': args})}\n\n"

                tool_result = tool_executor.execute(tc["name"], args)
                yield f"data: {json.dumps({'type': 'tool_result', 'tool': tc['name'], 'success': tool_result.success, 'result': tool_result.result})}\n\n"

                # Feed tool result back to LLM for final response
                messages.append({"role": "assistant", "content": collected_content, "tool_calls": [
                    {"id": f"call_{tc['name']}", "type": "function", "function": {"name": tc["name"], "arguments": json.dumps(args)}}
                ]})
                messages.append({"role": "tool", "tool_call_id": f"call_{tc['name']}", "content": json.dumps(tool_result.result)})

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
