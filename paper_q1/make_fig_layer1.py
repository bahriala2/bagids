"""
BAg-IDS – Figure « Layer 1 : détection réflexe » : pipeline par flux,
de x (78 features) au verdict ternaire, en montrant le ROLE de chaque
étage (détecteurs divers -> confiance honnête -> fusion trust-aware ->
porte de rejet). Bandeau : par flux, millisecondes, ~37 500 flux/s.

    python paper_q1/make_fig_layer1.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = Path("paper_q1/figures/layer1_reflex.png")

C_TXT = "#16223a"; C_MUT = "#44546e"
C_B = "#4f8cff"; C_BBG = "#eaf2ff"
C_G = "#27ae60"; C_GBG = "#eafaf0"
C_A = "#d64545"; C_ABG = "#fdeaea"
C_O = "#e08a00"; C_OBG = "#fff4e0"

fig, ax = plt.subplots(figsize=(12.4, 6.4))
ax.set_xlim(0, 12.4); ax.set_ylim(0, 6.4); ax.axis("off")


def box(x, y, w, h, fc, ec, title, lines=(), ts=9.2, ls=7.3, lw=1.5,
        tdy=0.24, lh=0.23, mono=False, tc=None):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.05",
        linewidth=lw, edgecolor=ec, facecolor=fc, zorder=2))
    ax.text(x + w / 2, y + h - tdy, title, ha="center", va="center",
            fontsize=ts, fontweight="bold", color=tc or C_TXT, zorder=3)
    for k, ln in enumerate(lines):
        ax.text(x + w / 2, y + h - tdy - 0.28 - k * lh, ln, ha="center",
                va="center", fontsize=ls, color=C_MUT, zorder=3,
                family="monospace" if mono else "sans-serif")


def arrow(p0, p1, color=C_MUT, lw=2.0, rad=0.0, style="-|>"):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle=style, mutation_scale=13,
        linewidth=lw, color=color, zorder=5,
        connectionstyle=f"arc3,rad={rad}"))


def role(x, y, txt, color=C_MUT):
    ax.text(x, y, txt, ha="center", va="center", fontsize=7.0, color=color,
            style="italic", zorder=4)


# titre de rôle (haut)
ax.text(6.2, 6.15, "Layer 1 – Reflex detection: turn every raw flow into a "
        "trustworthy verdict, cheaply", ha="center", fontsize=11.5,
        fontweight="bold", color=C_TXT)

yb = 3.55        # ligne de base des boîtes principales
h = 1.75

# 1. flux entrant
box(0.20, yb, 1.55, h, "#f2f5fa", "#8ea0bf", "Network flow",
    ["x ∈ R⁷⁸", "", "thousands", "per second"], ts=8.8, ls=7.4)

# 2. trois détecteurs
box(2.05, yb + 0.02, 2.5, h + 0.30, C_BBG, C_B, "3 detectors",
    ["RNN · CNN · DNN", "heterogeneous", "→ partially", "uncorrelated errors",
     "P(c | x, Mₘ)"], ts=8.8, ls=7.2)
role(3.30, yb - 0.28, "diversity")

# 3. calibration
box(4.85, yb, 1.75, h, C_BBG, C_B, "Calibration",
    ["temperature", "scaling  Tₘ", "→ honest", "confidence"], ts=8.8, ls=7.4)
role(5.72, yb - 0.28, "comparable scores")

# 4. CWC fusion
box(6.90, yb, 2.15, h, "#dcebff", C_B, "CWC fusion",
    ["weighted opinion", "pool  wₘ ∝ precₘ", "→ one trust-aware", "posterior",
     "self-excludes a", "poisoned member"], ts=8.8, ls=7.05, lh=0.215)
role(7.97, yb - 0.28, "robust consensus")

# 5. porte de rejet
box(9.35, yb, 1.75, h, C_BBG, C_B, "Reject gate τ",
    ["conf = maxₖ P̃", "", "≥ τ ? accept", "< τ ? reject"], ts=8.8, ls=7.4)
role(10.22, yb - 0.28, "abstain if unsure")

# flèches du pipeline
arrow((1.75, yb + h / 2), (2.05, yb + h / 2))
arrow((4.55, yb + h / 2), (4.85, yb + h / 2))
arrow((6.60, yb + h / 2), (6.90, yb + h / 2))
arrow((9.05, yb + h / 2), (9.35, yb + h / 2))

# 6. trois sorties (droite)
ox = 11.25
box(ox, yb + 1.30, 1.05, 0.66, C_GBG, C_G, "BENIGN", ["pass"], ts=7.8,
    ls=7.0, tdy=0.26, tc=C_G)
box(ox, yb + 0.52, 1.05, 0.66, C_ABG, C_A, "ATTACK", ["→ L2 / L3"], ts=7.8,
    ls=7.0, tdy=0.26, tc=C_A)
box(ox, yb - 0.26, 1.05, 0.66, C_OBG, C_O, "REJECT", ["→ drift"], ts=7.8,
    ls=7.0, tdy=0.26, tc=C_O)
arrow((11.10, yb + h / 2), (ox, yb + 1.63), color=C_G, lw=1.6, rad=0.15)
arrow((11.10, yb + h / 2), (ox, yb + 0.85), color=C_A, lw=1.8)
arrow((11.10, yb + h / 2), (ox, yb + 0.07), color=C_O, lw=1.6, rad=-0.15)

# bandeau bas : propriété opérationnelle
box(0.20, 1.25, 12.10, 1.35, "#eef4ff", C_B, "", (), lw=1.3)
ax.text(6.25, 2.28, "Operational role of the layer", ha="center",
        fontsize=9.2, fontweight="bold", color=C_B)
ax.text(6.25, 1.78, "Runs on EVERY flow, in the millisecond range "
        "(~37,500 flows/s on commodity CPU), and NEVER blocks on the network "
        "or on an external model.\nOnly the ATTACK verdict – a small fraction "
        "of traffic – is escalated to the costly deliberation (Layer 2) and "
        "consensus (Layer 3); REJECT feeds drift monitoring.",
        ha="center", va="center", fontsize=8.0, color=C_TXT)

# étiquettes verdicts au-dessus des sorties
ax.text(ox + 0.52, yb + 2.08, "verdict", ha="center", fontsize=7.2,
        color=C_MUT, style="italic")

fig.savefig(OUT, dpi=300, bbox_inches="tight", facecolor="white")
print("OK ->", OUT)
