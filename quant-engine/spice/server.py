"""Orchestrator HTTP/SSE server (FastAPI :8000).

Serves the frontend exactly per spice-frontend/lib/types.ts + API_CONTRACT.md:
  GET  /api/company              -> the hero company (real engine output)
  POST /api/run[?mock=true]      -> start a run, returns {run_id}
  GET  /api/run/{id}/events      -> Server-Sent Events stream of RunEvent
  POST /api/run/{id}/trigger     -> fire the climax (operator-controlled)

mock=true streams the deterministic scripted scenario (no LLM, no network) — the
bulletproof fallback. The live path (default) runs the Opus agent (spice.agent);
until that's wired it falls back to the scripted producer so the pipeline works.

Run:  uvicorn spice.server:app --port 8000
"""

from __future__ import annotations

import asyncio
import json
import uuid
from dataclasses import dataclass, field

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from . import agent, scenario
from .company_view import company_view

STEP_DELAY = 0.9       # seconds between streamed events (demo pacing)
AUTO_TRIGGER = 9.0     # auto-fire the climax if the operator doesn't (safety)

app = FastAPI(title="Spice orchestrator", version="0.1.0")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)


@dataclass
class Run:
    queue: "asyncio.Queue[dict | None]" = field(default_factory=asyncio.Queue)
    trigger: asyncio.Event = field(default_factory=asyncio.Event)
    task: asyncio.Task | None = None


RUNS: dict[str, Run] = {}


async def _emit(run: Run, events: list[dict]) -> None:
    for ev in events:
        await run.queue.put(ev)
        await asyncio.sleep(STEP_DELAY)


async def _scripted_producer(run: Run) -> None:
    """The mock / fallback run: stream pre-trigger, pause for the operator, then post."""
    try:
        await _emit(run, scenario.mock_pre())
        try:
            await asyncio.wait_for(run.trigger.wait(), timeout=AUTO_TRIGGER)
        except asyncio.TimeoutError:
            pass  # auto-fire the climax
        await _emit(run, scenario.mock_post())
    finally:
        await run.queue.put(None)  # sentinel: stream complete


async def _agent_producer(run: Run) -> None:
    """The live run: the Opus agent emits the pre-trigger beats, then the operator
    fires the on-chain climax (the scripted payout tail, reused)."""
    async def emit(ev: dict) -> None:
        await run.queue.put(ev)
        await asyncio.sleep(STEP_DELAY * 0.5)

    try:
        await agent.run_agent(emit)
        try:
            await asyncio.wait_for(run.trigger.wait(), timeout=AUTO_TRIGGER)
        except asyncio.TimeoutError:
            pass
        await _emit(run, scenario.mock_post())
    except Exception as e:  # never hang the stream on an agent error
        await run.queue.put({"type": "agent_message", "who": "Orchestrator",
                             "text": f"(agent error, falling back) {e}"})
        await _emit(run, scenario.mock_post())
    finally:
        await run.queue.put(None)


@app.get("/health")
async def health() -> dict:
    return {"ok": True}


@app.get("/api/company")
async def api_company() -> dict:
    return company_view()


@app.post("/api/run")
async def api_run(mock: bool = False) -> dict:
    run_id = f"r_{uuid.uuid4().hex[:8]}"
    run = Run()
    RUNS[run_id] = run
    # mock or no API key -> deterministic scripted run; otherwise the live Opus agent.
    producer = _scripted_producer if (mock or not agent.has_key()) else _agent_producer
    run.task = asyncio.create_task(producer(run))
    return {"run_id": run_id}


@app.get("/api/run/{run_id}/events")
async def api_events(run_id: str) -> StreamingResponse:
    run = RUNS.get(run_id)

    async def gen():
        if run is None:
            yield f"data: {json.dumps({'type': 'agent_message', 'text': 'unknown run'})}\n\n"
            return
        while True:
            ev = await run.queue.get()
            if ev is None:
                break
            yield f"data: {json.dumps(ev, ensure_ascii=False)}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")


@app.post("/api/run/{run_id}/trigger")
async def api_trigger(run_id: str) -> dict:
    run = RUNS.get(run_id)
    if run:
        run.trigger.set()
    return {"ok": run is not None}
