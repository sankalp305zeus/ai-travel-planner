import time
import uuid
import logging
import json
from contextvars import ContextVar
from typing import Callable
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

# Trigger configuration loading and validation
from backend import config

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

class PlanRequest(BaseModel):
    request: str

@app.post("/api/plan")
async def plan_trip(payload: PlanRequest):
    try:
        state = await run_travel_planner_graph(payload.request)
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

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in planning route: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "ok", "version": "0.1"}

