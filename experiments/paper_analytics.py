"""
BAg-IDS — Analyse par sous-système pour le papier Q1 (courbes RÉELLES).

Produit, à partir d'une inférence réelle des 3 détecteurs sur le split de
test CICIDS2017 (363 860 flux, 15 classes) :

  A. Par modèle (RNN, CNN, DNN) et pour l'ensemble CWC :
     - Courbes ROC et Précision-Rappel opérationnelles (BENIGN vs ATTACK)
     - Diagrammes de fiabilité avant/après calibration (ECE)
     - Matrices de confusion 15 classes (normalisées)
     - F1 par classe
  B. Chaîne d'ablation inter-sous-systèmes :
     - fusion CWC vs meilleur modèle seul vs moyenne uniforme vs vote
       majoritaire, avec et sans calibration
     - courbe risque-couverture de la région de rejet τ
     - charge transmise à la couche délibérative (L2) en fonction de τ
  C. Analyse statistique :
     - IC bootstrap à 95 % (1000 rééchantillonnages) sur F1/accuracy/FPR
     - tests de McNemar (χ², correction de continuité) entre modèles
     - table précision/rappel/F1/support par classe (ensemble)

Sorties : results/paper_analytics/{analytics.json, figures/*.png (300 dpi)}
Les probabilités brutes sont mises en cache (.npy) : relance rapide.

Usage :  python experiments/paper_analytics.py
"""
from __future__ import annotations

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

BUNDLE = ROOT / "results" / "fusion_experiment" / "deployment_bundle"
OUT = ROOT / "results" / "paper_analytics"
FIG = OUT / "figures"
FIG.mkdir(parents=True, exist_ok=True)

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

plt.rcParams.update({
    "figure.dpi": 100, "savefig.dpi": 300, "font.size": 9,
    "axes.grid": True, "grid.alpha": 0.3, "axes.spines.top": False,
    "axes.spines.right": False, "font.family": "DejaVu Sans",
})

COLORS = {"rnn": "#1f77b4", "cnn": "#d62728", "dnn": "#2ca02c",
          "ensemble": "#7d4fd3"}
LABELS = {"rnn": "RNN (LSTM)", "cnn": "CNN", "dnn": "DNN",
          "ensemble": "CWC ensemble"}

from scipy.special import softmax
from scipy.stats import chi2 as chi2_dist
from sklearn.metrics import (auc, average_precision_score,
                             precision_recall_curve, precision_recall_fscore_support,
                             roc_curve)

from src.calibration import expected_calibration_error, probs_to_logits


# --------------------------------------------------------------- inference
def get_probs():
    """Inférence réelle (ou cache) : probabilités brutes par modèle."""
    manifest = json.loads((BUNDLE / "manifest.json").read_text(encoding="utf-8"))
    X = np.load(BUNDLE / "X_test.npy")
    y = np.load(BUNDLE / "y_test.npy")
    probs_raw = {}
    todo = {n: p for n, p in manifest["models"].items()
            if not (OUT / f"probs_raw_{n}.npy").exists()}
    if todo:
        import tensorflow as tf  # import tardif
        from src.data_loader import reshape_for_model
        from src.model_loading import load_keras_model_compat
        print(f"TensorFlow {tf.__version__} — inférence sur {len(X):,} flux")
        for name, path in todo.items():
            t0 = time.time()
            model = load_keras_model_compat(path)
            Xr = reshape_for_model(model, X)
            p = model.predict(Xr, batch_size=8192, verbose=0)
            np.save(OUT / f"probs_raw_{name}.npy", p.astype(np.float32))
            print(f"  {name.upper():4s} : {time.time()-t0:6.1f} s "
                  f"({len(X)/(time.time()-t0):,.0f} flux/s)")
            del model, Xr
    for name in manifest["models"]:
        probs_raw[name] = np.load(OUT / f"probs_raw_{name}.npy")
    return manifest, X, y, probs_raw


def calibrate(probs: np.ndarray, T: float) -> np.ndarray:
    return softmax(probs_to_logits(probs) / T, axis=1)


