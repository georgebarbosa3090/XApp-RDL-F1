"""
Servidor Live de Simulação dos 6 Blocos O-RAN em Malha Fechada (FastAPI + SSE).
Skill: 09-cognitive-conflict-orchestrator & 08-ns3-oran-simulation-specialist

Fornece o backend de streaming em tempo real para o Dashboard 6-Panes na mesma tela.
"""

import os
import json
import asyncio
import logging
from typing import Dict, Any
from pathlib import Path

from fastapi import FastAPI, Response, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.observability.live_rich_simulation_engine import simulation_engine

logger = logging.getLogger("Live6PaneServer")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="O-RAN Cognitive Twin 6-Pane Live Server", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

WEB_DIR = Path(__file__).parent / "web"
INDEX_PATH = WEB_DIR / "index.html"


class ScenarioPayload(BaseModel):
    scenario: str


class PausePayload(BaseModel):
    paused: bool


@app.get("/", response_class=HTMLResponse)
async def get_index():
    if INDEX_PATH.exists():
        return HTMLResponse(content=INDEX_PATH.read_text(encoding="utf-8"))
    return HTMLResponse(content="<h1>Dashboard HTML not found.</h1>", status_code=404)


@app.get("/api/state")
async def get_current_state():
    return simulation_engine.get_full_state()


@app.post("/api/scenario")
async def set_scenario(payload: ScenarioPayload):
    simulation_engine.trigger_scenario(payload.scenario)
    logger.info("Cenário de simulação alterado para: %s", payload.scenario)
    return {"status": "OK", "scenario": payload.scenario}


@app.post("/api/pause")
async def set_pause(payload: PausePayload):
    simulation_engine.is_paused = payload.paused
    logger.info("Estado de pausa da simulação alterado para: %s", payload.paused)
    return {"status": "OK", "is_paused": simulation_engine.is_paused}


@app.get("/api/stream")
async def stream_live_events(request: Request):
    """Gera um stream SSE (Server-Sent Events) contínuo sincronizado a 1 Hz."""

    async def event_generator():
        while True:
            if await request.is_disconnected():
                break

            state = simulation_engine.step()
            payload = json.dumps(state)
            yield f"data: {payload}\n\n"
            await asyncio.sleep(0.8)  # Atualização a cada 800 ms

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


def start_server(host: str = "0.0.0.0", port: int = 8888):
    """Inicia o servidor uvicorn standalone."""
    import uvicorn
    uvicorn.run(app, host=host, port=port, log_level="info")


if __name__ == "__main__":
    start_server()
