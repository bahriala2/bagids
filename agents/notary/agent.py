"""
BAg-IDS — Agents Notary multi-instances avec consensus (étape 1.3).

Topologie (fidèle au flux endorse -> order -> commit de Fabric) :

  Sentinel --alerte--> Notary LEADER
                          |-- validation locale -> vote signé (Ed25519)
                          |-- POST /endorse vers chaque PAIR
                          |       (validation indépendante -> vote signé)
                          |-- soumet chaque vote au ledger, qui rejoue la
                          |   logique chaincode validateVote : signature,
                          |   autorisation, anti double-vote, quorum
                          `-- si ALERT_CERTIFIED (quorum atteint) :
                                actions -> Executor

Chaque notary VALIDE INDÉPENDAMMENT (il ne fait pas confiance au
Sentinel ni au leader) et signe son vote ; le ledger n'accepte que les
votes signés d'agents autorisés — un notary compromis isolé ne peut ni
certifier seul, ni usurper les votes des autres.

Lancement (une instance par processus) :
    python -m agents.notary.agent --config configs/agents.yaml --instance notary-01
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
import threading
import time
from pathlib import Path

import httpx
import uvicorn
import yaml
from fastapi import FastAPI

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

from agents.common.identity import AgentIdentity, SignerRegistry
from agents.common.ledger import SimulatedLedger, VoteValidationError
from agents.common.llm_client import Deliberator, build_clients
from agents.common.schemas import (
    AgentStatus,
    Alert,
    RemediationAction,
    Verdict,
    Vote,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-32s | %(levelname)-7s | %(message)s",
)
logger = logging.getLogger("bag_ids.agents.notary")

ACTION_TYPES = {"block_ip", "rate_limit", "isolate_host", "recalibrate",
                "retrain", "notify_operator", "no_action"}


def validate_alert(alert: Alert, voter_id: str) -> Vote:
    """Validation INDÉPENDANTE d'une alerte (identique pour leader et
    pairs) : chaque notary revérifie la décision au lieu de faire
    confiance à l'émetteur."""
    det = alert.detection
    checks: list[str] = []
    if det.verdict is Verdict.ATTACK and det.confidence < det.tau:
        checks.append("confidence_below_tau")
    top_class = max(det.class_probabilities, key=det.class_probabilities.get)
    if top_class != det.predicted_class:
        checks.append("argmax_mismatch")
    if alert.deliberation and alert.deliberation.provider not in (
            "openrouter", "lmstudio", "rules-fallback"):
        checks.append("unknown_deliberation_provider")
    approve = not checks
    return Vote(alert_id=alert.alert_id, voter_id=voter_id, approve=approve,
                reason="ok" if approve else ",".join(checks))


