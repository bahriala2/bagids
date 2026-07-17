/* Chapitre 6 — Implementation. */
module.exports = ({ h1, h2, h3, p, r, b, i, eq, li, caption, table, fig }) => [

  h1("Chapter 6. Implementation"),

  p("BAg-IDS is implemented as a working system rather than a paper design, "
  + "and every result in Chapter 7 is produced by the artefact described "
  + "here. This chapter records the technology choices (Section 6.1), the "
  + "realisation of each layer (Section 6.2), the deployment environment "
  + "(Section 6.3), the reproducibility provisions (Section 6.4) and the "
  + "engineering decisions that shape the measurements (Section 6.5)."),

  // ---------------------------------------------------------------- 6.1
  h2("6.1. Technology stack"),

  p([
    r("The detection and agent layers are written in Python. The three "
    + "detectors are Keras/TensorFlow models; calibration, fusion and metrics "
    + "use NumPy, SciPy and scikit-learn. Each of the four agents is an "
    + "independent service built on FastAPI and served by Uvicorn, "
    + "communicating over HTTP with Pydantic-validated JSON messages. The "
    + "deliberative layer talks to a large language model through the "
    + "OpenAI-compatible chat-completions interface, which lets the same "
    + "client address either a cloud model (via OpenRouter) or a local model "
    + "(via LM Studio); a deterministic rule-based fallback keeps the system "
    + "autonomous — and the measurements reproducible — when no model is "
    + "reachable."),
  ]),

  p([
    r("Agent identities are Ed25519 key pairs generated with the "),
    i("cryptography"), r(" library. The consensus layer has two "
    + "interchangeable back ends behind a single interface: a local, "
    + "hash-linked JSONL ledger used for development and unit testing, and a "
    + "Hyperledger Fabric 2.5 network used for the on-chain deployment. The "),
    i("validateVote"),
    r(" chaincode is written in Go with the contract API; a small Go gateway "
    + "process, built on the Fabric Gateway SDK, exposes the chaincode to the "
    + "Python agents as two local HTTP endpoints (submit and evaluate), so "
    + "that switching a notary from the simulated to the on-chain back end is "
    + "a one-line configuration change with no modification to its logic. The "
    + "supervision layer is a FastAPI backend with a React single-page "
    + "frontend; it is trilingual (English, French and Arabic with "
    + "right-to-left layout), role-based, and optional at run time through the "
    + "governed toggle of Section 5.6."),
  ]),

  // ---------------------------------------------------------------- 6.2
  h2("6.2. Realisation of the layers"),

  h3("6.2.1. Sentinel and the detection core"),
  p("The Sentinel loads a self-contained deployment bundle (Section 6.4) and "
  + "reconstructs the exact detection configuration measured offline: the "
  + "three models, their temperatures, the fusion weights and the threshold "
  + "τ. It processes flows in micro-batches, applies temperature scaling and "
  + "the linear opinion pool in vectorised form, and emits a typed Detection "
  + "message for each flow. Beyond its autonomous loop, the Sentinel exposes "
  + "an endpoint that accepts externally supplied flows and classifies them "
  + "through the same pipeline, which is used both for live operation and for "
  + "testing the system against operator-supplied attack traffic."),

  h3("6.2.2. Notary, Executor and Data Scientist"),
  p([
    r("The Notary is deployed as several instances — a leader and its peers — "
    + "that together realise the quorum. The leader receives alerts, collects "
    + "signed endorsements from the peers, submits the votes to the consensus "
    + "backend, and forwards the planned actions once an alert is certified. "
    + "The "), i("Executor"),
    r(" carries out remediations; in the evaluated configuration it runs in a "
    + "dry-run mode that logs each action without touching the network, so "
    + "that experiments are side-effect-free, while the interface to real "
    + "enforcement is in place. The "), i("Data Scientist"),
    r(" polls the Sentinel’s health, computes a sliding rejection rate, and "
    + "escalates suspected drift to deliberation and to a recalibration "
    + "recommendation."),
  ]),

  h3("6.2.3. Consensus backends and the gateway"),
  p([
    r("The simulated ledger implements the "), i("validateVote"),
    r(" semantics in Python over an append-only, hash-linked JSONL file, and "
    + "is covered by a property test suite that checks tamper-evidence, "
    + "signature authenticity, signer authorisation, anti-replay and quorum. "
    + "The Fabric backend implements the same semantics in Go chaincode "
    + "deployed on the test network; the Python client reaches it through the "
    + "Go gateway process over localhost. Because both backends expose an "
    + "identical interface, the Notary is agnostic to which is in use, and "
    + "the difference between them isolates exactly the cost of the "
    + "blockchain."),
  ]),

  h3("6.2.4. The human-in-the-loop console"),
  p("The supervision console is a role-based web application. Its backend "
  + "aggregates agent health and the ledger, manages the approval queue and "
  + "the governed policy, and drives the detection pipeline — starting and "
  + "stopping the agents and reporting the live flow count — from the "
  + "operator interface. Its frontend renders the dashboard, the incident and "
  + "audit views, the governance controls and the toggle, and an attack-test "
  + "view through which an operator submits candidate flows and observes the "
  + "system’s verdicts. Administrative actions performed through the console "
  + "are signed and anchored on-chain as described in Section 5.6.3."),

  // ---------------------------------------------------------------- 6.3
  h2("6.3. Deployment environment"),

  p("The evaluation runs on a single commodity workstation. The Python "
  + "agents, the supervision application and the detectors execute natively "
  + "on Windows; the Fabric network runs under WSL2 (Ubuntu) with a Docker "
  + "engine installed directly in the Linux distribution rather than through "
  + "a desktop virtualisation product. localhost port forwarding between "
  + "Windows and WSL2 lets the Python gateway client reach the Go gateway "
  + "process transparently. This heterogeneous but modest setup is "
  + "deliberate: it demonstrates that the full stack — calibrated ensemble, "
  + "agentic deliberation, permissioned blockchain and a supervision console "
  + "— runs on a single developer machine, which matters both for "
  + "reproducibility and for adoption by teams without a cluster."),

  // ---------------------------------------------------------------- 6.4
  h2("6.4. Reproducibility"),

  p("The pipeline is designed so that a measurement can be regenerated from "
  + "raw data. Data loading fixes the random seed and the stratified "
  + "70/15/15 split; the fitted temperature scalers, fusion weights, "
  + "rejection threshold, class list, feature scaler and the normalised test "
  + "partition are exported together as a self-contained deployment bundle, "
  + "which the Sentinel loads at start-up so that the agents reproduce "
  + "exactly the configuration measured offline. Legacy model files are "
  + "loaded through a compatibility shim that rewrites deprecated layer "
  + "attributes, so the original trained detectors run unchanged under "
  + "current TensorFlow. Each experiment of Chapter 7 is a single command "
  + "that writes its results as JSON, from which the tables and the 300-dpi "
  + "figures are regenerated by a synthesis script; the reported numbers and "
  + "plots are therefore traceable to those files."),

  p([
    r("One reproducibility caveat is stated plainly, as it also bounds the "
    + "interpretation of the detection results. The original training "
    + "preprocessing pipeline — specifically the feature scaler — was not "
    + "preserved with the released models, so the evaluation refits a scaler "
    + "on the training split under the same seed. This is sufficient for the "),
    b("relative"),
    r(" comparisons that carry the thesis’s claims — the calibration effect, "
    + "the τ ablation, consensus latency, and poisoning robustness are all "
    + "internally consistent within one pipeline — but it means the "),
    b("absolute"), r(" per-detector accuracies characterise this "
    + "reconstructed pipeline rather than the detectors’ peak reported "
    + "performance. The point is revisited in Chapter 9."),
  ]),

  // ---------------------------------------------------------------- 6.5
  h2("6.5. Engineering notes"),

  p("Two engineering decisions shape the measurements and are recorded here. "
  + "First, the reflex loop processes flows in micro-batches and performs all "
  + "per-flow work — inference, temperature scaling, fusion, thresholding — "
  + "with vectorised NumPy and TensorFlow operations, which is what keeps "
  + "detection in the millisecond range while the consensus layer operates in "
  + "seconds. Second, the deliberative layer is event-triggered and "
  + "rate-limited: it is invoked only on a certified attack or a burst of "
  + "rejections, and a minimum interval between calls bounds both the load on "
  + "the LLM and its influence on end-to-end latency, so that the language "
  + "model annotates a curated stream of events rather than sitting on the "
  + "per-flow critical path. The complete source, configurations and "
  + "experiment scripts are organised to run from a single repository, and an "
  + "operational guide documents the cold-start sequence for both the "
  + "simulated and the on-chain modes."),
];
