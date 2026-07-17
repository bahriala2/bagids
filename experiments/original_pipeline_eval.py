"""
BAg-IDS — Ré-évaluation des détecteurs sous le PRÉTRAITEMENT D'ORIGINE
(reconstitué depuis le notebook Colab d'entraînement, AMCAI 2023 [56]).

Recette exacte du notebook :
  1. Dataset combiné nettoyé (data/cicids2017_complet/..._combined8element.csv)
  2. attacks = Label != BENIGN (390 222) ; benign sous-échantillonné à
     390 222 via sklearn.utils.resample(replace=True, random_state=123)
  3. concat([attacks, benign_down])  (ordre du notebook, cell 55)
  4. RobustScaler().fit(features) sur TOUT le jeu équilibré (avant split,
     comme dans le notebook — fuite assumée, protocole d'origine)
  5. LabelEncoder (ordre alphabétique = manifest class_names)
  6. train_test_split(test_size=0.2, random_state=1) puis
     val = 0.25 du train (random_state=1)  ->  60/20/20
  7. Évaluation de rnn1/cnn2/dnn1 sur le test d'origine + pipeline CWC
     complet (températures et poids re-fittés sur la validation d'origine,
     rejet τ).

Sortie : results/original_pipeline/results.json

Usage : python experiments/original_pipeline_eval.py
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
CSV = ROOT / "data" / "cicids2017_complet" / \
    "C__Data processing_ISD2017_Dataset_combined8element.csv"
MANIFEST = ROOT / "results" / "fusion_experiment" / "deployment_bundle" / \
    "manifest.json"
OUT = ROOT / "results" / "original_pipeline"
OUT.mkdir(parents=True, exist_ok=True)

from sklearn.metrics import precision_recall_fscore_support
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder, RobustScaler
from sklearn.utils import resample

from src.calibration import TemperatureScaler, expected_calibration_error
from src.fusion import linear_opinion_pool, precision_weights


def bin_metrics(pred, y, benign_idx):
    y_b, p_b = (y != benign_idx), (pred != benign_idx)
    tp = int(np.sum(p_b & y_b)); fp = int(np.sum(p_b & ~y_b))
    fn = int(np.sum(~p_b & y_b)); tn = int(np.sum(~p_b & ~y_b))
    prec = tp / max(tp + fp, 1); rec = tp / max(tp + fn, 1)
    return {"acc15": float(np.mean(pred == y)),
            "op_precision": prec, "op_recall": rec,
            "op_f1": 2 * prec * rec / max(prec + rec, 1e-12),
            "op_fpr": fp / max(fp + tn, 1)}


def prep():
    """Étape 1 (sans TensorFlow) : CSV -> splits .npy compacts."""
    t0 = time.time()
    print("1) Chargement du CSV combiné ...")
    df = pd.read_csv(CSV)
    print(f"   {df.shape[0]:,} lignes, {df.shape[1]} colonnes "
          f"({time.time()-t0:.0f} s)")

    # ------------------------------------------- 2-3. downsample benign
    benign = df[df["Label"] == "BENIGN"]
    attacks = df[df["Label"] != "BENIGN"]
    n_att = len(attacks)
    print(f"2) attaques = {n_att:,} ; benign {len(benign):,} -> resample "
          f"(replace=True, n={n_att:,}, rs=123)")
    benign_down = resample(benign, replace=True, n_samples=n_att,
                           random_state=123)
    dfd = pd.concat([attacks, benign_down])
    print(f"   jeu équilibré : {dfd.shape[0]:,} lignes")

    # ------------------------------------------- 4-5. scaler + labels
    labels_raw = dfd["Label"]
    features = dfd.loc[:, dfd.columns != "Label"].astype("float64")
    print("3) RobustScaler().fit sur tout le jeu équilibré (protocole "
          "d'origine) ...")
    scaler = RobustScaler().fit(features)
    X = scaler.transform(features).astype(np.float32)
    LE = LabelEncoder().fit(labels_raw)
    y = LE.transform(labels_raw)
    classes = list(LE.classes_)
    print("   classes:", classes)
    manifest = json.loads(MANIFEST.read_text("utf-8"))
    assert classes == manifest["class_names"], "ordre de classes différent !"
    benign_idx = classes.index("BENIGN")

    # ------------------------------------------- 6. split 60/20/20
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2,
                                              random_state=1)
    X_tr, X_va, y_tr, y_va = train_test_split(X_tr, y_tr, test_size=0.25,
                                              random_state=1)
    print(f"4) split: train {len(y_tr):,} / val {len(y_va):,} / "
          f"test {len(y_te):,}")
    np.save(OUT / "X_val.npy", X_va)
    np.save(OUT / "y_val.npy", y_va)
    np.save(OUT / "X_test.npy", X_te)
    np.save(OUT / "y_test.npy", y_te)
    (OUT / "classes.json").write_text(json.dumps(classes), "utf-8")
    print(f"   splits sauvegardés dans {OUT} ({time.time()-t0:.0f} s)")


def evaluate():
    """Étape 2 (TensorFlow, arrays légers uniquement)."""
    t0 = time.time()
    import tensorflow as tf  # noqa: F401
    from src.data_loader import reshape_for_model
    from src.model_loading import load_keras_model_compat
    print(f"TensorFlow {tf.__version__}")
    X_va = np.load(OUT / "X_val.npy"); y_va = np.load(OUT / "y_val.npy")
    X_te = np.load(OUT / "X_test.npy"); y_te = np.load(OUT / "y_test.npy")
    classes = json.loads((OUT / "classes.json").read_text("utf-8"))
    manifest = json.loads(MANIFEST.read_text("utf-8"))
    benign_idx = classes.index("BENIGN")

    # ------------------------------------------- 7. modèles
    R = {"protocol": "original (RobustScaler, benign downsampled 390222, "
                     "split 60/20/20 rs=1)", "classes": classes,
         "n_test": int(len(y_te)), "per_model": {}}
    probs_va, probs_te = {}, {}
    for name, path in manifest["models"].items():
        t1 = time.time()
        model = load_keras_model_compat(path)
        pv = model.predict(reshape_for_model(model, X_va),
                           batch_size=8192, verbose=0)
        pt = model.predict(reshape_for_model(model, X_te),
                           batch_size=8192, verbose=0)
        probs_va[name], probs_te[name] = pv, pt
        m = bin_metrics(pt.argmax(1), y_te, benign_idx)
        pr, rc, f1, _ = precision_recall_fscore_support(
            y_te, pt.argmax(1), average="weighted", zero_division=0)
        m.update({"f1_weighted": float(f1), "precision_weighted": float(pr)})
        R["per_model"][name] = m
        print(f"   {name.upper():4s} acc15={m['acc15']*100:6.2f} %  "
              f"F1w={f1*100:6.2f} %  opFPR={m['op_fpr']*100:5.2f} %  "
              f"({time.time()-t1:.0f} s)")
        del model

    # ------------------------------------------- 8. CWC complet
    print("5) Calibration + CWC + rejet (fit sur validation d'origine) ...")
    scalers = {n: TemperatureScaler().fit(probs_va[n], y_va)
               for n in probs_va}
    cal_va = {n: scalers[n].transform(probs_va[n]) for n in probs_va}
    cal_te = {n: scalers[n].transform(probs_te[n]) for n in probs_te}
    weights = precision_weights(cal_va, y_va)
    ens_te = linear_opinion_pool(cal_te, weights)
    R["temperatures"] = {n: float(s.temperature_) for n, s in scalers.items()}
    R["fusion_weights"] = {n: float(w) for n, w in weights.items()}
    R["ece_ensemble"] = float(expected_calibration_error(ens_te, y_te))

    m = bin_metrics(ens_te.argmax(1), y_te, benign_idx)
    R["ensemble_all"] = m
    print(f"   ENSEMBLE acc15={m['acc15']*100:.2f} %  "
          f"opF1={m['op_f1']:.4f}  opFPR={m['op_fpr']*100:.2f} %")
    sweep = {}
    conf = ens_te.max(1)
    for tau in (0.5, 0.6, 0.7, 0.75, 0.8, 0.9):
        msk = conf >= tau
        if msk.sum() == 0:
            sweep[str(tau)] = {"coverage": 0.0}
            continue
        mm = bin_metrics(ens_te.argmax(1)[msk], y_te[msk], benign_idx)
        mm["coverage"] = float(msk.mean())
        sweep[str(tau)] = mm
        print(f"   tau={tau:4.2f}  cov={mm['coverage']*100:5.1f} %  "
              f"acc15={mm['acc15']*100:6.2f} %  opFPR={mm['op_fpr']*100:5.2f} %")
    R["tau_sweep"] = sweep

    (OUT / "results.json").write_text(json.dumps(R, indent=1), "utf-8")
    print(f"\nOK -> {OUT/'results.json'}  ({time.time()-t0:.0f} s au total)")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=["prep", "eval", "all"], default="all")
    a = ap.parse_args()
    if a.stage in ("prep", "all"):
        prep()
    if a.stage in ("eval", "all"):
        evaluate()
