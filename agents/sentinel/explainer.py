"""
BAg-IDS — Explicabilité (XAI) des alertes en attente d'approbation humaine.

Attribution de features par KernelSHAP sur l'ensemble calibré complet
(la fonction expliquée est exactement la décision : posteriors fusionnés
après temperature scaling et pool pondéré). KernelSHAP est agnostique au
modèle : il n'appelle que `EnsembleDetector.fused_probs`, ce qui le rend
robuste aux évolutions Keras/TF, au prix d'un coût de quelques secondes
par flux. Ce coût est volontairement payé HORS chemin critique : seules
les remédiations en file d'approbation humaine sont expliquées (mêmes
asymétries de coût que la délibération LLM).

Le résultat est fidèle (les contributions viennent du modèle, pas d'un
récit génératif) ; la couche narrative LLM en aval ne fait que REFORMULER
ces attributions, jamais en inventer.
"""

from __future__ import annotations

import json
import logging
import threading
import time
from pathlib import Path

import numpy as np

logger = logging.getLogger("bag_ids.agents.sentinel.explainer")


class FlowExplainer:
    """Attributions SHAP pour un flux classé par l'ensemble calibré.

    Paramètres (section `explain` de la config sentinel, tous optionnels) :
      background_size : nb de flux de référence tirés du jeu de test (déf. 20)
      nsamples        : budget d'évaluations KernelSHAP (déf. 1000)
      top_k           : nb de features retournées (déf. 8)
    """

    def __init__(self, detector, bundle_dir: str | Path, cfg: dict | None = None):
        cfg = cfg or {}
        self.detector = detector
        self.bundle_dir = Path(bundle_dir)
        self.background_size = int(cfg.get("background_size", 20))
        self.nsamples = int(cfg.get("nsamples", 1000))
        self.top_k = int(cfg.get("top_k", 8))
        # Une seule explication à la fois : KernelSHAP est gourmand (RAM/CPU)
        # et la file d'approbation n'a jamais besoin de parallélisme.
        self._lock = threading.Lock()
        self._background: np.ndarray | None = None
        self.feature_names = self._load_feature_names()

    # ------------------------------------------------------------ noms
    def _load_feature_names(self) -> list[str]:
        path = self.bundle_dir / "feature_names.json"
        if path.exists():
            names = json.loads(path.read_text(encoding="utf-8"))
            if len(names) == self.detector.n_features:
                return names
            logger.warning(
                "feature_names.json : %d noms pour %d features — ignoré",
                len(names), self.detector.n_features)
        return [f"feature_{i}" for i in range(self.detector.n_features)]

    # ------------------------------------------------------ background
    def _get_background(self) -> np.ndarray:
        """Échantillon de référence (distribution 'attendue' des flux),
        tiré du jeu de test du bundle avec une seed fixe (reproductible)."""
        if self._background is None:
            x_path = self.bundle_dir / "X_test.npy"
            if x_path.exists():
                X = np.load(x_path, mmap_mode="r")
                rng = np.random.default_rng(42)
                idx = rng.choice(len(X), size=min(self.background_size, len(X)),
                                 replace=False)
                self._background = np.asarray(X[np.sort(idx)], dtype=np.float32)
            else:
                logger.warning("X_test.npy absent du bundle : background nul "
                               "(les attributions restent valides mais la "
                               "référence est moins représentative)")
                self._background = np.zeros(
                    (1, self.detector.n_features), dtype=np.float32)
        return self._background

    # ---------------------------------------------------------- explain
    def explain(self, features: list[float]) -> dict:
        """Attributions SHAP pour UN flux normalisé.

        Retourne {predicted_class, confidence, base_value, top_features,
        latency_ms} où top_features = [{name, value, shap, direction}],
        trié par |contribution| décroissante, pour la classe prédite.
        """
        import shap  # import différé : ~2 s, seulement si XAI utilisée

        x = np.asarray(features, dtype=np.float32).reshape(1, -1)
        if x.shape[1] != self.detector.n_features:
            raise ValueError(
                f"{x.shape[1]} features reçues, "
                f"{self.detector.n_features} attendues")

        with self._lock:
            t0 = time.perf_counter()
            fused, _ = self.detector.fused_probs(x)
            class_idx = int(fused[0].argmax())
            pred_label = self.detector.class_names[class_idx]
            confidence = float(fused[0, class_idx])

            def f(batch: np.ndarray) -> np.ndarray:
                probs, _ = self.detector.fused_probs(
                    np.asarray(batch, dtype=np.float32))
                return probs[:, class_idx]

            background = self._get_background()
            explainer = shap.KernelExplainer(f, background)
            shap_values = explainer.shap_values(
                x, nsamples=self.nsamples, silent=True)
            values = np.asarray(shap_values).reshape(-1)
            base_value = float(np.asarray(explainer.expected_value).reshape(-1)[0])
            latency_ms = 1000 * (time.perf_counter() - t0)

        order = np.argsort(-np.abs(values))[: self.top_k]
        top = [{
            "name": self.feature_names[i],
            "value": round(float(x[0, i]), 4),          # valeur normalisée
            "shap": round(float(values[i]), 5),
            "direction": "supports" if values[i] > 0 else "opposes",
        } for i in order]

        logger.info("Explication SHAP : %s (conf %.3f) en %.1f s — top: %s",
                    pred_label, confidence, latency_ms / 1000,
                    ", ".join(t["name"] for t in top[:3]))
        return {
            "predicted_class": pred_label,
            "confidence": round(confidence, 4),
            "base_value": round(base_value, 4),
            "top_features": top,
            "nsamples": self.nsamples,
            "background_size": len(self._get_background()),
            "latency_ms": round(latency_ms, 1),
        }
