# BAg-IDS — Blockchain-Enabled Agentic AI IDS

Implémentation de référence du manuscrit **BAg-IDS** (Bahri, Jemili, Korbaa).
Système de détection d'intrusion à **4 couches** et **5 agents** autonomes :
détection réflexe (ensemble RNN+CNN+DNN calibré), délibération (LLM),
consensus décentralisé (Hyperledger Fabric), et supervision human-in-the-loop.

Ce README explique comment faire tourner le système **depuis zéro sur une
machine neuve**, étape par étape. Il y a deux niveaux :

- **Parcours A — Rapide (~15 min)** : détection + agents + console web, avec un
  **ledger simulé** (aucune blockchain à installer). Suffisant pour voir tout
  le système fonctionner, y compris la console et les enquêtes agentiques.
- **Parcours B — Complet** : ajoute la **vraie blockchain Hyperledger Fabric**
  (nécessite WSL2 + Docker). À faire seulement après que le Parcours A marche.

> Tout ce qui suit est écrit pour **Windows 10/11**. Les commandes de terminal
> sont pour **PowerShell** sauf mention `WSL`.

---

## 0. Ce dont vous avez besoin (fichiers non versionnés)

Trois emplacements ne sont **pas** dans le dépôt (trop volumineux) et doivent
être copiés depuis la machine d'origine (ou régénérés) :

| Emplacement | Contenu attendu |
|---|---|
| `models/SecondModelsWith15Labels/` | `rnn1.h5`, `cnn2.h5`, `dnn1.h5` (les 3 détecteurs entraînés) |
| `data/cicids2017_complet/` | `C__Data processing_ISD2017_Dataset_combined8element.csv` (CICIDS2017 combiné, 15 classes) |
| `results/fusion_experiment/deployment_bundle/` | `manifest.json`, `scaler.joblib`, `X_test.npy`, `y_test.npy` (le **bundle de déploiement** chargé par les agents) |

> Le `deployment_bundle` est le cœur : il contient le scaler, les températures
> de calibration, les poids de fusion, τ, et le jeu de test rejoué par le
> Sentinel. S'il est présent, **inutile de réentraîner ni de relancer
> l'expérience de fusion** pour utiliser l'application.

---

## 1. Prérequis logiciels

Installez, dans cet ordre :

1. **Python 3.11** (recommandé) — cocher « Add Python to PATH » à l'installation.
   TensorFlow ne supporte pas Python 3.13 ; utilisez 3.10, 3.11 ou 3.12.
   Vérifier : `py -3.11 --version`
2. **Node.js 18+** — seulement si vous voulez **recompiler** la console web
   (une version déjà compilée est fournie dans `hitl/frontend/dist/`).
   Vérifier : `node --version`

*(Le Parcours B ajoute WSL2 + Docker + Go — voir §7.)*

---

## 2. Installation Python (une seule fois)

Depuis la racine du projet (`bag-ids/`) :

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
```

> Si `Activate.ps1` est bloqué par la politique d'exécution PowerShell :
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` puis réessayez.

Vérifier que TensorFlow se charge :

```powershell
python -c "import tensorflow as tf; print('TF', tf.__version__)"
```

---

## 3. (Optionnel) Recompiler la console web

Seulement si `hitl/frontend/dist/index.html` n'existe pas, ou si vous modifiez
l'interface. Sinon, **passez à l'étape 4**.

```powershell
cd hitl\frontend
npm install
npm run build          # génère hitl/frontend/dist/
cd ..\..
```

---

## 4. Clé LLM OpenRouter (recommandé, gratuit)

La couche délibération utilise un LLM. Sans clé, le système **fonctionne quand
même** via un repli déterministe à base de règles — mais avec la clé, les
enquêtes de l'agent Investigator sont rédigées par un vrai LLM.

1. Créez un compte gratuit sur <https://openrouter.ai> et générez une clé API.
2. Dans **le terminal où vous lancerez l'application** :

```powershell
$env:OPENROUTER_API_KEY = "sk-or-v1-....votre_cle...."
```

> Cette variable ne vaut que pour la fenêtre PowerShell courante. Le modèle
> gratuit `nvidia/nemotron-3-super-120b-a12b:free` est essayé en premier
> (liste dans `configs/agents_live.yaml`). **Ne partagez jamais votre clé** ;
> si elle fuite, régénérez-la.

