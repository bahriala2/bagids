"""
Routes de contrôle : approbation d'incidents (analyste+), gouvernance
des paramètres et bascule HITL (admin), réception des demandes
d'approbation émises par les agents.
"""

from __future__ import annotations

import time
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends
from pydantic import BaseModel

from hitl.backend.auth import require_role
from hitl.backend.detection import CONTROLLER
from hitl.backend.governance import ANCHOR
from hitl.backend.state import STATE

router = APIRouter(prefix="/api", tags=["control"])
_analyst = Depends(require_role("analyst"))
_admin = Depends(require_role("admin"))
_reader = Depends(require_role("reader"))


# --------------------------------------------------- modèles de requête
class DecisionBody(BaseModel):
    approve: bool
    reason: str | None = None


class PolicyBody(BaseModel):
    tau: float | None = None
    quorum: int | None = None
    executor_dry_run: bool | None = None
    llm_provider_order: list[str] | None = None


class ToggleBody(BaseModel):
    enabled: bool


class ApprovalRequest(BaseModel):
    """Émise par le Notary/Executor quand une remédiation nécessite un
    feu vert humain (HITL activé + sévérité concernée)."""
    alert_id: str
    predicted_class: str
    severity: str
    confidence: float | None = None
    actions: list[str] = []
    rationale: str | None = None
    # Objets d'action complets, transmis à l'Executor après approbation.
    action_objects: list[dict] = []
    # Identifiant du flux à l'origine de l'alerte : permet de demander au
    # Sentinel l'explication XAI (SHAP) présentée à l'analyste.
    flow_id: str | None = None


# ------------------------------------------------ file d'approbation
@router.get("/pending")
def pending(user: dict = Depends(require_role("reader"))):
    return STATE.pending()


@router.get("/decisions")
def decisions(n: int = 100, user: dict = Depends(require_role("reader"))):
    return STATE.decisions(n)


@router.post("/pending/{item_id}/decide")
def decide(item_id: str, body: DecisionBody, user: dict = _analyst):
    item = STATE.decide(item_id, body.approve, user["username"], body.reason)
    if item is None:
        return {"error": "élément introuvable ou déjà traité"}
    receipt = ANCHOR.anchor("manual_decision", user["username"], {
        "alert_id": item.get("alert_id"), "approved": body.approve})
    # Sur approbation, la couche HITL transmet elle-même les actions à
    # l'Executor (le Notary avait différé l'exécution).
    executed = []
    if body.approve and item.get("action_objects"):
        executed = _forward_to_executor(item["action_objects"])
    return {"ok": True, "item": item, "anchor": receipt, "executed": executed}


def _forward_to_executor(action_objects: list[dict]) -> list[str]:
    import httpx
    from hitl.backend.config import CONFIG
    url = f"{CONFIG['agents']['executor']}/execute"
    done = []
    with httpx.Client(timeout=10.0) as http:
        for action in action_objects:
            try:
                r = http.post(url, json=action)
                if r.status_code == 200:
                    done.append(r.json().get("action_id"))
            except httpx.HTTPError:
                pass
    return done


@router.post("/agent/request-approval")
def request_approval(req: ApprovalRequest, background_tasks: BackgroundTasks):
    """Endpoint appelé par les agents (pas d'auth : réseau interne).
    Place la remédiation en file si HITL l'exige ; sinon auto-approuve."""
    if not STATE.requires_approval(req.severity):
        return {"auto_approved": True, "hitl_enabled": STATE.hitl_enabled}
    item = {
        "id": uuid.uuid4().hex,
        "alert_id": req.alert_id,
        "flow_id": req.flow_id,
        "predicted_class": req.predicted_class,
        "severity": req.severity,
        "confidence": req.confidence,
        "actions": req.actions,
        "rationale": req.rationale,
        "action_objects": req.action_objects,
        "created_at": time.time(),
        "status": "pending",
        # Explication XAI : null = calcul en cours (ou indisponible) ;
        # renseignée de façon asynchrone par _fetch_explanation.
        "explanation": None,
    }
    STATE.enqueue(item)
    # L'explication (SHAP + narration LLM, ~5-30 s) est demandée au
    # Sentinel HORS de la requête du Notary, qui doit répondre en <5 s.
    if req.flow_id:
        background_tasks.add_task(_fetch_explanation, item["id"], req.flow_id)
    return {"auto_approved": False, "queued": True, "id": item["id"]}


def _fetch_explanation(item_id: str, flow_id: str):
    """Tâche de fond : demande l'explication au Sentinel et l'attache à
    l'élément en attente (sans jamais bloquer la file d'approbation)."""
    import httpx
    from hitl.backend.config import CONFIG
    url = f"{CONFIG['agents']['sentinel']}/explain"
    try:
        with httpx.Client(timeout=120.0) as http:
            r = http.post(url, json={"flow_id": flow_id,
                                     "with_narrative": True})
            r.raise_for_status()
            data = r.json()
    except httpx.HTTPError as exc:
        data = {"error": f"sentinel injoignable : {exc}"}
    STATE.attach_explanation(item_id, data)


# ------------------------------------------------------ gouvernance
@router.get("/policy")
def get_policy(user: dict = Depends(require_role("reader"))):
    return STATE.snapshot()


@router.post("/policy")
def set_policy(body: PolicyBody, user: dict = _admin):
    changes = {k: v for k, v in body.model_dump().items() if v is not None}
    if not changes:
        return {"error": "aucun changement fourni"}
    after = STATE.update_policy(changes, user["username"])
    receipt = ANCHOR.anchor("update_policy", user["username"], changes)
    return {"ok": True, "policy": after, "anchor": receipt}


@router.post("/hitl/toggle")
def toggle_hitl(body: ToggleBody, user: dict = _admin):
    STATE.set_hitl(body.enabled, user["username"])
    receipt = ANCHOR.anchor("toggle_hitl", user["username"],
                            {"enabled": body.enabled})
    return {"ok": True, "hitl_enabled": body.enabled, "anchor": receipt}


# --------------------------------------------- contrôle de la détection
class InjectBody(BaseModel):
    flows: list[list[float]]
    labels: list[str] | None = None


@router.get("/detection/status")
def detection_status(user: dict = _reader):
    return CONTROLLER.status()


@router.post("/detection/start")
def detection_start(user: dict = _analyst):
    result = CONTROLLER.start()
    ANCHOR.anchor("detection_start", user["username"], {})
    return result


@router.post("/detection/stop")
def detection_stop(user: dict = _analyst):
    result = CONTROLLER.stop()
    ANCHOR.anchor("detection_stop", user["username"], {})
    return result


@router.get("/detection/meta")
def detection_meta(user: dict = _reader):
    return CONTROLLER.sentinel_meta() or {"error": "sentinel hors ligne"}


@router.post("/detection/inject")
def detection_inject(body: InjectBody, user: dict = _analyst):
    """Injecte des flux de test (attaques fournies par l'opérateur) dans le
    pipeline en cours et renvoie le verdict de chacun."""
    return CONTROLLER.inject(body.flows, body.labels)
