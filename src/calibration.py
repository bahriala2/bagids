"""
BAg-IDS — Calibration de confiance par temperature scaling.

Implémente la méthode de Guo et al. (ICML 2017, arXiv:1706.04599) :
les logits z de chaque modèle sont transformés par softmax(z / T),
T étant ajusté par minimisation de la log-vraisemblance négative (NLL)
sur le jeu de validation. La qualité de calibration est mesurée par
l'Expected Calibration Error (ECE).

Correspond à la sous-section « Confidence calibration » du manuscrit.
"""

from __future__ import annotations

import logging

import numpy as np
from scipy.optimize import minimize_scalar
from scipy.special import softmax

logger = logging.getLogger("bag_ids.calibration")

_EPS = 1e-12


def probs_to_logits(probs: np.ndarray) -> np.ndarray:
    """Récupère des logits (à une constante additive près) depuis des
    probabilités softmax : log(p). Suffisant pour le temperature scaling,
    invariant par translation des logits."""
    return np.log(np.clip(probs, _EPS, 1.0))


class TemperatureScaler:
    """Calibrateur à un seul paramètre T > 0 par modèle."""

    def __init__(self):
        self.temperature_: float = 1.0

    def fit(self, probs_val: np.ndarray, y_val: np.ndarray) -> "TemperatureScaler":
        logits = probs_to_logits(probs_val)
        n = len(y_val)

        def nll(t: float) -> float:
            p = softmax(logits / t, axis=1)
            return -np.mean(np.log(np.clip(p[np.arange(n), y_val], _EPS, 1.0)))

        res = minimize_scalar(nll, bounds=(0.05, 10.0), method="bounded")
        self.temperature_ = float(res.x)
        logger.info("Température optimale T = %.4f (NLL = %.4f)",
                    self.temperature_, res.fun)
        return self

    def transform(self, probs: np.ndarray) -> np.ndarray:
        logits = probs_to_logits(probs)
        return softmax(logits / self.temperature_, axis=1)


def expected_calibration_error(
    probs: np.ndarray, y_true: np.ndarray, n_bins: int = 15
) -> float:
    """ECE standard à bins de confiance égaux (Guo et al., 2017)."""
    conf = probs.max(axis=1)
    pred = probs.argmax(axis=1)
    correct = (pred == y_true).astype(float)

    bins = np.linspace(0.0, 1.0, n_bins + 1)
    ece = 0.0
    n = len(y_true)
    for lo, hi in zip(bins[:-1], bins[1:]):
        mask = (conf > lo) & (conf <= hi)
        if mask.sum() == 0:
            continue
        avg_conf = conf[mask].mean()
        avg_acc = correct[mask].mean()
        ece += (mask.sum() / n) * abs(avg_acc - avg_conf)
    return float(ece)


def reliability_curve(
    probs: np.ndarray, y_true: np.ndarray, n_bins: int = 15
):
    """Points (confiance moyenne, accuracy) par bin, pour le reliability diagram."""
    conf = probs.max(axis=1)
    pred = probs.argmax(axis=1)
    correct = (pred == y_true).astype(float)

    bins = np.linspace(0.0, 1.0, n_bins + 1)
    xs, ys, weights = [], [], []
    for lo, hi in zip(bins[:-1], bins[1:]):
        mask = (conf > lo) & (conf <= hi)
        if mask.sum() == 0:
            continue
        xs.append(conf[mask].mean())
        ys.append(correct[mask].mean())
        weights.append(int(mask.sum()))
    return np.array(xs), np.array(ys), np.array(weights)
