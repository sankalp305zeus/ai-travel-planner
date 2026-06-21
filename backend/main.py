import time
import uuid
import logging
import json
from contextvars import ContextVar
from typing import Callable
from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Trigger configuration loading and validation
from backend import config
from backend.instrumentation import setup_telemetry

setup_telemetry()

from backend.graph import run_travel_planner_graph

# ContextVar to store trace_id for the current request context
TRACE_ID_VAR: ContextVar[str] = ContextVar("trace_id", default="")

class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        trace_id = TRACE_ID_VAR.get()
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "trace_id": trace_id,
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_data)

# Configure JSON logging
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger = logging.getLogger("ai_travel_planner")
logger.setLevel(logging.INFO)
logger.addHandler(handler)
logger.propagate = False

app = FastAPI(title="AI Travel Planner API", version="0.1")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_trace_id_and_log(request: Request, call_next: Callable) -> Response:
    trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))
    token = TRACE_ID_VAR.set(trace_id)
    start_time = time.time()
    
    logger.info(f"Incoming request: {request.method} {request.url.path}")
    try:
        response = await call_next(request)
        process_time = (time.time() - start_time) * 1000
        logger.info(f"Completed request: {request.method} {request.url.path} - Status: {response.status_code} - Duration: {process_time:.2f}ms")
        response.headers["X-Trace-ID"] = trace_id
        return response
    except Exception as e:
        process_time = (time.time() - start_time) * 1000
        logger.error(f"Failed request: {request.method} {request.url.path} - Error: {str(e)} - Duration: {process_time:.2f}ms")
        raise e
    finally:
        TRACE_ID_VAR.reset(token)

from backend.schemas import AgentResult
import asyncio
from fastapi import BackgroundTasks
from fastapi.responses import StreamingResponse

class PlanRequest(BaseModel):
    request: str

plan_results = {}

async def run_graph_bg(request: str, plan_id: str):
    from backend.graph import run_travel_planner_graph, active_streams, emit_event
    try:
        active_streams[plan_id] = asyncio.Queue()
        state = await run_travel_planner_graph(request, plan_id=plan_id)
        plan_results[plan_id] = state
        
        status = "completed" if state.get("success", True) else "error"
        await emit_event(plan_id, {"status": status, "plan_id": plan_id})
        await active_streams[plan_id].put(None) # Sentinel
    except Exception as e:
        logger.error(f"Error in bg task: {e}")
        await emit_event(plan_id, {"status": "error", "plan_id": plan_id})
        if plan_id in active_streams:
            await active_streams[plan_id].put(None)

@app.post("/api/plan")
async def plan_trip(payload: PlanRequest, background_tasks: BackgroundTasks):
    plan_id = str(uuid.uuid4())
    background_tasks.add_task(run_graph_bg, payload.request, plan_id)
    return {"plan_id": plan_id}

@app.get("/api/plan/{plan_id}/stream")
async def stream_plan(plan_id: str):
    from backend.graph import active_streams
    async def event_generator():
        queue = active_streams.get(plan_id)
        if not queue:
            await asyncio.sleep(0.5)
            queue = active_streams.get(plan_id)
            if not queue:
                yield f'data: {{"status": "error", "error": "Not found"}}\n\n'
                return
        try:
            while True:
                event = await queue.get()
                if event is None:
                    break
                yield f"data: {json.dumps(event)}\n\n"
        finally:
            if plan_id in active_streams:
                del active_streams[plan_id]
                
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )

@app.get("/api/plan/{plan_id}/status")
async def get_plan_status(plan_id: str):
    if plan_id in plan_results:
        state = plan_results[plan_id]
        if not state.get("success", True):
            return {"status": "error", "error_detail": state.get("error_detail")}
        return {"status": "completed"}
    return {"status": "processing"}

@app.get("/api/plan/{plan_id}")
async def get_plan(plan_id: str):
    state = plan_results.get(plan_id)
    if not state:
        raise HTTPException(status_code=404, detail="Not found")
    if not state.get("success", True) or state.get("error_code"):
        return AgentResult(
            success=False,
            error_code=state.get("error_code"),
            error_detail=state.get("error_detail") or (state.get("errors")[0] if state.get("errors") else "Planning failed"),
            partial_data=state.get("draft_itinerary")
        )
    draft = state.get("draft_itinerary")
    if not draft:
        raise HTTPException(status_code=500, detail="Failed to construct itinerary draft.")
    return draft

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "0.1"}

