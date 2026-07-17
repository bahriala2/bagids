"""Étape 2 de original_pipeline_eval : TensorFlow importé EN PREMIER
(la DLL native échoue si pandas/sklearn sont chargés avant sous forte
pression mémoire). Lit les splits .npy produits par --stage prep."""
import tensorflow as tf  # noqa: E402 — impérativement le premier import

import json
import sys
import time
from pathlib import Path

import numpy as np

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
OUT = ROOT / "results" / "original_pipeline"
MANIFEST = ROOT / "results" / "fusion_experiment" / "deployment_bundle" / \
    "manifest.json"

from sklearn.metrics import precision_recall_fscore_support  # noqa: E402

from src.calibration import TemperatureScaler, expected_calibration_error  # noqa: E402
from src.data_loader import reshape_for_model  # noqa: E402
from src.fusion import linear_opinion_pool, precision_weights  # noqa: E402
from src.model_loading import load_keras_model_compat  # noqa: E402


def bin_metrics(pred, y, benign_idx):
    y_b, p_b = (y != benign_idx), (pred != benign_idx)
    tp = int(np.sum(p_b & y_b)); fp = int(np.sum(p_b & ~y_b))
    fn = int(np.sum(~p_b & y_b)); tn = int(np.sum(~p_b & ~y_b))
    prec = tp / max(tp + fp, 1); rec = tp / max(tp + fn, 1)
    return {"acc15": float(np.mean(pred == y)),
            "op_precision": prec, "op_recall": rec,
            "op_f1": 2 * prec * rec / max(prec + rec, 1e-12),
            "op_fpr": fp / max(fp + tn, 1)}


def main():
    t0 = time.time()
    print(f"TensorFlow {tf.__version__}")
    X_va = np.load(OUT / "X_val.npy"); y_va = np.load(OUT / "y_val.npy")
    X_te = np.load(OUT / "X_test.npy"); y_te = np.load(OUT / "y_test.npy")
    classes = json.loads((OUT / "classes.json").read_text("utf-8"))
    manifest = json.loads(MANIFEST.read_text("utf-8"))
    benign_idx = classes.index("BENIGN")

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

    print("Calibration + CWC + rejet (fit sur validation d'origine) ...")
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

    np.save(OUT / "probs_test_rnn.npy", probs_te["rnn"].astype(np.float32))
    np.save(OUT / "probs_test_cnn.npy", probs_te["cnn"].astype(np.float32))
    np.save(OUT / "probs_test_dnn.npy", probs_te["dnn"].astype(np.float32))
    np.save(OUT / "probs_val_rnn.npy", probs_va["rnn"].astype(np.float32))
    np.save(OUT / "probs_val_cnn.npy", probs_va["cnn"].astype(np.float32))
    np.save(OUT / "probs_val_dnn.npy", probs_va["dnn"].astype(np.float32))
    (OUT / "results.json").write_text(json.dumps(R, indent=1), "utf-8")
    print(f"\nOK -> {OUT/'results.json'}  ({time.time()-t0:.0f} s)")


if __name__ == "__main__":
    main()
