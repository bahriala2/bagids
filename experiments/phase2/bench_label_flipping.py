"""
BAg-IDS — Phase 2.3 : robustesse au label-flipping (data poisoning).

Modèle de menace : un adversaire empoisonne l'un des détecteurs de
l'ensemble (RNN, CNN ou DNN) en inversant une fraction p de ses
décisions — typiquement pour faire passer des attaques pour du trafic
bénin (évasion). On mesure si le mécanisme de fusion pondérée par la
précision (Conscious Weighted Consensus, Éq. 2 du manuscrit) neutralise
ce modèle corrompu.

Trois courbes comparées, en fonction de la fraction empoisonnée p :

  1. modèle empoisonné seul           -> s'effondre (référence attaque) ;
  2. ensemble à poids STATIQUES        -> fusion sans adaptation (poids
     appris sur données propres) : robustesse « passive » ;
  3. ensemble à poids ADAPTATIFS       -> poids recalculés sur validation
     (la précision du modèle corrompu chute => son poids chute) :
     c'est la défense revendiquée par BAg-IDS.

L'empoisonnement est appliqué sur validation ET test (un modèle
réellement corrompu l'est aux deux) : ainsi les poids adaptatifs
« voient » la baisse de précision et réagissent, comme en production.

Usage :
    python -m experiments.phase2.bench_label_flipping \
        --config configs/config.yaml --target cnn \
        --out results/phase2/label_flipping.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import yaml

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

from src.calibration import TemperatureScaler
from src.data_loader import load_dataset, reshape_for_model
from src.fusion import linear_opinion_pool, precision_weights
from src.metrics import full_report
from src.model_loading import load_keras_model_compat

RNG_SEED = 42


def poison_predictions(probs, y_true, benign_idx, n_classes, fraction, rng):
    """Inverse la décision du modèle pour une fraction des flux :
    attaque -> bénin (évasion) et bénin -> attaque (bruit). Renvoie une
    copie des probabilités où les flux empoisonnés sont forcés (one-hot)
    sur la classe inversée."""
    poisoned = probs.copy()
    n = len(probs)
    idx = rng.choice(n, size=int(fraction * n), replace=False)
    preds = probs.argmax(axis=1)
    for i in idx:
        if preds[i] == benign_idx:
            # bénin -> une classe d'attaque aléatoire
            attack = rng.integers(0, n_classes)
            while attack == benign_idx:
                attack = rng.integers(0, n_classes)
            target = attack
        else:
            # attaque -> bénin (le cas dangereux : évasion)
            target = benign_idx
        poisoned[i] = 0.0
        poisoned[i, target] = 1.0
    return poisoned


def main():
    parser = argparse.ArgumentParser(description="BAg-IDS phase 2.3 label-flip")
    parser.add_argument("--config", default="configs/config.yaml")
    parser.add_argument("--target", default="cnn",
                        help="modèle empoisonné (rnn/cnn/dnn)")
    parser.add_argument("--fractions", default="0,0.1,0.2,0.3,0.4,0.5,0.7,0.9,1.0")
    parser.add_argument("--out", default="results/phase2/label_flipping.json")
    args = parser.parse_args()

    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    Path("results/phase2").mkdir(parents=True, exist_ok=True)
    fractions = [float(x) for x in args.fractions.split(",")]

    print("Chargement des données et des modèles...")
    data = load_dataset(cfg)
    class_names = data["class_names"]
    benign_idx = class_names.index(cfg["data"]["benign_label"])
    n_classes = len(class_names)
    y_val, y_test = data["y_val"], data["y_test"]

    import tensorflow as tf  # noqa: F401
    batch = cfg["inference"]["batch_size"]
    probs_val, probs_test = {}, {}
    for name, path in cfg["models"].items():
        model = load_keras_model_compat(path)
        pv = model.predict(reshape_for_model(model, data["X_val"]),
                           batch_size=batch, verbose=0)
        pt = model.predict(reshape_for_model(model, data["X_test"]),
                           batch_size=batch, verbose=0)
        scaler = TemperatureScaler().fit(pv, y_val)
        probs_val[name] = scaler.transform(pv)
        probs_test[name] = scaler.transform(pt)
        print(f"  {name} chargé et calibré")

    target = args.target
    if target not in probs_val:
        raise SystemExit(f"cible '{target}' inconnue : {list(probs_val)}")

    # Poids de référence sur données propres (pour l'ensemble statique)
    clean_weights = precision_weights(probs_val, y_val)
    rng = np.random.default_rng(RNG_SEED)

    rows = []
    for frac in fractions:
        pv_pois = dict(probs_val)
        pt_pois = dict(probs_test)
        pv_pois[target] = poison_predictions(
            probs_val[target], y_val, benign_idx, n_classes, frac, rng)
        pt_pois[target] = poison_predictions(
            probs_test[target], y_test, benign_idx, n_classes, frac, rng)

        # 1. modèle empoisonné seul
        r_solo = full_report(y_test, pt_pois[target].argmax(axis=1), benign_idx)

        # 2. ensemble à poids statiques (pas d'adaptation)
        fused_static = linear_opinion_pool(pt_pois, clean_weights)
        r_static = full_report(y_test, fused_static.argmax(axis=1), benign_idx)

        # 3. ensemble à poids adaptatifs (recalculés sur val empoisonnée)
        adapt_weights = precision_weights(pv_pois, y_val)
        fused_adapt = linear_opinion_pool(pt_pois, adapt_weights)
        r_adapt = full_report(y_test, fused_adapt.argmax(axis=1), benign_idx)

        rows.append({
            "fraction": frac,
            "poisoned_weight_static": round(clean_weights[target], 4),
            "poisoned_weight_adaptive": round(adapt_weights[target], 4),
            "solo_poisoned": r_solo,
            "ensemble_static": r_static,
            "ensemble_adaptive": r_adapt,
        })
        print(f"  p={frac:.2f} | seul acc={r_solo['accuracy']*100:5.1f}% "
              f"FPR={r_solo['fpr_operational']*100:5.1f}% | "
              f"ens.adapt acc={r_adapt['accuracy']*100:5.1f}% "
              f"FPR={r_adapt['fpr_operational']*100:5.1f}% "
              f"(poids {target}: {clean_weights[target]:.3f}->"
              f"{adapt_weights[target]:.3f})")

    result = {
        "target_model": target,
        "n_classes": n_classes,
        "benign_label": cfg["data"]["benign_label"],
        "clean_weights": clean_weights,
        "rows": rows,
    }
    Path(args.out).write_text(json.dumps(result, indent=2, ensure_ascii=False),
                              encoding="utf-8")
    print(f"\nRésultats : {args.out}")


if __name__ == "__main__":
    main()
