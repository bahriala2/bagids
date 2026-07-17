"""
BAg-IDS – Figure 1 : vue d'ensemble de l'architecture à 4 couches et
chemin d'une attaque certifiée. Produit un PNG 300 dpi.

    python paper_q1/make_fig1.py
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = Path("paper_q1/figures/architecture_overview.png")

# Palette (cohérente avec les figures de résultats / la console)
C_BG = "#ffffff"
C_L1 = "#eaf2ff"; C_L1E = "#4f8cff"
C_L2 = "#f0 eafc".replace(" ", ""); C_L2E = "#7d4fd3"
C_L3 = "#eafaf0"; C_L3E = "#2ecc71"
C_L4 = "#fff4e0"; C_L4E = "#f0a202"
C_TXT = "#16223a"; C_MUT = "#5a6b86"


def box(ax, x, y, w, h, fc, ec, title, lines, title_size=11, lw=1.6):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.06",
        linewidth=lw, edgecolor=ec, facecolor=fc, zorder=2))
    ax.text(x + w / 2, y + h - 0.22, title, ha="center", va="top",
            fontsize=title_size, fontweight="bold", color=C_TXT, zorder=3)
    for i, ln in enumerate(lines):
        ax.text(x + w / 2, y + h - 0.52 - i * 0.28, ln, ha="center", va="top",
                fontsize=8.5, color=C_MUT, zorder=3)


def small(ax, x, y, w, h, fc, ec, label):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.015,rounding_size=0.05",
        linewidth=1.2, edgecolor=ec, facecolor=fc, zorder=3))
    ax.text(x + w / 2, y + h / 2, label, ha="center", va="center",
            fontsize=8.5, color=C_TXT, zorder=4)


def arrow(ax, p0, p1, color=C_MUT, style="-|>", lw=1.8, rad=0.0):
    ax.add_patch(FancyArrowPatch(
        p0, p1, arrowstyle=style, mutation_scale=13, linewidth=lw,
        color=color, zorder=5,
        connectionstyle=f"arc3,rad={rad}"))


def layer_band(ax, y, h, ec, tag):
    # Cadre pointillé de la couche ; l'étiquette est placée verticalement
    # dans la gouttière gauche (x<0.7, libre de toute boîte).
    ax.add_patch(FancyBboxPatch(
        (0.62, y), 12.25, h, boxstyle="round,pad=0.0,rounding_size=0.05",
        linewidth=1.0, edgecolor=ec, facecolor="none",
        linestyle=(0, (5, 3)), zorder=1, alpha=0.55))
    ax.text(0.4, y + h / 2, tag, ha="center", va="center", fontsize=8.5,
            fontweight="bold", color=ec, zorder=6, rotation=90)


def main():
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(9.2, 8.4))
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 12)
    ax.axis("off")

    # ---- bandes de couches
    layer_band(ax, 9.2, 2.5, C_L1E, "Layer 1 – Reflex detection")
    layer_band(ax, 6.7, 2.2, C_L2E, "Layer 2 – Deliberation")
    layer_band(ax, 3.1, 3.3, C_L3E, "Layer 3 – Consensus (blockchain)")
    layer_band(ax, 0.5, 2.3, C_L4E, "Layer 4 – Human-in-the-loop")

    # ---- Layer 1 : Sentinel + ensemble
    box(ax, 0.7, 9.45, 4.9, 2.05, C_L1, C_L1E, "Sentinel agent",
        ["Calibrated ensemble + Conscious Weighted Consensus",
         "Reject region (confidence < τ)"])
    small(ax, 1.0, 9.62, 1.15, 0.55, "#ffffff", C_L1E, "RNN")
    small(ax, 2.25, 9.62, 1.15, 0.55, "#ffffff", C_L1E, "CNN")
    small(ax, 3.5, 9.62, 1.15, 0.55, "#ffffff", C_L1E, "DNN")
    ax.text(8.8, 10.75, "network flows", ha="center", fontsize=9,
            style="italic", color=C_MUT)
    arrow(ax, (6.6, 10.5), (5.65, 10.5))  # flows into sentinel (right->left top)
    # verdicts out of layer 1
    ax.text(9.9, 10.15, "benign / rejected\n→ logged, drift signal",
            ha="left", va="center", fontsize=8, color=C_MUT)
    small(ax, 6.6, 9.7, 2.9, 0.75, C_L1, C_L1E, "verdict = ATTACK (certified)")

    # ---- Layer 2 : Deliberation (LLM) + Investigator (agentique)
    box(ax, 4.55, 6.95, 4.45, 1.75, "#f3eafc", C_L2E,
        "Deliberative layer (LLM)",
        ["Severity + rationale + actions",
         "OpenRouter / LM Studio / rules fallback"])
    arrow(ax, (8.05, 9.7), (7.2, 8.7), color=C_L2E)   # attack -> deliberation
    ax.text(8.35, 9.15, "salient\nevent", ha="left", va="center", fontsize=7.5,
            color=C_L2E)
    # Investigator : agent agentique (outils + mémoire), enquête post-cert.
    box(ax, 0.9, 6.95, 3.35, 1.75, "#f3eafc", C_L2E, "Investigator agent",
        ["agentic: tools + memory", "multi-step investigation",
         "report anchored on-chain"], title_size=10)
    arrow(ax, (4.55, 7.82), (4.25, 7.82), color=C_L2E)  # delib -> investigator
    ax.text(0.95, 6.72, "reads ledger · detects campaigns", ha="left",
            va="top", fontsize=6.5, color=C_MUT)
    # Data Scientist : surveillance de dérive (consomme le flux REJECT)
    box(ax, 9.3, 6.95, 3.2, 1.75, "#f3eafc", C_L2E, "Data Scientist agent",
        ["monitors rejection rate", "drift alarm → recommend",
         "recalibration / retraining"], title_size=10)
    arrow(ax, (10.9, 9.95), (10.9, 8.7), color=C_L2E, lw=1.4)
    ax.text(11.05, 9.35, "drift signal", ha="left", va="center",
            fontsize=7.5, color=C_L2E)

    # ---- Layer 3 : Notaries + chaincode
    box(ax, 0.7, 3.35, 5.0, 2.8, C_L3, C_L3E, "Notary agents (leader + peers)",
        ["Independent re-validation, Ed25519 signed votes",
         "+ optional LLM advisory (non-decisional)"])
    small(ax, 1.0, 3.6, 1.35, 0.6, "#ffffff", C_L3E, "notary-01")
    small(ax, 2.5, 3.6, 1.35, 0.6, "#ffffff", C_L3E, "notary-02")
    small(ax, 4.0, 3.6, 1.35, 0.6, "#ffffff", C_L3E, "notary-03")
    box(ax, 6.1, 3.35, 6.4, 2.8, "#eafaf0", C_L3E,
        "validateVote chaincode  –  Hyperledger Fabric",
        ["signature check · anti-replay · quorum (k/n)",
         "→ ALERT_CERTIFIED (tamper-evident, 2 orgs)",
         "RecordGovernance (admin actions anchored)"])
    arrow(ax, (6.5, 7.0), (3.2, 6.15), color=C_L3E, rad=-0.15)  # deliberation->notary
    ax.text(4.6, 6.75, "signed alert", ha="center", fontsize=7.5, color=C_L3E)
    arrow(ax, (5.7, 4.75), (6.1, 4.75), color=C_L3E)            # notary->chaincode
    arrow(ax, (6.1, 4.2), (5.7, 4.2), color=C_L3E)              # chaincode->notary (certified)

    # ---- Layer 4 : HITL + Executor
    box(ax, 0.7, 0.7, 6.0, 1.9, C_L4, C_L4E,
        "Human-in-the-loop console (optional, governed)",
        ["Dashboard · Incidents · Audit · Governance",
         "Roles: admin / analyst / reader – toggle on/off"])
    box(ax, 7.4, 0.7, 5.1, 1.9, "#fff4e0", C_L4E, "Executor agent",
        ["Remediation: block / rate-limit / notify",
         "gated by HITL approval when enabled"])
    arrow(ax, (3.4, 3.35), (3.4, 2.6), color=C_L4E)   # certified -> HITL
    ax.text(3.62, 2.98, "certified alert", ha="left", va="center",
            fontsize=7.5, color=C_L4E)
    arrow(ax, (6.7, 1.65), (7.4, 1.65), color=C_L4E)  # HITL approve -> executor
    ax.text(7.05, 1.9, "approve", ha="center", fontsize=7.5, color=C_L4E)
    # autonomous path (HITL off) : chaincode -> executor directly
    arrow(ax, (9.6, 3.35), (9.9, 2.6), color=C_MUT, style="-|>", lw=1.3)
    ax.text(10.1, 2.98, "autonomous\n(HITL off)", ha="left", va="center",
            fontsize=7, color=C_MUT)

    fig.suptitle("BAg-IDS: four-layer architecture and the path of a "
                 "certified attack", fontsize=12.5, fontweight="bold",
                 color=C_TXT, y=0.975)
    fig.tight_layout(rect=(0, 0, 1, 0.96))
    fig.savefig(OUT, dpi=300, facecolor=C_BG)
    plt.close(fig)
    print("Écrit :", OUT)


if __name__ == "__main__":
    main()