class NotaryAgent:
    def __init__(self, cfg: dict, instance_id: str):
        ncfg = cfg["notary"]
        instances = ncfg["instances"]
        self.me = next(i for i in instances if i["agent_id"] == instance_id)
        self.is_leader = instances[0]["agent_id"] == instance_id
        self.peers = [i for i in instances if i["agent_id"] != instance_id]
        self.agent_id = instance_id
        self.cfg = ncfg
        self.started_at = time.time()

        self.identity = AgentIdentity.load(ncfg["keys_dir"], instance_id)
        # Seul le leader détient le client ledger : ledger simulé (1.3)
        # ou chaincode validateVote sur Fabric via la passerelle (1.4),
        # selon `ledger_backend`. Interface identique dans les deux cas.
        self.ledger = None
        if self.is_leader:
            registry = SignerRegistry.load(ncfg["keys_dir"])
            backend = ncfg.get("ledger_backend", "simulated")
            if backend == "fabric":
                import json as _json
                from pathlib import Path as _Path

                from agents.common.fabric_ledger import FabricLedger
                self.ledger = FabricLedger(
                    proxy_url=ncfg["fabric_proxy_url"],
                    local_mirror_path=ncfg["ledger_path"],
                    signer_registry=registry,
                    quorum=int(ncfg["quorum"]))
                # Bootstrap : enregistre les clés publiques des notaries
                # dans l'état du chaincode (idempotent).
                signers = _json.loads(
                    (_Path(ncfg["keys_dir"]) / "authorized_signers.json")
                    .read_text(encoding="utf-8"))
                for inst in instances:
                    aid = inst["agent_id"]
                    self.ledger.register_signer(aid, signers[aid])
            else:
                self.ledger = SimulatedLedger(ncfg["ledger_path"],
                                              signer_registry=registry,
                                              quorum=int(ncfg["quorum"]))
            logger.info("[%s] Backend ledger : %s", self.agent_id, backend)
        self.processed = 0
        self.certified = 0
        self.not_certified = 0
        self.votes_rejected = 0
        self.endorsements = 0
        self.forwarded = 0
        self.deferred = 0
        # Porte Human-in-the-Loop (4e couche). Si `hitl_gate_url` est
        # configuré, chaque remédiation certifiée passe par la file
        # d'approbation avant exécution ; sinon, pleine autonomie.
        self.hitl_gate_url = ncfg.get("hitl_gate_url")
        # Second avis LLM CONSULTATIF (non décisionnel). Quand activé, chaque
        # notary joint à son vote un avis LLM ; cet avis est journalisé et
        # exposé pour audit mais NE MODIFIE JAMAIS la décision d'endossement,
        # qui reste la revalidation déterministe de validate_alert().
        self.advisory_enabled = bool(ncfg.get("advisory_enabled", False))
        self._deliberator = (Deliberator(build_clients(cfg["llm"]))
                             if self.advisory_enabled else None)
        self.advisories: dict[str, dict] = {}   # alert_id -> {voter: avis}
        self.advisories_made = 0

    def _advise(self, alert: Alert) -> dict | None:
        """Avis LLM consultatif sur une alerte (jamais décisionnel)."""
        if not self._deliberator:
            return None
        det = alert.detection
        summary = (
            f"A notary is about to endorse a certified {det.predicted_class} "
            f"alert (confidence {det.confidence:.3f}, tau {det.tau}). "
            f"Give a brief second opinion: does this look like a genuine "
            f"attack, and is there any concern? This opinion is ADVISORY only "
            f"and does not change the cryptographic vote.")
        res = self._deliberator.deliberate("notary_second_opinion", summary)
        self.advisories_made += 1
        advice = {"voter": self.agent_id, "provider": res.get("provider"),
                  "opinion": res.get("rationale") or res.get("summary", ""),
                  "severity_hint": res.get("severity")}
        self.advisories.setdefault(alert.alert_id, {})[self.agent_id] = advice
        logger.info("[%s] Avis consultatif (%s) sur %s : %s", self.agent_id,
                    advice["provider"], alert.alert_id,
                    (advice["opinion"] or "")[:60])
        return advice

    # -------------------------------------------------- endorsement (pair)
    def endorse(self, alert: Alert) -> dict:
        """Rôle de pair : valider indépendamment et renvoyer un vote signé.

        La décision (approve) est purement déterministe ; l'avis LLM
        éventuel est joint séparément, sans jamais influencer le vote."""
        self.endorsements += 1
        vote = validate_alert(alert, self.agent_id)          # DÉTERMINISTE
        payload = vote.model_dump(mode="json")
        # Avis consultatif en arrière-plan : le vote signé part immédiatement,
        # sans jamais attendre l'appel LLM (hors chemin critique du consensus).
        if self._deliberator:
            threading.Thread(target=self._advise, args=(alert,),
                             daemon=True).start()
        return {"vote": payload, "signature": self.identity.sign(payload)}

    # ----------------------------------------------- consensus (leader)
    async def handle_alert(self, alert: Alert) -> dict:
        """Rôle de leader : collecte des votes signés puis soumission au
        ledger (logique chaincode) jusqu'à certification éventuelle."""
        self.processed += 1
        self.ledger.submit("ALERT", alert.model_dump(mode="json"))

        # 1. Vote local du leader (déterministe) + avis consultatif éventuel
        own_vote = validate_alert(alert, self.agent_id)
        own_payload = own_vote.model_dump(mode="json")
        signed_votes = [(own_payload, self.identity.sign(own_payload))]
        # Avis consultatif calculé EN ARRIÈRE-PLAN : ne retarde jamais le
        # consensus (il est non décisionnel, donc hors du chemin critique).
        if self._deliberator:
            asyncio.create_task(asyncio.to_thread(self._advise, alert))

        # 2. Endorsements des pairs (en parallèle, timeout individuel)
        alert_json = alert.model_dump(mode="json")
        timeout = float(self.cfg.get("endorsement_timeout_s", 5))
        async with httpx.AsyncClient(timeout=timeout) as http:
            tasks = [
                http.post(f"http://{p['host']}:{p['port']}/endorse",
                          json=alert_json)
                for p in self.peers
            ]
            responses = await asyncio.gather(*tasks, return_exceptions=True)
        for peer, resp in zip(self.peers, responses):
            if isinstance(resp, Exception) or resp.status_code != 200:
                logger.warning("[%s] Pair %s injoignable : pas d'endorsement",
                               self.agent_id, peer["agent_id"])
                continue
            body = resp.json()
            signed_votes.append((body["vote"], body["signature"]))

        # 3. Soumission des votes à la logique chaincode validateVote
        certified = False
        for payload, signature in signed_votes:
            try:
                result = self.ledger.validate_vote(payload, signature)
                certified = certified or result["certified"]
            except VoteValidationError as exc:
                self.votes_rejected += 1
                logger.warning("[%s] Vote refusé par le ledger : %s",
                               self.agent_id, exc)

        # 4. Remédiation seulement si le consensus a certifié l'alerte
        if not certified and not self.ledger.is_certified(alert.alert_id):
            self.not_certified += 1
            logger.warning("[%s] Alerte %s NON certifiée (quorum %d non "
                           "atteint)", self.agent_id, alert.alert_id,
                           self.ledger.quorum)
            return {"alert_id": alert.alert_id, "certified": False}

        self.certified += 1
        actions = self._plan_actions(alert)
        for action in actions:
            self.ledger.submit("ACTION_PLANNED", action.model_dump(mode="json"))

        # Porte HITL : si la couche de supervision exige une approbation
        # humaine pour cette sévérité, les actions sont mises en file et
        # exécutées seulement après validation (par le backend HITL).
        gated = await self._hitl_gate(alert, actions)
        if gated:
            self.deferred += 1
            logger.info("[%s] Alerte %s certifiée : %d action(s) EN ATTENTE "
                        "d'approbation humaine", self.agent_id,
                        alert.alert_id, len(actions))
            return {"alert_id": alert.alert_id, "certified": True,
                    "pending_approval": True}

        await self._forward(actions)
        logger.info("[%s] Alerte %s certifiée par consensus : %d action(s)",
                    self.agent_id, alert.alert_id, len(actions))
        return {"alert_id": alert.alert_id, "certified": True,
                "actions": [a.action_id for a in actions]}

    async def _hitl_gate(self, alert: Alert,
                         actions: list[RemediationAction]) -> bool:
        """Consulte la couche HITL. Retourne True si les actions sont mises
        en attente (ne pas exécuter maintenant), False si l'exécution
        autonome est autorisée (HITL absent, désactivé, ou sévérité non
        soumise à approbation)."""
        if not self.hitl_gate_url:
            return False  # couche HITL non configurée : pleine autonomie
        payload = {
            "alert_id": alert.alert_id,
            # flow_id : permet à la couche HITL de demander au Sentinel
            # l'explication XAI (SHAP) du flux à l'origine de la remédiation.
            "flow_id": alert.detection.flow_id,
            "predicted_class": alert.detection.predicted_class,
            "severity": alert.severity.value,
            "confidence": alert.detection.confidence,
            "actions": [a.action_type for a in actions],
            "rationale": (alert.deliberation.rationale
                          if alert.deliberation else None),
            "action_objects": [a.model_dump(mode="json") for a in actions],
        }
        try:
            async with httpx.AsyncClient(timeout=5.0) as http:
                r = await http.post(
                    f"{self.hitl_gate_url}/api/agent/request-approval",
                    json=payload)
                r.raise_for_status()
                return not r.json().get("auto_approved", True)
        except httpx.HTTPError as exc:
            # Couche HITL injoignable : on n'immobilise pas la remédiation
            # (disponibilité prioritaire), on exécute en autonomie.
            logger.warning("[%s] Couche HITL injoignable (%s) — exécution "
                           "autonome", self.agent_id, exc)
            return False

    def _plan_actions(self, alert: Alert) -> list[RemediationAction]:
        recommended = (alert.deliberation.recommended_actions
                       if alert.deliberation else ["notify_operator"])
        actions = []
        for name in recommended:
            if name not in ACTION_TYPES or name == "no_action":
                continue
            actions.append(RemediationAction(
                alert_id=alert.alert_id,
                action_type=name,
                parameters={
                    "predicted_class": alert.detection.predicted_class,
                    "confidence": f"{alert.detection.confidence:.4f}",
                    "severity": alert.severity.value,
                },
            ))
        return actions

    async def _forward(self, actions: list[RemediationAction]):
        url = f"{self.cfg['executor_url']}/execute"
        async with httpx.AsyncClient(timeout=10.0) as http:
            for action in actions:
                try:
                    r = await http.post(url, json=action.model_dump(mode="json"))
                    r.raise_for_status()
                    self.forwarded += 1
                except httpx.HTTPError as exc:
                    logger.warning("[%s] Executor injoignable (%s) — action "
                                   "%s reste ancrée au ledger", self.agent_id,
                                   exc, action.action_id)

    # --------------------------------------------------------------- état
    def status(self) -> AgentStatus:
        extra = {"role": "leader" if self.is_leader else "peer",
                 "endorsements": self.endorsements,
                 "advisories": self.advisories_made}
        if self.is_leader:
            extra.update({
                "certified": self.certified,
                "not_certified": self.not_certified,
                "votes_rejected_by_ledger": self.votes_rejected,
                "actions_forwarded": self.forwarded,
                "deferred_to_hitl": self.deferred,
                "ledger_entries": self.ledger._index,
                "quorum": self.ledger.quorum,
            })
        return AgentStatus(
            agent_id=self.agent_id,
            agent_type="notary",
            uptime_s=round(time.time() - self.started_at, 1),
            processed=self.processed,
            extra=extra,
        )


