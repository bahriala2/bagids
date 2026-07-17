# BAg-IDS — Guide d'exécution du système (étape par étape)

Ce guide explique comment lancer l'intégralité du système BAg-IDS, de zéro
jusqu'aux mesures de la phase 2. Il suppose la machine déjà configurée pendant
le développement (Windows 11 + WSL2 Ubuntu 22.04, projet dans
`D:\these\projet\bag-ids\bag-ids`).

> **Convention** : les commandes `PowerShell/Windows` se lancent dans un terminal
> Windows ; les commandes `WSL` se lancent dans un terminal Ubuntu (tape `wsl`
> puis Entrée dans PowerShell, ou ouvre « Ubuntu » depuis le menu Démarrer).

---

## 0. Architecture en un coup d'œil

| Couche | Où ça tourne | Composant |
|---|---|---|
| 1. Détection (réflexe) | Windows, `.venv` | Ensemble RNN+CNN+DNN calibré (`src/`, `agents/sentinel/`) |
| 2. Délibération | Windows → API | LLM OpenRouter (cloud) ou LM Studio (local), repli règles |
| 3. Consensus | Windows *ou* WSL | Ledger simulé (`SimulatedLedger`) **ou** Hyperledger Fabric |
| 4. Human-in-the-Loop | Windows (FastAPI+React) | Console de supervision `hitl/` (dashboard, incidents, audit, gouvernance) |
| Agents | Windows, FastAPI | Sentinel, Notary×3, Executor, Data Scientist |
| Blockchain | WSL2 + Docker natif | test-network Fabric + chaincode Go `validatevote` |

Deux modes d'exécution :
- **Mode simulé** (rapide, autonome, aucune dépendance externe) → `configs/agents.yaml`
- **Mode Fabric** (blockchain réelle) → `configs/agents_fabric.yaml` (nécessite les sections 4-5)

---

## 1. Prérequis (à faire une seule fois)

Déjà installés sur cette machine — listés ici pour reproductibilité.

**Windows :**
- Python 3.11 avec l'environnement virtuel `.venv` à la racine du projet
- Dépendances : `.venv\Scripts\activate` puis `pip install -r requirements.txt`

**WSL2 Ubuntu (pour le mode Fabric uniquement) :**
- Docker Engine **natif** (PAS Docker Desktop — cassé sur cette machine, bug
  « Inference manager »). Script d'install : `~/install_docker.sh`
- Go 1.22 local dans `~/.local/go/bin`
- Fabric 2.5.16 + fabric-samples dans `~/fabric-samples`
- Wrapper `docker-compose` → `docker compose` dans `/usr/local/bin/docker-compose`
- `~/.wslconfig` (côté Windows) contient `vmIdleTimeout=-1` pour que la VM WSL
  ne s'éteigne pas (sinon les conteneurs Fabric s'arrêtent)

**Clé LLM (mode agents avec vrai LLM) :**
La variable `OPENROUTER_API_KEY` est enregistrée dans l'environnement utilisateur
Windows. Pour vérifier (PowerShell) :
```powershell
echo $env:OPENROUTER_API_KEY
```
Si vide dans un nouveau terminal, rouvre-le, ou redéfinis-la :
```powershell
$env:OPENROUTER_API_KEY = "sk-or-v1-..."
```

---

## 2. Étape 1.1 — Mesurer l'ensemble calibré (base de tout)

C'est l'étape qui produit le **bundle de déploiement** dont les agents ont besoin.
À relancer si tu changes de dataset ou de modèles.

**PowerShell/Windows :**
```powershell
cd D:\these\projet\bag-ids\bag-ids
.venv\Scripts\activate
python run_fusion_experiment.py --config configs/config.yaml --export-bundle
```

- Durée : ~6-8 min (chargement CSV 1,1 Go + inférence des 3 modèles).
- Sorties : `results/fusion_experiment/` — `results.json`, `table_II.tex`,
  4 figures, et surtout `deployment_bundle/` (scaler, températures, poids, τ,
  X_test) consommé par le Sentinel.
