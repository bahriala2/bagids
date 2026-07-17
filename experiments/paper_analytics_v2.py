"""
BAg-IDS — Compléments d'analyse pour la révision du papier (v2).

  1. Baselines de fusion robuste sous corruption simulée des sorties du
     RNN (même modèle de corruption que phase 2.3) : CWC statique
     (recalcul de contrôle) + pool MÉDIAN (= trimmed mean pour M=3).
     -> fig_robust_fusion.png + robust_fusion.json
  2. Ligne τ = 0.75 manquante (accuracy / F1 acceptés).
  3. Courbe risque-couverture avec baseline sélective (RNN seul,
     softmax-response) -> fig_risk_coverage.png (remplacée).
  4. Benchmark du chemin réflexe : latence batch-1 (p50/p95) par modèle
     et pipeline complet (3 modèles + calibration + fusion + rejet),
     débit par lots. -> reflex_bench.json

Usage : python experiments/paper_analytics_v2.py [--skip-bench]
"""
from __future__ import annotations

import argparse
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

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams.update({
    "savefig.dpi": 300, "font.size": 9, "axes.grid": True, "grid.alpha": 0.3,
    "axes.spines.top": False, "axes.spines.right": False,
})

from scipy.special import softmax
from src.calibration import probs_to_logits

RNG_SEED = 42


def calibrate(p, T):
    return softmax(probs_to_logits(p) / T, axis=1)


def poison_predictions(probs, benign_idx, n_classes, fraction, rng):
    """Reproduit experiments/phase2/bench_label_flipping.py :
    inversion one-hot de la décision pour une fraction des flux."""
    poisoned = probs.copy()
    n = len(probs)
    idx = rng.choice(n, size=int(fraction * n), replace=False)
    preds = probs.argmax(axis=1)
    ben = preds[idx] == benign_idx
    # bénin -> attaque aléatoire
    for i in idx[ben]:
        a = rng.integers(0, n_classes)
        while a == benign_idx:
            a = rng.integers(0, n_classes)
        poisoned[i] = 0.0
        poisoned[i, a] = 1.0
    # attaque -> bénin
    poisoned[idx[~ben]] = 0.0
    poisoned[idx[~ben], benign_idx] = 1.0
    return poisoned


