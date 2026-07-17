"""
BAg-IDS — Outils de l'agent Investigator.

Un agent (au sens fort) décide lui-même quels outils invoquer. Ces
fonctions sont les outils que l'Investigator peut appeler au fil de son
enquête : lire le ledger, corréler des incidents, consulter sa mémoire.
Chaque outil est pur et journalisable, ce qui rend la trace agentique
rejouable et auditable.
"""

from __future__ import annotations

import json
import time
from pathlib import Path


class LedgerTool:
    """Lecture du ledger (miroir local d'audit) : incidents récents,
    incidents liés à une classe d'attaque, historique d'un émetteur."""

    def __init__(self, mirror_path: str):
        self.path = Path(mirror_path)

    def _entries(self) -> list[dict]:
        if not self.path.exists():
            return []
        out = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return out

    def recent_alerts(self, window_s: float = 3600.0, limit: int = 200) -> list[dict]:
        """Alertes ancrées dans la fenêtre de temps donnée."""
        now = time.time()
        alerts = []
        for e in self._entries():
            if e.get("kind") != "ALERT":
                continue
            p = e.get("payload", {})
            ts = p.get("timestamp") or e.get("timestamp", 0)
            if now - ts <= window_s:
                det = p.get("detection", {})
                alerts.append({
                    "alert_id": p.get("alert_id"),
                    "predicted_class": det.get("predicted_class")
                        or p.get("predicted_class"),
                    "confidence": det.get("confidence") or p.get("confidence"),
                    "timestamp": ts,
                })
        return alerts[-limit:]

    def related_by_class(self, predicted_class: str, exclude_id: str,
                         window_s: float = 3600.0) -> list[dict]:
        """Incidents récents de la même classe d'attaque (proxy de campagne)."""
        return [a for a in self.recent_alerts(window_s)
                if a.get("predicted_class") == predicted_class
                and a.get("alert_id") != exclude_id]


def correlate(related: list[dict]) -> dict:
    """Outil d'analyse : mesure l'intensité temporelle d'incidents liés
    (rafale récente = signe de campagne coordonnée)."""
    n = len(related)
    if n == 0:
        return {"count": 0, "burst": False, "rate_per_min": 0.0}
    ts = sorted(a.get("timestamp", 0) for a in related)
    span = max(1.0, ts[-1] - ts[0])
    rate = n / (span / 60.0)
    # rafale : au moins 3 incidents liés et > 1 par minute
    return {"count": n, "burst": n >= 3 and rate > 1.0,
            "rate_per_min": round(rate, 2)}