- Variante CICIDS2018 : remplacer par `--config configs/config_cicids2018.yaml`.

> ⚠️ Le flag `--export-bundle` est **obligatoire** avant de lancer les agents,
> sinon `results/fusion_experiment/deployment_bundle/` n'existe pas.

---

## 3. Mode SIMULÉ — Démo des agents (le plus simple)

Aucune blockchain requise. Idéal pour développer et démontrer le pipeline.

**PowerShell/Windows :**
```powershell
cd D:\these\projet\bag-ids\bag-ids
.venv\Scripts\activate
python -m agents.launch_demo --config configs/agents.yaml
```

Ce que fait le lanceur :
1. Démarre en sous-processus : Notary×3 (leader + 2 pairs), Executor, Data Scientist.
2. Attend que chacun réponde sur `/health`.
3. Lance le Sentinel qui rejoue le jeu de test (500-5000 flux selon `max_flows`).
4. Affiche un rapport final (compteurs par agent + état du ledger).

Sans clé LLM, la délibération bascule automatiquement sur les règles
(`rules-fallback`) — le système reste 100 % fonctionnel.

**Tests unitaires du consensus (rapide, sans réseau) :**
```powershell
python -m agents.test_step13
```
Vérifie les 5 propriétés : immuabilité, authenticité, autorisation, anti-rejeu, quorum.

---

## 4. Mode FABRIC — Démarrer la blockchain (WSL)

### 4.1 Démarrer / vérifier le réseau Fabric

**WSL :**
```bash
# Laisser CE terminal ouvert en permanence (sinon la VM WSL s'arrête)
cd ~/fabric-samples/test-network

# Les conteneurs sont-ils déjà là ?
docker ps --format "{{.Names}} ({{.Status}})"
```

- **Si `docker ps` liste 6 conteneurs Up** (orderer, 2 peers, 3 CA) → le réseau
  tourne, passe à 4.2.
- **Si les conteneurs sont « Exited »** (arrêtés après un reboot) :
  ```bash
  docker start ca_org1 ca_org2 ca_orderer orderer.example.com \
    peer0.org1.example.com peer0.org2.example.com
  ```
- **Si aucun conteneur (repartir de zéro)** :
  ```bash
  export PATH=~/.local/go/bin:$PATH
  ./network.sh down
  ./network.sh up createChannel -ca
  ```
  (~2-3 min ; recrée le canal `mychannel` — efface le ledger existant.)

### 4.2 Déployer le chaincode (seulement si pas déjà committé)

**WSL :**
```bash
export PATH=~/.local/go/bin:$PATH
cd ~/fabric-samples/test-network
# Vérifier s'il est déjà déployé :
peer lifecycle chaincode querycommitted --channelID mychannel 2>/dev/null | grep validatevote

# Sinon, (re)copier la source depuis Windows et déployer :
cp -r /mnt/d/these/projet/bag-ids/bag-ids/chaincode/validatevote ~/fabric-samples/chaincode-bagids/
./network.sh deployCC -ccn validatevote \
  -ccp ~/fabric-samples/chaincode-bagids/validatevote -ccl go
```
Si tu modifies le chaincode et redéploies, ajoute `-ccs 2` (incrémenter la séquence).

### 4.3 Lancer la passerelle HTTP (pont Python ↔ Fabric)

**WSL (dans le même terminal gardé ouvert, ou un second) :**
```bash
cd ~/fabric-samples/chaincode-bagids/gateway-proxy
# (re)compiler si besoin : export PATH=~/.local/go/bin:$PATH && go build -o gateway-proxy .
nohup ./gateway-proxy -listen 127.0.0.1:8445 > ~/gateway-proxy.log 2>&1 &

# Vérifier :
curl -s http://127.0.0.1:8445/health
```
Attendu : `{"chaincode":"validatevote","channel":"mychannel","status":"ok"}`.
Le port 8445 est accessible depuis Windows (WSL2 forwarde localhost).

---

## 5. Mode FABRIC — Lancer les agents sur la blockchain

Une fois les sections 4.1-4.3 OK :

