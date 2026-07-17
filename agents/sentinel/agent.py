"""
BAg-IDS — Agent Sentinel autonome (étape 1.2).

Architecture hybride :
  - Couche RÉFLEXE (rapide, par flux) : ensemble calibré + rejet tau.
    Boucle autonome perception -> décision -> action, sans intervention
    extérieure, sur chaque micro-batch de flux.
  - Couche DÉLIBÉRATIVE (lente, par événement) : un LLM (OpenRouter ou
    LM Studio, repli sur règles) n'est sollicité que sur événements
    significatifs — attaque certifiée, rafale de rejets (dérive
    suspectée) — et produit sévérité, justification et actions
    recommandées, jointes à l'alerte transmise au Notary.

Lancement (depuis la racine du dépôt) :
    python -m agents.sentinel.agent --config configs/agents.yaml
"""

from __future__ import annotations

# IMPORTANT — TensorFlow DOIT être importé avant pandas/pyarrow : sous
# Windows, les DLL C++ de pyarrow (chargé automatiquement par pandas 2.x
# via src.data_loader) entrent en conflit avec celles de TF 2.20 et font
# échouer l'initialisation native (« DLL load failed :
# _pywrap_tensorflow_internal »). Importer TF en premier fixe l'ordre de
# chargement des DLL et immunise le Sentinel contre ce conflit.
import tensorflow  # noqa: F401  (doit rester le premier import lourd)

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
from pydantic import BaseModel

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

from agents.common.llm_client import Deliberator, build_clients
from agents.common.schemas import (
    Alert,
    AlertSeverity,
    AgentStatus,
    DeliberationResult,
    Detection,
    FlowFeatures,
    Verdict,
)
from agents.sentinel.detector import EnsembleDetector
from agents.sentinel.flow_source import ReplayFlowSource

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-32s | %(levelname)-7s | %(message)s",
)


class InjectBody(BaseModel):
    """Flux injectés pour test (bruts par défaut : normalisés côté Sentinel)."""
    flows: list[list[float]]
    labels: list[str] | None = None
    raw: bool = True
logger = logging.getLogger("bag_ids.agents.sentinel")