# --------------------------------------------------------------- metrics
def binary_ops(probs, y, benign_idx):
    """Score et labels opérationnels ATTACK=1 / BENIGN=0."""
    score = 1.0 - probs[:, benign_idx]
    y_bin = (y != benign_idx).astype(int)
    pred_bin = (probs.argmax(1) != benign_idx).astype(int)
    return score, y_bin, pred_bin


def bin_metrics(y_bin, pred_bin):
    tp = int(np.sum((pred_bin == 1) & (y_bin == 1)))
    fp = int(np.sum((pred_bin == 1) & (y_bin == 0)))
    fn = int(np.sum((pred_bin == 0) & (y_bin == 1)))
    tn = int(np.sum((pred_bin == 0) & (y_bin == 0)))
    prec = tp / max(tp + fp, 1)
    rec = tp / max(tp + fn, 1)
    f1 = 2 * prec * rec / max(prec + rec, 1e-12)
    return {"precision": prec, "recall": rec, "f1": f1,
            "fpr": fp / max(fp + tn, 1),
            "accuracy": (tp + tn) / len(y_bin)}


def bootstrap_ci(y_bin, pred_bin, n_boot=1000, seed=42):
    rng = np.random.default_rng(seed)
    n = len(y_bin)
    stats = {"f1": [], "fpr": [], "accuracy": []}
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        m = bin_metrics(y_bin[idx], pred_bin[idx])
        for k in stats:
            stats[k].append(m[k])
    return {k: {"mean": float(np.mean(v)),
                "lo": float(np.percentile(v, 2.5)),
                "hi": float(np.percentile(v, 97.5))}
            for k, v in stats.items()}


def mcnemar(correct_a, correct_b):
    b = int(np.sum(correct_a & ~correct_b))
    c = int(np.sum(~correct_a & correct_b))
    stat = (abs(b - c) - 1) ** 2 / max(b + c, 1)
    p = float(chi2_dist.sf(stat, df=1))
    return {"b": b, "c": c, "chi2": float(stat), "p_value": p}


def reliability_bins(probs, y, n_bins=15):
    conf = probs.max(1)
    correct = (probs.argmax(1) == y)
    edges = np.linspace(0, 1, n_bins + 1)
    xs, accs, fracs = [], [], []
    for i in range(n_bins):
        m = (conf > edges[i]) & (conf <= edges[i + 1])
        if m.sum() > 0:
            xs.append(conf[m].mean())
            accs.append(correct[m].mean())
            fracs.append(m.mean())
    return np.array(xs), np.array(accs), np.array(fracs)