**PowerShell/Windows :**
```powershell
cd D:\these\projet\bag-ids\bag-ids
.venv\Scripts\activate
python -m agents.launch_demo --config configs/agents_fabric.yaml
```

Différence avec le mode simulé : le Notary leader utilise `FabricLedger`, qui
soumet `RecordAlert` + `ValidateVote` au chaincode. Chaque alerte certifiée est
donc réellement ancrée sur la blockchain (2 organisations endossent, ~2 s/tx).
`max_flows` est réduit à 500 dans ce config car chaque alerte coûte plusieurs
transactions.

**Inspecter le ledger on-chain** (WSL) :
```bash
cd ~/fabric-samples/test-network
# exemple : vérifier qu'une alerte est certifiée
peer chaincode query -C mychannel -n validatevote \
  -c '{"function":"IsCertified","Args":["<alert_id>"]}'
```

---

## 6. Phase 2 — Reproduire les mesures

Réseau Fabric + passerelle actifs (sections 4.1-4.3) pour les mesures Fabric.

**PowerShell/Windows :**
```powershell
cd D:\these\projet\bag-ids\bag-ids
.venv\Scripts\activate

# 2.1 — Latence ±blockchain (quorum 1, 2, 3)
python -m experiments.phase2.bench_latency --config configs/agents_fabric.yaml --n-alerts 40 --quorum 1 --out results/phase2/latency_q1.json
python -m experiments.phase2.bench_latency --config configs/agents_fabric.yaml --n-alerts 40 --quorum 2 --out results/phase2/latency_q2.json
python -m experiments.phase2.bench_latency --config configs/agents_fabric.yaml --n-alerts 40 --quorum 3 --out results/phase2/latency_q3.json

# 2.3 — Robustesse label-flipping (cible cnn puis rnn)
python -m experiments.phase2.bench_label_flipping --config configs/config.yaml --target cnn --out results/phase2/label_flipping_cnn.json
python -m experiments.phase2.bench_label_flipping --config configs/config.yaml --target rnn --out results/phase2/label_flipping_rnn.json

# 2.2 + 2.4 — Agrégation : tables LaTeX + figures 300 dpi + synthèse
python -m experiments.phase2.synthesize
```

Livrables dans `results/phase2/` : `table_latency.tex`, `table_tau.tex`,
`table_flipping.tex`, `figures/*.png`, `summary_phase2.md`.

> Note : `bench_latency` en mode `simulated` seul ne nécessite pas Fabric
> (`--backends simulated`). Le mode par défaut compare `simulated,fabric`.

---

## 6bis. Couche Human-in-the-Loop (application de supervision)

La 4ᵉ couche est une application web (backend FastAPI + frontend React) qui
donne à l'opérateur une console de supervision : dashboard temps réel, gestion
des incidents, audit de la blockchain, et **gouvernance** (interrupteur HITL,
réglage τ/quorum, approbation des remédiations). Toute action de gouvernance
est signée et ancrée dans le ledger.

### 6bis.1 Compiler le frontend (une fois, ou après modification de l'UI)

```powershell
cd D:\these\projet\bag-ids\bag-ids\hitl\frontend
npm install        # première fois seulement
npm run build      # génère hitl/frontend/dist/ (servi par le backend)
```

### 6bis.2 Lancer la console

```powershell
cd D:\these\projet\bag-ids\bag-ids
.venv\Scripts\activate
python -m hitl.backend.main
```

Ouvrir **http://127.0.0.1:8090** dans le navigateur.
Comptes de démonstration :

| Compte | Mot de passe | Rôle | Peut… |
|---|---|---|---|
| `admin` | `admin123` | administrateur | tout, dont gouvernance + toggle HITL |
| `analyste` | `analyste123` | analyste | approuver/rejeter les incidents |
| `lecteur` | `lecteur123` | lecteur | consulter uniquement |

L'application est **trilingue** (FR/EN/AR avec RTL) et propose un **thème
clair/sombre** — boutons en haut à droite.

### 6bis.3 Effet du toggle HITL

