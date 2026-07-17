"""
BAg-IDS — Agent Data Scientist (étape 1.2).

Rôle : agent de MAINTENANCE proactif. Il observe en continu la santé du
Sentinel (taux de rejet glissant = proxy de dérive de distribution) et,
quand le seuil est franchi, DÉLIBÈRE (LLM ou règles) pour décider s'il
faut recalibrer (temperature scaling sur données récentes) ou
ré-entraîner. En V1, la recommandation est journalisée et exposée ;
le ré-entraînement automatique arrive en phase 2.

Ce comportement proactif (l'agent décide seul de surveiller et d'alerter)
illustre la propriété d'autonomie décrite dans le manuscrit.

Lancement :
    python -m agents.data_scientist.agent --config configs/agents.yaml
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
import time
from pathlib import Path

import httpx
import uvicorn
import yaml
from fastapi import FastAPI

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

from agents.common.llm_client import Deliberator, build_clients
from agents.common.schemas import AgentStatus

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-32s | %(levelname)-7s | %(message)s",
)
logger = logging.getLogger("bag_ids.agents.datasci")


class DataScientistAgent:
    def __init__(self, cfg: dict):
        self.cfg = cfg["data_scientist"]
        self.agent_id = self.cfg["agent_id"]
        self.started_at = time.time()
        self.deliberator = Deliberator(build_clients(cfg["llm"]))
        self.sentinel_url = cfg["sentinel"].get("self_url") or (
            f"http://{cfg['sentinel']['host']}:{cfg['sentinel']['port']}")
        self.threshold = float(self.cfg["drift"]["rejection_rate_threshold"])
        self.poll_interval = float(self.cfg.get("poll_interval_s", 15))
        self.checks = 0
        self.drift_events = 0
        self.recommendations: list[dict] = []
        self._prev = {"processed": 0, "rejected": 0}
        self._stop = asyncio.Event()

    async def run(self):
        logger.info("[%s] Surveillance de dérive démarrée (seuil=%.0f%%, "
                    "période=%.0fs)", self.agent_id, 100 * self.threshold,
                    self.poll_interval)
        async with httpx.AsyncClient(timeout=5.0) as http:
            while not self._stop.is_set():
                await self._check_once(http)
                try:
                    await asyncio.wait_for(self._stop.wait(),
                                           timeout=self.poll_interval)
                except asyncio.TimeoutError:
                    pass

    async def _check_once(self, http: httpx.AsyncClient):
        try:
            r = await http.get(f"{self.sentinel_url}/health")
            r.raise_for_status()
            h = r.json()
        except httpx.HTTPError:
            return  # Sentinel hors ligne : rien à surveiller pour l'instant
        self.checks += 1
        processed = int(h["processed"])
        rejected = int(h["extra"].get("verdict_rejected", 0))

        d_proc = processed - self._prev["processed"]
        d_rej = rejected - self._prev["rejected"]
        self._prev = {"processed": processed, "rejected": rejected}
        if d_proc <= 0:
            return
        rate = d_rej / d_proc
        logger.info("[%s] Fenêtre : %d flux, taux de rejet %.1f%%",
                    self.agent_id, d_proc, 100 * rate)
        if rate >= self.threshold:
            self.drift_events += 1
            summary = (
                f"Drift monitor: rejection rate over last window is "
                f"{rate:.2%} (threshold {self.threshold:.0%}), "
                f"{d_proc} flows processed, sentinel counters: {h['extra']}. "
                f"Decide between: recalibrate (temperature scaling on recent "
                f"data), retrain (full model update), or no_action."
            )
            result = await asyncio.to_thread(
                self.deliberator.deliberate, "drift_suspected", summary)
            rec = {
                "timestamp": time.time(),
                "rejection_rate": rate,
                "provider": result["provider"],
                "severity": result["severity"],
                "actions": result["recommended_actions"],
                "rationale": result["rationale"],
            }
            self.recommendations.append(rec)
            logger.warning("[%s] DÉRIVE suspectée (%.1f%%) — recommandation "
                           "%s via %s", self.agent_id, 100 * rate,
                           rec["actions"], rec["provider"])

    def status(self) -> AgentStatus:
        return AgentStatus(
            agent_id=self.agent_id,
            agent_type="data_scientist",
            uptime_s=round(time.time() - self.started_at, 1),
            processed=self.checks,
            extra={
                "drift_events": self.drift_events,
                "recommendations": len(self.recommendations),
            },
        )


def build_app(agent: DataScientistAgent) -> FastAPI:
    app = FastAPI(title="BAg-IDS Data Scientist", version="0.1")

    @app.get("/health", response_model=AgentStatus)
    def health():
        return agent.status()

    @app.get("/recommendations")
    def recommendations(n: int = 10):
        return agent.recommendations[-n:]

    @app.post("/stop")
    def stop():
        agent._stop.set()
        return {"stopping": True}

    return app


async def main_async(cfg: dict):
    agent = DataScientistAgent(cfg)
    app = build_app(agent)
    server = uvicorn.Server(uvicorn.Config(
        app, host=agent.cfg["host"], port=int(agent.cfg["port"]),
        log_level="warning"))
    api_task = asyncio.create_task(server.serve())
    await agent.run()
    server.should_exit = True
    await api_task


def main():
    parser = argparse.ArgumentParser(description="BAg-IDS Data Scientist agent")
    parser.add_argument("--config", default="configs/agents.yaml")
    args = parser.parse_args()
    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    asyncio.run(main_async(cfg))


if __name__ == "__main__":
    main()