---

## 5. Parcours A — Lancer le système (console + agents)

Mode le plus simple : ledger **simulé**, aucune blockchain requise. Le bouton
« Démarrer la détection » de la console lance les 5 agents.

### 5.1 Démarrer la console

Dans un terminal, à la racine du projet, **environnement activé** :

```powershell
.\.venv\Scripts\Activate.ps1
$env:OPENROUTER_API_KEY = "sk-or-v1-...."   # facultatif mais recommandé
python -m hitl.backend.main
```

Laissez ce terminal ouvert. Il sert la console sur **<http://127.0.0.1:8090>**.

### 5.2 Se connecter

Ouvrez <http://127.0.0.1:8090>. Comptes de démonstration :

| Rôle | Identifiant | Mot de passe | Peut… |
|---|---|---|---|
| Administrateur | `admin` | `admin123` | tout : gouvernance, toggle HITL, τ/quorum |
| Analyste | `analyste` | `analyste123` | approuver/rejeter les remédiations |
| Lecteur | `lecteur` | `lecteur123` | observer seulement |

### 5.3 Démarrer la détection

Sur le **Tableau de bord**, cliquez **« Démarrer la détection »**. Patientez
**1 à 2 minutes** (le Sentinel charge les 3 modèles). Vous verrez alors :

- « Détection ACTIVE » et le compteur **Flux traités** qui monte,
- **5/5 agents en ligne** (Sentinel · Notary · Executor · DataSci · Investigator),
- les graphiques de verdicts (bénins / attaques / rejetés) se remplir.

### 5.4 Explorer

- **Investigations** : cliquez une enquête → la **trace de raisonnement
  agentique** (perçois → raisonne → agis → réfléchis). Avec la clé LLM active :
  `provider: openrouter` ; sinon `rules-fallback`.
- **Incidents** : détail des alertes, votes des notaries, avis LLM consultatif.
- **Approbations** : file d'attente (active si le toggle HITL est ON).
- **Audit blockchain** : le registre immuable (ici, le ledger simulé).
- **Gouvernance** (admin) : basculer HITL on/off, changer τ et le quorum —
  chaque action est signée et enregistrée.

### 5.5 Arrêter

« Arrêter la détection » dans la console, puis `Ctrl+C` dans le terminal du
backend.

---

## 6. (Optionnel) Reproduire les résultats du papier

Sans console, en ligne de commande. Environnement activé.

```powershell
# Ensemble calibré sous le protocole d'origine (chiffres du papier)
python experiments\original_pipeline_eval.py --stage prep     # CSV -> splits .npy
python experiments\original_pipeline_eval_tf.py               # inférence + CWC + rejet

# Toutes les figures et statistiques du papier (courbes réelles)
python experiments\paper_analytics_original.py
```

Sorties dans `results/original_pipeline/` et `results/paper_analytics_original/`.

> **Piège Windows connu** : sur cette pile, `import tensorflow` doit précéder
> `pandas`/`pyarrow`, sinon l'init native de TF échoue (« DLL load failed »).
> C'est déjà géré dans le code des agents et les scripts `*_tf.py`. Si vous
> écrivez un nouveau script utilisant TF **et** pandas, importez TensorFlow
> **en premier**.

---

## 7. Parcours B — Vraie blockchain Hyperledger Fabric

À ne faire **qu'après** que le Parcours A fonctionne. La blockchain tourne dans
WSL2 ; les agents (Windows) s'y connectent via une passerelle HTTP.

### 7.1 Prérequis WSL (une seule fois)

Dans PowerShell (admin) : `wsl --install -d Ubuntu-22.04`, puis dans Ubuntu :

- **Docker Engine natif** (⚠️ pas Docker Desktop) — doc Docker pour Ubuntu,
  ajouter l'utilisateur au groupe `docker`.
- **Go 1.22** dans `~/.local/go/bin`.
- **Fabric 2.5.16 + fabric-samples** dans `~/fabric-samples`
  (script officiel `install-fabric.sh`).