- **HITL activé** (Gouvernance → Activer) : les remédiations de sévérité
  `high`/`critical` certifiées par le consensus sont mises en file
  d'attente ; l'analyste doit les approuver (onglet Approbations) avant que
  l'Executor n'agisse.
- **HITL désactivé** : les agents agissent en pleine autonomie (la file est
  contournée). La bascule elle-même est ancrée dans le ledger.

Pour que les agents respectent la porte HITL, `hitl_gate_url` doit être présent
dans `configs/agents.yaml` / `configs/agents_fabric.yaml` (déjà configuré,
pointant sur `http://127.0.0.1:8090`). Ordre de lancement recommandé pour une
démo supervisée :

```
1. (WSL) réseau Fabric + passerelle (§4)         — si mode fabric
2. (Windows) python -m hitl.backend.main          — la console
3. (navigateur) activer HITL dans Gouvernance
4. (Windows) python -m agents.launch_demo --config configs/agents_fabric.yaml
5. (navigateur) onglet Approbations : approuver les remédiations en attente
```

### 6bis.4 Gouvernance on-chain

Quand la passerelle Fabric tourne, chaque toggle / changement de paramètre /
approbation est ancré on-chain via le contrat `RecordGovernance` (visible dans
Gouvernance → journal, champ « ancrage : fabric »). Sinon, repli en mode local.

---

## 7. Arrêt propre

**Agents** : `Ctrl+C` dans le terminal du lanceur (il arrête les sous-processus).

**Passerelle Fabric** (WSL) :
```bash
pkill -f gateway-proxy
```

**Réseau Fabric** (WSL) — deux options :
```bash
cd ~/fabric-samples/test-network
docker stop $(docker ps -q)        # pause (conserve le ledger, redémarrable avec docker start)
# ou
./network.sh down                  # arrêt complet (efface le ledger)
```

---

## 8. Dépannage (problèmes rencontrés pendant le dev)

| Symptôme | Cause | Solution |
|---|---|---|
| Agents : `deployment_bundle introuvable` | Bundle pas généré | Relancer §2 avec `--export-bundle` |
| `connection refused` sur localhost:7051 | Conteneurs Fabric arrêtés (VM WSL éteinte) | §4.1 `docker start ...` ; garder un terminal WSL ouvert |
| `docker-compose could not be found` | Fabric appelle l'ancien nom | Wrapper déjà posé dans `/usr/local/bin` ; sinon recréer |
| `error getting credentials ... docker-credential-desktop.exe` | Reste de Docker Desktop | `echo '{}' > ~/.docker/config.json` |
| Passerelle `/health` ne répond pas | Proxy non lancé | §4.3 `nohup ./gateway-proxy ...` |
| Délibération toujours `rules-fallback` | Clé LLM absente | Définir `OPENROUTER_API_KEY` (§1) ou lancer LM Studio sur :1234 |
| OpenRouter HTTP 429 | Modèle gratuit saturé | Le client essaie automatiquement les modèles suivants ; sinon repli règles |
| CSV chargement lent / RAM saturée | Dataset volumineux (2018) | Fermer Chrome ; le loader est déjà optimisé (float32 par fichier) |

---

## 9. Récapitulatif « démarrage à froid » (après reboot du PC)

```
1. (Windows) Ouvrir Docker ? NON — on utilise Docker natif WSL.
2. (WSL, terminal à garder ouvert)
     cd ~/fabric-samples/test-network
     docker start ca_org1 ca_org2 ca_orderer orderer.example.com peer0.org1.example.com peer0.org2.example.com
     cd ~/fabric-samples/chaincode-bagids/gateway-proxy && nohup ./gateway-proxy -listen 127.0.0.1:8445 > ~/gateway-proxy.log 2>&1 &
     curl -s http://127.0.0.1:8445/health          # doit répondre status:ok
3. (Windows)
     cd D:\these\projet\bag-ids\bag-ids ; .venv\Scripts\activate
     python -m agents.launch_demo --config configs/agents_fabric.yaml
```

Pour le mode simulé, seule l'étape 3 (avec `configs/agents.yaml`) suffit.
