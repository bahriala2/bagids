"""
BAg-IDS HITL — Ancrage on-chain des actions de gouvernance.

Toute action sensible de la couche de supervision (bascule HITL,
changement de policy, décision manuelle d'approbation) est signée par
l'identité de gouvernance et soumise au chaincode. Ainsi l'administrateur
lui-même est auditable : la trace des interventions humaines est
immuable, au même titre que les votes des notaries.

Si la passerelle Fabric n'est pas joignable, l'ancrage retombe sur le
ledger local (miroir) — la gouvernance reste journalisée, sans la
garantie blockchain.
"""

from __future__ import annotations

import json
import logging

import httpx

from agents.common.identity import AgentIdentity
from hitl.backend.config import CONFIG

logger = logging.getLogger("bag_ids.hitl.governance")


class GovernanceAnchor:
    def __init__(self):
        self.proxy_url = CONFIG.get("fabric_proxy_url")
        self.signer_id = CONFIG["governance_signer"]
        try:
            self.identity = AgentIdentity.load(CONFIG["keys_dir"],
                                               self.signer_id)
        except FileNotFoundError:
            self.identity = None
            logger.warning("Identité de gouvernance introuvable : ancrage "
                           "on-chain désactivé")

    def _fabric_available(self) -> bool:
        if not self.proxy_url:
            return False
        try:
            return httpx.get(f"{self.proxy_url}/health",
                             timeout=2.0).status_code == 200
        except httpx.HTTPError:
            return False

    def anchor(self, action: str, actor: str, details: dict) -> dict:
        """Enregistre une action de gouvernance. Retourne un reçu avec le
        mode d'ancrage effectif (fabric / local)."""
        # Le signataire (identité de gouvernance) est inclus dans le
        # payload signé : le lien acteur→signataire est ainsi cryptographique.
        record = {"action": action, "actor": actor,
                  "signer": self.signer_id, "details": details}
        if self.identity and self._fabric_available():
            payload = json.dumps(record, sort_keys=True, separators=(",", ":"),
                                 ensure_ascii=False)
            signature = self.identity.sign(record)
            try:
                r = httpx.post(f"{self.proxy_url}/submit", json={
                    "function": "RecordGovernance",
                    "args": [action, actor, self.signer_id, payload, signature],
                }, timeout=30.0)
                if r.status_code == 200 and not r.json().get("error"):
                    return {"anchored": "fabric", "signature": signature[:16]}
                logger.warning("Ancrage Fabric refusé : %s", r.text[:200])
            except httpx.HTTPError as exc:
                logger.warning("Passerelle Fabric injoignable : %s", exc)
        # Repli : journalisation locale (déjà faite par STATE.record_governance)
        return {"anchored": "local"}


ANCHOR = GovernanceAnchor()
