# BAg-IDS — Synthèse de la phase 2 (mesures)

## 2.1 Latence du consensus (par alerte certifiée, médiane)

| Quorum | Simulé | Fabric | Surcoût blockchain |
|---|---|---|---|
| 1 | 1.8 ms | 4.13 s | +4.13 s |
| 2 | 2.2 ms | 6.19 s | +6.18 s |
| 3 | 2.8 ms | 8.21 s | +8.21 s |

Latence Fabric ≈ (1 + quorum) × ~2,06 s : dominée par le BatchTimeout de l'orderer (2 s), pas par la cryptographie. Paramètre d'infrastructure réglable (batching, votes parallèles).

## 2.3 Robustesse au label-flipping (cible : RNN, meilleur modèle)

- RNN seul : 89.1% (sain) -> 1.9% (100% empoisonné)
- Ensemble adaptatif : 88.2% -> 87.2% (perte ≈ 1 point)
- Poids du RNN : 0.334 -> 0.058 (auto-exclusion)
- Creux à p=0,5 (~84,4%) : l'empoisonnement partiel est le plus sournois — motive la surveillance de dérive (agent Data Scientist).

## Fichiers produits

- table_latency.tex, table_tau.tex, table_flipping.tex
- figures/latency_quorum.png, label_flipping.png, poisoned_weight.png