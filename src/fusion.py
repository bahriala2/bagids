"""
BAg-IDS — Conscious Weighted Consensus.

Implémente les équations (1)-(3) du manuscrit :
  (1) P̃(c|x) = Σ_m w_m · P(c|x, M_m)          (linear opinion pool)
  (2) w_m = prec_m / Σ_k prec_k                (poids ∝ précision historique)
  (3) ĉ = argmax_c P̃(c|x), conf(x) = max_c P̃  (règle de décision)
avec région de rejet : seules les décisions dont conf(x) >= tau sont
certifiées (transmises à la couche 3 dans l'architecture complète).

Le schéma de mise à jour Dirichlet en mini-batch (fenêtre W) est fourni
pour le pipeline temps-réel (étape 1.2) ; ici, en évaluation hors-ligne,
les poids sont estimés une fois sur le jeu de validation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np
from sklearn.metrics import precision_score

logger = logging.getLogger("bag_ids.fusion")


def precision_weights(
    probs_per_model: dict[str, np.ndarray], y_val: np.ndarray
) -> dict[str, float]:
    """Éq. (2) : poids normalisés proportionnels à la précision (weighted)
    de chaque modèle sur le jeu de validation."""
    precisions = {}
    for name, probs in probs_per_model.items():
        pred = probs.argmax(axis=1)
        prec = precision_score(y_val, pred, average="weighted", zero_division=0)
        precisions[name] = float(prec)
        logger.info("Précision (val) %s = %.4f", name, prec)
    total = sum(precisions.values())
    weights = {k: v / total for k, v in precisions.items()}
    logger.info("Poids de fusion : %s",
                {k: round(v, 4) for k, v in weights.items()})
    return weights


def linear_opinion_pool(
    probs_per_model: dict[str, np.ndarray], weights: dict[str, float]
) -> np.ndarray:
    """Éq. (1) : fusion pondérée des posteriors calibrés."""
    fused = None
    for name, probs in probs_per_model.items():
        contrib = weights[name] * probs
        fused = contrib if fused is None else fused + contrib
    # Renormalisation de sécurité (erreurs d'arrondi)
    fused = fused / fused.sum(axis=1, keepdims=True)
    return fused


def decide_with_rejection(fused: np.ndarray, tau: float):
    """Éq. (3) + région de rejet.

    Retourne (predictions, confidences, accepted_mask).
    Les décisions avec conf < tau sont rejetées : dans l'architecture
    complète, elles ne sont ni certifiées ni transmises à la remédiation.
    """
    preds = fused.argmax(axis=1)
    confs = fused.max(axis=1)
    accepted = confs >= tau
    return preds, confs, accepted


@dataclass
class DirichletWeightUpdater:
    """Mise à jour bayésienne des poids en mini-batch (section
    « Practical update scheme » du manuscrit).

    Prior uniforme alpha_m = 1 ; à la fin de chaque fenêtre de W flux,
    alpha_m += nb de détections correctement certifiées attribuées à M_m,
    puis w_m = alpha_m / Σ_k alpha_k. Un facteur de décroissance
    down-weight les preuves anciennes (suivi du concept drift).
    """

    model_names: list[str]
    window_size: int = 1000
    decay: float = 0.99
    alphas: dict[str, float] = field(default_factory=dict)
    _buffer: dict[str, int] = field(default_factory=dict)
    _count: int = 0

    def __post_init__(self):
        for m in self.model_names:
            self.alphas.setdefault(m, 1.0)
            self._buffer.setdefault(m, 0)

    def record(self, correct_by_model: dict[str, bool]) -> dict[str, float] | None:
        """Enregistre un flux certifié ; retourne les nouveaux poids
        à la fin de la fenêtre, sinon None."""
        self._count += 1
        for m, ok in correct_by_model.items():
            if ok:
                self._buffer[m] += 1
        if self._count >= self.window_size:
            for m in self.model_names:
                self.alphas[m] = self.decay * self.alphas[m] + self._buffer[m]
                self._buffer[m] = 0
            self._count = 0
            return self.weights()
        return None

    def weights(self) -> dict[str, float]:
        total = sum(self.alphas.values())
        return {m: a / total for m, a in self.alphas.items()}
