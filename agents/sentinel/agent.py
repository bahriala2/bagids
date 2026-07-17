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

import json

from agents.common.llm_client import Deliberator, LLMError, build_clients
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
from agents.sentinel.explainer import FlowExplainer
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


class ExplainBody(BaseModel):
    """Demande d'explication XAI pour un flux déjà classé (par flow_id)."""
    flow_id: str
    with_narrative: bool = True
logger = logging.getLogger("bag_ids.agents.sentinel")


class SentinelAgent:
    def __init__(self, cfg: dict):
        self.cfg = cfg["sentinel"]
        self.agent_id = self.cfg["agent_id"]
        self.started_at = time.time()

        self.detector = EnsembleDetector(self.cfg["bundle_dir"])
        self.deliberator = Deliberator(build_clients(cfg["llm"]))
        # XAI : attributions SHAP servies à la demande (file d'approbation
        # HITL uniquement — hors chemin critique par construction).
        self.explainer = FlowExplainer(self.detector, self.cfg["bundle_dir"],
                                       self.cfg.get("explain"))
        self.explanations_made = 0

        # État interne (autonomie : l'agent tient ses propres compteurs)
        self.processed = 0
        self.counts = {v.value: 0 for v in Verdict}
        self.alerts_sent = 0
        self.deliberations = 0
        self._consecutive_rejections = 0
        self._last_deliberation_ts = 0.0
        self._stop = asyncio.Event()
        # Cache des vecteurs de features des flux non bénins récents :
        # nécessaire pour expliquer a posteriori une alerte mise en file
        # d'approbation (le flow_id seul circule dans les alertes).
        self._flow_cache: dict[str, list[float]] = {}
        self._flow_cache_order: list[str] = []
        self._flow_cache_max = int(self.cfg.get("explain", {}).get(
            "cache_size", 4096) if isinstance(self.cfg.get("explain"), dict)
            else 4096)

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
                for flow, det in zip(batch, detections):
                    self._cache_flow(flow, det)
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
            for flow, det in zip(flows, detections):
                self._cache_flow(flow, det)
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

    # ------------------------------------------------------- XAI (HITL)
    def _cache_flow(self, flow: FlowFeatures, det: Detection):
        """Mémorise le vecteur de features des flux NON bénins récents,
        pour pouvoir expliquer a posteriori une remédiation mise en file
        d'approbation. Éviction FIFO au-delà de `explain.cache_size`."""
        if det.verdict is Verdict.BENIGN or det.flow_id in self._flow_cache:
            return
        self._flow_cache[det.flow_id] = list(flow.features)
        self._flow_cache_order.append(det.flow_id)
        if len(self._flow_cache_order) > self._flow_cache_max:
            oldest = self._flow_cache_order.pop(0)
            self._flow_cache.pop(oldest, None)

    #: L'interprétation PARTICULARISE le socle de connaissances avec les
    #: attributions SHAP du flux : toute feature absente de la liste est
    #: interdite, et la recommandation reste déterministe (hors LLM).
    INTERPRET_SYSTEM = (
        "You are the explanation layer of an intrusion-detection system, "
        "writing for a SOC analyst who must approve or reject a proposed "
        "remediation. You receive: the attack class predicted by a "
        "calibrated neural ensemble, its confidence, the per-detector "
        "votes, the SHAP feature attributions for this specific flow, and "
        "a trusted knowledge-base entry about this attack class. Produce:\n"
        "1. \"interpretation\": 3-4 sentences that (a) say what this attack "
        "is, (b) explain how the LISTED features and their directions "
        "match that attack's known network behaviour, concretely (e.g. "
        "'a very small minimum packet length matches Hulk's flood of tiny "
        "randomised requests'), and (c) mention the main false-positive "
        "cause to rule out. Ground every claim in the listed features or "
        "the knowledge base; NEVER invent traffic details you were not "
        "given.\n"
        "2. \"checks\": 3-4 short, concrete verification actions for THIS "
        "alert (adapt the knowledge-base checklist to the observed "
        "features).\n"
        "Reply with a single JSON object, nothing else:\n"
        '{"interpretation": {"en": "...", "fr": "...", "ar": "..."}, '
        '"checks": {"en": ["..."], "fr": ["..."], "ar": ["..."]}} '
        "(same content in English, French and Arabic)."
    )

    def _interpret(self, attribution: dict, votes: dict,
                   agreement: int) -> tuple[dict, str]:
        """Interprétation + checklist via LLM (ancrées sur SHAP + base de
        connaissances), avec repli intégral sur le socle déterministe.
        Retourne (payload, provider). La recommandation est TOUJOURS
        calculée par la règle déterministe de attack_kb.recommend."""
        from agents.sentinel.attack_kb import build_fallback, get_kb, recommend
        n_models = len(votes)
        fallback = build_fallback(attribution, agreement, n_models)
        kb = get_kb(attribution["predicted_class"])

        feats = "\n".join(
            f"- {t['name']} (normalised value {t['value']:+.3f}): "
            f"SHAP {t['shap']:+.5f} ({t['direction']})"
            for t in attribution["top_features"])
        user = (
            f"Predicted class: {attribution['predicted_class']} "
            f"(fused confidence {attribution['confidence']:.3f})\n"
            f"Per-detector votes: {votes} "
            f"(agreement {agreement}/{n_models})\n"
            f"Top SHAP attributions for this flow:\n{feats}\n\n"
            f"Knowledge base for this class:\n"
            f"- What it is: {kb['what']['en']}\n"
            f"- Typical network signals: {kb['signals']['en']}\n"
            f"- Known false-positive causes: {kb['fp_notes']['en']}\n"
            f"- Generic checklist: {kb['checks']['en']}")

        for client in self.deliberator.clients:
            try:
                raw = client.chat(self.INTERPRET_SYSTEM, user,
                                  max_tokens=1600)
                text = raw.strip().strip("`")
                if text.startswith("json"):
                    text = text[4:]
                start, end = text.find("{"), text.rfind("}")
                data = json.loads(text[start:end + 1])
                interp, checks = data["interpretation"], data["checks"]
                if not all(isinstance(interp.get(k), str) and interp[k]
                           for k in ("en", "fr", "ar")):
                    raise ValueError("interpretation en/fr/ar manquante")
                if not all(isinstance(checks.get(k), list) and checks[k]
                           for k in ("en", "fr", "ar")):
                    raise ValueError("checks en/fr/ar manquants")
                payload = {
                    "attack_profile": kb["what"],
                    "interpretation": interp,
                    "checks": checks,
                    "recommendation": fallback["recommendation"],
                }
                return payload, f"{client.provider}:{client.model}"
            except (LLMError, ValueError, KeyError, TypeError,
                    json.JSONDecodeError, IndexError) as exc:
                logger.warning("Interprétation XAI via %s échouée : %s",
                               client.provider, exc)
        return fallback, "kb-template"

    async def explain_flow(self, flow_id: str, with_narrative: bool) -> dict:
        """Explication complète pour l'analyste : attributions SHAP,
        interprétation métier, checklist de vérification et recommandation
        consultative. Bloquant ~2-30 s : exécuté dans des threads, appelé
        uniquement par la couche HITL pour les remédiations en attente."""
        import numpy as _np
        features = self._flow_cache.get(flow_id)
        if features is None:
            return {"error": "flow_id inconnu ou évincé du cache",
                    "flow_id": flow_id}
        attribution = await asyncio.to_thread(
            self.explainer.explain, features)

        # Votes par détecteur (accord = signal de fiabilité pour l'analyste)
        def _votes():
            X = _np.asarray(features, dtype=_np.float32).reshape(1, -1)
            _, calibrated = self.detector.fused_probs(X)
            return {name: self.detector.class_names[int(p[0].argmax())]
                    for name, p in calibrated.items()}
        votes = await asyncio.to_thread(_votes)
        agreement = sum(1 for v in votes.values()
                        if v == attribution["predicted_class"])

        analysis, provider = await asyncio.to_thread(
            self._interpret, attribution, votes, agreement)
        self.explanations_made += 1
        return {**attribution, **analysis, "flow_id": flow_id,
                "per_model_votes": votes,
                "agreement": {"agree": agreement, "total": len(votes)},
                "narrative_provider": provider,
                "method": f"KernelSHAP(nsamples={attribution['nsamples']}, "
                          f"background={attribution['background_size']})"}

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
                "explanations": self.explanations_made,
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

    @app.post("/explain")
    async def explain(body: ExplainBody):
        """Explication XAI (SHAP + narration) d'un flux alerté — appelé par
        la couche HITL pour les remédiations en attente d'approbation."""
        try:
            return await agent.explain_flow(body.flow_id, body.with_narrative)
        except Exception as exc:  # jamais fatal pour l'agent
            logger.exception("Explication XAI échouée pour %s", body.flow_id)
            return {"error": str(exc), "flow_id": body.flow_id}

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
