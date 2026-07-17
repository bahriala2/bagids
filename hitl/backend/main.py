"""
BAg-IDS — Human-in-the-Loop Layer : application FastAPI (backend).

Lancement :
    python -m hitl.backend.main

Sert l'API REST (/api/*), un flux temps réel WebSocket (/ws), et — en
production — les fichiers statiques du frontend React compilé
(hitl/frontend/dist).
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

from hitl.backend import aggregator
from hitl.backend.config import CONFIG
from hitl.backend.routes import auth_routes, control_routes, monitor_routes
from hitl.backend.state import STATE

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-24s | %(levelname)-7s | %(message)s")
logger = logging.getLogger("bag_ids.hitl")

app = FastAPI(title="BAg-IDS — Human-in-the-Loop Layer", version="1.0")

# Le frontend Vite (dev) tourne sur un autre port : CORS ouvert en local.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"])

app.include_router(auth_routes.router)
app.include_router(monitor_routes.router)
app.include_router(control_routes.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "layer": "human-in-the-loop",
            "hitl_enabled": STATE.hitl_enabled}


@app.websocket("/ws")
async def ws(websocket: WebSocket):
    """Pousse un instantané dashboard + événements toutes les 2 s."""
    await websocket.accept()
    try:
        while True:
            snapshot = {
                "metrics": aggregator.metrics_summary(),
                "hitl": STATE.snapshot(),
                "pending": STATE.pending(),
                "events": STATE.events(15),
            }
            await websocket.send_json(snapshot)
            await asyncio.sleep(2.0)
    except WebSocketDisconnect:
        pass
    except Exception as exc:  # noqa: BLE001
        logger.warning("WebSocket fermé : %s", exc)


# Frontend compilé (présent seulement après `npm run build`)
_dist = Path(__file__).resolve().parents[1] / "frontend" / "dist"
if _dist.exists():
    app.mount("/", StaticFiles(directory=str(_dist), html=True), name="spa")
    logger.info("Frontend servi depuis %s", _dist)
else:
    @app.get("/")
    def root():
        return {"message": "BAg-IDS HITL backend actif. Frontend non compilé "
                "(lancer `npm run dev` dans hitl/frontend, ou `npm run build`).",
                "api_docs": "/docs"}


def main():
    uvicorn.run(app, host=CONFIG["host"], port=int(CONFIG["port"]),
                log_level="info")


if __name__ == "__main__":
    main()