def bin_fpr_acc(pred, y, benign_idx):
    y_bin = (y != benign_idx)
    p_bin = (pred != benign_idx)
    fp = np.sum(p_bin & ~y_bin)
    tn = np.sum(~p_bin & ~y_bin)
    return float(fp / max(fp + tn, 1)), float(np.mean(pred == y))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-bench", action="store_true")
    args = ap.parse_args()

    manifest = json.loads((BUNDLE / "manifest.json").read_text("utf-8"))
    classes = manifest["class_names"]
    benign_idx = classes.index(manifest["benign_label"])
    C = len(classes)
    temps, weights, tau0 = (manifest["temperatures"],
                            manifest["fusion_weights"], manifest["tau"])
    y = np.load(BUNDLE / "y_test.npy")
    names = list(manifest["models"].keys())
    probs_cal = {n: calibrate(np.load(OUT / f"probs_raw_{n}.npy"), temps[n])
                 for n in names}
    ens = sum(weights[n] * probs_cal[n] for n in names)

    R = {}

    # ------------------------------------------------ 1. robust baselines
    print("1) Baselines robustes sous corruption du RNN ...")
    fractions = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.7, 0.9, 1.0]
    phase2 = json.loads((ROOT / "results/phase2/label_flipping_rnn.json")
                        .read_text("utf-8"))
    p2 = {round(row["fraction"], 2): row for row in phase2["rows"]}
    rows = []
    for frac in fractions:
        rng = np.random.default_rng(RNG_SEED)
        pois = poison_predictions(probs_cal["rnn"], benign_idx, C, frac, rng)
        stack = {"rnn": pois, "cnn": probs_cal["cnn"], "dnn": probs_cal["dnn"]}
        static = sum(weights[n] * stack[n] for n in names).argmax(1)
        median = np.median(np.stack([stack[n] for n in names]), axis=0).argmax(1)
        fpr_s, acc_s = bin_fpr_acc(static, y, benign_idx)
        fpr_m, acc_m = bin_fpr_acc(median, y, benign_idx)
        ref = p2.get(round(frac, 2), {})
        rows.append({
            "fraction": frac,
            "static_acc": acc_s, "static_fpr": fpr_s,
            "median_acc": acc_m, "median_fpr": fpr_m,
            "phase2_static_acc": ref.get("ensemble_static", {}).get("accuracy"),
            "phase2_adaptive_acc": ref.get("ensemble_adaptive", {}).get("accuracy"),
            "phase2_solo_acc": ref.get("solo_poisoned", {}).get("accuracy"),
        })
        print(f"  p={frac:0.1f}  static={acc_s:.4f} (phase2 "
              f"{ref.get('ensemble_static',{}).get('accuracy',0):.4f})  "
              f"median={acc_m:.4f}  adaptive(p2)="
              f"{ref.get('ensemble_adaptive',{}).get('accuracy',0):.4f}")
    R["robust_fusion"] = rows

    fig, axes = plt.subplots(1, 2, figsize=(9, 3.4))
    fr = [r["fraction"] for r in rows]
    axes[0].plot(fr, [r["phase2_solo_acc"] for r in rows], "o-", c="#999",
                 lw=1.4, ms=3.5, label="Corrupted RNN alone")
    axes[0].plot(fr, [r["static_acc"] for r in rows], "s-", c="#4f8cff",
                 lw=1.6, ms=3.5, label="Static weights")
    axes[0].plot(fr, [r["median_acc"] for r in rows], "^-", c="#f0a202",
                 lw=1.6, ms=3.5, label="Median pool (= trimmed, M=3)")
    axes[0].plot(fr, [r["phase2_adaptive_acc"] for r in rows], "D-",
                 c="#7d4fd3", lw=1.8, ms=3.5, label="Adaptive weights (CWC)")
    axes[0].set(xlabel="Corruption fraction p", ylabel="15-class accuracy",
                title="(a) Accuracy under simulated corruption of the RNN")
    axes[0].legend(fontsize=7.5)
    axes[1].plot(fr, [r["static_fpr"] for r in rows], "s-", c="#4f8cff",
                 lw=1.6, ms=3.5, label="Static weights")
    axes[1].plot(fr, [r["median_fpr"] for r in rows], "^-", c="#f0a202",
                 lw=1.6, ms=3.5, label="Median pool")
    axes[1].set(xlabel="Corruption fraction p", ylabel="Operational FPR",
                title="(b) FPR of the non-adaptive baselines")
    axes[1].legend(fontsize=7.5)
    fig.tight_layout()
    fig.savefig(FIG / "fig_robust_fusion.png", bbox_inches="tight")
    plt.close(fig)

    # ------------------------------------------------ 2. tau = 0.75
    conf = ens.max(1)
    pred = ens.argmax(1)
    m = conf >= 0.75
    y_bin = (y != benign_idx)
    p_bin = (pred != benign_idx)
    tp = np.sum(p_bin[m] & y_bin[m]); fp = np.sum(p_bin[m] & ~y_bin[m])
    fn = np.sum(~p_bin[m] & y_bin[m])
    prec = tp / max(tp + fp, 1); rec = tp / max(tp + fn, 1)
    R["tau_075"] = {
        "coverage": float(m.mean()),
        "acc15_accepted": float(np.mean(pred[m] == y[m])),
        "f1_accepted": float(2 * prec * rec / max(prec + rec, 1e-12)),
    }
    print("2) tau=0.75 :", R["tau_075"])

    # ------------------------------------------------ 3. risk-coverage + selective baseline
    print("3) Courbe risque-couverture avec baseline sélective RNN ...")
    taus = np.round(np.arange(0.30, 0.996, 0.01), 3)
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.4))
    for P, c, lab in ((probs_cal["rnn"], "#1f77b4",
                       "RNN alone, selective (softmax-response)"),
                      (ens, "#7d4fd3", "CWC ensemble, selective")):
        cf, pd_, ok = P.max(1), P.argmax(1), (P.argmax(1) == y)
        cov = [float((cf >= t).mean()) for t in taus]
        risk = [float(1 - ok[cf >= t].mean()) if (cf >= t).any() else 0.0
                for t in taus]
        axes[0].plot(cov, risk, c=c, lw=1.7, label=lab)
    i0 = int(np.argmin(np.abs(taus - tau0)))
    cf = ens.max(1); ok = (ens.argmax(1) == y)
    cov0 = float((cf >= tau0).mean())
    risk0 = float(1 - ok[cf >= tau0].mean())
    axes[0].plot(cov0, risk0, "o", c="#d62728", ms=7,
                 label=f"operating point τ={tau0}")
    axes[0].set(xlabel="Coverage (accepted fraction)",
                ylabel="Selective risk (error on accepted)",
                title="(a) Risk–coverage: CWC vs single-model baseline")
    axes[0].legend(fontsize=7.3)
    # panel b identical to before (deferred + fpr)
    l2, fpr_acc = [], []
    pred = ens.argmax(1); p_bin = (pred != benign_idx)
    for t in taus:
        mm = cf >= t
        l2.append(float(1 - mm.mean()))
        fp = np.sum(p_bin[mm] & ~y_bin[mm]); tn = np.sum(~p_bin[mm] & ~y_bin[mm])
        fpr_acc.append(float(fp / max(fp + tn, 1)))
    axes[1].plot(taus, l2, c="#f0a202", lw=1.8, label="Deferred to Layer 2 (LLM)")
    axes[1].plot(taus, fpr_acc, c="#ff5c6c", lw=1.8, label="FPR on accepted")
    axes[1].axvline(tau0, color="#d62728", ls="--", lw=1, alpha=0.7)
    axes[1].text(tau0 + 0.005, 0.55, f"τ={tau0}", color="#d62728", fontsize=8)
    axes[1].set(xlabel="Reject threshold τ", ylabel="Fraction",
                title="(b) Impact of τ on the deliberative layer load")
    axes[1].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(FIG / "fig_risk_coverage.png", bbox_inches="tight")
    plt.close(fig)

    # ------------------------------------------------ 4. reflex bench
    if not args.skip_bench:
        print("4) Benchmark chemin réflexe (batch-1 et par lots) ...")
        import tensorflow as tf
        from src.data_loader import reshape_for_model
        from src.model_loading import load_keras_model_compat
        X = np.load(BUNDLE / "X_test.npy")
        models, X_r = {}, {}
        for n, path in manifest["models"].items():
            models[n] = load_keras_model_compat(path)
            X_r[n] = reshape_for_model(models[n], X)
        # warmup
        for n in names:
            models[n].predict(X_r[n][:64], batch_size=64, verbose=0)
        # batch-1 : pipeline complet (3 modèles + calib + fusion + rejet)
        n_iter = 200
        lat = []
        idxs = np.random.default_rng(0).integers(0, len(X), n_iter)
        Ts = np.array([temps[n] for n in names])
        Ws = np.array([weights[n] for n in names])
        for j in idxs:
            t0 = time.perf_counter()
            ps = []
            for n in names:
                pr = models[n](X_r[n][j:j + 1], training=False).numpy()
                ps.append(softmax(probs_to_logits(pr) / temps[n], axis=1))
            fused = sum(w * p_ for w, p_ in zip(Ws, ps))
            _ = (fused.argmax(1), fused.max(1) >= tau0)
            lat.append((time.perf_counter() - t0) * 1000)
        lat = np.array(lat)
        # débit par lots (batch 8192, pipeline complet)
        t0 = time.perf_counter()
        ps = {n: models[n].predict(X_r[n], batch_size=8192, verbose=0)
              for n in names}
        fused = sum(weights[n] * calibrate(ps[n], temps[n]) for n in names)
        _ = (fused.argmax(1), fused.max(1) >= tau0)
        dt = time.perf_counter() - t0
        R["reflex_bench"] = {
            "batch1_ms_p50": float(np.percentile(lat, 50)),
            "batch1_ms_p95": float(np.percentile(lat, 95)),
            "batch1_ms_mean": float(lat.mean()),
            "batched_flows_per_s": float(len(X) / dt),
            "batched_total_s": float(dt),
            "n_flows": int(len(X)),
        }
        print(f"  batch-1 pipeline : p50={R['reflex_bench']['batch1_ms_p50']:.1f} ms "
              f"p95={R['reflex_bench']['batch1_ms_p95']:.1f} ms ; "
              f"par lots : {R['reflex_bench']['batched_flows_per_s']:,.0f} flux/s")

    (OUT / "analytics_v2.json").write_text(json.dumps(R, indent=1), "utf-8")
    print("OK -> analytics_v2.json + fig_robust_fusion.png + fig_risk_coverage.png")


if __name__ == "__main__":
    main()
