# Aurelinth — FastAPI SSE Monitor
import json
import subprocess
import asyncio
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
from memory import get_redis
from monitor.api.events import redis_event_stream

app = FastAPI(title="Aurelinth Monitor")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/full")
def health_full():
    from orchestrator.health import health_summary
    return health_summary()


@app.get("/stream")
async def stream():
    """SSE endpoint — browser connects here for real-time events."""
    r = get_redis()
    return EventSourceResponse(redis_event_stream(r))


@app.get("/events/history")
def history(limit: int = 100):
    """Recent events from Redis Stream for initial page load."""
    r = get_redis()
    try:
        results = r.xrevrange("aurelinth:events", count=limit)
        events = []
        for msg_id, fields in reversed(results):
            events.append({
                "id": msg_id,
                "type": fields.get("type", "unknown"),
                "data": json.loads(fields.get("data", "{}"))
            })
        return {"events": events}
    except Exception as e:
        return {"events": [], "error": str(e)}


@app.post("/run")
async def run_pipeline(
    target: str,
    notes: str = "",
    flag_format: str = "",
    local_target: str = "",
    source_code: str = "",
):
    """Start pipeline in background subprocess."""
    # Clear stale Redis task sets before new run
    r = get_redis()
    r.delete("aurelinth:tasks:done", "aurelinth:tasks:failed")

    cmd = ["python3", "run.py", target]
    if notes:
        cmd += ["--notes", notes]
    if flag_format:
        cmd += ["--flag-format", flag_format]
    if local_target:
        cmd += ["--local-target", local_target]
    if source_code:
        cmd += ["--source-code", source_code]

    subprocess.Popen(
        cmd,
        cwd="/home/foqs/aurelinth",
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    mode = "whitebox" if source_code else "blackbox"
    return {"status": "started", "target": target, "mode": mode}


@app.get("/tasks")
def get_tasks():
    """Current task statuses from Redis."""
    r = get_redis()
    done = r.smembers("aurelinth:tasks:done") or set()
    failed = r.smembers("aurelinth:tasks:failed") or set()
    return {
        "done": list(done),
        "failed": list(failed),
    }