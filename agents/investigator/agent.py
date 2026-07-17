"""
BAg-IDS — Agent Investigator / Triage (agent au sens fort).

Contrairement à la couche délibérative one-shot du Sentinel, cet agent
mène une ENQUÊTE AUTONOME MULTI-ÉTAPES quand une attaque est certifiée.
Il suit une boucle agentique explicite et faite main —
perçois → raisonne → agis (outils) → réfléchis → conclus — en décidant
lui-même quels outils invoquer (lecture du ledger, corrélation), en
gardant une mémoire des campagnes observées, et en produisant un rapport
d'incident structuré. Sa conclusion (et sa trace) est ancrée on-chain :
même le raisonnement autonome de l'agent est ainsi auditable.

Cet agent NE participe PAS à la certification (déterministe, couche 3) :
il enrichit et priorise APRÈS certification. Le cœur mesuré du système
reste donc indépendant de ce composant non déterministe.

Lancement :
    python -m agents.investigator.agent --config configs/agents.yaml
"""

from __future__ import annotations

import argparse
import asyncio
import json
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

from agents.common.llm_client import Deliberator, build_clients
from agents.common.schemas import (
    AgentStatus,
    Alert,
    AlertSeverity,
    InvestigationReport,
    InvestigationStep,
)
from agents.investigator.tools import LedgerTool, correlate

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-32s | %(levelname)-7s | %(message)s",
)
logger = logging.getLogger("bag_ids.agents.investigator")

_SYSTEM = (
    "You are the Investigator agent of an autonomous intrusion-detection "
    "system. You receive a certified attack and the evidence gathered by "
    "your tools (related recent incidents of the same class and a temporal "
    "correlation analysis). Reason about whether this is an isolated event "
    "or part of a coordinated campaign, and reply with a SINGLE JSON object "
    'with keys: "campaign_suspected" (bool), "severity" '
    '("low"|"medium"|"high"|"critical"), "summary" (2-4 sentences), '
    '"recommended_response" (list of short imperative strings from: block_ip, '
    "rate_limit, isolate_host, threat_hunt, notify_operator, escalate, "
    "no_action)."
)


