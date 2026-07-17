"""
BAg-IDS – Figure 2 : architecture détaillée, reproductible, couche par
couche (modèles exacts, calibration, CWC, τ, agents, chaincode, HITL).

    python paper_q1/make_fig2.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

OUT = Path("paper_q1/figures/architecture_detailed.png")

C_TXT = "#16223a"; C_MUT = "#49597a"
C_L1 = "#eaf2ff"; C_L1E = "#4f8cff"
C_L2 = "#f0eafc"; C_L2E = "#7d4fd3"
C_L3 = "#eafaf0"; C_L3E = "#27ae60"
C_L4 = "#fff4e0"; C_L4E = "#e08a00"
C_DP = "#f2f5fa"; C_DPE = "#8ea0bf"
C_RED = "#d64545"

FW, FH = 13.6, 12.2
fig, ax = plt.subplots(figsize=(FW, FH))
ax.set_xlim(0, FW); ax.set_ylim(0, FH)
ax.axis("off")


def box(x, y, w, h, fc, ec, title, lines, ts=9.5, ls=7.6, lh=0.245,
        lw=1.5, mono=False, title_dy=0.20):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.05",
        linewidth=lw, edgecolor=ec, facecolor=fc, zorder=2))
    ax.text(x + w / 2, y + h - title_dy, title, ha="center", va="center",
            fontsize=ts, fontweight="bold", color=C_TXT, zorder=3)
    for k, ln in enumerate(lines):
        ax.text(x + w / 2, y + h - title_dy - 0.30 - k * lh, ln,
                ha="center", va="center", fontsize=ls, color=C_MUT, zorder=3,
                family="monospace" if mono else "sans-serif")


def band(y, h, ec, tag, sub=""):
    ax.add_patch(FancyBboxPatch((0.72, y), FW - 0.95, h,
        boxstyle="round,pad=0.0,rounding_size=0.04", linewidth=1.1,
        edgecolor=ec, facecolor="none", linestyle=(0, (4, 3)), zorder=1))
    ax.text(0.42, y + h / 2, tag, ha="center", va="center", rotation=90,
            fontsize=9.5, fontweight="bold", color=ec)
    if sub:
        ax.text(0.60, y + h / 2, sub, ha="center", va="center", rotation=90,
                fontsize=6.6, color=C_MUT)


def arrow(p0, p1, color=C_MUT, lw=1.7, rad=0.0, style="-|>", ls="-"):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle=style, mutation_scale=12,
        linewidth=lw, color=color, zorder=6, linestyle=ls,
        connectionstyle=f"arc3,rad={rad}"))


def alabel(x, y, txt, color=C_MUT, fs=7.2, ha="center"):
    ax.text(x, y, txt, ha=ha, va="center", fontsize=fs, color=color,
            zorder=7, style="italic",
            bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none",
                      alpha=0.85))


# ===================================================== data plane (top)
band(11.05, 1.02, C_DPE, "DATA")
box(0.95, 11.15, 5.6, 0.82, C_DP, C_DPE, "CICIDS2017 (15 classes)",
    ["2.42 M flows -> clean -> benign downsampled to 390,222 (50/50)"], ls=7.4)
box(6.80, 11.15, 3.1, 0.82, C_DP, C_DPE, "RobustScaler",
    ["median/IQR, F = 78  [56]"], ls=7.8)
box(10.15, 11.15, 3.1, 0.82, C_DP, C_DPE, "Split",
    ["60 / 20 / 20  (seed 1)"], ls=7.8)
arrow((6.55, 11.56), (6.80, 11.56)); arrow((9.90, 11.56), (10.15, 11.56))

# ===================================================== L1 band
band(6.55, 4.28, C_L1E, "LAYER 1 – REFLEX DETECTION", "Sentinel  :8001")

mw, mh, my = 2.86, 2.14, 8.52
box(0.95, my, mw, mh, "white", C_L1E, "RNN – 81,775 par.",
    ["input (78, 1)", "SimpleRNN(32, relu)", "Dropout 0.1 - Flatten",
     "Dense 32 + LeakyReLU", "Dense 16 + LeakyReLU", "Dense 15 softmax"],
    ts=8.6, mono=True)
box(4.01, my, mw, mh, "white", C_L1E, "CNN – 158,543 par.",
    ["input (78, 1)", "Conv1D(64, k=3)+LReLU", "MaxPool 2 - Drop 0.3",
     "Flatten", "Dense 64/32 + LReLU", "Dense 15 softmax"],
    ts=8.6, mono=True)
box(7.07, my, mw, mh, "white", C_L1E, "DNN – 24,079 par.",
    ["input (78,)", "Dense 256 relu", "Dropout 0.1", "Dense 15 softmax",
     "", ""],
    ts=8.6, mono=True)

# calibration chips
cy = 7.86
for cx, t in ((0.95, "T_rnn = 1.93"), (4.01, "T_cnn = 1.63"),
              (7.07, "T_dnn = 1.99")):
    box(cx + 0.28, cy, 2.30, 0.50, C_L1, C_L1E, "",
        [], lw=1.2)
    ax.text(cx + 0.28 + 1.15, cy + 0.25, f"temp. scaling  {t}",
            ha="center", va="center", fontsize=7.6, color=C_TXT, zorder=4)
    arrow((cx + mw / 2, my), (cx + mw / 2, cy + 0.50), lw=1.4)
    arrow((cx + mw / 2, cy), (cx + mw / 2, 7.50), lw=1.4)

# CWC box
box(0.95, 6.70, 8.98, 0.80, "#dcebff", C_L1E,
    "Conscious Weighted Consensus (CWC)",
    ["P(c|x) = Sum_m  w_m . softmax(z_m / T_m)     w_m = prec_m / Sum_k prec_k"
     "     (Dirichlet online update, decay)"], ls=7.4)

# tau gate
box(10.30, 6.70, 2.95, 3.96, "white", C_L1E, "Reject gate τ = 0.70",
    ["conf = max_c P(c|x)", "", "conf >= τ and c = BENIGN", "-> pass (87.3 %)",
     "", "conf >= τ and c = ATTACK", "-> signed alert", "",
     "conf < τ -> REJECT", "-> drift signal (12.7 %)"], ts=9, ls=7.4)
arrow((9.93, 7.10), (10.30, 7.10), lw=2.0)

# ===================================================== L2 band
band(4.42, 1.92, C_L2E, "LAYER 2 – DELIBERATION", "LLM + fallback")
box(0.95, 4.55, 4.10, 1.62, "white", C_L2E, "Sentinel deliberation",
    ["on certified ATTACK / rejection burst", "rate-limited event summary",
     "-> severity, rationale,", "recommended actions",
     "OpenRouter -> LM Studio -> rules"], ts=8.8)
box(5.30, 4.55, 4.35, 1.62, "white", C_L2E, "Investigator  :8005",
    ["agentic loop: perceive -> reason", "-> act (tools) -> reflect",
     "tools: query_ledger | correlate | llm",
     "campaign memory -> incident report", "report anchored on-chain"],
    ts=8.8)
box(9.90, 4.55, 3.35, 1.62, "white", C_L2E, "Data Scientist  :8004",
    ["monitors rolling reject rate", "drift alarm -> recommend",
     "recalibration / retraining", "(consumes REJECT stream)"], ts=8.8)

# ===================================================== L3 band
band(2.28, 1.92, C_L3E, "LAYER 3 – CONSENSUS", "Hyperledger Fabric 2.5")
box(0.95, 2.41, 3.30, 1.62, "white", C_L3E, "Notaries (x3)",
    ["leader :8002, peers :8012/:8022", "independent re-validation",
     "conf >= τ ? argmax ok ?", "Ed25519-signed vote",
     "advisory LLM opinion (non-decisional)"], ts=8.8)
box(4.50, 2.41, 4.45, 1.62, "white", C_L3E, "validateVote chaincode (Go)",
    ["(i) signer is authorised notary", "(ii) Ed25519 signature valid",
     "(iii) no double vote", "(iv) quorum 2/3 -> ALERT_CERTIFIED",
     "RecordGovernance: signed admin actions"], ts=8.8, mono=False)
box(9.20, 2.41, 4.05, 1.62, "white", C_L3E, "Fabric network (WSL2)",
    ["1 orderer (BatchTimeout 2 s)", "2 orgs x 1 peer, 3 CAs",
     "execute-order-validate", "immutable, replicated ledger"], ts=8.8)

# ===================================================== L4 band
band(0.14, 1.92, C_L4E, "LAYER 4 – HITL", "console :8090")
box(0.95, 0.27, 7.20, 1.62, "white", C_L4E,
    "Supervision console (React + FastAPI, FR/EN/AR)",
    ["roles: reader / analyst / admin  –  governed toggle HITL on/off",
     "live dashboard - incidents - agentic investigation traces",
     "approval queue (severity-gated) - ledger audit view",
     "every admin action signed + anchored on-chain"], ts=8.8)
box(8.45, 0.27, 2.55, 1.62, "white", C_L4E, "Executor  :8003",
    ["block | rate-limit |", "isolate | notify", "acts only on certified",
     "(+ approved) alerts"], ts=8.8)
box(11.25, 0.27, 2.0, 1.62, C_L4, C_L4E, "Operator",
    ["approve / reject", "tune τ, quorum", "toggle autonomy"], ts=8.8)

# ===================================================== flows
arrow((3.75, 11.15), (3.75, 10.80), lw=2.0)
ax.text(3.95, 10.97, "x in R^78", fontsize=7.5, color=C_MUT, style="italic")
for cx in (2.38, 5.44, 8.50):
    arrow((3.75, 10.80), (cx, my + mh), rad=0.0, lw=1.5)

# ATTACK path: tau gate -> Sentinel deliberation -> notaries -> chaincode
arrow((10.9, 6.70), (3.0, 6.17), rad=0.18, color=C_L2E, lw=2.0)
alabel(6.7, 6.38, "certified-candidate ATTACK (signed alert)", color=C_L2E)
arrow((3.0, 4.55), (2.6, 4.03), color=C_L3E, lw=2.0)
alabel(2.75, 4.30, "alert + deliberation", color=C_L3E)
arrow((4.25, 3.22), (4.50, 3.22), color=C_L3E, lw=1.8)
alabel(4.38, 3.50, "votes", color=C_L3E, fs=6.8)
arrow((8.95, 3.22), (9.20, 3.22), color=C_L3E, lw=1.8)

# REJECT path -> Data Scientist
arrow((12.6, 6.70), (11.9, 6.17), color=C_RED, lw=1.7, rad=-0.12)
alabel(12.35, 6.40, "REJECT stream", color=C_RED, fs=6.8)

# certified -> investigator + approval queue + executor
arrow((6.7, 4.03), (6.9, 4.55), color=C_L2E, lw=1.7, rad=0.1)
alabel(6.55, 4.28, "ALERT_CERTIFIED", color=C_L2E, fs=6.8)
arrow((6.0, 2.41), (5.5, 1.89), color=C_L4E, lw=1.9, rad=0.08)
alabel(5.6, 2.14, "certified alert -> approval queue (if HITL on)", color=C_L4E)
arrow((8.15, 1.10), (8.45, 1.10), color=C_L4E, lw=1.8)
alabel(8.30, 1.32, "approved", color=C_L4E, fs=6.8)
arrow((11.25, 1.10), (11.00, 1.10), color=C_L4E, lw=1.4, style="-|>")
arrow((12.25, 1.89), (12.6, 2.41), color=C_L4E, lw=1.6, ls=(0, (4, 2)))
alabel(12.9, 2.14, "RecordGovernance (signed)", color=C_L4E, fs=6.6)

fig.suptitle("BAg-IDS – detailed architecture (models, calibration, CWC, "
             "reject gate, agents, chaincode, HITL)", y=0.995, fontsize=12)
fig.tight_layout(rect=(0, 0, 1, 0.985))
fig.savefig(OUT, dpi=300, bbox_inches="tight")
print(f"OK -> {OUT}")
