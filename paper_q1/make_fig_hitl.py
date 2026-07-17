"""
BAg-IDS – Figure « Layer 4 : le rôle de l'humain » :
  (a) échelle des trois rôles (reader ⊂ analyst ⊂ admin),
  (b) mode supervisé vs mode autonome (les deux chemins comparés),
  (c) bandeau responsabilité : chaque action humaine = transaction
      signée ancrée on-chain (RecordGovernance).

    python paper_q1/make_fig_hitl.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = Path("paper_q1/figures/hitl_layer.png")

C_TXT = "#16223a"; C_MUT = "#44546e"
C_O = "#e08a00"; C_OBG = "#fff4e0"
C_G = "#27ae60"; C_GBG = "#eafaf0"
C_R = "#d64545"
C_B = "#4f8cff"


def box(ax, x, y, w, h, fc, ec, title, lines=(), ts=9.3, ls=7.5, lw=1.5,
        tdy=0.22, lh=0.235, tc=None):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.05",
        linewidth=lw, edgecolor=ec, facecolor=fc, zorder=2))
    ax.text(x + w / 2, y + h - tdy, title, ha="center", va="center",
            fontsize=ts, fontweight="bold", color=tc or C_TXT, zorder=3)
    for k, ln in enumerate(lines):
        ax.text(x + w / 2, y + h - tdy - 0.29 - k * lh, ln, ha="center",
                va="center", fontsize=ls, color=C_MUT, zorder=3)


def arrow(ax, p0, p1, color=C_MUT, lw=1.7, rad=0.0, ls="-", style="-|>"):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle=style, mutation_scale=12,
        linewidth=lw, color=color, zorder=6, linestyle=ls,
        connectionstyle=f"arc3,rad={rad}"))


def lab(ax, x, y, txt, color=C_MUT, fs=7.3):
    ax.text(x, y, txt, ha="center", va="center", fontsize=fs, color=color,
            zorder=7, style="italic",
            bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none",
                      alpha=0.9))


fig, ax = plt.subplots(figsize=(11.4, 6.9))
ax.set_xlim(0, 11.4); ax.set_ylim(0, 6.9); ax.axis("off")

# ============================== (a) échelle des rôles (gauche)
ax.text(2.15, 6.45, "(a) Operator roles – capability ladder",
        ha="center", fontsize=10, fontweight="bold", color=C_TXT)
box(ax, 0.30, 4.55, 3.7, 1.55, "#eaf2ff", C_B, "READER   –   observe",
    ["live dashboard, health of the 5 agents",
     "incidents + agentic investigation traces",
     "ledger audit view (immutable record)"], ls=7.3)
box(ax, 0.30, 2.70, 3.7, 1.55, C_GBG, C_G, "ANALYST   –   + decide",
    ["everything READER can do, plus:",
     "approval queue: approve / reject",
     "high- & critical-severity remediations"], ls=7.3)
box(ax, 0.30, 0.85, 3.7, 1.55, C_OBG, C_O, "ADMIN   –   + govern",
    ["everything ANALYST can do, plus:",
     "toggle supervision ON / OFF",
     "tune τ, quorum, severity policy"], ls=7.3)
arrow(ax, (2.15, 4.55), (2.15, 4.25), lw=1.4)
arrow(ax, (2.15, 2.70), (2.15, 2.40), lw=1.4)

# ============================== (b) deux modes côte à côte (droite)
ax.text(7.85, 6.45, "(b) The two operating modes – where the human sits",
        ha="center", fontsize=10, fontweight="bold", color=C_TXT)

# mode supervisé
ax.add_patch(FancyBboxPatch((4.55, 3.55), 6.55, 2.55,
    boxstyle="round,pad=0.02,rounding_size=0.05", linewidth=1.2,
    edgecolor=C_O, facecolor="none", linestyle=(0, (4, 3)), zorder=1))
ax.text(4.75, 5.85, "SUPERVISED  (HITL on)", fontsize=8.6,
        fontweight="bold", color=C_O, ha="left")
box(ax, 4.75, 4.45, 1.7, 0.85, C_GBG, C_G, "ALERT_", ["CERTIFIED"],
    ts=8, ls=8, tdy=0.28)
box(ax, 6.75, 4.45, 1.55, 0.85, "white", C_O, "severity ≥",
    ["gate level ?"], ts=8, ls=7.6, tdy=0.28)
box(ax, 8.60, 4.45, 1.35, 0.85, C_OBG, C_O, "approval", ["queue"],
    ts=8, ls=7.6, tdy=0.28)
box(ax, 9.55, 3.68, 1.55, 0.62, "white", C_G, "Executor acts", (), ts=7.8,
    tdy=0.31)
arrow(ax, (6.45, 4.87), (6.75, 4.87), lw=1.5)
arrow(ax, (8.30, 4.87), (8.60, 4.87), lw=1.5)
lab(ax, 8.45, 5.12, "yes", fs=6.8)
arrow(ax, (7.5, 4.45), (7.5, 4.0), lw=1.3)
arrow(ax, (7.5, 4.0), (9.55, 4.0), lw=1.3)
lab(ax, 7.95, 4.18, "below gate: direct", fs=6.6)
# décision humaine
lab(ax, 9.27, 5.62, "ANALYST decides", color=C_O, fs=7.4)
arrow(ax, (9.27, 5.48), (9.27, 5.32), color=C_O, lw=1.6)
arrow(ax, (9.60, 4.45), (9.95, 4.32), color=C_G, lw=1.7)
ax.text(10.25, 4.62, "approve", fontsize=6.9, color=C_G, ha="center")
ax.text(8.55, 4.22, "reject → cancelled", fontsize=6.8, color=C_R,
        ha="center")

# mode autonome
ax.add_patch(FancyBboxPatch((4.55, 1.75), 6.55, 1.45,
    boxstyle="round,pad=0.02,rounding_size=0.05", linewidth=1.2,
    edgecolor=C_MUT, facecolor="none", linestyle=(0, (4, 3)), zorder=1))
ax.text(4.75, 2.95, "AUTONOMOUS  (HITL off – one governed toggle)",
        fontsize=8.6, fontweight="bold", color=C_MUT, ha="left")
box(ax, 4.75, 1.95, 1.7, 0.85, C_GBG, C_G, "ALERT_", ["CERTIFIED"],
    ts=8, ls=8, tdy=0.28)
box(ax, 8.90, 1.95, 1.9, 0.85, "white", C_G, "Executor acts",
    ["immediately"], ts=8, ls=7.6, tdy=0.28)
arrow(ax, (6.45, 2.37), (8.90, 2.37), lw=1.7)
lab(ax, 7.68, 2.58, "no human on the path", fs=6.9)
ax.text(7.85, 1.52, "fail-open: if the console is unreachable, agents fall "
        "back to autonomous action – oversight is a control surface, not a "
        "single point of failure", ha="center", fontsize=6.8, color=C_MUT,
        style="italic")

# ============================== (c) bandeau responsabilité
box(ax, 0.30, 0.06, 10.80, 0.62, "#f2f5fa", "#8ea0bf", "",
    (), lw=1.2)
ax.text(5.7, 0.37, "(c) Accountability: every human action – approval, "
        "rejection, toggle, τ/quorum change – is a signed transaction "
        "anchored on-chain\n(RecordGovernance): the administrator is "
        "auditable.", ha="center", va="center", fontsize=7.6, color=C_TXT,
        fontweight="bold")

fig.suptitle("Layer 4 – the human's role: what each operator may do, and "
             "where the human sits on the decision path",
             fontsize=11.5, fontweight="bold", color=C_TXT, y=0.985)
fig.savefig(OUT, dpi=300, bbox_inches="tight", facecolor="white")
print("OK ->", OUT)
