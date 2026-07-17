"""
BAg-IDS HITL — Agrégateur : collecte l'état des agents et du ledger.

Interroge les endpoints /health des 4 agents et lit le ledger (miroir
local, ou passerelle Fabric) pour alimenter le dashboard, la vue
incidents et la vue d'audit. Tolérant aux agents hors ligne (l'app
reste utilisable pour l'audit historique même sans agents actifs).
"""

from __future__ import annotations

import json
from pathlib import Path

import httpx

from hitl.backend.config import CONFIG

_AGENTS = CONFIG["agents"]


def agent_health() -> dict:
    """Santé des 4 agents ; chaque agent absent => status offline."""
    out = {}
    with httpx.Client(timeout=2.0) as http:
        for name, url in _AGENTS.items():
            try:
                r = http.get(f"{url}/health")
                r.raise_for_status()
                out[name] = {"online": True, **r.json()}
            except httpx.HTTPError:
                out[name] = {"online": False}
    return out


def _read_mirror(n: int | None = None) -> list[dict]:
    path = Path(CONFIG["ledger_mirror"])
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    if n:
        lines = lines[-n:]
    out = []
    for line in lines:
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def ledger_entries(n: int = 200) -> list[dict]:
    """Dernières entrées du ledger (miroir local d'audit)."""
    return list(reversed(_read_mirror(n)))


def ledger_verify_via_gateway() -> dict | None:
    """Si la passerelle Fabric est joignable, renvoie son état /health."""
    url = CONFIG.get("fabric_proxy_url")
    if not url:
        return None
    try:
        r = httpx.get(f"{url}/health", timeout=2.0)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPError:
        return None


def investigations(n: int = 30) -> list[dict]:
    """Rapports d'enquête de l'agent Investigator (traces agentiques)."""
    url = _AGENTS.get("investigator")
    if not url:
        return []
    try:
        r = httpx.get(f"{url}/reports", params={"n": n}, timeout=3.0)
        r.raise_for_status()
        return list(reversed(r.json()))   # plus récents d'abord
    except httpx.HTTPError:
        return []


def notary_advisories(n: int = 50) -> dict:
    """Avis LLM consultatifs (non décisionnels) attachés par les notaries."""
    url = _AGENTS.get("notary_leader")
    if not url:
        return {}
    try:
        r = httpx.get(f"{url}/advisories", params={"n": n}, timeout=3.0)
        r.raise_for_status()
        return r.json()
    except httpx.HTTPError:
        return {}


def onchain_governance() -> list[dict] | None:
    """Récupère le journal de gouvernance ancré on-chain via la passerelle
    (ListGovernance). Renvoie None si Fabric indisponible."""
    url = CONFIG.get("fabric_proxy_url")
    if not url:
        return None
    try:
        r = httpx.post(f"{url}/evaluate", json={
            "function": "ListGovernance", "args": []}, timeout=5.0)
        r.raise_for_status()
        body = r.json()
        if body.get("error") or not body.get("result"):
            return []
        import json as _json
        return _json.loads(body["result"])
    except (httpx.HTTPError, ValueError):
        return None


def incidents(n: int = 200) -> list[dict]:
    """Reconstruit la liste des incidents (alertes) depuis le ledger,
    en attachant leur statut de certification et les votes reçus."""
    entries = _read_mirror()
    alerts: dict[str, dict] = {}
    for e in entries:
        kind, payload = e.get("kind"), e.get("payload", {})
        aid = payload.get("alert_id")
        if not aid:
            continue
        if kind == "ALERT":
            det = payload.get("detection", {})
            alerts.setdefault(aid, {})
            alerts[aid].update({
                "alert_id": aid,
                "timestamp": e.get("timestamp"),
                "sentinel_id": payload.get("sentinel_id"),
                "severity": payload.get("severity"),
                "predicted_class": det.get("predicted_class"),
                "confidence": det.get("confidence"),
                "deliberation": payload.get("deliberation"),
                "votes": alerts.get(aid, {}).get("votes", {}),
                "certified": alerts.get(aid, {}).get("certified", False),
            })
        elif kind == "VOTE":
            a = alerts.setdefault(aid, {"alert_id": aid, "votes": {}})
            a.setdefault("votes", {})[payload.get("voter_id")] = \
                payload.get("approve")
        elif kind == "ALERT_CERTIFIED":
            a = alerts.setdefault(aid, {"alert_id": aid, "votes": {}})
            a["certified"] = True
            a["approvals"] = payload.get("approvals")
    ordered = sorted(alerts.values(),
                     key=lambda x: x.get("timestamp", 0), reverse=True)
    return ordered[:n]


def metrics_summary() -> dict:
    """Agrège quelques métriques clés pour le dashboard."""
    health = agent_health()
    sentinel = health.get("sentinel", {})
    extra = sentinel.get("extra", {}) if sentinel.get("online") else {}
    incs = incidents(1000)
    certified = sum(1 for i in incs if i.get("certified"))
    return {
        "sentinel_online": sentinel.get("online", False),
        "flows_processed": sentinel.get("processed", 0),
        "verdict_benign": extra.get("verdict_benign", 0),
        "verdict_attack": extra.get("verdict_attack", 0),
        "verdict_rejected": extra.get("verdict_rejected", 0),
        "incidents_total": len(incs),
        "incidents_certified": certified,
        "agents_online": sum(1 for a in health.values() if a.get("online")),
        "agents_total": len(health),
    }
