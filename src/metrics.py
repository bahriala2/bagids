"""
BAg-IDS — Métriques d'évaluation, figures et export LaTeX.

Produit exactement les quantités attendues par les Tableaux II/III et
les figures du papier : accuracy, précision, rappel, F1, FPR opérationnel,
matrice de confusion, reliability diagram, balayage de tau.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

from .calibration import reliability_curve

logger = logging.getLogger("bag_ids.metrics")


def operational_fpr(y_true, y_pred, benign_idx: int) -> float:
    """FPR opérationnel : proportion de flux bénins classés comme attaque.
    FPR = FP / (FP + TN), la classe négative étant BENIGN."""
    benign_mask = y_true == benign_idx
    if benign_mask.sum() == 0:
        return float("nan")
    false_alarms = (y_pred[benign_mask] != benign_idx).sum()
    return float(false_alarms / benign_mask.sum())


def full_report(y_true, y_pred, benign_idx: int) -> dict:
    if len(y_true) == 0:
        # Couverture nulle à ce seuil tau (aucune décision certifiée) :
        # les métriques ne sont pas définies plutôt que de planter.
        nan = float("nan")
        return {
            "accuracy": nan,
            "precision_weighted": nan,
            "recall_weighted": nan,
            "f1_weighted": nan,
            "f1_macro": nan,
            "fpr_operational": nan,
        }
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "precision_weighted": float(
            precision_score(y_true, y_pred, average="weighted", zero_division=0)
        ),
        "recall_weighted": float(
            recall_score(y_true, y_pred, average="weighted", zero_division=0)
        ),
        "f1_weighted": float(
            f1_score(y_true, y_pred, average="weighted", zero_division=0)
        ),
        "f1_macro": float(
            f1_score(y_true, y_pred, average="macro", zero_division=0)
        ),
        "fpr_operational": operational_fpr(y_true, y_pred, benign_idx),
    }


# ---------------------------------------------------------------- figures

def plot_confusion_matrix(y_true, y_pred, class_names, out_path: Path):
    cm = confusion_matrix(y_true, y_pred, normalize="true")
    fig, ax = plt.subplots(figsize=(9, 7.5))
    im = ax.imshow(cm, cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(range(len(class_names)))
    ax.set_yticks(range(len(class_names)))
    ax.set_xticklabels(class_names, rotation=60, ha="right", fontsize=7)
    ax.set_yticklabels(class_names, fontsize=7)
    ax.set_xlabel("Classe prédite")
    ax.set_ylabel("Classe réelle")
    ax.set_title("BAg-IDS — Matrice de confusion normalisée (ensemble calibré)")
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            if cm[i, j] >= 0.01:
                ax.text(j, i, f"{cm[i, j]:.2f}", ha="center", va="center",
                        fontsize=5.5,
                        color="white" if cm[i, j] > 0.5 else "black")
    fig.colorbar(im, fraction=0.046, pad=0.04)
    fig.tight_layout()
    fig.savefig(out_path, dpi=300)
    plt.close(fig)
    logger.info("Figure sauvegardée : %s", out_path)


def plot_reliability(probs_before, probs_after, y_true, n_bins, out_path: Path):
    fig, ax = plt.subplots(figsize=(5.5, 5))
    for probs, label, marker in [
        (probs_before, "Avant calibration", "o"),
        (probs_after, "Après calibration (T-scaling)", "s"),
    ]:
        xs, ys, _ = reliability_curve(probs, y_true, n_bins)
        ax.plot(xs, ys, marker=marker, linewidth=1.2, markersize=4, label=label)
    ax.plot([0, 1], [0, 1], "k--", linewidth=0.8, label="Calibration parfaite")
    ax.set_xlabel("Confiance moyenne")
    ax.set_ylabel("Accuracy empirique")
    ax.set_title("Reliability diagram — ensemble BAg-IDS")
    ax.legend(fontsize=8)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=300)
    plt.close(fig)
    logger.info("Figure sauvegardée : %s", out_path)


def plot_tau_sweep(sweep_rows: list[dict], tau_default: float, out_path: Path):
    taus = [r["tau"] for r in sweep_rows]
    accs = [r["accuracy_accepted"] for r in sweep_rows]
    covs = [r["coverage"] for r in sweep_rows]
    fprs = [r["fpr_accepted"] for r in sweep_rows]

    fig, ax1 = plt.subplots(figsize=(6.5, 4.5))
    ax1.plot(taus, accs, "o-", color="tab:blue", label="Accuracy (acceptés)")
    ax1.plot(taus, covs, "s-", color="tab:green", label="Couverture")
    ax1.set_xlabel(r"Seuil de confiance $\tau$")
    ax1.set_ylabel("Accuracy / Couverture")
    ax1.axvline(tau_default, color="gray", linestyle=":",
                label=fr"$\tau$ = {tau_default} (défaut)")
    ax1.grid(alpha=0.3)

    ax2 = ax1.twinx()
    ax2.plot(taus, fprs, "^--", color="tab:red", label="FPR (acceptés)")
    ax2.set_ylabel("FPR opérationnel", color="tab:red")
    ax2.tick_params(axis="y", labelcolor="tab:red")

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, fontsize=8, loc="center left")
    ax1.set_title(r"Ablation : balayage du seuil de rejet $\tau$")
    fig.tight_layout()
    fig.savefig(out_path, dpi=300)
    plt.close(fig)
    logger.info("Figure sauvegardée : %s", out_path)


def plot_model_comparison(per_model: dict, ensemble: dict, out_path: Path):
    names = list(per_model.keys()) + ["BAg-IDS\n(ensemble)"]
    accs = [per_model[m]["accuracy"] * 100 for m in per_model] + [
        ensemble["accuracy"] * 100
    ]
    colors = ["#f0a202", "#5bc0eb", "#2ecc71", "#7d4fd3"]
    fig, ax = plt.subplots(figsize=(6, 4.2))
    bars = ax.bar(names, accs, color=colors[: len(names)])
    for bar, acc in zip(bars, accs):
        ax.text(bar.get_x() + bar.get_width() / 2, acc + 0.03,
                f"{acc:.2f}", ha="center", fontsize=9, fontweight="bold")
    ax.set_ylim(min(accs) - 1, 100.2)
    ax.set_ylabel("Accuracy (%)")
    ax.set_title("Modèles individuels vs ensemble calibré (MESURÉ)")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(out_path, dpi=300)
    plt.close(fig)
    logger.info("Figure sauvegardée : %s", out_path)


# ---------------------------------------------------------------- exports

def export_latex_table(per_model: dict, ensemble: dict, out_path: Path):
    """Génère les lignes LaTeX du Tableau II — toutes MESURÉES."""

    def row(name, r):
        return (
            f"{name} & {r['accuracy']*100:.2f} & "
            f"{r['precision_weighted']*100:.2f} & "
            f"{r['recall_weighted']*100:.2f} & "
            f"{r['f1_weighted']*100:.2f} & "
            f"{r['fpr_operational']*100:.3f} \\\\"
        )

    lines = [
        "% Tableau II — généré automatiquement par run_fusion_experiment.py",
        "% Toutes les valeurs sont MESURÉES (plus aucune projection).",
        "\\begin{tabular}{lccccc}",
        "\\toprule",
        "Model & Acc. & Prec. & Recall & F1 & FPR \\\\",
        "\\midrule",
    ]
    for name, r in per_model.items():
        lines.append(row(f"{name.upper()} (measured)", r))
    lines.append("\\midrule")
    lines.append(row("\\textbf{BAg-IDS ensemble (measured)}", ensemble))
    lines += ["\\bottomrule", "\\end{tabular}"]
    out_path.write_text("\n".join(lines), encoding="utf-8")
    logger.info("Tableau LaTeX exporté : %s", out_path)


def save_json(obj: dict, out_path: Path):
    out_path.write_text(json.dumps(obj, indent=2, ensure_ascii=False),
                        encoding="utf-8")
    logger.info("Résultats JSON : %s", out_path)