- Côté Windows, créer `C:\Users\<vous>\.wslconfig` avec :
  ```
  [wsl2]
  vmIdleTimeout=-1
  ```
  (sinon la VM WSL s'éteint et coupe les conteneurs Fabric).

Détails exacts des chemins et scripts utilisés pendant le développement dans
**`GUIDE_EXECUTION.md`** (§1, §4, §5).

### 7.2 Démarrer Fabric + passerelle (à chaque session)

Terminal **WSL** (à laisser ouvert) :

```bash
cd ~/fabric-samples/test-network
./network.sh up createChannel -c mychannel -ca        # si pas déjà lancé
# déployer le chaincode validatevote (voir GUIDE_EXECUTION.md §4.2)
cd ~/fabric-samples/chaincode-bagids/gateway-proxy && ./gateway-proxy   # port 8445
```

### 7.3 Lancer les agents en mode Fabric

La config `configs/agents_fabric.yaml` pointe le backend blockchain sur Fabric
au lieu du ledger simulé. Suivez `GUIDE_EXECUTION.md` §5.

---

## 8. Dépannage

| Symptôme | Cause / solution |
|---|---|
| **Sentinel hors ligne, « Flux traités » à 0** | Init TensorFlow échouée. Le correctif (import TF en premier) est déjà dans `agents/sentinel/agent.py`. Libérez de la RAM (fermez des onglets), puis Arrêter → Démarrer à nouveau. |
| **`DLL load failed: _pywrap_tensorflow_internal`** | Conflit de DLL pyarrow↔TensorFlow. Toujours importer `tensorflow` avant `pandas` dans tout nouveau script. |
| **`Activate.ps1` interdit** | `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`. |
| **Port 8090 déjà utilisé** | Un backend tourne déjà : `Get-Process python \| Stop-Process -Force`, puis relancer. |
| **Investigations affiche `rules-fallback` au lieu de `openrouter`** | `OPENROUTER_API_KEY` non définie **dans le terminal du backend**, ou modèle gratuit temporairement saturé (429). Redéfinissez la clé et relancez. |
| **Console « figure/agents indisponibles »** | Frontend non compilé : voir §3. |
| **Modèles ou CSV introuvables** | Vérifiez les chemins de la §0 (référencés dans `deployment_bundle/manifest.json` et `configs/`). |

---

## 9. Récapitulatif « démarrage à froid »

Sur une machine déjà installée (§1–§3 faits) :

```powershell
cd <chemin>\bag-ids
.\.venv\Scripts\Activate.ps1
$env:OPENROUTER_API_KEY = "sk-or-v1-...."
python -m hitl.backend.main
# → navigateur : http://127.0.0.1:8090  (admin / admin123)
# → « Démarrer la détection » → attendre ~1 min → onglet Investigations
```

Pour la blockchain réelle, ajoutez le Parcours B (§7) **avant** de démarrer les
agents.

---

## 10. Structure du dépôt

```
bag-ids/
├── README.md                  # ce fichier
├── GUIDE_EXECUTION.md         # guide détaillé (dont mode Fabric complet)
├── requirements.txt
├── configs/                   # agents.yaml (simulé), agents_live.yaml, agents_fabric.yaml
├── src/                       # data_loader, calibration, fusion, metrics, model_loading
├── agents/                    # sentinel, notary, executor, data_scientist, investigator
│   └── run_pipeline.py        # lance les 5 agents (appelé par la console)
├── hitl/
│   ├── backend/               # console FastAPI (port 8090)  ← python -m hitl.backend.main
│   └── frontend/              # console React (dist/ = version compilée)
├── chaincode/                 # validatevote (Go) + gateway-proxy (mode Fabric)
├── experiments/               # reproduction des mesures et figures du papier
├── models/                    # ← modèles .h5 (à fournir, §0)
├── data/                      # ← CSV CICIDS2017 (à fournir, §0)
├── results/                   # sorties + deployment_bundle (à fournir, §0)
└── paper_q1/                  # manuscrit Q1 (.docx) + scripts de figures
```

---

**Détecteurs** entraînés et publiés dans : M. A. E. Bahri, F. Jemili, O. Korbaa,
*Comparative study between ML approaches in intrusion detection context*,
IEEE AMCAI 2023, doi:10.1109/AMCAI59331.2023.10431511.
