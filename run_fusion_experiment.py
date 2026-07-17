"""
BAg-IDS — Étape 1.1 : Expérience de fusion calibrée (MESURE RÉELLE).

Ce script transforme la ligne « projetée » du Tableau II du manuscrit
en résultats mesurés :

  1. Charge CICIDS2017 prétraité et reproduit le split 70/15/15.
  2. Charge les modèles RNN, CNN, DNN entraînés (.h5/.keras).
  3. Calibre chaque modèle par temperature scaling (fit sur validation).
  4. Estime les poids Dirichlet w_m ∝ précision sur validation.
  5. Fusionne par linear opinion pool et applique la région de rejet τ.
  6. Mesure sur le jeu de TEST : accuracy, précision, rappel, F1, FPR,
     ECE avant/après, et balayage de τ (ablation).
  7. Exporte : results.json, table_II.tex, figures PNG 300 dpi.

Usage :
    python run_fusion_experiment.py --config configs/config.yaml
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import time
from pathlib import Path

import numpy as np
import yaml

# Consoles Windows (cp1252) ne savent pas encoder τ, →, etc. : on force
# stdout/stderr en UTF-8 pour que logs et print() ne plantent jamais.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

from src.calibration import TemperatureScaler, expected_calibration_error
from src.data_loader import load_dataset, reshape_for_model
from src.fusion import decide_with_rejection, linear_opinion_pool, precision_weights
from src.model_loading import load_keras_model_compat
from src.metrics import (
    export_latex_table,
    full_report,
    plot_confusion_matrix,
    plot_model_comparison,
    plot_reliability,
    plot_tau_sweep,
    save_json,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)-20s | %(levelname)-7s | %(message)s",
)
logger = logging.getLogger("bag_ids.experiment")


def export_deployment_bundle(out_dir, cfg, data, scalers, weights, tau,
                             class_names):
    """Sauvegarde les artefacts nécessaires aux agents (étape 1.2) :
    scaler, températures, poids de fusion, tau, classes, chemins des
    modèles, et le split test (déjà normalisé) pour le mode replay."""
    import joblib

    bundle_dir = out_dir / "deployment_bundle"
    bundle_dir.mkdir(parents=True, exist_ok=True)

    joblib.dump(data["scaler"], bundle_dir / "scaler.joblib")
    np.save(bundle_dir / "X_test.npy", data["X_test"])
    np.save(bundle_dir / "y_test.npy", data["y_test"])

    manifest = {
        "models": {name: str(Path(path).resolve())
                   for name, path in cfg["models"].items()},
        "temperatures": {name: s.temperature_ for name, s in scalers.items()},
        "fusion_weights": weights,
        "tau": tau,
        "class_names": class_names,
        "benign_label": cfg["data"]["benign_label"],
        "n_features": int(data["X_test"].shape[1]),
    }
    (bundle_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    logger.info("Bundle de déploiement exporté : %s", bundle_dir)


def main():
    parser = argparse.ArgumentParser(description="BAg-IDS fusion experiment")
    parser.add_argument("--config", default="configs/config.yaml")
    parser.add_argument("--export-bundle", action="store_true",
                        help="Exporte scaler/températures/poids/X_test pour "
                             "les agents (étape 1.2)")
    args = parser.parse_args()

    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    out_dir = Path(cfg["output_dir"])
    (out_dir / "figures").mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------- données
    data = load_dataset(cfg)
    class_names = data["class_names"]
    benign_idx = class_names.index(cfg["data"]["benign_label"])
    y_val, y_test = data["y_val"], data["y_test"]

    # ------------------------------------------------------------- modèles
    # Import tardif de TensorFlow (démarrage plus rapide en cas d'erreur config)
    import tensorflow as tf  # noqa: E402

    logger.info("TensorFlow %s — GPU : %s", tf.__version__,
                tf.config.list_physical_devices("GPU") or "aucun (CPU)")

    batch = cfg["inference"]["batch_size"]
    models_cfg = cfg["models"]
    probs_val_raw, probs_test_raw = {}, {}
    inference_times = {}

    for name, path in models_cfg.items():
        logger.info("Chargement du modèle %s : %s", name.upper(), path)
        model = load_keras_model_compat(path)
        Xv = reshape_for_model(model, data["X_val"])
        Xt = reshape_for_model(model, data["X_test"])

        t0 = time.perf_counter()
        probs_val_raw[name] = model.predict(Xv, batch_size=batch, verbose=0)
        probs_test_raw[name] = model.predict(Xt, batch_size=batch, verbose=0)
        dt = time.perf_counter() - t0
        inference_times[name] = {
            "total_s": round(dt, 2),
            "per_flow_ms": round(1000 * dt / (len(Xv) + len(Xt)), 4),
        }
        logger.info("%s : inférence en %.1fs (%.4f ms/flux)",
                    name.upper(), dt, inference_times[name]["per_flow_ms"])

    # ------------------------------------------------------- calibration
    calibrated_val, calibrated_test = {}, {}
    calibration_report = {}
    temp_scalers = {}
    for name in models_cfg:
        scaler = TemperatureScaler().fit(probs_val_raw[name], y_val)
        temp_scalers[name] = scaler
        calibrated_val[name] = scaler.transform(probs_val_raw[name])
        calibrated_test[name] = scaler.transform(probs_test_raw[name])
        calibration_report[name] = {
            "temperature": scaler.temperature_,
            "ece_before": expected_calibration_error(
                probs_test_raw[name], y_test, cfg["fusion"]["ece_bins"]),
            "ece_after": expected_calibration_error(
                calibrated_test[name], y_test, cfg["fusion"]["ece_bins"]),
        }
        logger.info("%s : T=%.3f, ECE %.4f -> %.4f", name.upper(),
                    scaler.temperature_,
                    calibration_report[name]["ece_before"],
                    calibration_report[name]["ece_after"])

    # ------------------------------------------------- poids et fusion
    weights = precision_weights(calibrated_val, y_val)
    fused_test = linear_opinion_pool(calibrated_test, weights)
    fused_test_raw = linear_opinion_pool(probs_test_raw, weights)

    tau = cfg["fusion"]["tau"]
    preds, confs, accepted = decide_with_rejection(fused_test, tau)

    # ------------------------------------------------------- métriques
    per_model = {
        name: full_report(y_test, calibrated_test[name].argmax(axis=1), benign_idx)
        for name in models_cfg
    }
    ensemble_all = full_report(y_test, preds, benign_idx)
    ensemble_accepted = full_report(y_test[accepted], preds[accepted], benign_idx)
    ece_ensemble = {
        "before_calibration": expected_calibration_error(
            fused_test_raw, y_test, cfg["fusion"]["ece_bins"]),
        "after_calibration": expected_calibration_error(
            fused_test, y_test, cfg["fusion"]["ece_bins"]),
    }

    # Balayage de tau (ablation 3 du plan expérimental)
    lo, hi, step = cfg["fusion"]["tau_sweep"]
    sweep = []
    for t in np.arange(lo, hi + 1e-9, step):
        _, _, acc_mask = decide_with_rejection(fused_test, float(t))
        if acc_mask.sum() == 0:
            continue
        r = full_report(y_test[acc_mask], preds[acc_mask], benign_idx)
        sweep.append({
            "tau": round(float(t), 2),
            "coverage": float(acc_mask.mean()),
            "accuracy_accepted": r["accuracy"],
            "f1_accepted": r["f1_weighted"],
            "fpr_accepted": r["fpr_operational"],
        })

    # ------------------------------------------------------------ exports
    results = {
        "dataset": {
            "n_val": int(len(y_val)),
            "n_test": int(len(y_test)),
            "n_classes": len(class_names),
            "classes": class_names,
        },
        "calibration": calibration_report,
        "fusion_weights": weights,
        "tau": tau,
        "coverage_at_tau": float(accepted.mean()),
        "per_model_test": per_model,
        "ensemble_all_decisions": ensemble_all,
        "ensemble_accepted_only": ensemble_accepted,
        "ece_ensemble": ece_ensemble,
        "tau_sweep": sweep,
        "inference_times": inference_times,
    }
    save_json(results, out_dir / "results.json")
    export_latex_table(per_model, ensemble_all, out_dir / "table_II.tex")

    if args.export_bundle:
        export_deployment_bundle(out_dir, cfg, data, temp_scalers, weights,
                                 tau, class_names)

    figs = out_dir / "figures"
    plot_confusion_matrix(y_test, preds, class_names,
                          figs / "confusion_matrix_ensemble.png")
    plot_reliability(fused_test_raw, fused_test, y_test,
                     cfg["fusion"]["ece_bins"], figs / "reliability_diagram.png")
    plot_tau_sweep(sweep, tau, figs / "tau_sweep.png")
    plot_model_comparison(per_model, ensemble_all,
                          figs / "model_comparison.png")

    # ------------------------------------------------------------ résumé
    print("\n" + "=" * 62)
    print("  BAg-IDS — RÉSULTATS MESURÉS DE L'ENSEMBLE (jeu de test)")
    print("=" * 62)
    for name, r in per_model.items():
        print(f"  {name.upper():<6} acc={r['accuracy']*100:6.2f}%  "
              f"F1={r['f1_weighted']*100:6.2f}%  "
              f"FPR={r['fpr_operational']*100:.3f}%")
    print("-" * 62)
    r = ensemble_all
    print(f"  ENSEMBLE (toutes décisions)  acc={r['accuracy']*100:6.2f}%  "
          f"F1={r['f1_weighted']*100:6.2f}%  FPR={r['fpr_operational']*100:.3f}%")
    r = ensemble_accepted
    print(f"  ENSEMBLE (certifiées, τ={tau})  acc={r['accuracy']*100:6.2f}%  "
          f"F1={r['f1_weighted']*100:6.2f}%  "
          f"couverture={results['coverage_at_tau']*100:.1f}%")
    print(f"  ECE ensemble : {ece_ensemble['before_calibration']:.4f} -> "
          f"{ece_ensemble['after_calibration']:.4f}")
    print("=" * 62)
    print(f"\nSorties : {out_dir.resolve()}")
    print("  - results.json (toutes les métriques)")
    print("  - table_II.tex (Tableau II mesuré, prêt pour le papier)")
    print("  - figures/*.png (300 dpi, prêtes pour le papier)")


if __name__ == "__main__":
    main()
