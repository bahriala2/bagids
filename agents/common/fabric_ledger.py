"""
BAg-IDS — Client Fabric du Notary (étape 1.4).

Même interface que SimulatedLedger (submit / validate_vote /
is_certified / verify_chain), mais les transactions de consensus
partent vers le chaincode `validatevote` sur Hyperledger Fabric, via la
passerelle HTTP locale (chaincode/gateway-proxy, SDK fabric-gateway).

Répartition des écritures :
  - ALERT            -> RecordAlert (on-chain)
  - votes            -> ValidateVote (on-chain : signature Ed25519
                        vérifiée PAR LE CHAINCODE, anti-rejeu, quorum)
  - autres kinds     -> miroir local JSONL (journal d'exploitation ;
                        ex. ACTION_PLANNED, hors périmètre consensus)

L'intégrité de la partie consensus est garantie par Fabric lui-même
(ledger répliqué, endorsement des 2 organisations) : verify_chain ne
revalide donc que le miroir local.
"""

from __future__ import annotations

import logging

import httpx

from agents.common.identity import SignerRegistry
from agents.common.ledger import SimulatedLedger, VoteValidationError

logger = logging.getLogger("bag_ids.agents.fabric_ledger")


class FabricLedger:
    def __init__(self, proxy_url: str, local_mirror_path: str,
                 signer_registry: SignerRegistry | None = None,
                 quorum: int = 1, timeout_s: float = 60.0):
        self.proxy_url = proxy_url.rstrip("/")
        self.quorum = quorum
        self.registry = signer_registry   # non utilisé pour vérifier (le
        # chaincode s'en charge) mais gardé pour l'enregistrement initial
        self._http = httpx.Client(timeout=timeout_s)
        # Miroir local pour les entrées hors consensus + audit lisible
        self._mirror = SimulatedLedger(local_mirror_path)
        health = self._http.get(f"{self.proxy_url}/health").json()
        logger.info("FabricLedger connecté : canal=%s, chaincode=%s",
                    health.get("channel"), health.get("chaincode"))

    # ------------------------------------------------------------ interne
    def _submit(self, function: str, args: list[str]) -> str:
        r = self._http.post(f"{self.proxy_url}/submit",
                            json={"function": function, "args": args})
        body = r.json()
        if r.status_code != 200 or body.get("error"):
            raise RuntimeError(body.get("error", f"HTTP {r.status_code}"))
        return body.get("result", "")

    def _evaluate(self, function: str, args: list[str]) -> str:
        r = self._http.post(f"{self.proxy_url}/evaluate",
                            json={"function": function, "args": args})
        body = r.json()
        if r.status_code != 200 or body.get("error"):
            raise RuntimeError(body.get("error", f"HTTP {r.status_code}"))
        return body.get("result", "")

    # -------------------------------------------------------- bootstrap
    def register_signer(self, agent_id: str, public_key_hex: str):
        """Enregistre un notary autorisé dans l'état du chaincode
        (idempotent). À appeler au démarrage du leader."""
        self._submit("RegisterSigner", [agent_id, public_key_hex])
        logger.info("Signataire %s enregistré on-chain", agent_id)

    # ------------------------------------------------ interface ledger
    def submit(self, kind: str, payload: dict) -> dict:
        if kind == "ALERT":
            det = payload.get("detection", {})
            self._submit("RecordAlert", [
                payload.get("alert_id", ""),
                payload.get("sentinel_id", ""),
                str(det.get("predicted_class", "")),
                str(det.get("confidence", 0.0)),
                str(payload.get("severity", "")),
                "{}",  # payload complet volumineux : ancré en miroir local
            ])
        # Toutes les entrées (y compris ALERT) sont aussi journalisées
        # localement pour l'audit lisible et les kinds hors consensus.
        return self._mirror.submit(kind, payload)

    def validate_vote(self, vote_payload: dict, signature_hex: str) -> dict:
        """Soumet le vote signé AU CHAINCODE : c'est lui qui vérifie la
        signature, l'autorisation, l'anti-rejeu et le quorum."""
        import json as _json
        canonical = _json.dumps(vote_payload, sort_keys=True,
                                separators=(",", ":"), ensure_ascii=False)
        try:
            result = self._submit("ValidateVote", [
                vote_payload.get("alert_id", ""),
                vote_payload.get("voter_id", ""),
                "true" if vote_payload.get("approve") else "false",
                canonical,
                signature_hex,
                str(self.quorum),
            ])
        except RuntimeError as exc:
            # Erreurs d'endorsement du chaincode = vote refusé
            raise VoteValidationError(str(exc)) from exc
        alert = _json.loads(result) if result else {}
        self._mirror.submit("VOTE", {**vote_payload,
                                     "signature": signature_hex})
        certified = bool(alert.get("certified"))
        approvals = sum(1 for ok in (alert.get("votes") or {}).values() if ok)
        if certified:
            self._mirror.submit("ALERT_CERTIFIED", {
                "alert_id": vote_payload.get("alert_id", ""),
                "approvals": approvals,
                "quorum": self.quorum,
                "voters": sorted((alert.get("votes") or {})),
            })
        return {"accepted": True, "certified": certified,
                "approvals": approvals}

    def is_certified(self, alert_id: str) -> bool:
        try:
            return self._evaluate("IsCertified", [alert_id]) == "true"
        except RuntimeError:
            return False

    def last_n(self, n: int = 10) -> list[dict]:
        return self._mirror.last_n(n)

    def verify_chain(self) -> bool:
        # La partie consensus est garantie par Fabric ; on vérifie le miroir.
        return self._mirror.verify_chain()

    @property
    def _index(self) -> int:
        return self._mirror._index
