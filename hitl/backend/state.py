"""
BAg-IDS HITL — État partagé de la couche de supervision.

Détient, en mémoire du backend :
  - l'interrupteur HITL (approbation humaine requise ou pleine autonomie) ;
  - la file des remédiations en attente d'approbation ;
  - la policy courante (tau, quorum, backend LLM, dry-run) ;
  - un journal d'événements récents (pour le flux temps réel du dashboard).

Toute mutation sensible (toggle, policy, décision manuelle) est ancrée
dans le ledger via governance.py — cet objet n'est que le cache vivant.
"""

from __future__ import annotations

import threading
import time
from collections import deque

from hitl.backend.config import CONFIG


class HITLState:
    def __init__(self):
        self._lock = threading.Lock()
        self.hitl_enabled = bool(CONFIG["hitl_enabled_default"])
        self.policy = dict(CONFIG["policy"])
        self.approval_severities = set(CONFIG["approval_required_severities"])
        # file d'attente : liste de dicts {id, alert, severity, actions, ...}
        self._pending: dict[str, dict] = {}
        self._decisions: deque = deque(maxlen=500)   # historique approuvé/rejeté
        self._events: deque = deque(maxlen=1000)      # flux temps réel
        self._governance: deque = deque(maxlen=500)   # journal des changements

    # --------------------------------------------------------- toggle
    def set_hitl(self, enabled: bool, actor: str):
        with self._lock:
            self.hitl_enabled = enabled
        self.record_governance("toggle_hitl", actor,
                               {"enabled": enabled})
        self.push_event("hitl_toggle",
                        f"HITL {'activé' if enabled else 'désactivé'} "
                        f"par {actor}")

    # --------------------------------------------------------- policy
    def update_policy(self, changes: dict, actor: str) -> dict:
        with self._lock:
            before = dict(self.policy)
            self.policy.update(changes)
            after = dict(self.policy)
        self.record_governance("update_policy", actor,
                               {"before": before, "after": after})
        self.push_event("policy_update",
                        f"Paramètres modifiés par {actor} : {changes}")
        return after

    # ------------------------------------------------- file d'approbation
    def requires_approval(self, severity: str) -> bool:
        return self.hitl_enabled and severity in self.approval_severities

    def enqueue(self, item: dict):
        with self._lock:
            self._pending[item["id"]] = item
        self.push_event("pending",
                        f"Remédiation en attente d'approbation : "
                        f"{item.get('predicted_class')} ({item.get('severity')})")

    def attach_explanation(self, item_id: str, explanation: dict):
        """Attache le résultat XAI (SHAP + narration) à une remédiation
        encore en attente. Si l'analyste a déjà tranché, l'explication est
        jointe à la décision historisée (utile pour l'audit a posteriori)."""
        with self._lock:
            item = self._pending.get(item_id)
            if item is not None:
                item["explanation"] = explanation
                return
            for decided in self._decisions:
                if decided.get("id") == item_id:
                    decided["explanation"] = explanation
                    return

    def pending(self) -> list[dict]:
        with self._lock:
            return sorted(self._pending.values(),
                          key=lambda x: x["created_at"], reverse=True)

    def decide(self, item_id: str, approve: bool, actor: str,
               reason: str | None = None) -> dict | None:
        with self._lock:
            item = self._pending.pop(item_id, None)
            if item is None:
                return None
            item["decided_by"] = actor
            item["approved"] = approve
            item["reason"] = reason
            item["decided_at"] = time.time()
            self._decisions.appendleft(item)
        self.record_governance("manual_decision", actor, {
            "alert_id": item.get("alert_id"), "approved": approve,
            "reason": reason})
        self.push_event("decision",
                        f"{'Approuvé' if approve else 'Rejeté'} par {actor} : "
                        f"{item.get('predicted_class')}")
        return item

    def decisions(self, n: int = 100) -> list[dict]:
        with self._lock:
            return list(self._decisions)[:n]

    # ------------------------------------------------------- événements
    def push_event(self, kind: str, message: str, extra: dict | None = None):
        with self._lock:
            self._events.appendleft({
                "ts": time.time(), "kind": kind, "message": message,
                **(extra or {})})

    def events(self, n: int = 100) -> list[dict]:
        with self._lock:
            return list(self._events)[:n]

    def record_governance(self, action: str, actor: str, details: dict):
        with self._lock:
            self._governance.appendleft({
                "ts": time.time(), "action": action, "actor": actor,
                "details": details})

    def governance_log(self, n: int = 200) -> list[dict]:
        with self._lock:
            return list(self._governance)[:n]

    def snapshot(self) -> dict:
        with self._lock:
            return {
                "hitl_enabled": self.hitl_enabled,
                "policy": dict(self.policy),
                "pending_count": len(self._pending),
                "approval_severities": sorted(self.approval_severities),
            }


STATE = HITLState()
