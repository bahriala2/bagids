"""
BAg-IDS – Figure « comparaison des agents » : matrice 5 colonnes
(un agent par colonne) × 6 lignes (mission, perçoit, décide, agit,
usage du LLM, empreinte on-chain). Facilite la comparaison des rôles.

    python paper_q1/make_fig_agents.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

OUT = Path("paper_q1/figures/agents_comparison.png")

C_TXT = "#16223a"; C_MUT = "#44546e"
AGENTS = [
    ("Sentinel", ":8001", "#4f8cff", "#eaf2ff", [
        ("Mission", "per-flow detection\n(reflex layer)"),
        ("Perceives", "network flows\n(78 features)"),
        ("Decides", "CWC verdict +\nreject gate (τ)"),
        ("Acts", "signed alert +\ndeliberation summary"),
        ("LLM use", "event-triggered\nseverity judgement"),
        ("On-chain", "RecordAlert\n(every alert)"),
    ]),
    ("Notary ×3", ":8002 /12 /22", "#27ae60", "#eafaf0", [
        ("Mission", "collective\ncertification"),
        ("Perceives", "signed alerts\nfrom Sentinel"),
        ("Decides", "consistency\nre-validation → vote"),
        ("Acts", "Ed25519-signed\nvote (quorum 2/3)"),
        ("LLM use", "advisory opinion\n(non-decisional)"),
        ("On-chain", "ValidateVote,\nALERT_CERTIFIED"),
    ]),
    ("Executor", ":8003", "#e08a00", "#fff4e0", [
        ("Mission", "remediation of\ncertified attacks"),
        ("Perceives", "certified (+ approved)\nalerts"),
        ("Decides", "action mapping\nper severity"),
        ("Acts", "block / rate-limit /\nisolate / notify"),
        ("LLM use", "none\n(deterministic)"),
        ("On-chain", "execution\nrecords"),
    ]),
    ("Data Scientist", ":8004", "#0e8fa3", "#e8f7fa", [
        ("Mission", "model-health &\ndrift guardian"),
        ("Perceives", "REJECT stream,\nverdict statistics"),
        ("Decides", "drift alarm\n(rolling reject rate)"),
        ("Acts", "recommend recalib. /\nretraining"),
        ("LLM use", "none\n(statistical)"),
        ("On-chain", "– (reports to\nsupervision)"),
    ]),
    ("Investigator", ":8005", "#7d4fd3", "#f0eafc", [
        ("Mission", "triage & campaign\ndetection"),
        ("Perceives", "certified incidents +\nledger history"),
        ("Decides", "agentic loop:\nreason → act (tools)"),
        ("Acts", "incident report,\ntriage severity"),
        ("LLM use", "multi-step reasoning\n(rules fallback)"),
        ("On-chain", "report anchored\n(auditable reasoning)"),
    ]),
]
ROWS = ["Mission", "Perceives", "Decides", "Acts", "LLM use", "On-chain"]

CW, CH, HH = 2.42, 0.86, 0.62          # largeur colonne, hauteur cellule/entête
GX, GY = 1.30, 0.20                     # gouttière gauche / marge basse
FW = GX + 5 * (CW + 0.12) + 0.15
FH = GY + HH + 6 * (CH + 0.06) + 0.55

fig, ax = plt.subplots(figsize=(FW, FH))
ax.set_xlim(0, FW); ax.set_ylim(0, FH); ax.axis("off")

top = FH - 0.55
# étiquettes de lignes (gouttière)
for r, lab in enumerate(ROWS):
    y = top - HH - 0.06 - r * (CH + 0.06) - CH / 2
    ax.text(GX - 0.12, y, lab, ha="right", va="center", fontsize=9,
            fontweight="bold", color=C_MUT)

for c, (name, port, ec, fc, rows) in enumerate(AGENTS):
    x = GX + c * (CW + 0.12)
    # entête
    ax.add_patch(FancyBboxPatch((x, top - HH), CW, HH,
        boxstyle="round,pad=0.015,rounding_size=0.05",
        linewidth=1.8, edgecolor=ec, facecolor=ec, zorder=2))
    ax.text(x + CW / 2, top - HH / 2 + 0.09, name, ha="center", va="center",
            fontsize=10.5, fontweight="bold", color="white", zorder=3)
    ax.text(x + CW / 2, top - HH / 2 - 0.17, port, ha="center", va="center",
            fontsize=7.5, color="white", zorder=3, family="monospace")
    # cellules
    for r, (_, txt) in enumerate(rows):
        y = top - HH - 0.06 - r * (CH + 0.06) - CH
        ax.add_patch(FancyBboxPatch((x, y), CW, CH,
            boxstyle="round,pad=0.015,rounding_size=0.04",
            linewidth=1.1, edgecolor=ec, facecolor=fc, zorder=2))
        ax.text(x + CW / 2, y + CH / 2, txt, ha="center", va="center",
                fontsize=7.6, color=C_TXT, zorder=3)

fig.suptitle("The five BAg-IDS agents – roles compared",
             fontsize=12, fontweight="bold", color=C_TXT, y=0.985)
fig.savefig(OUT, dpi=300, bbox_inches="tight", facecolor="white")
print("OK ->", OUT)
