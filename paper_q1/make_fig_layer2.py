"""
BAg-IDS – Figure « Layer 2 : délibération » : montre le ROLE de la couche
– réserver le raisonnement LLM (coûteux) aux quelques événements qui le
méritent. Deux voies : délibération one-shot du Sentinel, et boucle
agentique multi-étapes de l'Investigator ; chaîne de repli gracieux.

    python paper_q1/make_fig_layer2.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = Path("paper_q1/figures/layer2_deliberation.png")

C_TXT = "#16223a"; C_MUT = "#44546e"
C_P = "#7d4fd3"; C_PBG = "#f0eafc"
C_A = "#d64545"; C_ABG = "#fdeaea"
C_G = "#27ae60"; C_GBG = "#eafaf0"
C_O = "#e08a00"

fig, ax = plt.subplots(figsize=(12.4, 7.0))
ax.set_xlim(0, 12.4); ax.set_ylim(0, 7.0); ax.axis("off")


def box(x, y, w, h, fc, ec, title, lines=(), ts=9.2, ls=7.3, lw=1.5,
        tdy=0.24, lh=0.23, tc=None):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.05",
        linewidth=lw, edgecolor=ec, facecolor=fc, zorder=2))
    ax.text(x + w / 2, y + h - tdy, title, ha="center", va="center",
            fontsize=ts, fontweight="bold", color=tc or C_TXT, zorder=3)
    for k, ln in enumerate(lines):
        ax.text(x + w / 2, y + h - tdy - 0.28 - k * lh, ln, ha="center",
                va="center", fontsize=ls, color=C_MUT, zorder=3)


def arrow(p0, p1, color=C_MUT, lw=1.9, rad=0.0, style="-|>"):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle=style, mutation_scale=12,
        linewidth=lw, color=color, zorder=5,
        connectionstyle=f"arc3,rad={rad}"))


def lab(x, y, txt, color=C_MUT, fs=7.2):
    ax.text(x, y, txt, ha="center", va="center", fontsize=fs, color=color,
            style="italic", zorder=6,
            bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none",
                      alpha=0.9))


ax.text(6.2, 6.75, "Layer 2 – Deliberation: reserve costly LLM reasoning for "
        "the few events that truly need judgement", ha="center",
        fontsize=11.3, fontweight="bold", color=C_TXT)

# ---- déclencheur (gauche)
box(0.20, 4.35, 2.15, 1.5, C_ABG, C_A, "Trigger (rare)",
    ["certified ATTACK", "or rejection burst", "", "rate-limited:",
     "few / minute"], ts=8.8, ls=7.2, tc=C_A)
ax.text(1.27, 3.95, "NOT every flow", ha="center", fontsize=7.2,
        color=C_A, style="italic")

# ---- voie A : délibération one-shot du Sentinel
box(2.85, 4.75, 3.55, 1.5, C_PBG, C_P, "Sentinel deliberation  (single-shot)",
    ["compact event summary →  LLM →", "{ severity, rationale,",
     "  recommended actions }", "one prompt, one structured answer"],
    ts=8.6, ls=7.2)
lab(2.62, 5.5, "A", color=C_P, fs=8.5)

# ---- voie B : boucle agentique de l'Investigator
box(2.85, 2.30, 5.9, 2.05, C_PBG, C_P,
    "Investigator  (multi-step agentic loop)", (), ts=8.8)
# 4 étapes en cercle/ligne
steps = [("perceive", "frame the\ncertified attack"),
         ("reason", "decide which\ntool to use"),
         ("act (tools)", "query_ledger ·\ncorrelate · memory"),
         ("reflect", "campaign? →\ntriage + response")]
sx = 3.05; sw = 1.36
for k, (t, d) in enumerate(steps):
    x = sx + k * (sw + 0.10)
    ax.add_patch(FancyBboxPatch((x, 2.50), sw, 1.15,
        boxstyle="round,pad=0.015,rounding_size=0.05", linewidth=1.2,
        edgecolor=C_P, facecolor="white", zorder=3))
    ax.text(x + sw / 2, 3.45, f"{k+1}. {t}", ha="center", va="center",
            fontsize=7.6, fontweight="bold", color=C_P, zorder=4)
    ax.text(x + sw / 2, 2.95, d, ha="center", va="center", fontsize=6.7,
            color=C_MUT, zorder=4)
    if k < 3:
        arrow((x + sw, 3.07), (x + sw + 0.10, 3.07), color=C_P, lw=1.4)
# boucle de retour
arrow((sx + 3 * (sw + 0.10) + sw / 2, 2.50),
      (sx + sw / 2, 2.50), color=C_P, lw=1.2, rad=0.35, style="-|>")
ax.text(sx + 2 * sw, 2.36, "loop until concluded", ha="center", fontsize=6.6,
        color=C_P, style="italic")
lab(2.62, 4.10, "B", color=C_P, fs=8.5)

arrow((2.35, 5.35), (2.85, 5.35), color=C_A, lw=1.8)
arrow((2.35, 4.7), (2.85, 3.6), color=C_A, lw=1.8, rad=-0.1)

# ---- chaîne de backends LLM (droite haut)
box(6.65, 4.75, 3.05, 1.5, "white", C_P, "LLM backends",
    ["OpenRouter (cloud)", "↓ if unreachable", "LM Studio (local)",
     "↓ if unreachable", "rule-based fallback"], ts=8.6, ls=7.1, lh=0.215)
arrow((6.40, 5.5), (6.65, 5.5), color=C_P, lw=1.6)
arrow((8.75, 4.35), (8.18, 4.35), color=C_P, lw=1.4, rad=0.0)
lab(9.9, 4.35, "graceful\ndegradation", color=C_P, fs=6.8)

# ---- sorties : sévérité/actions + ancrage
box(9.95, 4.75, 2.30, 1.5, C_GBG, C_G, "Structured output",
    ["severity (low→critical)", "rationale", "actions (block, isolate,",
     "  rate-limit, notify…)"], ts=8.4, ls=7.0, tc=C_G)
arrow((6.40, 5.5), (9.95, 5.5), color=C_MUT, lw=1.2, rad=-0.18)

box(9.0, 2.55, 3.25, 1.05, C_GBG, C_G,
    "Incident report + full trace", ["anchored on-chain →",
    "even the agent's reasoning", "is auditable"], ts=8.2, ls=7.0, tc=C_G)
arrow((8.75, 3.1), (9.0, 3.1), color=C_G, lw=1.6)

# ---- bandeau bas : rôle / propriété
box(0.20, 0.30, 12.05, 1.55, "#f6f1fd", C_P, "", (), lw=1.3)
ax.text(6.22, 1.55, "Why this layer is affordable – and safe",
        ha="center", fontsize=9.2, fontweight="bold", color=C_P)
ax.text(6.22, 0.92, "Event-triggered and rate-limited, the LLM sees a curated "
        "stream (a few events/min), never line-rate traffic – so agentic "
        "reasoning is cheap.\nIt runs OFF the deterministic critical path: it "
        "enriches an already-certified decision and never alters "
        "certification, so autonomy and reproducibility hold even when no LLM "
        "is reachable.", ha="center", va="center", fontsize=8.0, color=C_TXT)

fig.savefig(OUT, dpi=300, bbox_inches="tight", facecolor="white")
print("OK ->", OUT)
