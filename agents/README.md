# Agents BAg-IDS (Étape 1.2 — à venir)

Quatre microservices FastAPI, un par agent PRPA :

- `sentinel/`       — perception : replay CSV / NFStream, filtrage 2.5σ, vecteurs suspects
- `data_scientist/` — cognition : inférence RNN/CNN/DNN + fusion calibrée (réutilise src/)
- `notary/`         — confiance : construction de la transaction, appel validateVote()
- `executor/`       — action : remédiation graduée Tier 1-4 (mock Firewall API)
