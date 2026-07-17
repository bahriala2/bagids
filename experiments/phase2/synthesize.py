"""
BAg-IDS — Phase 2.2 + 2.4 : ablations et synthèse (figures + LaTeX).

Agrège les mesures des campagnes de la phase 2 en livrables prêts pour
le manuscrit :

  Entrées :
    results/fusion_experiment/results.json      (tau_sweep, étape 1.1)
    results/phase2/latency_q{1,2,3}.json        (campagne 2.1)
    results/phase2/label_flipping_{cnn,rnn}.json (campagne 2.3)

  Sorties (results/phase2/) :
    table_latency.tex        Ablation quorum -> latence ±blockchain
    table_tau.tex            Ablation seuil de rejet tau
    table_flipping.tex       Robustesse au label-flipping (cible RNN)
    figures/latency_quorum.png
    figures/label_flipping.png
    figures/poisoned_weight.png
    summary_phase2.md        Rapport de synthèse lisible

Usage :
    python -m experiments.phase2.synthesize
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

P2 = Path("results/phase2")
FIGS = P2 / "figures"


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


# ------------------------------------------------------------- latence
def latency_table_and_figure():
    rows = []
    for q in (1, 2, 3):
        data = load(P2 / f"latency_q{q}.json")
        runs = {r["backend"]: r for r in data["runs"]}
        rows.append({
            "quorum": q,
            "sim_ms": runs["simulated"]["consensus"]["median_ms"],
            "fab_ms": runs["fabric"]["consensus"]["median_ms"],
            "fab_p95": runs["fabric"]["consensus"]["p95_ms"],
            "overhead_ms": data["blockchain_overhead_median_ms"],
        })

    lines = [
        "% Table — Ablation quorum -> latence du consensus (mesurée, phase 2.1)",
        "\\begin{tabular}{ccccc}", "\\toprule",
        "Quorum & Simulated (ms) & Fabric (ms) & Fabric p95 (ms) & "
        "Overhead (ms) \\\\", "\\midrule",
    ]
    for r in rows:
        lines.append(f"{r['quorum']} & {r['sim_ms']:.1f} & {r['fab_ms']:.0f} & "
                     f"{r['fab_p95']:.0f} & {r['overhead_ms']:.0f} \\\\")
    lines += ["\\bottomrule", "\\end{tabular}"]
    (P2 / "table_latency.tex").write_text("\n".join(lines), encoding="utf-8")

    fig, ax = plt.subplots(figsize=(6, 4.2))
    qs = [r["quorum"] for r in rows]
    ax.plot(qs, [r["sim_ms"] for r in rows], "s-", color="tab:green",
            label="Ledger simulé (étape 1.3)")
    ax.plot(qs, [r["fab_ms"] for r in rows], "o-", color="tab:purple",
            label="Hyperledger Fabric (étape 1.4)")
    ax.set_yscale("log")
    ax.set_xticks(qs)
    ax.set_xlabel("Quorum (votes d'approbation requis)")
    ax.set_ylabel("Latence médiane du consensus (ms, échelle log)")
    ax.set_title("Coût du consensus par alerte certifiée (mesuré)")
    ax.grid(alpha=0.3, which="both")
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIGS / "latency_quorum.png", dpi=300)
    plt.close(fig)
    return rows


# ------------------------------------------------------------------ tau
def tau_table():
    res = load("results/fusion_experiment/results.json")
    sweep = res["tau_sweep"]
    keep = [r for r in sweep if round(r["tau"] * 100) % 10 == 0]  # pas de 0.1
    lines = [
        "% Table — Ablation du seuil de rejet tau (mesurée, étape 1.1)",
        "\\begin{tabular}{ccccc}", "\\toprule",
        "$\\tau$ & Couverture & Acc. (accept.) & F1 (accept.) & "
        "FPR (accept.) \\\\", "\\midrule",
    ]
    for r in keep:
        lines.append(
            f"{r['tau']:.2f} & {r['coverage']*100:.1f}\\% & "
            f"{r['accuracy_accepted']*100:.2f}\\% & "
            f"{r['f1_accepted']*100:.2f}\\% & "
            f"{r['fpr_accepted']*100:.3f}\\% \\\\")
    lines += ["\\bottomrule", "\\end{tabular}"]
    (P2 / "table_tau.tex").write_text("\n".join(lines), encoding="utf-8")
    return keep


# ------------------------------------------------------- label flipping
def flipping_table_and_figures():
    rnn = load(P2 / "label_flipping_rnn.json")
    cnn = load(P2 / "label_flipping_cnn.json")

    lines = [
        "% Table — Robustesse au label-flipping du RNN (mesurée, phase 2.3)",
        "\\begin{tabular}{cccccc}", "\\toprule",
        "$p$ & \\multicolumn{2}{c}{RNN empoisonné seul} & "
        "\\multicolumn{2}{c}{Ensemble adaptatif} & Poids RNN \\\\",
        " & Acc. & FPR & Acc. & FPR & (adaptatif) \\\\", "\\midrule",
    ]
    for r in rnn["rows"]:
        solo, ada = r["solo_poisoned"], r["ensemble_adaptive"]
        lines.append(
            f"{r['fraction']:.1f} & {solo['accuracy']*100:.1f}\\% & "
            f"{solo['fpr_operational']*100:.1f}\\% & "
            f"{ada['accuracy']*100:.1f}\\% & "
            f"{ada['fpr_operational']*100:.1f}\\% & "
            f"{r['poisoned_weight_adaptive']:.3f} \\\\")
    lines += ["\\bottomrule", "\\end{tabular}"]
    (P2 / "table_flipping.tex").write_text("\n".join(lines), encoding="utf-8")

    # Figure principale : accuracy vs fraction
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    fr = [r["fraction"] for r in rnn["rows"]]
    ax.plot(fr, [r["solo_poisoned"]["accuracy"] * 100 for r in rnn["rows"]],
            "v--", color="tab:red", label="RNN empoisonné seul")
    ax.plot(fr, [r["ensemble_static"]["accuracy"] * 100 for r in rnn["rows"]],
            "s-", color="tab:orange", label="Ensemble (poids statiques)")
    ax.plot(fr, [r["ensemble_adaptive"]["accuracy"] * 100 for r in rnn["rows"]],
            "o-", color="tab:blue",
            label="Ensemble (poids adaptatifs, BAg-IDS)")
    ax.set_xlabel("Fraction de décisions empoisonnées $p$ (cible : RNN)")
    ax.set_ylabel("Accuracy sur le jeu de test (%)")
    ax.set_title("Robustesse au label-flipping — Conscious Weighted Consensus")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIGS / "label_flipping.png", dpi=300)
    plt.close(fig)

    # Figure secondaire : poids adaptatif du modèle empoisonné
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.plot(fr, [r["poisoned_weight_adaptive"] for r in rnn["rows"]],
            "o-", color="tab:blue", label="RNN (fort) empoisonné")
    fr_c = [r["fraction"] for r in cnn["rows"]]
    ax.plot(fr_c, [r["poisoned_weight_adaptive"] for r in cnn["rows"]],
            "s--", color="tab:cyan", label="CNN (faible) empoisonné")
    ax.axhline(1 / 3, color="gray", linestyle=":", linewidth=0.9,
               label="Poids uniforme (1/3)")
    ax.set_xlabel("Fraction de décisions empoisonnées $p$")
    ax.set_ylabel("Poids de fusion du modèle empoisonné")
    ax.set_title("Auto-exclusion du détecteur corrompu (Éq. 2)")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIGS / "poisoned_weight.png", dpi=300)
    plt.close(fig)
    return rnn


# ------------------------------------------------------------ synthèse
def summary(latency_rows, rnn_flip):
    r100 = next(r for r in rnn_flip["rows"] if r["fraction"] == 1.0)
    r0 = next(r for r in rnn_flip["rows"] if r["fraction"] == 0.0)
    lines = [
        "# BAg-IDS — Synthèse de la phase 2 (mesures)",
        "",
        "## 2.1 Latence du consensus (par alerte certifiée, médiane)",
        "",
        "| Quorum | Simulé | Fabric | Surcoût blockchain |",
        "|---|---|---|---|",
    ]
    for r in latency_rows:
        lines.append(f"| {r['quorum']} | {r['sim_ms']:.1f} ms | "
                     f"{r['fab_ms']/1000:.2f} s | "
                     f"+{r['overhead_ms']/1000:.2f} s |")
    lines += [
        "",
        "Latence Fabric ≈ (1 + quorum) × ~2,06 s : dominée par le "
        "BatchTimeout de l'orderer (2 s), pas par la cryptographie. "
        "Paramètre d'infrastructure réglable (batching, votes parallèles).",
        "",
        "## 2.3 Robustesse au label-flipping (cible : RNN, meilleur modèle)",
        "",
        f"- RNN seul : {r0['solo_poisoned']['accuracy']*100:.1f}% (sain) "
        f"-> {r100['solo_poisoned']['accuracy']*100:.1f}% (100% empoisonné)",
        f"- Ensemble adaptatif : {r0['ensemble_adaptive']['accuracy']*100:.1f}% "
        f"-> {r100['ensemble_adaptive']['accuracy']*100:.1f}% "
        "(perte ≈ 1 point)",
        f"- Poids du RNN : {r0['poisoned_weight_adaptive']:.3f} -> "
        f"{r100['poisoned_weight_adaptive']:.3f} (auto-exclusion)",
        "- Creux à p=0,5 (~84,4%) : l'empoisonnement partiel est le plus "
        "sournois — motive la surveillance de dérive (agent Data Scientist).",
        "",
        "## Fichiers produits",
        "",
        "- table_latency.tex, table_tau.tex, table_flipping.tex",
        "- figures/latency_quorum.png, label_flipping.png, poisoned_weight.png",
    ]
    (P2 / "summary_phase2.md").write_text("\n".join(lines), encoding="utf-8")


def main():
    FIGS.mkdir(parents=True, exist_ok=True)
    latency_rows = latency_table_and_figure()
    print("Table + figure latence : OK")
    tau_table()
    print("Table tau : OK")
    rnn_flip = flipping_table_and_figures()
    print("Table + figures label-flipping : OK")
    summary(latency_rows, rnn_flip)
    print(f"Synthèse : {P2 / 'summary_phase2.md'}")


if __name__ == "__main__":
    main()
