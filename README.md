# BAg-IDS — Blockchain-Enabled Agentic AI for Trustworthy Intrusion Detection

Reference implementation and reproduction package for the manuscript:

> **BAg-IDS: A Blockchain-Enabled Agentic AI Architecture for Trustworthy
> Intrusion Detection** — M. A. E. Bahri, F. Jemili, O. Korbaa.
> *Under review.*

BAg-IDS is a four-layer, five-agent intrusion detection architecture in which
every remediation-triggering verdict is certified by a quorum of
cryptographically signed notary votes on a Hyperledger Fabric smart contract:

1. **Reflex layer** — calibrated RNN+CNN+DNN ensemble, reliability-weighted
   fusion (CWC) and a confidence-gated reject option, per-flow, in milliseconds;
2. **Deliberative layer** — an LLM invoked only on salient events (agentic
   perceive–reason–act–reflect loop, off the critical path);
3. **Consensus layer** — Ed25519-signed multi-party voting with quorum,
   anti-replay and tamper-evident audit, on-chain (Hyperledger Fabric);
4. **Human-in-the-loop layer** — a governed web console; every administrative
   action (including switching autonomy on/off) is signed and anchored on-chain.

Every number reported in the paper is measured by the code in this repository.

*Un guide détaillé en français est disponible : [README.fr.md](README.fr.md)
et [GUIDE_EXECUTION.md](GUIDE_EXECUTION.md).*

---

## 1. What is (and is not) in this repository

| Included | Location |
|---|---|
| The five agents (Sentinel, Notary ×3, Executor, Data Scientist, Investigator) | `agents/` |
| Fusion, calibration, rejection, metrics | `src/` |
| Go chaincode `validatevote` + HTTP gateway proxy for Fabric | `chaincode/` |
| Human-in-the-loop console (FastAPI backend + React frontend sources) | `hitl/` |
| All measurement scripts behind the paper's tables and figures | `experiments/` |
| Trained detector checkpoints (RNN, CNN, DNN — 15 classes) | `models/SecondModelsWith15Labels/` |
| Deployment bundle (scaler, temperatures, fusion weights, τ) | `results/fusion_experiment/deployment_bundle/` |
| Paper sources, figure scripts, build | `paper_q1/` |

**Not distributed** (see §2 for how to obtain or regenerate):

- **CICIDS2017 dataset** (~1 GB CSV): the University of New Brunswick licence
  does not permit redistribution. Download from
  <https://www.unb.ca/cic/datasets/ids-2017.html>.
- **Agent private keys** (`keys/*.key`): regenerate in one command (§2.3).
- **Large `.npy` artefacts** (data splits, cached probabilities): regenerated
  by the preparation scripts (§4).
- **Compiled console frontend** (`hitl/frontend/dist/`): one `npm run build`.

---

## 2. Setup

Tested on Windows 10/11; the Python stack is OS-agnostic except where noted.
The Fabric network runs under WSL2/Linux (§6).