# --------------------------------------------------------------- main
def main():
    manifest, X, y, probs_raw = get_probs()
    classes = manifest["class_names"]
    benign_idx = classes.index(manifest["benign_label"])
    temps = manifest["temperatures"]
    weights = manifest["fusion_weights"]
    tau0 = manifest["tau"]
    names = list(probs_raw.keys())

    probs_cal = {n: calibrate(probs_raw[n], temps[n]) for n in names}
    ens_cal = sum(weights[n] * probs_cal[n] for n in names)
    ens_raw = sum(weights[n] * probs_raw[n] for n in names)
    ens_uniform = sum(probs_cal[n] for n in names) / len(names)

    # vote majoritaire (classe la plus votée ; départage par confiance moyenne)
    votes = np.stack([probs_cal[n].argmax(1) for n in names])
    maj = np.zeros(len(y), dtype=int)
    conf_mean = ens_uniform
    for i in range(len(y)):
        vals, cnt = np.unique(votes[:, i], return_counts=True)
        top = vals[cnt == cnt.max()]
        maj[i] = top[np.argmax(conf_mean[i, top])] if len(top) > 1 else top[0]

    A = {}  # analytics accumulator

    # ---------------- A1. ROC / PR opérationnelles -----------------------
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.6))
    roc_auc, ap = {}, {}
    all_probs = {**{n: probs_cal[n] for n in names}, "ensemble": ens_cal}
    for n, P in all_probs.items():
        score, y_bin, _ = binary_ops(P, y, benign_idx)
        fpr, tpr, _ = roc_curve(y_bin, score)
        roc_auc[n] = float(auc(fpr, tpr))
        axes[0].plot(fpr, tpr, color=COLORS[n], lw=1.6,
                     label=f"{LABELS[n]} (AUC={roc_auc[n]:.4f})")
        pr, rc, _ = precision_recall_curve(y_bin, score)
        ap[n] = float(average_precision_score(y_bin, score))
        axes[1].plot(rc, pr, color=COLORS[n], lw=1.6,
                     label=f"{LABELS[n]} (AP={ap[n]:.4f})")
    axes[0].plot([0, 1], [0, 1], "k--", lw=0.8, alpha=0.5)
    axes[0].set(xlabel="False positive rate", ylabel="True positive rate",
                title="(a) Operational ROC — BENIGN vs ATTACK", xlim=(-0.02, 1), ylim=(0, 1.02))
    axes[1].set(xlabel="Recall", ylabel="Precision",
                title="(b) Precision–Recall", xlim=(0, 1), ylim=(0, 1.02))
    for ax in axes:
        ax.legend(fontsize=7.5, loc="lower right")
    fig.tight_layout()
    fig.savefig(FIG / "fig_roc_pr.png", bbox_inches="tight")
    plt.close(fig)
    A["roc_auc"], A["average_precision"] = roc_auc, ap

    # ---------------- A2. Fiabilité avant/après calibration --------------
    fig, axes = plt.subplots(1, 4, figsize=(13, 3.2), sharey=True)
    ece = {}
    panels = [(n, probs_raw[n], probs_cal[n]) for n in names] + \
             [("ensemble", ens_raw, ens_cal)]
    for ax, (n, praw, pcal) in zip(axes, panels):
        e_b = expected_calibration_error(praw, y)
        e_a = expected_calibration_error(pcal, y)
        ece[n] = {"before": float(e_b), "after": float(e_a)}
        for P, c, lab in ((praw, "#bbbbbb", f"raw (ECE={e_b:.3f})"),
                          (pcal, COLORS[n], f"calibrated (ECE={e_a:.3f})")):
            xs, accs, _ = reliability_bins(P, y)
            ax.plot(xs, accs, "o-", ms=3, lw=1.3, color=c, label=lab)
        ax.plot([0, 1], [0, 1], "k--", lw=0.8, alpha=0.5)
        ax.set(title=LABELS[n], xlabel="Confidence", xlim=(0, 1), ylim=(0, 1))
        ax.legend(fontsize=7, loc="upper left")
    axes[0].set_ylabel("Empirical accuracy")
    fig.suptitle("Reliability diagrams — before vs after temperature scaling",
                 y=1.03, fontsize=10)
    fig.tight_layout()
    fig.savefig(FIG / "fig_reliability.png", bbox_inches="tight")
    plt.close(fig)
    A["ece"] = ece

    # ---------------- A3. Matrices de confusion --------------------------
    from sklearn.metrics import confusion_matrix
    short = [c.replace("Web_Attack", "Web_").replace("DoS_", "DoS ")
             for c in classes]
    fig, axes = plt.subplots(2, 2, figsize=(11, 10))
    for ax, (n, P) in zip(axes.flat, all_probs.items()):
        cm = confusion_matrix(y, P.argmax(1), labels=range(len(classes)))
        cmn = cm / np.maximum(cm.sum(1, keepdims=True), 1)
        im = ax.imshow(cmn, cmap="Blues", vmin=0, vmax=1)
        ax.set(title=LABELS[n], xticks=range(len(classes)),
               yticks=range(len(classes)))
        ax.set_xticklabels(short, rotation=90, fontsize=6)
        ax.set_yticklabels(short, fontsize=6)
        ax.grid(False)
        for i in range(len(classes)):
            v = cmn[i, i]
            ax.text(i, i, f"{v:.2f}", ha="center", va="center", fontsize=5,
                    color="white" if v > 0.6 else "#1f3a5f")
    fig.colorbar(im, ax=axes, fraction=0.02, pad=0.02, label="Row-normalised rate")
    fig.suptitle("Confusion matrices (15 classes, row-normalised)", fontsize=11)
    fig.savefig(FIG / "fig_confusion.png", bbox_inches="tight")
    plt.close(fig)

    # ---------------- A4. F1 par classe -----------------------------------
    per_class = {}
    fig, ax = plt.subplots(figsize=(10, 3.6))
    xpos = np.arange(len(classes))
    w = 0.2
    for k, (n, P) in enumerate(all_probs.items()):
        pr, rc, f1, sup = precision_recall_fscore_support(
            y, P.argmax(1), labels=range(len(classes)), zero_division=0)
        per_class[n] = {"precision": pr.tolist(), "recall": rc.tolist(),
                        "f1": f1.tolist(), "support": sup.tolist()}
        ax.bar(xpos + (k - 1.5) * w, f1, w, color=COLORS[n], label=LABELS[n])
    ax.set(xticks=xpos, ylabel="F1-score", ylim=(0, 1.05),
           title="Per-class F1 on the CICIDS2017 test split")
    ax.set_xticklabels(short, rotation=45, ha="right", fontsize=7)
    ax.legend(fontsize=8, ncol=4)
    fig.tight_layout()
    fig.savefig(FIG / "fig_f1_per_class.png", bbox_inches="tight")
    plt.close(fig)
    A["per_class"] = per_class
    A["class_names"] = classes

    # ---------------- B1. Ablation fusion ---------------------------------
    strategies = {
        "RNN alone (best single)": probs_cal["rnn"].argmax(1),
        "Uniform mean": ens_uniform.argmax(1),
        "Majority vote": maj,
        "CWC (weighted, calibrated)": ens_cal.argmax(1),
        "CWC without calibration": ens_raw.argmax(1),
    }
    y_bin = (y != benign_idx).astype(int)
    abl = {}
    for lab, pred in strategies.items():
        pb = (pred != benign_idx).astype(int)
        m = bin_metrics(y_bin, pb)
        m["accuracy_multiclass"] = float(np.mean(pred == y))
        abl[lab] = m
    # CWC + rejet (accepté seulement)
    conf = ens_cal.max(1)
    acc_mask = conf >= tau0
    pb = (ens_cal.argmax(1) != benign_idx).astype(int)
    m = bin_metrics(y_bin[acc_mask], pb[acc_mask])
    m["accuracy_multiclass"] = float(np.mean(ens_cal.argmax(1)[acc_mask] == y[acc_mask]))
    m["coverage"] = float(acc_mask.mean())
    abl[f"CWC + reject (tau={tau0}, accepted)"] = m
    A["ablation_fusion"] = abl

    fig, ax = plt.subplots(figsize=(8.5, 3.4))
    labs = list(abl.keys())
    f1s = [abl[l]["f1"] for l in labs]
    fprs = [abl[l]["fpr"] for l in labs]
    xp = np.arange(len(labs))
    ax.bar(xp - 0.17, f1s, 0.34, color="#4f8cff", label="Operational F1")
    ax.bar(xp + 0.17, fprs, 0.34, color="#ff5c6c", label="Operational FPR")
    for i, (a, b) in enumerate(zip(f1s, fprs)):
        ax.text(i - 0.17, a + 0.01, f"{a:.3f}", ha="center", fontsize=7)
        ax.text(i + 0.17, b + 0.01, f"{b:.3f}", ha="center", fontsize=7)
    ax.set(xticks=xp, ylim=(0, 1.1),
           title="Fusion strategy ablation (operational BENIGN vs ATTACK)")
    ax.set_xticklabels([l.replace(" (", "\n(") for l in labs], fontsize=7)
    ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG / "fig_ablation_fusion.png", bbox_inches="tight")
    plt.close(fig)

    # ---------------- B2. Risque-couverture + charge L2 -------------------
    taus = np.round(np.arange(0.30, 0.996, 0.01), 3)
    cov, risk, fpr_acc, l2 = [], [], [], []
    pred = ens_cal.argmax(1)
    correct = (pred == y)
    pb_all = (pred != benign_idx).astype(int)
    for t in taus:
        m = conf >= t
        cov.append(float(m.mean()))
        risk.append(float(1 - correct[m].mean()) if m.any() else 0.0)
        mm = bin_metrics(y_bin[m], pb_all[m]) if m.any() else {"fpr": 0}
        fpr_acc.append(mm["fpr"])
        l2.append(float(1 - m.mean()))
    A["risk_coverage"] = {"tau": taus.tolist(), "coverage": cov,
                          "risk_accepted": risk, "fpr_accepted": fpr_acc,
                          "l2_load": l2}

    fig, axes = plt.subplots(1, 2, figsize=(9, 3.4))
    axes[0].plot(cov, risk, color=COLORS["ensemble"], lw=1.8)
    i0 = int(np.argmin(np.abs(taus - tau0)))
    axes[0].plot(cov[i0], risk[i0], "o", color="#d62728", ms=7,
                 label=f"operating point τ={tau0}")
    axes[0].set(xlabel="Coverage (accepted fraction)",
                ylabel="Selective risk (error on accepted)",
                title="(a) Risk–coverage curve (CWC ensemble)")
    axes[0].legend(fontsize=8)
    ax2 = axes[1]
    ax2.plot(taus, l2, color="#f0a202", lw=1.8, label="Deferred to Layer 2 (LLM)")
    ax2.plot(taus, fpr_acc, color="#ff5c6c", lw=1.8, label="FPR on accepted")
    ax2.axvline(tau0, color="#d62728", ls="--", lw=1, alpha=0.7)
    ax2.text(tau0 + 0.005, 0.55, f"τ={tau0}", color="#d62728", fontsize=8)
    ax2.set(xlabel="Reject threshold τ", ylabel="Fraction",
            title="(b) Impact of τ on the deliberative layer load")
    ax2.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG / "fig_risk_coverage.png", bbox_inches="tight")
    plt.close(fig)

    # ---------------- C1. Bootstrap IC 95 % -------------------------------
    print("Bootstrap (1000 rééchantillonnages) ...")
    boot = {}
    for n, P in all_probs.items():
        _, yb, pb2 = binary_ops(P, y, benign_idx)
        boot[n] = bootstrap_ci(yb, pb2)
        print(f"  {n:9s} F1={boot[n]['f1']['mean']:.4f} "
              f"[{boot[n]['f1']['lo']:.4f}, {boot[n]['f1']['hi']:.4f}]")
    A["bootstrap_ci95"] = boot

    fig, ax = plt.subplots(figsize=(6.5, 3))
    order = ["cnn", "dnn", "rnn", "ensemble"]
    for i, n in enumerate(order):
        b = boot[n]["f1"]
        ax.errorbar(b["mean"], i, xerr=[[b["mean"] - b["lo"]], [b["hi"] - b["mean"]]],
                    fmt="o", color=COLORS[n], capsize=4, ms=6)
        ax.text(b["mean"], i + 0.18, f"{b['mean']:.4f}", ha="center", fontsize=7.5)
    ax.set(yticks=range(len(order)), ylim=(-0.5, len(order) - 0.3),
           xlabel="Operational F1 (95% bootstrap CI, n=1000)",
           title="Statistical comparison of detectors")
    ax.set_yticklabels([LABELS[n] for n in order])
    fig.tight_layout()
    fig.savefig(FIG / "fig_bootstrap_ci.png", bbox_inches="tight")
    plt.close(fig)

    # ---------------- C2. McNemar ------------------------------------------
    correct_by = {n: (P.argmax(1) == y) for n, P in all_probs.items()}
    pairs = [("rnn", "cnn"), ("rnn", "dnn"), ("cnn", "dnn"),
             ("ensemble", "rnn"), ("ensemble", "dnn"), ("ensemble", "cnn")]
    A["mcnemar"] = {f"{a}_vs_{b}": mcnemar(correct_by[a], correct_by[b])
                    for a, b in pairs}
    for k, v in A["mcnemar"].items():
        print(f"  McNemar {k:18s} chi2={v['chi2']:12.1f}  p={v['p_value']:.2e}")

    # ---------------- global summary ---------------------------------------
    A["operational_summary"] = {n: bin_metrics(*(binary_ops(P, y, benign_idx)[1:]))
                                for n, P in all_probs.items()}
    A["n_test"] = int(len(y))
    A["tau"] = tau0
    A["fusion_weights"] = weights
    A["temperatures"] = temps
    (OUT / "analytics.json").write_text(
        json.dumps(A, indent=1), encoding="utf-8")
    print(f"\nOK — analytics.json + {len(list(FIG.glob('*.png')))} figures dans {FIG}")


if __name__ == "__main__":
    main()
