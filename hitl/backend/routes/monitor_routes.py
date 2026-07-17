"""Routes de supervision : dashboard, incidents, audit ledger, agents."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from hitl.backend import aggregator
from hitl.backend.auth import require_role
from hitl.backend.state import STATE

router = APIRouter(prefix="/api", tags=["monitor"])
_reader = Depends(require_role("reader"))


@router.get("/dashboard")
def dashboard(user: dict = _reader):
    return {
        "metrics": aggregator.metrics_summary(),
        "hitl": STATE.snapshot(),
        "agents": aggregator.agent_health(),
        "fabric": aggregator.ledger_verify_via_gateway(),
        "recent_events": STATE.events(30),
    }


@router.get("/agents")
def agents(user: dict = _reader):
    return aggregator.agent_health()


@router.get("/incidents")
def incidents(n: int = 200, user: dict = _reader):
    return aggregator.incidents(n)


@router.get("/investigations")
def investigations(n: int = 30, user: dict = _reader):
    """Enquêtes autonomes de l'agent Investigator (traces agentiques)."""
    return aggregator.investigations(n)


@router.get("/advisories")
def advisories(n: int = 50, user: dict = _reader):
    """Avis LLM consultatifs (non décisionnels) des notaries."""
    return aggregator.notary_advisories(n)


@router.get("/ledger")
def ledger(n: int = 200, user: dict = _reader):
    return {
        "entries": aggregator.ledger_entries(n),
        "fabric": aggregator.ledger_verify_via_gateway(),
    }


@router.get("/events")
def events(n: int = 100, user: dict = _reader):
    return STATE.events(n)


@router.get("/governance/log")
def governance_log(n: int = 200, user: dict = _reader):
    # Journal local (temps réel) + gouvernance ancrée on-chain (audit).
    return {
        "local": STATE.governance_log(n),
        "onchain": aggregator.onchain_governance(),
    }