### 2.1 Python environment (Python 3.10–3.12; TensorFlow does not support 3.13)

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -c "import tensorflow as tf; print('TF', tf.__version__)"
```

> **Known Windows pitfall.** `import tensorflow` must come **before**
> `pandas`/`pyarrow` in any process, otherwise TensorFlow's native
> initialisation fails (`DLL load failed: _pywrap_tensorflow_internal`).
> All shipped scripts already respect this ordering.

### 2.2 Dataset

Download CICIDS2017 from the UNB page above and place the combined 15-class
CSV at the path referenced in `configs/config.yaml`
(`data/cicids2017_complet/`). The exact preprocessing (RobustScaler fitted on
the class-rebalanced set, benign down-sampled to 390,222, 60/20/20 split,
fixed seeds) is fully specified in the paper (§4.2.1) and implemented in
`experiments/original_pipeline_eval.py`.

### 2.3 Agent identities (Ed25519)

```powershell
python -m agents.common.identity          # writes keys/*.key + keys/authorized_signers.json
```

### 2.4 Console frontend (only to use the web console)

```powershell
cd hitl\frontend
npm install && npm run build              # produces hitl/frontend/dist/
```

### 2.5 LLM key (optional)

The deliberative layer uses OpenRouter. Without a key the system still runs,
falling back to a deterministic rule-based analyst.

```powershell
$env:OPENROUTER_API_KEY = "sk-or-v1-<your key>"   # never commit this
```

---

## 3. Quick start: run the full system (simulated ledger)

```powershell
.\.venv\Scripts\Activate.ps1
python -m hitl.backend.main
# browser: http://127.0.0.1:8090
```

Demo credentials (deliberately weak, **demo only**): `admin`/`admin123`,
`analyste`/`analyste123`, `lecteur`/`lecteur123`.

On the dashboard, click **Start detection**, wait ~1–2 min for the Sentinel to
load the three models, then watch: 5/5 agents online, live verdicts, agentic
investigation traces (Investigations tab), quorum votes (Incidents tab),
signed governance actions (Governance tab, admin).

---

## 4. Reproducing the paper's results

All commands from the repo root, environment activated. Outputs land in
`results/`.

| Step | Command | Produces (paper artefact) |
|---|---|---|
| 1. Data preparation | `python experiments\original_pipeline_eval.py --stage prep` | splits under the original protocol (`results/original_pipeline/`) |
| 2. Detector + ensemble evaluation | `python experiments\original_pipeline_eval_tf.py` | per-detector metrics (Table 4), calibration (Table 6), CWC 96.60%, τ=0.70 certified 99.65% / FPR 0.04% (Tables 7–8) |
| 3. Analytics + figures | `python experiments\paper_analytics_original.py` | ROC/PR, reliability, confusion, per-class F1, fusion ablation (Table 7, Fig. 15), risk–coverage, bootstrap CIs, corruption robustness (Figs. 10–19) |
| 4. Reflex throughput | measured in step 2 output | 37,500 flows/s batched (§6.2.2) |
| 5. Consensus latency vs quorum | requires the real Fabric network (§6), then `python -m agents.launch_demo --config configs\agents_fabric.yaml` | ~2 s/signed vote, linear in quorum (Table 9, §6.6) |
| 6. Architecture diagrams | `python paper_q1\make_fig1.py` (etc. `make_fig_*.py`) | Figures 1–8 |
| 7. Console screenshot | `python experiments\capture_console.py` (backend running) | Figure 9 |
| 8. Manuscript build | `cd paper_q1 && npm install && node build_v9.js` | `BAg-IDS_ComputersSecurity_v9.docx` |

Steps 1–4 need only the dataset and the shipped models; no blockchain and no
LLM key. Step 5 is the only one that requires the WSL2/Fabric stack.

---

## 5. Repository layout

```
bag-ids/
├── agents/            # the five agents + common identity/signature code
├── src/               # data loading, calibration, fusion (CWC), rejection, metrics
├── experiments/       # every measurement script behind the paper
├── configs/           # agents.yaml (simulated ledger), agents_live.yaml, agents_fabric.yaml
├── chaincode/         # validatevote (Go) + gateway-proxy (Fabric HTTP gateway)
├── hitl/              # supervision console: backend/ (FastAPI) + frontend/ (React)
├── models/            # trained detector checkpoints (.h5)
├── results/           # measured outputs; deployment_bundle consumed by the agents
├── paper_q1/          # manuscript sources (docx build), figure scripts
└── thesis_report/     # PhD thesis report chapters
```

---

## 6. Real blockchain (Hyperledger Fabric 2.5)

The consensus layer runs against Fabric's `test-network` (one orderer, two
orgs) under WSL2 Ubuntu 22.04 with native Docker Engine. Deploy the
`chaincode/validatevote` Go contract, start the HTTP gateway
(`chaincode/gateway-proxy`, port 8445), then launch the agents with
`configs/agents_fabric.yaml`. Step-by-step instructions (network bring-up,
chaincode deployment, gateway build): [GUIDE_EXECUTION.md](GUIDE_EXECUTION.md)
§4–§5 (French).

---

## 7. Troubleshooting

| Symptom | Fix |
|---|---|
| `DLL load failed: _pywrap_tensorflow_internal` | Import `tensorflow` before `pandas`/`pyarrow`; free RAM (>4 GB); already handled in shipped scripts. |
| Sentinel offline, 0 flows processed | Same TensorFlow issue: free RAM, then Stop → Start detection. |
| Investigations show `rules-fallback` instead of `openrouter` | `OPENROUTER_API_KEY` not set in the backend's terminal, or free-tier model rate-limited (429). |
| Console assets missing | Build the frontend (§2.4). |
| Port 8090 busy | A previous backend is still running; kill the python process. |
| Fabric containers gone after reboot | Keep a WSL session open (`vmIdleTimeout=-1` in `.wslconfig`); `docker start` the containers and relaunch the gateway. |

---

## 8. Provenance and citation

The three detectors were trained and published in:

> M. A. E. Bahri, F. Jemili, O. Korbaa, *Comparative study between ML
> approaches in intrusion detection context*, IEEE AMCAI 2023, Hammamet,
> pp. 1–6, doi:[10.1109/AMCAI59331.2023.10431511](https://doi.org/10.1109/AMCAI59331.2023.10431511).

A citation entry for BAg-IDS will be added upon publication.