class SentinelAgent:
    def __init__(self, cfg: dict):
        self.cfg = cfg["sentinel"]
        self.agent_id = self.cfg["agent_id"]
        self.started_at = time.time()

        self.detector = EnsembleDetector(self.cfg["bundle_dir"])
        self.deliberator = Deliberator(build_clients(cfg["llm"]))

        # État interne (autonomie : l'agent tient ses propres compteurs)
        self.processed = 0
        self.counts = {v.value: 0 for v in Verdict}
        self.alerts_sent = 0
        self.deliberations = 0
        self._consecutive_rejections = 0
        self._last_deliberation_ts = 0.0
        self._stop = asyncio.Event()

    # ------------------------------------------------------------ boucle
    async def run(self):
        """Boucle autonome principale : consomme la source de flux."""
        source = ReplayFlowSource(
            bundle_dir=self.cfg["bundle_dir"],
            class_names=self.detector.class_names,
            flows_per_second=float(self.cfg["replay"]["flows_per_second"]),
            max_flows=int(self.cfg["replay"]["max_flows"]),
            loop=bool(self.cfg["replay"].get("loop", False)),
        )
        logger.info("[%s] Boucle réflexe démarrée", self.agent_id)
        async with httpx.AsyncClient(timeout=10.0) as http:
            async for batch in source.stream():
                if self._stop.is_set():
                    break
                detections = self.detector.detect_batch(batch)
                self.processed += len(detections)
                for det in detections:
                    await self._handle_detection(det, http)
        logger.info(
            "[%s] Boucle terminée : %d flux, verdicts=%s, alertes=%d, "
            "délibérations=%d", self.agent_id, self.processed, self.counts,
            self.alerts_sent, self.deliberations)

    async def detect_injected(self, raw_flows: list[list[float]],
                              labels: list[str] | None = None,
                              raw: bool = True) -> list[dict]:
        """Classe des flux injectés (test d'attaques fournies par l'opérateur)
        à travers le pipeline complet, exactement comme les flux du réseau.
        `raw=True` : les vecteurs sont bruts et normalisés par le scaler
        d'entraînement ; `raw=False` : déjà normalisés."""
        import numpy as _np
        X = (self.detector.scale_raw(raw_flows) if raw
             else _np.asarray(raw_flows, dtype=_np.float32))
        flows = [
            FlowFeatures(features=X[i].tolist(),
                        true_label=(labels[i] if labels and i < len(labels)
                                    else None))
            for i in range(len(X))
        ]
        detections = self.detector.detect_batch(flows)
        self.processed += len(detections)
        out = []
        async with httpx.AsyncClient(timeout=10.0) as http:
            for det in detections:
                await self._handle_detection(det, http)
                out.append({
                    "flow_id": det.flow_id,
                    "verdict": det.verdict.value,
                    "predicted_class": det.predicted_class,
                    "confidence": det.confidence,
                    "true_label": det.true_label,
                    "certified": det.verdict.value == "attack",
                })
        return out

    async def _handle_detection(self, det: Detection, http: httpx.AsyncClient):
        self.counts[det.verdict.value] += 1

        if det.verdict is Verdict.REJECTED:
            self._consecutive_rejections += 1
            burst = int(self.cfg["deliberation"]["on_rejection_burst"])
            if burst and self._consecutive_rejections >= burst:
                self._consecutive_rejections = 0
                await self._deliberate_and_alert(
                    det, http, trigger=f"rejection_burst({burst})")
            return

        self._consecutive_rejections = 0
        if det.verdict is Verdict.ATTACK:
            if self.cfg["deliberation"]["on_certified_attack"]:
                await self._deliberate_and_alert(
                    det, http, trigger="certified_attack")
            else:
                await self._send_alert(det, None, http)

    # ------------------------------------------------------ délibération
    async def _deliberate_and_alert(self, det: Detection,
                                    http: httpx.AsyncClient, trigger: str):
        min_gap = float(self.cfg["deliberation"]["min_seconds_between_calls"])
        deliberation = None
        if time.time() - self._last_deliberation_ts >= min_gap:
            self._last_deliberation_ts = time.time()
            self.deliberations += 1
            summary = self._event_summary(det, trigger)
            # L'appel LLM (bloquant) part dans un thread pour ne pas
            # suspendre la boucle réflexe.
            result = await asyncio.to_thread(
                self.deliberator.deliberate, trigger, summary)
            deliberation = DeliberationResult(
                trigger=trigger,
                provider=result["provider"],
                model=result["model"],
                severity=AlertSeverity(result["severity"]),
                rationale=result["rationale"],
                recommended_actions=result["recommended_actions"],
                latency_ms=result["latency_ms"],
            )
            logger.info("[%s] Délibération (%s) via %s : sévérité=%s",
                        self.agent_id, trigger, deliberation.provider,
                        deliberation.severity.value)
        await self._send_alert(det, deliberation, http)

    def _event_summary(self, det: Detection, trigger: str) -> str:
        top = sorted(det.class_probabilities.items(),
                     key=lambda kv: kv[1], reverse=True)[:4]
        lines = [
            f"Trigger: {trigger}",
            f"Ensemble verdict: {det.verdict.value} "
            f"(class={det.predicted_class}, confidence={det.confidence:.3f}, "
            f"tau={det.tau})",
            f"Top fused posteriors: {top}",
            "Per-model decisions: " + ", ".join(
                f"{name}: {info['predicted_class']} "
                f"({float(info['confidence']):.3f})"
                for name, info in det.per_model.items()),
            f"Recent verdict counts: {self.counts}",
        ]
        return "\n".join(lines)

    # ------------------------------------------------------------ alerte
    async def _send_alert(self, det: Detection,
                          deliberation: DeliberationResult | None,
                          http: httpx.AsyncClient):
        severity = (deliberation.severity if deliberation
                    else AlertSeverity.MEDIUM)
        alert = Alert(sentinel_id=self.agent_id, detection=det,
                      severity=severity, deliberation=deliberation)
        url = f"{self.cfg['notary_url']}/alert"
        payload = alert.model_dump(mode="json")
        try:
            r = await http.post(url, json=payload)
            r.raise_for_status()
            self.alerts_sent += 1
        except httpx.HTTPError as exc:
            # Autonomie : le Sentinel continue même si le Notary est absent.
            logger.warning("[%s] Notary injoignable (%s) — alerte %s "
                           "journalisée localement", self.agent_id, exc,
                           alert.alert_id)
        # Déclenche l'enquête agentique en parallèle (fire-and-forget, non
        # bloquant) : l'Investigator enrichit après coup, hors chemin critique.
        inv_url = self.cfg.get("investigator_url")
        if inv_url and det.verdict is Verdict.ATTACK:
            try:
                await http.post(f"{inv_url}/investigate", json=payload,
                                timeout=3.0)
            except httpx.HTTPError:
                pass  # l'Investigator est optionnel

    # ------------------------------------------------------------- état
    def status(self) -> AgentStatus:
        return AgentStatus(
            agent_id=self.agent_id,
            agent_type="sentinel",
            uptime_s=round(time.time() - self.started_at, 1),
            processed=self.processed,
            extra={
                **{f"verdict_{k}": v for k, v in self.counts.items()},
                "alerts_sent": self.alerts_sent,
                "deliberations": self.deliberations,
            },
        )


def build_app(agent: SentinelAgent) -> FastAPI:
    app = FastAPI(title="BAg-IDS Sentinel", version="0.1")

    @app.get("/health", response_model=AgentStatus)
    def health():
        return agent.status()

    @app.post("/stop")
    def stop():
        agent._stop.set()
        return {"stopping": True}

    @app.post("/detect")
    async def detect(body: InjectBody):
        try:
            results = await agent.detect_injected(
                body.flows, body.labels, raw=body.raw)
        except ValueError as exc:
            return {"error": str(exc)}
        return {"n": len(results), "results": results}

    @app.get("/meta")
    def meta():
        return {"n_features": agent.detector.n_features,
                "classes": agent.detector.class_names,
                "benign_label": agent.detector.benign_label,
                "tau": agent.detector.tau}

    return app


async def main_async(cfg: dict):
    agent = SentinelAgent(cfg)
    app = build_app(agent)
    server = uvicorn.Server(uvicorn.Config(
        app, host=agent.cfg["host"], port=int(agent.cfg["port"]),
        log_level="warning"))
    # L'API (observabilité + injection) et la boucle autonome vivent côte à
    # côte. La boucle tourne en tâche de fond ; l'API reste vivante même
    # après épuisement du replay (sauf mode boucle où elle ne s'épuise pas),
    # afin que le tableau de bord et l'injection restent disponibles.
    loop_task = asyncio.create_task(agent.run())
    await server.serve()
    agent._stop.set()
    await loop_task


def main():
    parser = argparse.ArgumentParser(description="BAg-IDS Sentinel agent")
    parser.add_argument("--config", default="configs/agents.yaml")
    args = parser.parse_args()
    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    asyncio.run(main_async(cfg))


if __name__ == "__main__":
    main()