def build_app(agent: NotaryAgent) -> FastAPI:
    app = FastAPI(title=f"BAg-IDS Notary ({agent.agent_id})", version="0.2")

    @app.post("/endorse")
    def endorse(payload: Alert):
        return agent.endorse(payload)

    @app.get("/advisories")
    def advisories(n: int = 50):
        # Avis LLM consultatifs (non décisionnels), pour audit.
        items = list(agent.advisories.items())[-n:]
        return {aid: adv for aid, adv in items}

    @app.get("/health", response_model=AgentStatus)
    def health():
        return agent.status()

    if agent.is_leader:
        @app.post("/alert")
        async def alert(payload: Alert):
            return await agent.handle_alert(payload)

        @app.get("/ledger")
        def ledger(n: int = 10):
            return {
                "chain_valid": agent.ledger.verify_chain(),
                "entries": agent.ledger.last_n(n),
            }

    return app


def main():
    parser = argparse.ArgumentParser(description="BAg-IDS Notary agent")
    parser.add_argument("--config", default="configs/agents.yaml")
    parser.add_argument("--instance", required=True,
                        help="agent_id de l'instance à lancer (ex. notary-01)")
    args = parser.parse_args()
    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    agent = NotaryAgent(cfg, args.instance)
    app = build_app(agent)
    logger.info("[%s] Notary (%s) en écoute sur %s:%s", agent.agent_id,
                "leader" if agent.is_leader else "pair",
                agent.me["host"], agent.me["port"])
    uvicorn.run(app, host=agent.me["host"], port=int(agent.me["port"]),
                log_level="warning")


if __name__ == "__main__":
    main()
