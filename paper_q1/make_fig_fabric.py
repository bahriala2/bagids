"""
BAg-IDS – Deux figures blockchain :
  1. fabric_anatomy.png    : anatomie du réseau Hyperledger Fabric déployé
     (orgs, peers, orderer, CAs, canal, chaincode, ledger, passerelle).
  2. consensus_sequence.png: séquence du consensus BAg-IDS – de l'alerte
     signée à ALERT_CERTIFIED (execute-order-validate, votes, quorum),
     avec le coût mesuré ~2,06 s/transaction (soumission séquentielle).

    python paper_q1/make_fig_fabric.py
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

C_TXT = "#16223a"; C_MUT = "#44546e"
C_G = "#27ae60"; C_GBG = "#eafaf0"
C_B = "#4f8cff"; C_BBG = "#eaf2ff"
C_O = "#e08a00"; C_OBG = "#fff4e0"
C_P = "#7d4fd3"


def box(ax, x, y, w, h, fc, ec, title, lines=(), ts=9.5, ls=7.6, lw=1.5,
        tdy=0.22, lh=0.24):
    ax.add_patch(FancyBboxPatch((x, y), w, h,
        boxstyle="round,pad=0.02,rounding_size=0.05",
        linewidth=lw, edgecolor=ec, facecolor=fc, zorder=2))
    ax.text(x + w / 2, y + h - tdy, title, ha="center", va="center",
            fontsize=ts, fontweight="bold", color=C_TXT, zorder=3)
    for k, ln in enumerate(lines):
        ax.text(x + w / 2, y + h - tdy - 0.30 - k * lh, ln, ha="center",
                va="center", fontsize=ls, color=C_MUT, zorder=3)


def arrow(ax, p0, p1, color=C_MUT, lw=1.7, rad=0.0, ls="-", style="-|>"):
    ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle=style, mutation_scale=12,
        linewidth=lw, color=color, zorder=6, linestyle=ls,
        connectionstyle=f"arc3,rad={rad}"))


def lab(ax, x, y, txt, color=C_MUT, fs=7.4, ha="center"):
    ax.text(x, y, txt, ha=ha, va="center", fontsize=fs, color=color,
            zorder=7, style="italic",
            bbox=dict(boxstyle="round,pad=0.12", fc="white", ec="none",
                      alpha=0.9))


# ================================================= 1. anatomie Fabric
def fabric_anatomy():
    fig, ax = plt.subplots(figsize=(10.8, 6.6))
    ax.set_xlim(0, 10.8); ax.set_ylim(0, 6.6); ax.axis("off")

    # côté agents
    box(ax, 0.25, 4.55, 2.5, 1.5, "#f0eafc", C_P, "BAg-IDS agents",
        ["notaries (leader + peers)", "HTTP/JSON clients"])
    box(ax, 0.25, 2.45, 2.5, 1.35, "#f2f5fa", "#8ea0bf",
        "gateway-proxy  :8445",
        ["HTTP -> Fabric Gateway", "(gRPC, identities Org1)"])
    arrow(ax, (1.5, 4.55), (1.5, 3.8), lw=1.8)
    lab(ax, 1.5, 4.18, "invoke / query")

    # réseau Fabric
    ax.add_patch(FancyBboxPatch((3.15, 0.25), 7.4, 6.1,
        boxstyle="round,pad=0.02,rounding_size=0.06", linewidth=1.4,
        edgecolor=C_G, facecolor="none", linestyle=(0, (5, 3)), zorder=1))
    ax.text(6.85, 6.14, "Hyperledger Fabric 2.5 test network – channel "
            "“mychannel”  (WSL2, native Docker)", ha="center", fontsize=9,
            fontweight="bold", color=C_G)

    for k, org in enumerate(("Org1", "Org2")):
        x = 3.45 + k * 3.65
        box(ax, x, 3.45, 3.35, 2.25, C_GBG, C_G, f"{org}  (organisation)",
            [f"CA {org.lower()}  (identities, MSP)",
             f"peer0.{org.lower()}  – endorsing peer",
             "chaincode: validatevote (Go)",
             "ledger copy: blocks + world state"], ls=7.4)
    box(ax, 3.45, 0.55, 3.35, 1.6, C_OBG, C_O, "Ordering service",
        ["orderer (etcdraft)", "BatchTimeout = 2 s (default)",
         "cuts and signs blocks"], ls=7.4)
    box(ax, 7.10, 0.55, 3.35, 1.6, "#f2f5fa", "#8ea0bf",
        "Ledger (replicated)",
        ["hash-linked blocks (immutable)",
         "world state: alerts, votes, signers,",
         "certifications, governance"], ls=7.4)

    arrow(ax, (2.75, 3.1), (3.45, 3.1), lw=1.8)
    arrow(ax, (5.1, 3.45), (5.1, 2.15), lw=1.5)
    arrow(ax, (8.75, 3.45), (8.75, 2.15), lw=1.5, rad=0.0)
    lab(ax, 5.1, 2.8, "endorsed tx", fs=7)
    lab(ax, 8.78, 2.8, "commit/validate", fs=7)
    arrow(ax, (6.8, 1.35), (7.10, 1.35), lw=1.5)
    lab(ax, 6.95, 1.62, "blocks", fs=7)
    ax.text(6.85, 0.12, "Endorsement policy: signatures of BOTH "
            "organisations required for every transaction", ha="center",
            fontsize=7.8, color=C_MUT, style="italic")

    out = Path("paper_q1/figures/fabric_anatomy.png")
    fig.tight_layout()
    fig.savefig(out, dpi=300, bbox_inches="tight", facecolor="white")
    print("OK ->", out)
    plt.close(fig)


# ================================================= 2. séquence consensus
def consensus_sequence():
    fig, ax = plt.subplots(figsize=(11.6, 7.6))
    ax.set_xlim(0, 11.6); ax.set_ylim(0, 7.6); ax.axis("off")

    actors = [("Sentinel", 0.9, C_B), ("Notary leader", 3.0, C_G),
              ("Notary peers (×2)", 5.25, C_G),
              ("validateVote chaincode", 7.6, C_G),
              ("Orderer + ledger", 10.2, C_O)]
    top, bot = 6.9, 0.5
    for name, x, c in actors:
        box(ax, x - 1.02, top, 2.04, 0.52, "white", c, name, ts=8.6, lw=1.6)
        ax.plot([x, x], [bot, top], color=c, lw=1.0, ls=(0, (4, 3)),
                alpha=0.55, zorder=1)

    def step(y, x0, x1, txt, color=C_MUT, dy=0.14):
        arrow(ax, (x0, y), (x1, y), color=color, lw=1.7)
        ax.text((x0 + x1) / 2, y + dy, txt, ha="center", fontsize=7.4,
                color=color, zorder=7,
                bbox=dict(boxstyle="round,pad=0.1", fc="white", ec="none",
                          alpha=0.9))

    # note : invariants vérifiés par le chaincode sur CHAQUE vote
    ax.text(7.6, 6.58, "checks every vote:  (i) authorised signer   "
            "(ii) valid Ed25519\n(iii) no double vote   (iv) count quorum",
            ha="center", fontsize=6.6, color=C_MUT,
            bbox=dict(boxstyle="round,pad=0.16", fc="white", ec=C_G, lw=0.8))

    y = 6.30
    step(y, 0.9, 3.0, "1. signed alert (Ed25519) + deliberation", C_B)
    y -= 0.55
    step(y, 3.0, 7.6, "2. RecordAlert transaction", C_G)
    step(y - 0.38, 7.6, 10.2, "endorse (Org1+Org2) -> order", C_O)
    ax.text(10.32, y - 0.72, "block cut\n(<= 2 s)", fontsize=6.8, color=C_O,
            ha="left")
    y -= 1.15
    step(y, 3.0, 5.25, "3. alert broadcast to peers", C_G)
    y -= 0.5
    ax.text(4.15, y, "4. each notary independently re-validates:\n"
            "conf >= τ ?  class = argmax ?  -> vote_i (signed)",
            ha="center", fontsize=7.4, color=C_G,
            bbox=dict(boxstyle="round,pad=0.2", fc="#eafaf0", ec=C_G, lw=1))
    y -= 0.75
    for k in (1, 2, 3):
        step(y, 5.25 if k > 1 else 3.0, 7.6,
             f"5.{k} ValidateVote(vote_{k})", C_G)
        step(y - 0.3, 7.6, 10.2, "endorse -> order -> commit", C_O)
        y -= 0.82
    y -= 0.05
    ax.text(7.6, y, "6. quorum 2/3 reached -> chaincode seals "
            "ALERT_CERTIFIED", ha="center", fontsize=8.2, fontweight="bold",
            color=C_TXT,
            bbox=dict(boxstyle="round,pad=0.25", fc="#eafaf0", ec=C_G,
                      lw=1.4))
    y -= 0.62
    step(y, 7.6, 0.9, "7. certification event -> Executor / approval queue / "
         "Investigator", C_P)

    ax.text(5.8, 0.12, "Measured: ~2.06 s per transaction (Table 8) – the "
            "(1 + quorum) scaling comes from SEQUENTIAL submission; "
            "concurrent votes would take ~2 block intervals regardless of "
            "quorum (§6.6).", ha="center", fontsize=7.6, color=C_MUT,
            style="italic")

    out = Path("paper_q1/figures/consensus_sequence.png")
    fig.tight_layout()
    fig.savefig(out, dpi=300, bbox_inches="tight", facecolor="white")
    print("OK ->", out)
    plt.close(fig)


if __name__ == "__main__":
    fabric_anatomy()
    consensus_sequence()
