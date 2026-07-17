"""
BAg-IDS — Ledger simulé + logique chaincode validateVote (étape 1.3).

Deux couches, comme sur Hyperledger Fabric à l'étape 1.4 :

  1. Journal append-only à chaînage de hachages (immuabilité vérifiable :
     toute modification a posteriori casse `verify_chain`) — l'équivalent
     du ledger répliqué de Fabric.

  2. Logique transactionnelle `validateVote` — l'équivalent du chaincode :
       - un vote n'est accepté que s'il est SIGNÉ (Ed25519) par un agent
         du registre des signataires autorisés ;
       - un agent ne vote qu'une fois par alerte (anti-rejeu) ;
       - quand `quorum` votes d'approbation valides sont réunis, le
         ledger scelle lui-même une entrée ALERT_CERTIFIED (résultat du
         consensus, pas une décision d'un agent isolé).

À l'étape 1.4, cette classe est remplacée par un client Fabric qui
soumet les mêmes transactions au chaincode Go `validateVote` : les
agents (Notary en tête) ne changent pas.
"""

from __future__ import annotations

import hashlib
import json
import logging
import threading
import time
from pathlib import Path

from agents.common.identity import SignerRegistry

logger = logging.getLogger("bag_ids.agents.ledger")

GENESIS_HASH = "0" * 64


def _canonical(obj: dict) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)


class VoteValidationError(ValueError):
    """Vote refusé par la logique chaincode (signature, autorisation,
    double vote...). Le motif exact est dans le message."""


class SimulatedLedger:
    def __init__(self, path: str | Path,
                 signer_registry: SignerRegistry | None = None,
                 quorum: int = 1):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.registry = signer_registry
        self.quorum = quorum
        self._lock = threading.Lock()
        self._last_hash = GENESIS_HASH
        self._index = 0
        # État "chaincode" : votes par alerte + alertes déjà certifiées
        self._votes: dict[str, dict[str, bool]] = {}
        self._certified: set[str] = set()
        if self.path.exists():
            self._replay()

    def _replay(self):
        """Reprise sur fichier existant : restaure chaîne ET état votes."""
        for line in self.path.read_text(encoding="utf-8").splitlines():
            entry = json.loads(line)
            self._last_hash = entry["hash"]
            self._index = entry["index"] + 1
            if entry["kind"] == "VOTE":
                p = entry["payload"]
                self._votes.setdefault(p["alert_id"], {})[p["voter_id"]] = \
                    p["approve"]
            elif entry["kind"] == "ALERT_CERTIFIED":
                self._certified.add(entry["payload"]["alert_id"])

    # ------------------------------------------------------------ journal
    def submit(self, kind: str, payload: dict) -> dict:
        """Ajoute une transaction ; retourne l'entrée scellée (avec hash)."""
        with self._lock:
            return self._append(kind, payload)

    def _append(self, kind: str, payload: dict) -> dict:
        entry = {
            "index": self._index,
            "timestamp": time.time(),
            "kind": kind,
            "payload": payload,
            "prev_hash": self._last_hash,
        }
        entry["hash"] = hashlib.sha256(
            (entry["prev_hash"] + _canonical(payload)).encode("utf-8")
        ).hexdigest()
        with self.path.open("a", encoding="utf-8") as f:
            f.write(_canonical(entry) + "\n")
        self._last_hash = entry["hash"]
        self._index += 1
        return entry

    # ------------------------------------------- logique chaincode (1.4)
    def validate_vote(self, vote_payload: dict, signature_hex: str) -> dict:
        """Transaction validateVote : vérifie puis ancre un vote signé.

        Retourne {"accepted": True, "certified": bool} ; lève
        VoteValidationError si le vote est refusé (raison en message).
        Sémantique identique à celle du futur chaincode Go.
        """
        if self.registry is None:
            raise VoteValidationError("aucun registre de signataires chargé")
        voter = vote_payload.get("voter_id", "")
        alert_id = vote_payload.get("alert_id", "")
        if not self.registry.is_authorized(voter):
            raise VoteValidationError(f"signataire non autorisé : {voter}")
        if not self.registry.verify(voter, vote_payload, signature_hex):
            raise VoteValidationError(f"signature invalide pour {voter}")

        with self._lock:
            votes = self._votes.setdefault(alert_id, {})
            if voter in votes:
                raise VoteValidationError(
                    f"double vote de {voter} sur {alert_id}")
            votes[voter] = bool(vote_payload.get("approve", False))
            self._append("VOTE", {**vote_payload, "signature": signature_hex})

            certified = False
            approvals = sum(1 for ok in votes.values() if ok)
            if approvals >= self.quorum and alert_id not in self._certified:
                self._certified.add(alert_id)
                certified = True
                self._append("ALERT_CERTIFIED", {
                    "alert_id": alert_id,
                    "approvals": approvals,
                    "quorum": self.quorum,
                    "voters": sorted(votes),
                })
                logger.info("Alerte %s CERTIFIÉE (%d/%d approbations)",
                            alert_id, approvals, self.quorum)
        return {"accepted": True, "certified": certified,
                "approvals": approvals}

    def is_certified(self, alert_id: str) -> bool:
        return alert_id in self._certified

    # ------------------------------------------------------------ lecture
    def last_n(self, n: int = 10) -> list[dict]:
        if not self.path.exists():
            return []
        lines = self.path.read_text(encoding="utf-8").splitlines()
        return [json.loads(line) for line in lines[-n:]]

    def verify_chain(self) -> bool:
        """Revalide l'intégrité complète de la chaîne de hachages."""
        prev = GENESIS_HASH
        for line in self.path.read_text(encoding="utf-8").splitlines():
            entry = json.loads(line)
            expected = hashlib.sha256(
                (prev + _canonical(entry["payload"])).encode("utf-8")
            ).hexdigest()
            if entry["prev_hash"] != prev or entry["hash"] != expected:
                return False
            prev = entry["hash"]
        return True
