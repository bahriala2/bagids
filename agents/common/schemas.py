"""
BAg-IDS — Schémas des messages échangés entre agents.

Chaque message inter-agents est un modèle Pydantic : validation
automatique aux frontières (FastAPI) et sérialisation JSON canonique
(celle qui sera signée/ancrée dans le ledger aux étapes 1.3/1.4).
"""

from __future__ import annotations

import time
import uuid
from enum import Enum

from pydantic import BaseModel, Field


def _now() -> float:
    return time.time()


def _new_id() -> str:
    return uuid.uuid4().hex


class Verdict(str, Enum):
    """Issue de la boucle réflexe du Sentinel pour un flux."""

    BENIGN = "benign"          # classé bénin avec confiance >= tau
    ATTACK = "attack"          # classé attaque avec confiance >= tau
    REJECTED = "rejected"      # confiance < tau : non certifié (zone grise)


class FlowFeatures(BaseModel):
    """Un flux réseau prétraité (vecteur de features CICFlowMeter).

    Les features sont transmises déjà ordonnées selon le schéma
    d'entraînement ; le Sentinel applique lui-même le scaler.
    """

    flow_id: str = Field(default_factory=_new_id)
    timestamp: float = Field(default_factory=_now)
    features: list[float]
    # Vérité terrain optionnelle (mode replay/évaluation uniquement)
    true_label: str | None = None


class Detection(BaseModel):
    """Décision de la boucle réflexe du Sentinel pour un flux."""

    detection_id: str = Field(default_factory=_new_id)
    flow_id: str
    timestamp: float = Field(default_factory=_now)
    verdict: Verdict
    predicted_class: str
    confidence: float
    tau: float
    # Posteriors fusionnés par classe (pour audit et délibération)
    class_probabilities: dict[str, float]
    # Contributions par modèle : classe prédite et confiance individuelles
    per_model: dict[str, dict[str, float | str]]
    inference_ms: float
    true_label: str | None = None


class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Alert(BaseModel):
    """Alerte émise par le Sentinel vers le Notary quand une attaque
    est certifiée (ou qu'un motif suspect récurrent est délibéré)."""

    alert_id: str = Field(default_factory=_new_id)
    timestamp: float = Field(default_factory=_now)
    sentinel_id: str
    detection: Detection
    severity: AlertSeverity
    # Résultat de la couche délibérative (LLM), si elle a été sollicitée
    deliberation: DeliberationResult | None = None


class DeliberationResult(BaseModel):
    """Sortie structurée de la couche délibérative (LLM ou règles)."""

    deliberation_id: str = Field(default_factory=_new_id)
    timestamp: float = Field(default_factory=_now)
    trigger: str                     # ce qui a déclenché la délibération
    provider: str                    # openrouter / lmstudio / rules-fallback
    model: str
    severity: AlertSeverity
    rationale: str                   # justification en langage naturel
    recommended_actions: list[str]
    latency_ms: float


class Vote(BaseModel):
    """Vote d'un agent sur une alerte (consensus de la couche 3).

    À l'étape 1.4, ce message est signé et soumis au chaincode
    validateVote ; ici il transite en clair vers le ledger simulé.
    """

    vote_id: str = Field(default_factory=_new_id)
    timestamp: float = Field(default_factory=_now)
    alert_id: str
    voter_id: str
    approve: bool
    reason: str | None = None


class RemediationAction(BaseModel):
    """Action de remédiation décidée après consensus, exécutée par l'Executor."""

    action_id: str = Field(default_factory=_new_id)
    timestamp: float = Field(default_factory=_now)
    alert_id: str
    action_type: str                 # ex. block_ip, rate_limit, isolate_host, notify
    parameters: dict[str, str] = Field(default_factory=dict)
    executed: bool = False
    result: str | None = None


class InvestigationStep(BaseModel):
    """Une étape de la boucle agentique de l'Investigator (trace auditable).

    Chaque étape enregistre la pensée de l'agent, l'outil qu'il a décidé
    d'utiliser et l'observation obtenue — rendant le raisonnement
    autonome transparent et rejouable."""

    index: int
    thought: str                     # pourquoi l'agent fait cette étape
    tool: str                        # outil invoqué (query_ledger, correlate…)
    tool_input: dict = Field(default_factory=dict)
    observation: str                 # résultat de l'outil, résumé


class InvestigationReport(BaseModel):
    """Sortie de l'agent Investigator : conclusion d'une enquête autonome
    multi-étapes déclenchée par une attaque certifiée."""

    report_id: str = Field(default_factory=_new_id)
    timestamp: float = Field(default_factory=_now)
    alert_id: str
    investigator_id: str
    # Trace agentique complète (perçois → raisonne → agis → réfléchis)
    steps: list[InvestigationStep] = Field(default_factory=list)
    # Conclusions de l'enquête
    related_incidents: list[str] = Field(default_factory=list)
    campaign_suspected: bool = False           # attaque coordonnée ?
    severity: AlertSeverity = AlertSeverity.MEDIUM
    summary: str = ""                          # synthèse en langage naturel
    recommended_response: list[str] = Field(default_factory=list)
    provider: str = "rules-fallback"
    model: str = ""
    latency_ms: float = 0.0


class AgentStatus(BaseModel):
    """Réponse standard de l'endpoint /health de chaque agent."""

    agent_id: str
    agent_type: str
    uptime_s: float
    processed: int
    extra: dict[str, float | int | str] = Field(default_factory=dict)


# Résolution des références avant (Alert référence DeliberationResult défini après)
Alert.model_rebuild()
