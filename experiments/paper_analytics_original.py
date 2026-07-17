"""
BAg-IDS – Analyses complètes du papier sous le PROTOCOLE D'ORIGINE
(RobustScaler + benign équilibré + split 60/20/20 rs=1, cf. [56]).

Ne nécessite PAS TensorFlow : tout est recalculé à partir des
probabilités sauvegardées par original_pipeline_eval_tf.py.

Produit (mêmes noms de fichiers -> le .docx les reprend tel quel) :
  fig_roc_pr, fig_reliability, fig_confusion, fig_f1_per_class,
  fig_ablation_fusion, fig_risk_coverage, fig_bootstrap_ci,
  fig_robust_fusion (corruption : solo/statique/adaptatif/médiane),
  fig_corruption_weight (poids adaptatif vs p, cibles RNN et CNN)
+ results/paper_analytics_original/analytics.json

Usage : python experiments/paper_analytics_original.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

for _s in (sys.stdout, sys.stderr):
    if hasattr(_s, "reconfigure"):
        _s.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
ORIG = ROOT / "results" / "original_pipeline"
OUT = ROOT / "results" / "paper_analytics_original"
FIG = OUT / "figures"
FIG.mkdir(parents=True, exist_ok=True)
PFIG = ROOT / "paper_q1" / "figures"

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

from scipy.stats import chi2 as chi2_dist
from sklearn.metrics import (auc, average_precision_score, confusion_matrix,
                             precision_recall_curve,
                             precision_recall_fscore_support, roc_curve)

from src.calibration import TemperatureScaler, expected_calibration_error
from src.fusion import linear_opinion_pool, precision_weights

RNG_SEED = 42


# ------------------------------------------------------------------ utils
def bin_ops(P, y, b):
    return 1.0 - P[:, b], (y != b).astype(int), (P.argmax(1) != b).astype(int)


def bin_metrics(y_bin, pred_bin):
    tp = int(np.sum((pred_bin == 1) & (y_bin == 1)))
    fp = int(np.sum((pred_bin == 1) & (y_bin == 0)))
    fn = int(np.sum((pred_bin == 0) & (y_bin == 1)))
    tn = int(np.sum((pred_bin == 0) & (y_bin == 0)))
    prec = tp / max(tp + fp, 1); rec = tp / max(tp + fn, 1)
    return {"precision": prec, "recall": rec,
            "f1": 2 * prec * rec / max(prec + rec, 1e-12),
            "fpr": fp / max(fp + tn, 1), "accuracy": (tp + tn) / len(y_bin)}


def bootstrap_ci(y_bin, pred_bin, n_boot=1000, seed=RNG_SEED):
    rng = np.random.default_rng(seed)
    n = len(y_bin)
    st = {"f1": [], "fpr": [], "accuracy": []}
    for _ in range(n_boot):
        idx = rng.integers(0, n, n)
        m = bin_metrics(y_bin[idx], pred_bin[idx])
        for k in st:
            st[k].append(m[k])
    return {k: {"mean": float(np.mean(v)), "lo": float(np.percentile(v, 2.5)),
                "hi": float(np.percentile(v, 97.5))} for k, v in st.items()}


def mcnemar(a, b):
    x = int(np.sum(a & ~b)); y_ = int(np.sum(~a & b))
    stat = (abs(x - y_) - 1) ** 2 / max(x + y_, 1)
    return {"b": x, "c": y_, "chi2": float(stat),
            "p_value": float(chi2_dist.sf(stat, df=1))}


def reliability_bins(P, y, n_bins=15):
    conf, correct = P.max(1), (P.argmax(1) == y)
    edges = np.linspace(0, 1, n_bins + 1)
    xs, accs = [], []
    for i in range(n_bins):
        m = (conf > edges[i]) & (conf <= edges[i + 1])
        if m.sum() > 0:
            xs.append(conf[m].mean()); accs.append(correct[m].mean())
    return np.array(xs), np.array(accs)


def poison(P, benign_idx, C, frac, rng):
    """Corruption des sorties, identique à phase2/bench_label_flipping."""
    Q = P.copy()
    idx = rng.choice(len(P), size=int(frac * len(P)), replace=False)
    preds = P.argmax(1)
    ben = preds[idx] == benign_idx
    for i in idx[ben]:
        a = rng.integers(0, C)
        while a == benign_idx:
            a = rng.integers(0, C)
        Q[i] = 0.0; Q[i, a] = 1.0
    Q[idx[~ben]] = 0.0
    Q[idx[~ben], benign_idx] = 1.0
    return Q


def main():
    y_va = np.load(ORIG / "y_val.npy"); y = np.load(ORIG / "y_test.npy")
    classes = json.loads((ORIG / "classes.json").read_text("utf-8"))
    C = len(classes); b = classes.index("BENIGN")
    names = ["rnn", "cnn", "dnn"]
    raw_va = {n: np.load(ORIG / f"probs_val_{n}.npy") for n in names}
    raw_te = {n: np.load(ORIG / f"probs_test_{n}.npy") for n in names}

    scalers = {n: TemperatureScaler().fit(raw_va[n], y_va) for n in names}
    cal_va = {n: scalers[n].transform(raw_va[n]) for n in names}
    cal_te = {n: scalers[n].transform(raw_te[n]) for n in names}
    weights = precision_weights(cal_va, y_va)
    ens = linear_opinion_pool(cal_te, weights)
    ens_raw = linear_opinion_pool(raw_te, weights)
    ens_uni = sum(cal_te[n] for n in names) / 3.0
    tau0 = 0.70

    A = {"protocol": "original [56]", "n_test": int(len(y)),
         "temperatures": {n: float(s.temperature_) for n, s in scalers.items()},
         "fusion_weights": {n: float(w) for n, w in weights.items()}}
    allP = {**cal_te, "ensemble": ens}

    # ------------------------------ ROC / PR
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.6))
    A["roc_auc"], A["average_precision"] = {}, {}
    for n, P in allP.items():
        s, yb, _ = bin_ops(P, y, b)
        fpr, tpr, _ = roc_curve(yb, s)
        A["roc_auc"][n] = float(auc(fpr, tpr))
        axes[0].plot(fpr, tpr, color=COLORS[n], lw=1.6,
                     label=f"{LABELS[n]} (AUC={A['roc_auc'][n]:.4f})")
        pr, rc, _ = precision_recall_curve(yb, s)
        A["average_precision"][n] = float(average_precision_score(yb, s))
        axes[1].plot(rc, pr, color=COLORS[n], lw=1.6,
                     label=f"{LABELS[n]} (AP={A['average_precision'][n]:.4f})")
    axes[0].plot([0, 1], [0, 1], "k--", lw=0.8, alpha=0.5)
    axes[0].set(xlabel="False positive rate", ylabel="True positive rate",
                title="(a) Operational ROC – BENIGN vs ATTACK",
                xlim=(-0.02, 1), ylim=(0, 1.02))
    axes[1].set(xlabel="Recall", ylabel="Precision",
                title="(b) Precision–Recall", xlim=(0, 1), ylim=(0, 1.02))
    for ax in axes:
        ax.legend(fontsize=7.5, loc="lower right")
    fig.tight_layout(); fig.savefig(FIG / "fig_roc_pr.png",
                                    bbox_inches="tight"); plt.close(fig)

    # ------------------------------ fiabilité
    fig, axes = plt.subplots(1, 4, figsize=(13, 3.2), sharey=True)
    A["ece"] = {}
    panels = [(n, raw_te[n], cal_te[n]) for n in names] + \
             [("ensemble", ens_raw, ens)]
    for ax, (n, praw, pcal) in zip(axes, panels):
        eb = expected_calibration_error(praw, y)
        ea = expected_calibration_error(pcal, y)
        A["ece"][n] = {"before": float(eb), "after": float(ea)}
        for P, c, lab in ((praw, "#bbbbbb", f"raw (ECE={eb:.3f})"),
                          (pcal, COLORS[n], f"calibrated (ECE={ea:.3f})")):
            xs, accs = reliability_bins(P, y)
            ax.plot(xs, accs, "o-", ms=3, lw=1.3, color=c, label=lab)
        ax.plot([0, 1], [0, 1], "k--", lw=0.8, alpha=0.5)
        ax.set(title=LABELS[n], xlabel="Confidence", xlim=(0, 1), ylim=(0, 1))
        ax.legend(fontsize=7, loc="upper left")
    axes[0].set_ylabel("Empirical accuracy")
    fig.suptitle("Reliability diagrams – before vs after temperature scaling",
                 y=1.03, fontsize=10)
    fig.tight_layout(); fig.savefig(FIG / "fig_reliability.png",
                                    bbox_inches="tight"); plt.close(fig)

    # ------------------------------ confusions
    short = [c.replace("Web_Attack", "Web_").replace("DoS_", "DoS ")
             for c in classes]
    fig, axes = plt.subplots(2, 2, figsize=(11, 10))
    for ax, (n, P) in zip(axes.flat, allP.items()):
        cm = confusion_matrix(y, P.argmax(1), labels=range(C))
        cmn = cm / np.maximum(cm.sum(1, keepdims=True), 1)
        im = ax.imshow(cmn, cmap="Blues", vmin=0, vmax=1)
        ax.set(title=LABELS[n], xticks=range(C), yticks=range(C))
        ax.set_xticklabels(short, rotation=90, fontsize=6)
        ax.set_yticklabels(short, fontsize=6)
        ax.grid(False)
        for i in range(C):
            v = cmn[i, i]
            ax.text(i, i, f"{v:.2f}", ha="center", va="center", fontsize=5,
                    color="white" if v > 0.6 else "#1f3a5f")
    fig.colorbar(im, ax=axes, fraction=0.02, pad=0.02,
                 label="Row-normalised rate")
    fig.suptitle("Confusion matrices (15 classes, row-normalised)",
                 fontsize=11)
    fig.savefig(FIG / "fig_confusion.png", bbox_inches="tight"); plt.close(fig)

    # ------------------------------ F1 par classe
    A["per_class"] = {}
    fig, ax = plt.subplots(figsize=(10, 3.6))
    xpos = np.arange(C); w = 0.2
    for k, (n, P) in enumerate(allP.items()):
        pr, rc, f1, sup = precision_recall_fscore_support(
            y, P.argmax(1), labels=range(C), zero_division=0)
        A["per_class"][n] = {"f1": f1.tolist(), "support": sup.tolist()}
        ax.bar(xpos + (k - 1.5) * w, f1, w, color=COLORS[n], label=LABELS[n])
    ax.set(xticks=xpos, ylabel="F1-score", ylim=(0, 1.05),
           title="Per-class F1 (original training protocol, balanced test)")
    ax.set_xticklabels(short, rotation=45, ha="right", fontsize=7)
    ax.legend(fontsize=8, ncol=4)
    fig.tight_layout(); fig.savefig(FIG / "fig_f1_per_class.png",
                                    bbox_inches="tight"); plt.close(fig)
    A["class_names"] = classes

    # ------------------------------ ablation fusion
    votes = np.stack([cal_te[n].argmax(1) for n in names])
    maj = np.zeros(len(y), dtype=int)
    for i in range(len(y)):
        vals, cnt = np.unique(votes[:, i], return_counts=True)
        top = vals[cnt == cnt.max()]
        maj[i] = top[np.argmax(ens_uni[i, top])] if len(top) > 1 else top[0]
    yb = (y != b).astype(int)
    best_single = max(names,
                      key=lambda n: np.mean(cal_te[n].argmax(1) == y))
    strategies = {
        f"{best_single.upper()} alone (best single)":
            cal_te[best_single].argmax(1),
        "Uniform mean": ens_uni.argmax(1),
        "Majority vote": maj,
        "CWC (weighted, calibrated)": ens.argmax(1),
        "CWC without calibration": ens_raw.argmax(1),
    }
    A["ablation_fusion"] = {}
    for lab, pred in strategies.items():
        m = bin_metrics(yb, (pred != b).astype(int))
        m["accuracy_multiclass"] = float(np.mean(pred == y))
        A["ablation_fusion"][lab] = m
    conf = ens.max(1); msk = conf >= tau0
    pb = (ens.argmax(1) != b).astype(int)
    m = bin_metrics(yb[msk], pb[msk])
    m["accuracy_multiclass"] = float(np.mean(ens.argmax(1)[msk] == y[msk]))
    m["coverage"] = float(msk.mean())
    A["ablation_fusion"][f"CWC + reject (tau={tau0}, accepted)"] = m

    fig, ax = plt.subplots(figsize=(8.5, 3.4))
    labs = list(A["ablation_fusion"].keys())
    f1s = [A["ablation_fusion"][l]["f1"] for l in labs]
    fprs = [A["ablation_fusion"][l]["fpr"] for l in labs]
    xp = np.arange(len(labs))
    ax.bar(xp - 0.17, f1s, 0.34, color="#4f8cff", label="Operational F1")
    ax.bar(xp + 0.17, fprs, 0.34, color="#ff5c6c", label="Operational FPR")
    for i, (a_, b_) in enumerate(zip(f1s, fprs)):
        ax.text(i - 0.17, a_ + 0.01, f"{a_:.3f}", ha="center", fontsize=7)
        ax.text(i + 0.17, b_ + 0.01, f"{b_:.4f}", ha="center", fontsize=7)
    ax.set(xticks=xp, ylim=(0, 1.13),
           title="Fusion strategy ablation (operational BENIGN vs ATTACK)")
    ax.set_xticklabels([l.replace(" (", "\n(") for l in labs], fontsize=7)
    ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(FIG / "fig_ablation_fusion.png",
                                    bbox_inches="tight"); plt.close(fig)

    # ------------------------------ risque-couverture + baseline sélective
    taus = np.round(np.arange(0.30, 0.996, 0.01), 3)
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.4))
    for P, c, lab in ((cal_te[best_single], COLORS[best_single],
                       f"{best_single.upper()} alone, selective "
                       "(softmax-response)"),
                      (ens, COLORS["ensemble"], "CWC ensemble, selective")):
        cf, ok = P.max(1), (P.argmax(1) == y)
        cov = [float((cf >= t).mean()) for t in taus]
        risk = [float(1 - ok[cf >= t].mean()) if (cf >= t).any() else 0.0
                for t in taus]
        axes[0].plot(cov, risk, c=c, lw=1.7, label=lab)
    cf, ok = ens.max(1), (ens.argmax(1) == y)
    axes[0].plot(float((cf >= tau0).mean()),
                 float(1 - ok[cf >= tau0].mean()), "o", c="#d62728", ms=7,
                 label=f"operating point τ={tau0}")
    axes[0].set(xlabel="Coverage (accepted fraction)",
                ylabel="Selective risk (error on accepted)",
                title="(a) Risk–coverage: CWC vs single-model baseline")
    axes[0].legend(fontsize=7.3)
    l2, fpr_acc = [], []
    pred = ens.argmax(1); pball = (pred != b).astype(int)
    rc_data = {"tau": taus.tolist()}
    for t in taus:
        mm = cf >= t
        l2.append(float(1 - mm.mean()))
        met = bin_metrics(yb[mm], pball[mm]) if mm.any() else {"fpr": 0}
        fpr_acc.append(met["fpr"])
    rc_data.update({"l2_load": l2, "fpr_accepted": fpr_acc})
    A["risk_coverage"] = rc_data
    axes[1].plot(taus, l2, c="#f0a202", lw=1.8,
                 label="Deferred to Layer 2 (LLM)")
    axes[1].plot(taus, fpr_acc, c="#ff5c6c", lw=1.8, label="FPR on accepted")
    axes[1].axvline(tau0, color="#d62728", ls="--", lw=1, alpha=0.7)
    axes[1].text(tau0 + 0.005, 0.55, f"τ={tau0}", color="#d62728", fontsize=8)
    axes[1].set(xlabel="Reject threshold τ", ylabel="Fraction",
                title="(b) Impact of τ on the deliberative layer load")
    axes[1].legend(fontsize=8)
    fig.tight_layout(); fig.savefig(FIG / "fig_risk_coverage.png",
                                    bbox_inches="tight"); plt.close(fig)

    # ------------------------------ bootstrap + McNemar
    print("Bootstrap (1000) ...")
    A["bootstrap_ci95"] = {}
    for n, P in allP.items():
        _, yb2, pb2 = bin_ops(P, y, b)
        A["bootstrap_ci95"][n] = bootstrap_ci(yb2, pb2)
        bprovíncia = A["bootstrap_ci95"][n]["f1"]
        print(f"  {n:9s} F1={bprovíncia['mean']:.4f} "
              f"[{bprovíncia['lo']:.4f}, {bprovíncia['hi']:.4f}]")
    fig, ax = plt.subplots(figsize=(6.5, 3))
    order = ["cnn", "rnn", "dnn", "ensemble"]
    for i, n in enumerate(order):
        d = A["bootstrap_ci95"][n]["f1"]
        ax.errorbar(d["mean"], i,
                    xerr=[[d["mean"] - d["lo"]], [d["hi"] - d["mean"]]],
                    fmt="o", color=COLORS[n], capsize=4, ms=6)
        ax.text(d["mean"], i + 0.18, f"{d['mean']:.4f}", ha="center",
                fontsize=7.5)
    ax.set(yticks=range(len(order)), ylim=(-0.5, len(order) - 0.3),
           xlabel="Operational F1 (95% bootstrap CI, n=1000)",
           title="Statistical comparison of detectors")
    ax.set_yticklabels([LABELS[n] for n in order])
    fig.tight_layout(); fig.savefig(FIG / "fig_bootstrap_ci.png",
                                    bbox_inches="tight"); plt.close(fig)

    correct = {n: (P.argmax(1) == y) for n, P in allP.items()}
    pairs = [("rnn", "cnn"), ("rnn", "dnn"), ("cnn", "dnn"),
             ("ensemble", "rnn"), ("ensemble", "dnn"), ("ensemble", "cnn")]
    A["mcnemar"] = {f"{a}_vs_{c2}": mcnemar(correct[a], correct[c2])
                    for a, c2 in pairs}
    for k, v in A["mcnemar"].items():
        print(f"  McNemar {k:18s} chi2={v['chi2']:10.1f}  p={v['p_value']:.2e}")

    # ------------------------------ corruption (solo/static/adaptive/median)
    print("Corruption simulée (protocole d'origine) ...")
    fracs = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.7, 0.9, 1.0]
    A["corruption"] = {}
    for target in ("rnn", "cnn"):
        rows = []
        for frac in fracs:
            rng = np.random.default_rng(RNG_SEED)
            pois_va = poison(cal_va[target], b, C, frac, rng)
            pois_te = poison(cal_te[target], b, C, frac, rng)
            va = {**cal_va, target: pois_va}
            te = {**cal_te, target: pois_te}
            w_ad = precision_weights(va, y_va)
            solo = pois_te.argmax(1)
            stat = linear_opinion_pool(te, weights).argmax(1)
            adap = linear_opinion_pool(te, w_ad).argmax(1)
            med = np.median(np.stack([te[n] for n in names]), axis=0).argmax(1)
            row = {"fraction": frac,
                   "weight_adaptive": float(w_ad[target]),
                   "solo_acc": float(np.mean(solo == y)),
                   "static_acc": float(np.mean(stat == y)),
                   "adaptive_acc": float(np.mean(adap == y)),
                   "median_acc": float(np.mean(med == y)),
                   "static_fpr": bin_metrics(yb, (stat != b).astype(int))["fpr"],
                   "adaptive_fpr": bin_metrics(yb, (adap != b).astype(int))["fpr"],
                   "median_fpr": bin_metrics(yb, (med != b).astype(int))["fpr"]}
            rows.append(row)
            if target == "rnn":
                print(f"  p={frac:0.1f} solo={row['solo_acc']:.3f} "
                      f"stat={row['static_acc']:.3f} "
                      f"adap={row['adaptive_acc']:.3f} "
                      f"med={row['median_acc']:.3f} w={row['weight_adaptive']:.3f}")
        A["corruption"][target] = rows

    rows = A["corruption"]["rnn"]
    fr = [r["fraction"] for r in rows]
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.4))
    axes[0].plot(fr, [r["solo_acc"] for r in rows], "o-", c="#999", lw=1.4,
                 ms=3.5, label="Corrupted RNN alone")
    axes[0].plot(fr, [r["static_acc"] for r in rows], "s-", c="#4f8cff",
                 lw=1.6, ms=3.5, label="Static weights")
    axes[0].plot(fr, [r["median_acc"] for r in rows], "^-", c="#f0a202",
                 lw=1.6, ms=3.5, label="Median pool (= trimmed, M=3)")
    axes[0].plot(fr, [r["adaptive_acc"] for r in rows], "D-", c="#7d4fd3",
                 lw=1.8, ms=3.5, label="Adaptive weights (CWC)")
    axes[0].set(xlabel="Corruption fraction p", ylabel="15-class accuracy",
                title="(a) Accuracy under simulated corruption of the RNN")
    axes[0].legend(fontsize=7.5)
    axes[1].plot(fr, [r["static_fpr"] for r in rows], "s-", c="#4f8cff",
                 lw=1.6, ms=3.5, label="Static weights")
    axes[1].plot(fr, [r["median_fpr"] for r in rows], "^-", c="#f0a202",
                 lw=1.6, ms=3.5, label="Median pool")
    axes[1].plot(fr, [r["adaptive_fpr"] for r in rows], "D-", c="#7d4fd3",
                 lw=1.6, ms=3.5, label="Adaptive (CWC)")
    axes[1].set(xlabel="Corruption fraction p", ylabel="Operational FPR",
                title="(b) Operational FPR")
    axes[1].legend(fontsize=7.5)
    fig.tight_layout(); fig.savefig(FIG / "fig_robust_fusion.png",
                                    bbox_inches="tight"); plt.close(fig)

    fig, ax = plt.subplots(figsize=(5.5, 3.2))
    for tgt, c in (("rnn", COLORS["rnn"]), ("cnn", COLORS["cnn"])):
        rws = A["corruption"][tgt]
        ax.plot([r["fraction"] for r in rws],
                [r["weight_adaptive"] for r in rws], "o-", color=c, lw=1.7,
                ms=4, label=f"target: {tgt.upper()}")
    ax.axhline(1 / 3, color="#888", ls="--", lw=0.9, alpha=0.7)
    ax.text(0.02, 1 / 3 + 0.008, "uniform 1/3", fontsize=7.5, color="#666")
    ax.set(xlabel="Corruption fraction p", ylabel="Adaptive fusion weight",
           title="Weight of the corrupted detector (CWC)")
    ax.legend(fontsize=8)
    fig.tight_layout(); fig.savefig(FIG / "fig_corruption_weight.png",
                                    bbox_inches="tight"); plt.close(fig)

    # ------------------------------ tau sweep table + export
    A["tau_table"] = {}
    for t in (0.5, 0.6, 0.7, 0.75, 0.8, 0.9):
        mm = cf >= t
        met = bin_metrics(yb[mm], pball[mm])
        met["coverage"] = float(mm.mean())
        met["acc15"] = float(np.mean(pred[mm] == y[mm]))
        A["tau_table"][str(t)] = met
    (OUT / "analytics.json").write_text(json.dumps(A, indent=1), "utf-8")

    # copie vers les figures du papier
    import shutil
    for f in FIG.glob("*.png"):
        shutil.copy(f, PFIG / f.name)
    print(f"\nOK -> {OUT/'analytics.json'} + {len(list(FIG.glob('*.png')))} "
          f"figures copiées vers paper_q1/figures/")


if __name__ == "__main__":
    main()
