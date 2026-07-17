"""
BAg-IDS — Boucle réflexe du Sentinel : ensemble calibré + rejet tau.

Charge le bundle de déploiement produit par run_fusion_experiment.py
(--export-bundle) et rejoue exactement le même pipeline que l'étape 1.1 :
posteriors par modèle -> temperature scaling -> linear opinion pool
pondéré -> décision avec région de rejet.
"""

from __future__ import annotations

import json
import logging
import time
from pathlib import Path

import numpy as np

from src.calibration import TemperatureScaler
from src.data_loader import reshape_for_model
from src.fusion import decide_with_rejection, linear_opinion_pool
from src.model_loading import load_keras_model_compat

from agents.common.schemas import Detection, FlowFeatures, Verdict

logger = logging.getLogger("bag_ids.agents.sentinel.detector")


class EnsembleDetector:
    """Détecteur d'ensemble prêt pour l'inférence flux par flux (ou par
    micro-batch), fidèle à la configuration mesurée à l'étape 1.1."""

    def __init__(self, bundle_dir: str | Path):
        bundle_dir = Path(bundle_dir)
        manifest = json.loads(
            (bundle_dir / "manifest.json").read_text(encoding="utf-8"))

        self.class_names: list[str] = manifest["class_names"]
        self.benign_label: str = manifest["benign_label"]
        self.tau: float = float(manifest["tau"])
        self.weights: dict[str, float] = manifest["fusion_weights"]
        self.n_features: int = int(manifest["n_features"])

        self.temp_scalers: dict[str, TemperatureScaler] = {}
        for name, temp in manifest["temperatures"].items():
            scaler = TemperatureScaler()
            scaler.temperature_ = float(temp)
            self.temp_scalers[name] = scaler

        # Scaler d'entraînement (pour normaliser des flux BRUTS injectés
        # par l'opérateur lors des tests d'attaques).
        self.scaler = None
        scaler_path = bundle_dir / "scaler.joblib"
        if scaler_path.exists():
            import joblib
            self.scaler = joblib.load(scaler_path)

        self.models = {}
        for name, path in manifest["models"].items():
            logger.info("Chargement du modèle %s : %s", name.upper(), path)
            self.models[name] = load_keras_model_compat(path)
        logger.info(
            "Détecteur prêt : %d modèles, tau=%.2f, %d classes, %d features",
            len(self.models), self.tau, len(self.class_names), self.n_features)

    def scale_raw(self, raw_rows: list[list[float]]) -> np.ndarray:
        """Normalise des vecteurs de features BRUTS avec le scaler
        d'entraînement (même prétraitement que le jeu de test)."""
        X = np.asarray(raw_rows, dtype=np.float32)
        if X.shape[1] != self.n_features:
            raise ValueError(
                f"{X.shape[1]} features fournies, {self.n_features} attendues")
        # Robustesse : les flux réels peuvent contenir des inf/nan
        # (ex. Flow Bytes/s) que le prétraitement d'entraînement écartait.
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
        if self.scaler is not None:
            X = self.scaler.transform(X).astype(np.float32)
        X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
        return X

    def detect_batch(self, flows: list[FlowFeatures]) -> list[Detection]:
        """Décide pour un micro-batch de flux déjà normalisés (scaler
        appliqué en amont par la source, comme à l'entraînement)."""
        X = np.asarray([f.features for f in flows], dtype=np.float32)
        if X.shape[1] != self.n_features:
            raise ValueError(
                f"{X.shape[1]} features reçues, {self.n_features} attendues")

        t0 = time.perf_counter()
        calibrated = {}
        per_model_argmax = {}
        for name, model in self.models.items():
            probs = model.predict(reshape_for_model(model, X),
                                  batch_size=len(X), verbose=0)
            calibrated[name] = self.temp_scalers[name].transform(probs)
            per_model_argmax[name] = calibrated[name]
        fused = linear_opinion_pool(calibrated, self.weights)
        preds, confs, accepted = decide_with_rejection(fused, self.tau)
        dt_ms = 1000 * (time.perf_counter() - t0)
        per_flow_ms = dt_ms / len(flows)

        detections = []
        for i, flow in enumerate(flows):
            pred_label = self.class_names[int(preds[i])]
            if not accepted[i]:
                verdict = Verdict.REJECTED
            elif pred_label == self.benign_label:
                verdict = Verdict.BENIGN
            else:
                verdict = Verdict.ATTACK
            detections.append(Detection(
                flow_id=flow.flow_id,
                verdict=verdict,
                predicted_class=pred_label,
                confidence=float(confs[i]),
                tau=self.tau,
                class_probabilities={
                    cls: round(float(fused[i, j]), 6)
                    for j, cls in enumerate(self.class_names)
                },
                per_model={
                    name: {
                        "predicted_class": self.class_names[
                            int(probs[i].argmax())],
                        "confidence": round(float(probs[i].max()), 6),
                    }
                    for name, probs in per_model_argmax.items()
                },
                inference_ms=round(per_flow_ms, 4),
                true_label=flow.true_label,
            ))
        return detections