class InvestigatorAgent:
    def __init__(self, cfg: dict):
        icfg = cfg.get("investigator", {})
        self.cfg = icfg
        self.agent_id = icfg.get("agent_id", "investigator-01")
        self.started_at = time.time()
        self.deliberator = Deliberator(build_clients(cfg["llm"]))
        mirror = icfg.get("ledger_mirror") or cfg["notary"].get("ledger_path") \
            or "results/agents/ledger_fabric_mirror.jsonl"
        self.ledger = LedgerTool(mirror)
        # Mémoire de l'agent : campagnes observées (classe -> compteur)
        self.memory: dict[str, int] = {}
        self.reports: list[InvestigationReport] = []
        self.investigations = 0
        # Ancrage on-chain optionnel des rapports (gouvernance étendue)
        self.anchor_url = icfg.get("fabric_proxy_url") \
            or cfg.get("notary", {}).get("fabric_proxy_url")
        self.signer = icfg.get("signer", "notary-01")
        self.keys_dir = cfg.get("notary", {}).get("keys_dir", "keys")

    # ----------------------------------------------- boucle agentique
    def investigate(self, alert: Alert) -> InvestigationReport:
        """Boucle perçois → raisonne → agis (outils) → réfléchis → conclus."""
        t0 = time.perf_counter()
        det = alert.detection
        cls = det.predicted_class
        steps: list[InvestigationStep] = []

        # Étape 1 — PERCEVOIR : cadrer l'enquête
        steps.append(InvestigationStep(
            index=1, thought=f"A certified {cls} attack was reported. I will "
            "look for other recent incidents of the same class to judge "
            "whether this is isolated or coordinated.",
            tool="frame", tool_input={"class": cls},
            observation=f"target class = {cls}, confidence = "
            f"{det.confidence:.3f}"))

        # Étape 2 — AGIR (outil ledger) : chercher les incidents liés
        related = self.ledger.related_by_class(cls, det.detection_id
                                               if hasattr(det, "detection_id")
                                               else alert.alert_id)
        related_ids = [a["alert_id"] for a in related if a.get("alert_id")]
        steps.append(InvestigationStep(
            index=2, thought="Query the ledger for recent incidents of the "
            "same attack class.", tool="query_ledger",
            tool_input={"class": cls, "window_s": 3600},
            observation=f"{len(related)} related incident(s) found on-chain"))

        # Étape 3 — AGIR (outil corrélation) : rafale temporelle ?
        corr = correlate(related)
        steps.append(InvestigationStep(
            index=3, thought="Correlate the related incidents in time to "
            "detect a burst indicative of a campaign.",
            tool="correlate", tool_input={"n": len(related)},
            observation=f"count={corr['count']}, burst={corr['burst']}, "
            f"rate={corr['rate_per_min']}/min"))

        # Étape 4 — RÉFLÉCHIR (LLM) : synthèse et décision de triage
        evidence = (
            f"Certified attack: class={cls}, confidence={det.confidence:.3f}, "
            f"severity(initial)={alert.severity.value}.\n"
            f"Related incidents (same class, last hour): {len(related)} "
            f"-> {related_ids[:10]}.\n"
            f"Temporal correlation: {corr}.\n"
            f"Investigator memory (campaigns seen so far): {self.memory}."
        )
        result = self.deliberator.deliberate("investigation", evidence)
        # Normalisation (le repli règles ne renvoie pas tous les champs)
        campaign = bool(result.get("campaign_suspected", corr["burst"]))
        severity = result.get("severity", alert.severity.value)
        if severity not in ("low", "medium", "high", "critical"):
            severity = alert.severity.value
        summary = result.get("rationale") or result.get("summary") \
            or f"{cls} attack; {len(related)} related incidents; " \
            f"campaign={'yes' if campaign else 'no'}."
        actions = result.get("recommended_actions") \
            or result.get("recommended_response") or ["notify_operator"]
        steps.append(InvestigationStep(
            index=4, thought="Synthesise the evidence and decide triage.",
            tool="llm_reason", tool_input={"provider": result.get("provider")},
            observation=f"campaign={campaign}, severity={severity}"))

        # RÉFLÉCHIR / mémoire : mettre à jour la mémoire de campagnes
        if campaign:
            self.memory[cls] = self.memory.get(cls, 0) + 1

        report = InvestigationReport(
            alert_id=alert.alert_id, investigator_id=self.agent_id,
            steps=steps, related_incidents=related_ids,
            campaign_suspected=campaign, severity=AlertSeverity(severity),
            summary=summary, recommended_response=actions,
            provider=result.get("provider", "rules-fallback"),
            model=result.get("model", ""),
            latency_ms=round(1000 * (time.perf_counter() - t0), 1))
        self.reports.append(report)
        self.investigations += 1
        self._anchor(report)
        logger.info("[%s] Enquête %s : campagne=%s, sévérité=%s, %d étapes, "
                    "%d incidents liés", self.agent_id, alert.alert_id,
                    campaign, severity, len(steps), len(related_ids))
        return report

    def _anchor(self, report: InvestigationReport):
        """Ancre la conclusion de l'enquête on-chain (RecordGovernance),
        pour que le raisonnement autonome de l'agent soit auditable."""
        if not self.anchor_url:
            return
        try:
            import httpx
            from agents.common.identity import AgentIdentity
            ident = AgentIdentity.load(self.keys_dir, self.signer)
            record = {"action": "investigation", "actor": self.agent_id,
                      "signer": self.signer,
                      "details": {"alert_id": report.alert_id,
                                  "campaign": report.campaign_suspected,
                                  "severity": report.severity.value}}
            payload = json.dumps(record, sort_keys=True, separators=(",", ":"),
                                 ensure_ascii=False)
            sig = ident.sign(record)
            httpx.post(f"{self.anchor_url}/submit", json={
                "function": "RecordGovernance",
                "args": ["investigation", self.agent_id, self.signer,
                         payload, sig]}, timeout=15.0)
        except Exception as exc:  # ancrage best-effort
            logger.warning("[%s] Ancrage enquête échoué : %s",
                           self.agent_id, exc)

    def status(self) -> AgentStatus:
        return AgentStatus(
            agent_id=self.agent_id, agent_type="investigator",
            uptime_s=round(time.time() - self.started_at, 1),
            processed=self.investigations,
            extra={"campaigns_tracked": len(self.memory),
                   "reports": len(self.reports)})


def build_app(agent: InvestigatorAgent) -> FastAPI:
    app = FastAPI(title="BAg-IDS Investigator", version="0.1")

    @app.post("/investigate")
    def investigate(alert: Alert):
        return agent.investigate(alert).model_dump(mode="json")

    @app.get("/reports")
    def reports(n: int = 20):
        return [r.model_dump(mode="json") for r in agent.reports[-n:]]

    @app.get("/health", response_model=AgentStatus)
    def health():
        return agent.status()

    return app


def main():
    parser = argparse.ArgumentParser(description="BAg-IDS Investigator agent")
    parser.add_argument("--config", default="configs/agents.yaml")
    args = parser.parse_args()
    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    agent = InvestigatorAgent(cfg)
    app = build_app(agent)
    host = agent.cfg.get("host", "127.0.0.1")
    port = int(agent.cfg.get("port", 8005))
    logger.info("[%s] Investigator en écoute sur %s:%s", agent.agent_id,
                host, port)
    uvicorn.run(app, host=host, port=port, log_level="warning")


if __name__ == "__main__":
    main()
