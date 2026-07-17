"""
BAg-IDS — Agent Executor (étape 1.2).

Rôle : exécuter les actions de remédiation approuvées par le consensus.
V1 : mode dry-run — chaque action est simulée et journalisée (aucune
commande système réelle) ; les manipulations réseau réelles (pare-feu,
isolation) seront branchées en phase 2 sur l'environnement de test.

Lancement :
    python -m agents.executor.agent --config configs/agents.yaml
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

import uvicorn
import yaml
from fastapi import FastAPI

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

from agents.common.schemas import AgentStatus, RemediationAction

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-32s | %(levelname)-7s | %(message)s",
)
logger = logging.getLogger("bag_ids.agents.executor")


class ExecutorAgent:
    def __init__(self, cfg: dict):
        self.cfg = cfg["executor"]
        self.agent_id = self.cfg["agent_id"]
        self.dry_run = bool(self.cfg.get("dry_run", True))
        self.started_at = time.time()
        self.actions: list[RemediationAction] = []
        self.by_type: dict[str, int] = {}

    def execute(self, action: RemediationAction) -> RemediationAction:
        if self.dry_run:
            action.result = f"dry-run: {action.action_type} simulé"
        else:
            # Phase 2 : brancher ici les vraies remédiations (netsh/iptables,
            # API de l'orchestrateur réseau, etc.)
            action.result = "non implémenté hors dry-run"
        action.executed = True
        self.actions.append(action)
        self.by_type[action.action_type] = \
            self.by_type.get(action.action_type, 0) + 1
        logger.info("[%s] Action %s (%s) exécutée : %s", self.agent_id,
                    action.action_id, action.action_type, action.result)
        return action

    def status(self) -> AgentStatus:
        return AgentStatus(
            agent_id=self.agent_id,
            agent_type="executor",
            uptime_s=round(time.time() - self.started_at, 1),
            processed=len(self.actions),
            extra={**self.by_type, "dry_run": int(self.dry_run)},
        )


def build_app(agent: ExecutorAgent) -> FastAPI:
    app = FastAPI(title="BAg-IDS Executor", version="0.1")

    @app.post("/execute")
    def execute(action: RemediationAction):
        done = agent.execute(action)
        return {"action_id": done.action_id, "executed": done.executed,
                "result": done.result}

    @app.get("/health", response_model=AgentStatus)
    def health():
        return agent.status()

    @app.get("/actions")
    def actions(n: int = 20):
        return [a.model_dump(mode="json") for a in agent.actions[-n:]]

    return app


def main():
    parser = argparse.ArgumentParser(description="BAg-IDS Executor agent")
    parser.add_argument("--config", default="configs/agents.yaml")
    args = parser.parse_args()
    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    agent = ExecutorAgent(cfg)
    app = build_app(agent)
    logger.info("[%s] Executor en écoute sur %s:%s (dry_run=%s)",
                agent.agent_id, agent.cfg["host"], agent.cfg["port"],
                agent.dry_run)
    uvicorn.run(app, host=agent.cfg["host"], port=int(agent.cfg["port"]),
                log_level="warning")


if __name__ == "__main__":
    main()
