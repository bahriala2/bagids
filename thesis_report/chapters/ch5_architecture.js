/* Chapitre 5 — The BAg-IDS Architecture. */
module.exports = ({ h1, h2, h3, p, r, b, i, eq, li, caption, table, fig }) => [

  h1("Chapter 5. The BAg-IDS Architecture"),

  p([
    r("BAg-IDS is organised as four cooperating layers that separate the "),
    b("speed of detection"), r(", the "), b("deliberation of judgement"),
    r(", the "), b("trust of the decision record"), r(", and the "),
    b("authority of human oversight"),
    r(". Figure 5.1 shows the four layers and the path of a certified attack. "
    + "This chapter presents the design principle behind the layering "
    + "(Section 5.1) and then each layer in turn: the reflex detection layer "
    + "and its calibrated ensemble (Section 5.2), the Conscious Weighted "
    + "Consensus fusion rule (Section 5.3), the deliberative layer "
    + "(Section 5.4), the consensus layer (Section 5.5) and the "
    + "human-in-the-loop layer (Section 5.6)."),
  ]),

  fig("paper_q1/figures/architecture_overview.png", 470),
  caption("Figure 5.1. The four-layer BAg-IDS architecture and the path of a "
    + "certified attack."),

  // ---------------------------------------------------------------- 5.1
  h2("5.1. Design principle: asymmetric cost"),

  p([
    r("The organising principle of BAg-IDS is a deliberate "),
    b("asymmetry of cost"),
    r(" between the layers. The reflex path detects every flow in the "
    + "millisecond range and never blocks on the network or on an external "
    + "model. Only the small fraction of flows that yield a certified attack "
    + "incur the far greater cost of LLM deliberation and on-chain consensus. "
    + "This asymmetry is what makes an agentic, blockchain-backed IDS "
    + "operationally viable: were the deliberation or the consensus applied to "
    + "every flow, the system could not keep pace with a real network. "
    + "Because they are applied only to the decisions that actually trigger "
    + "action, their cost is bounded and their benefit — contextual judgement "
    + "and decentralised, auditable trust — is delivered exactly where it "
    + "matters. Chapter 7 measures both the low cost of the reflex path and "
    + "the higher, quorum-dependent cost of consensus, confirming that the "
    + "asymmetry holds in practice."),
  ]),

  p("The agents realising the four layers are autonomous in the strong sense: "
  + "each pursues its own objective and acts without being polled. The "
  + "Sentinel decides on every flow; the Data Scientist decides, on its own "
  + "initiative, when the system is drifting; the notaries decide "
  + "independently whether to endorse an alert. No single agent is trusted to "
  + "be correct — the premise the consensus layer enforces."),

  // ---------------------------------------------------------------- 5.2
  h2("5.2. Reflex layer: the calibrated neural ensemble"),

  p([
    r("The reflex layer is embodied in the "), b("Sentinel"),
    r(" agent, which classifies every flow through an ensemble of three "
    + "calibrated neural detectors — the RNN, CNN and DNN of Chapter 3 — and "
    + "applies a confidence-gated reject region. For each flow, every model "
    + "produces a posterior over the classes. Each posterior is first "),
    b("calibrated"), r(" by temperature scaling, using the per-model "
    + "temperature learnt offline on the validation split, so that the "
    + "confidences the fusion and rejection steps consume are meaningful. The "
    + "calibrated posteriors are then fused (Section 5.3), and the decision "
    + "rule of Section 3.2 is applied: the predicted class is the arg-max of "
    + "the fused posterior, and the flow is "), i("certified"),
    r(" only if the corresponding confidence reaches the threshold "),
    i("τ"), r("; otherwise it is placed in the reject region."),
  ]),

  p([
    r("The reject region is not an admission of failure but a design feature. "
    + "Flows on which the ensemble is not confident — the inherently "
    + "ambiguous ones — are not forwarded to consensus and remediation, which "
    + "concentrates the expensive trust machinery on the decisions the "
    + "ensemble is sure of and simultaneously suppresses false alarms. The "
    + "rejected flows are not discarded: their rate is a signal that the Data "
    + "Scientist agent monitors as a proxy for distribution drift "
    + "(Section 5.4). The whole reflex computation — inference, temperature "
    + "scaling, fusion and thresholding — is performed in vectorised form "
    + "over micro-batches of flows, which is what keeps it in the "
    + "millisecond-per-flow range measured in Chapter 7."),
  ]),

  // ---------------------------------------------------------------- 5.3
  h2("5.3. Conscious Weighted Consensus"),

  p([
    r("The heart of the detection layer is the fusion rule, which we call "),
    b("Conscious Weighted Consensus (CWC)"),
    r(". Rather than combining the detectors with fixed weights, CWC weights "
    + "each detector by its "), b("recent, calibrated reliability"),
    r(". Concretely, the weight of model "), i("m"),
    r(" is proportional to its precision on a validation stream:"),
  ]),

  eq("w_m = prec_m / Σ_k prec_k,"),

  p([
    r("and the calibrated posteriors are fused by the linear opinion pool of "
    + "Section 3.3, P̃(c | x) = Σ_m w_m · P(c | x, M_m). The adjective "),
    i("conscious"),
    r(" captures the essential property: the ensemble is aware of how "
    + "reliable each member currently is, and it discounts members whose "
    + "reliability has fallen. In the real-time pipeline the weights are "
    + "maintained by a mini-batch Dirichlet update over a sliding window, so "
    + "that they track changes in each detector’s trustworthiness; in the "
    + "offline evaluation they are estimated once on the validation split."),
  ]),

  p([
    r("This design has a consequence that goes well beyond accuracy "
    + "aggregation. If a detector is corrupted — by label-flipping poisoning, "
    + "for instance — its precision on the validation stream falls, and CWC "
    + "therefore reduces its weight automatically, "),
    b("without the system ever having to detect that an attack is underway"),
    r(". A fully corrupted detector is driven to a near-zero weight and is, "
    + "in effect, excluded from the decision. Chapter 7 measures this: when "
    + "the strongest detector is fully poisoned, the ensemble loses only "
    + "about one accuracy point while the corrupted detector’s weight "
    + "collapses. CWC is thus simultaneously the accuracy mechanism and the "
    + "poisoning defence of BAg-IDS, satisfying design goal G1."),
  ]),

  // ---------------------------------------------------------------- 5.4
  h2("5.4. Deliberative layer"),

  p([
    r("Above the reflex path sits the "), b("deliberative layer"),
    r(", which applies large-language-model reasoning — but only to salient "
    + "events. The Sentinel invokes deliberation on two triggers: a certified "
    + "attack, and a burst of consecutive rejections that may signal drift or "
    + "a novel pattern. On such an event the Sentinel assembles a compact, "
    + "structured summary — the fused verdict and its confidence, the "
    + "per-model votes, the top posterior classes and recent verdict counts — "
    + "and submits it to the LLM under a strict instruction to return a "
    + "single structured object containing a "), i("severity"),
    r(" (low, medium, high or critical), a technical "), i("rationale"),
    r(", and a list of "), i("recommended actions"),
    r(" drawn from a fixed vocabulary (block, rate-limit, isolate, "
    + "recalibrate, retrain, notify, no-op)."),
  ]),

  p([
    r("Two backends are supported behind an identical interface — a cloud "
    + "model and a locally served model — and the system tries them in a "
    + "configured order. Crucially, if no LLM backend is reachable, a "
    + "deterministic "), b("rule-based fallback"),
    r(" produces a valid deliberation from the same event summary. The "
    + "deliberative layer therefore degrades gracefully and never blocks "
    + "autonomy: the pipeline continues to detect, certify and remediate even "
    + "with no language model available, a property that also makes the "
    + "measurements of Chapter 7 reproducible. Deliberation is additionally "
    + "rate-limited by a minimum interval between calls, bounding both the "
    + "load on the model and its influence on end-to-end latency."),
  ]),

  p([
    r("Complementing the Sentinel, the "), b("Data Scientist"),
    r(" agent is a proactive maintenance agent. It continuously observes the "
    + "Sentinel’s rejection rate as a proxy for distribution drift and, when "
    + "a threshold is crossed, deliberates — by the same LLM-or-rules "
    + "mechanism — over whether to recommend recalibration or retraining. "
    + "This is the intended second line of defence against the slow, partial "
    + "poisoning that CWC alone absorbs least well (Chapter 8)."),
  ]),

  // ---------------------------------------------------------------- 5.5
  h2("5.5. Consensus layer: permissioned blockchain"),

  p([
    r("The consensus layer converts a single agent’s alert into a "),
    b("collectively certified, tamper-evident record"),
    r(". Rather than trusting the Sentinel, or any one notary, BAg-IDS "
    + "requires a quorum of independent "), b("Notary"),
    r(" agents to endorse an alert before it is committed and before the "
    + "Executor may act. Endorsement, ordering and commitment are realised on "
    + "the Hyperledger Fabric ledger of Chapter 3."),
  ]),

  h3("5.5.1. Independent validation and signed votes"),
  p([
    r("When the Sentinel raises an alert, it is sent to a leading notary, "
    + "which requests endorsements from its peers. Each notary "),
    b("re-validates the alert independently"),
    r(" — checking that an attack verdict genuinely exceeds τ and that the "
    + "claimed class is the arg-max of the pooled posteriors — rather than "
    + "trusting the Sentinel’s assertion. A notary that agrees casts a vote "
    + "consisting of its decision signed with its Ed25519 private key over a "
    + "canonical serialisation of the vote payload. Because each notary "
    + "revalidates and signs, a compromised Sentinel cannot manufacture "
    + "consensus by asserting a verdict, and a compromised host cannot forge "
    + "a vote on another notary’s behalf."),
  ]),

  h3("5.5.2. The validateVote chaincode"),
  p([
    r("The consensus logic is expressed as a smart contract, the "),
    i("validateVote"), r(" chaincode. It maintains, per alert, the set of "
    + "received votes and a certification flag, and it enforces four "
    + "invariants on every submitted vote: (i) the signer is an authorised "
    + "notary in the registry; (ii) the Ed25519 signature over the canonical "
    + "payload is valid; (iii) the notary has not already voted on this alert "
    + "(anti-replay); and (iv) once the number of valid approving votes "
    + "reaches the quorum, the contract itself seals an "),
    i("ALERT_CERTIFIED"),
    r(" record. Because these checks run inside the chaincode and are "
    + "endorsed by the peers of two independent organisations, a compromised "
    + "or malicious agent cannot forge an endorsement, cannot certify an "
    + "alert alone, and cannot tamper with the record after the fact — "
    + "satisfying goals G2, G3 and G4."),
  ]),

  p([
    r("The same logic is first specified and unit-tested against a "
    + "hash-chained "), i("simulated ledger"),
    r(", then deployed unchanged in semantics as Fabric chaincode, so that "
    + "the notary agents switch from the simulated to the on-chain backend "
    + "without any change to their reasoning. This two-stage approach — "
    + "specify and test the trust logic locally, then deploy it on the real "
    + "blockchain — is a deliberate methodological choice that Chapter 6 "
    + "details and Chapter 7 exploits to measure the precise cost the "
    + "blockchain adds."),
  ]),

  // ---------------------------------------------------------------- 5.6
  h2("5.6. Human-in-the-loop supervision layer"),

  p([
    r("The three preceding layers form a fully autonomous pipeline. Real "
    + "security operations, however, demand a point of "),
    b("human authority"),
    r(" — to review what the agents are doing, to gate high-impact actions, "
    + "and to tune the system’s posture. BAg-IDS therefore adds a fourth "
    + "layer: a role-based supervision console, the operator-facing face of "
    + "the system. Crucially, this layer is "),
    b("optional and switchable"),
    r(": a single governed toggle turns human oversight on or off, so the "
    + "same deployment can run supervised or fully autonomous on demand."),
  ]),

  h3("5.6.1. Observability and audit"),
  p([
    r("The console aggregates, in real time, the health of the four agents, "
    + "the live verdict stream and the incident list, and it exposes the "
    + "blockchain ledger as a first-class "), b("audit view"),
    r(". Because certified decisions, votes and their endorsements are read "
    + "directly from the tamper-evident ledger, what the operator sees is not "
    + "a mutable application log but the same immutable record the consensus "
    + "layer produced. Three roles — reader, analyst and administrator — "
    + "partition access: reading is open to all authenticated users, incident "
    + "approval requires the analyst role, and governance requires the "
    + "administrator role."),
  ]),

  h3("5.6.2. Human-gated remediation"),
  p("When supervision is enabled, remediations whose severity exceeds a "
  + "configurable level are not executed immediately: after the notaries "
  + "certify the alert on-chain, the planned actions are held in an approval "
  + "queue, and the Executor acts only once an analyst approves them; a "
  + "rejection cancels them. When supervision is disabled, the queue is "
  + "bypassed and the Executor acts autonomously, exactly as in the "
  + "three-layer configuration. The gate is deliberately fail-open with "
  + "respect to availability: if the supervision layer is unreachable, the "
  + "agents fall back to autonomous action rather than stalling the response "
  + "— oversight is a control surface, not a single point of failure."),

  h3("5.6.3. Governed, auditable administration"),
  p([
    r("A supervision layer that can lower the rejection threshold, shrink the "
    + "quorum, or disable oversight is itself a high-value target. BAg-IDS "
    + "closes this loop by treating every administrative action as a "),
    b("first-class, signed transaction"),
    r(". Toggling supervision, changing a governed parameter (τ, quorum, "
    + "Executor mode) and every manual approval are serialised, signed by a "
    + "governance identity, and anchored on the same blockchain via a "),
    i("RecordGovernance"), r(" contract call that verifies the signature "
    + "before committing. The chaincode distinguishes the "),
    i("human actor"), r(" (the operator account, stored as metadata) from the "),
    i("cryptographic signer"),
    r(" (the registered governance identity), binding the human chain of "
    + "responsibility to an unforgeable record. The result is a system in "
    + "which even the administrator is auditable — the ledger holds not only "
    + "what the agents decided, but every human intervention that shaped their "
    + "behaviour, including the decision to remove oversight itself. This "
    + "satisfies goal G5 and is verified in Chapter 8."),
  ]),
];
