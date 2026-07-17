/* Section 4 — BAg-IDS Architecture.
 * Structure en DEUX parties : (I) architecture globale + Figure 1 ;
 * (II) architecture detaillee reproductible, couche par couche, modele
 * par modele + Figure 3 (+ Table 3 : architectures exactes). */
module.exports = ({ h1, h2, h3, p, r, b, i, eq, li, caption, table, fig }) => [

  h1("4. The BAg-IDS Architecture"),

  p([
    r("This section presents our contribution in two complementary parts. "),
    b("Part I (Section 4.1)"),
    r(" gives the global architecture: the four layers, the five agents, and "
    + "the end-to-end path of a network flow, at the level of abstraction "
    + "needed to understand the design decisions. "),
    b("Part II (Section 4.2)"),
    r(" then descends into a detailed, reproducible specification of every "
    + "layer and every model (exact network architectures, calibration "
    + "procedure and fitted parameters, fusion equations, message and vote "
    + "formats, chaincode invariants, and deployment topology), so that the "
    + "system can be re-implemented from the paper alone. Each subsystem "
    + "specified here is evaluated in isolation in Section 6, where we also "
    + "measure how its output quality conditions the subsystem that consumes "
    + "it."),
  ]),

  // ==================================================================
  // PART I — GLOBAL ARCHITECTURE
  // ==================================================================
  h2("4.1. Part I: global architecture"),

  h3("4.1.1. Four layers, one asymmetry"),

  p([
    r("BAg-IDS is organised as four cooperating layers that separate the "),
    b("speed of detection"), r(", the "), b("deliberation of judgement"),
    r(", the "), b("trust of the decision record"), r(", and the "),
    b("authority of human oversight"),
    r(" (Figure 1). The "), i("reflex detection layer"),
    r(" performs per-flow inference in the millisecond range through a "
    + "calibrated ensemble of neural detectors and a confidence-gated "
    + "rejection rule. The "), i("deliberative layer"),
    r(" is invoked only on salient events (a certified attack or a burst of "
    + "rejections) and applies a large language model (LLM) to reason about "
    + "severity and remediation. The "), i("consensus layer"),
    r(" anchors every certified decision on a permissioned blockchain, where "
    + "independent notary agents cross-validate and cryptographically endorse "
    + "the outcome before any remediation is executed. The "),
    i("human-in-the-loop supervision layer"),
    r(" gives a security operator a governed, auditable point of control, "
    + "and can be switched off to cede full autonomy to the agents."),
  ]),

  p([
    r("The design follows a "), b("reflex/deliberative hybrid"),
    r(" that is deliberately asymmetric in cost. Thousands of flows per "
    + "second traverse the reflex path, which never blocks on the network or "
    + "on an external model; only the small fraction of flows that yield a "
    + "certified attack incur the cost of LLM deliberation and on-chain "
    + "consensus. This asymmetry is what makes an agentic, blockchain-backed "
    + "IDS operationally viable, and it is quantified subsystem by subsystem "
    + "in Section 6."),
  ]),

  h3("4.1.2. Agent roles"),

  p([
    r("BAg-IDS is realised as five autonomous agents, each an independent "
    + "process exposing an HTTP interface and running its own perception, "
    + "decision and action loop:"),
  ]),

  li([b("Sentinel: "), r("the detection agent. It ingests network flows, "
    + "runs the calibrated ensemble, applies the Conscious Weighted Consensus "
    + "fusion, and, for certified attacks, triggers deliberation before "
    + "emitting a signed alert.")]),
  li([b("Notary: "), r("the consensus agent, deployed as several independent "
    + "instances. Each notary re-validates an incoming alert on its own and "
    + "casts a cryptographically signed vote; the outcome is committed to the "
    + "ledger only when a quorum of valid endorsements is reached.")]),
  li([b("Executor: "), r("the remediation agent. It carries out the actions "
    + "attached to a certified, quorum-approved alert (block, rate-limit, "
    + "isolate, notify) and records their execution.")]),
  li([b("Data Scientist: "), r("the maintenance agent. It continuously "
    + "monitors the health of the Sentinel (chiefly the rolling rejection "
    + "rate as a proxy for distribution drift) and proactively recommends "
    + "recalibration or retraining when a threshold is crossed.")]),
  li([b("Investigator: "), r("the triage agent. On a certified attack it "
    + "conducts an autonomous, multi-step investigation (querying the ledger "
    + "for related incidents, correlating them to detect campaigns, and "
    + "reasoning to a prioritised incident report) with its conclusion "
    + "anchored on-chain.")]),

  p([
    r("Agents are autonomous in the strong sense: each pursues its own "
    + "objective and acts without being polled. The Sentinel decides on every "
    + "flow; the Data Scientist decides, on its own initiative, when the "
    + "system is drifting; the notaries decide independently whether to "
    + "endorse. No single agent is trusted to be correct, which is the "
    + "premise the consensus layer enforces. Figure 2 contrasts the five "
    + "agents side by side (what each perceives, decides and does, how it "
    + "uses or deliberately does not use the LLM, and what it writes "
    + "on-chain), making the division of labour, and the deliberate "
    + "asymmetry of LLM usage across the agents, directly comparable."),
  ]),

  fig("paper_q1/figures/agents_comparison.png", 620),
  caption("Figure 2. The five BAg-IDS agents compared: mission, "
    + "perception, decision, action, LLM usage and on-chain footprint. "
    + "Only the Sentinel (event-triggered), the notaries (advisory only) "
    + "and the Investigator (multi-step reasoning) touch the LLM; the "
    + "Executor and Data Scientist are deliberately deterministic."),

  h3("4.1.3. Life of a flow"),

  p([
    r("The global data path is as follows. A flow enters the reflex layer "
    + "and receives one of three verdicts: "), b("benign"),
    r(" (passed, no further cost), "), b("rejected"),
    r(" (withheld from automation and streamed to the Data Scientist as a "
    + "drift signal), or "), b("attack"),
    r(". Only the attack verdict propagates: the Sentinel attaches an LLM "
    + "deliberation, signs the alert, and submits it to the notaries. Each "
    + "notary independently re-validates the decision and votes; when the "
    + "chaincode observes a quorum of valid signed votes it seals an "),
    i("ALERT_CERTIFIED"),
    r(" record. Certification triggers two parallel consumers: the "
    + "Investigator opens an autonomous investigation, and the remediation "
    + "path either executes immediately (autonomous mode) or is held in the "
    + "operator’s approval queue (supervised mode). Every step (alert, "
    + "votes, certification, investigation conclusion, human approval, and "
    + "every governance action) lands on the same immutable ledger."),
  ]),

  // ==================================================================
  // PART II — DETAILED ARCHITECTURE
  // ==================================================================
  h2("4.2. Part II: detailed, reproducible architecture"),

  p([
    r("Figure 3 expands Figure 1 into the complete technical specification: "
    + "the data plane, the exact detector architectures and their "
    + "calibration temperatures, the fusion and rejection rules, the three "
    + "deliberative agents, the consensus machinery with its chaincode "
    + "invariants, and the supervision layer. The remainder of this section "
    + "walks through Figure 3 top to bottom; all numeric values are the ones "
    + "used in the evaluation of Section 6."),
  ]),

  fig("paper_q1/figures/architecture_detailed.png", 620),
  caption("Figure 3. Detailed BAg-IDS architecture: data plane, exact "
    + "detector stacks and fitted calibration temperatures, Conscious "
    + "Weighted Consensus, rejection gate, deliberative agents, consensus "
    + "layer with the validateVote invariants, and governed human-in-the-"
    + "loop supervision. Ports identify the concrete deployed services."),

  h3("4.2.1. Data plane and preprocessing"),

  p([
    r("All detectors consume the same flow representation, produced by "
    + "the "), b("exact preprocessing under which they were trained"),
    r(" [56], which we recovered from the original training notebook and "
    + "reproduce seed for seed. The CICIDS2017 corpus (2.42 million flows "
    + "after concatenating the daily captures and dropping duplicates, "
    + "NaN and infinite values) yields "), i("F"),
    r(" = 78 numeric flow features per record and 15 classes (benign plus "
    + "fourteen attack families, 390,222 attack flows in total). The "
    + "corpus is then class-balanced by down-sampling benign traffic to "
    + "the attack count (sklearn resample, replace=true, seed 123), "
    + "giving 780,444 flows; features are scaled with a "),
    b("RobustScaler"),
    r(" (median/IQR, robust to the heavy-tailed flow statistics) fitted "
    + "on the balanced corpus; labels are integer-encoded in "
    + "lexicographic order; and the data are split 60/20/20 into "
    + "training, validation and test partitions (test_size 0.2 then "
    + "validation 0.25 of the remainder, seed 1). The test partition "
    + "contains 156,089 flows. The validation partition serves three "
    + "distinct purposes downstream (fitting the calibration "
    + "temperatures, estimating the fusion weights, and monitoring drift) "
    + "and is never used for training or testing. The recurrent and "
    + "convolutional detectors receive the feature vector reshaped to "
    + "(78, 1); the dense detector receives the flat (78,) vector."),
  ]),

  h3("4.2.2. Layer 1a: the three neural detectors"),

  p([
    r("Figure 4 summarises the whole reflex layer end to end, showing the "
    + "role of each stage described in Sections 4.2.2 to 4.2.4. The reflex "
    + "layer classifies each flow with an ensemble of "), i("M"),
    r(" = 3 heterogeneous deep detectors with distinct inductive biases "
    + "(recurrence, convolution and dense projection), so that their errors "
    + "are only partially correlated. The detectors are not new to this "
    + "paper: they were trained and evaluated on CICIDS2017 in our prior "
    + "comparative study [56], and are reused here exactly as released, "
    + "which both documents their provenance and lets this paper focus on "
    + "the architecture built around them. Table 3 gives the exact "
    + "architectures as deployed (layer types, dimensions, activations, "
    + "dropout rates and parameter counts). All three end in a 15-way "
    + "softmax; given a flow "), i("x"), r(", detector "), i("M"),
    r("m produces a posterior P(c | x, Mm) over the "), i("C"),
    r(" = 15 classes."),
  ]),

  table(
    ["Detector", "Exact layer stack (as deployed)", "Input", "Params"],
    [
      ["RNN",
       "SimpleRNN(32, ReLU) → Dropout(0.1) → Flatten → Dense(32)+LeakyReLU "
       + "→ Dense(16)+LeakyReLU → Dense(15, softmax)",
       "(78, 1)", "81,775"],
      ["CNN",
       "Conv1D(64, k=3)+LeakyReLU → MaxPool(2) → Dropout(0.3) → Flatten → "
       + "Dense(64)+LeakyReLU → Dense(32)+LeakyReLU → Dense(15, softmax)",
       "(78, 1)", "158,543"],
      ["DNN",
       "Dense(256, ReLU) → Dropout(0.1) → Dense(15, softmax)",
       "(78,)", "24,079"],
    ],
    [1100, 5500, 1200, 1160],
    {}),
  caption("Table 3. Exact architectures of the three deployed detectors "
    + "(Keras). Together with the preprocessing of Section 4.2.1 and the "
    + "parameters of Sections 4.2.3 to 4.2.4, this specification is "
    + "sufficient to reproduce the reflex layer."),

  h3("4.2.3. Layer 1b: confidence calibration (temperature scaling)"),

  p([
    r("Raw neural posteriors are notoriously over-confident, which is "
    + "damaging when a downstream consensus rule must weigh models against "
    + "one another and reject low-confidence decisions. Every detector is "
    + "therefore calibrated with "), b("temperature scaling"),
    r(": a single scalar "), i("T"),
    r("m > 0 per model is fitted by minimising the negative log-likelihood "
    + "on the validation partition (bounded scalar search on "
    + "Tm ∈ [0.05, 10]), and posteriors are recomputed as "
    + "softmax(zm / Tm) from the logits zm. The fitted values on CICIDS2017 "
    + "are Trnn = 1.93, Tcnn = 1.63 and Tdnn = 1.99, moderate temperatures "
    + "that quantify a mild in-distribution over-confidence (they grow "
    + "dramatically when the same models are fed out-of-distribution "
    + "inputs, Section 8.3.1). Temperature scaling preserves the arg-max, "
    + "so per-model accuracy is unchanged; what it changes, measurably "
    + "(Sections 6.3 and 6.4), is the comparability of the confidence scores "
    + "that the fusion weights and the rejection rule depend on."),
  ]),

  h3("4.2.4. Layer 1c: Conscious Weighted Consensus and the reject gate"),

  p([
    r("The heart of the reflex layer is the fusion of the calibrated "
    + "detectors into a single, trust-aware decision, which we call "),
    b("Conscious Weighted Consensus (CWC)"),
    r(": the ensemble is “conscious” of each member’s historical "
    + "reliability and weighs its vote accordingly. Fusion is a linear "
    + "opinion pool of the calibrated posteriors (Eq. 1) with weights "
    + "proportional to each detector’s weighted validation precision "
    + "(Eq. 2), followed by a confidence-gated decision with an explicit "
    + "rejection region (Eq. 3):"),
  ]),

  eq("P̃(c | x) = Σm  wm · softmax(zm / Tm)", "1"),
  eq("wm = precm / Σk preck", "2"),
  eq("ĉ = argmax_c P̃(c | x)  if  max_c P̃(c | x) ≥ τ,   else REJECT", "3"),

  p([
    r("On clean CICIDS2017 validation data the three precisions are nearly "
    + "equal, giving near-uniform weights (wrnn = 0.332, wcnn = 0.323, "
    + "wdnn = 0.345), so in the clean regime the CWC behaves close to a "
    + "uniform pool, with a small measured margin over it (Section 6.4). "
    + "The decisive value of Eq. 2 is a "),
    b("security mechanism"),
    r(". If a detector is corrupted, for instance by label-flipping "
    + "poisoning, its validation precision collapses, its weight shrinks "
    + "automatically, and its influence on the fused decision vanishes "),
    b("without any explicit attack detection"),
    r(" (measured in Section 6.7). For continuous operation the weights "
    + "follow a mini-batch Dirichlet update: starting from a uniform prior "
    + "αm = 1, each window of W certified flows increments αm by the number "
    + "of correct certified detections attributed to Mm, weights are "
    + "renormalised, and a decay factor down-weights ageing evidence so the "
    + "“consciousness” tracks concept drift."),
  ]),

  p([
    r("A remark on novelty is in order. Algorithmically, the CWC is "
    + "deliberately assembled from standard, well-understood components: "
    + "a precision-weighted linear opinion pool over temperature-scaled "
    + "posteriors with a reject option. The name designates the "),
    i("architectural role"),
    r(" this reliability-weighted calibrated fusion plays in BAg-IDS (the "
    + "stage that makes downstream consensus and rejection meaningful and "
    + "that absorbs a corrupted member), not an algorithmic invention. The "
    + "contribution of this paper is architectural and empirical, namely "
    + "the co-design and subsystem-by-subsystem measurement of the full "
    + "stack, rather than a new fusion algorithm."),
  ]),

  p([
    r("The reject gate (Eq. 3, τ = 0.70 by default) makes the layer’s "
    + "output ternary: "), b("benign"), r(", "), b("attack"), r(", or "),
    b("rejected"),
    r(". Rejection is not a failure but a routing decision with two "
    + "consumers: rejected flows are withheld from automated remediation, "
    + "and their rate is streamed to the Data Scientist as the primary "
    + "drift signal. The choice of τ therefore simultaneously sets the "
    + "reliability of what Layer 3 will certify and the load offered to "
    + "Layer 2, a coupling we measure explicitly in Section 6.5."),
  ]),

  fig("paper_q1/figures/layer1_reflex.png", 610),
  caption("Figure 4. The reflex detection layer at a glance. A raw flow "
    + "passes through three heterogeneous detectors (diverse errors), "
    + "temperature calibration (comparable confidences), the Conscious "
    + "Weighted Consensus (one trust-aware posterior, self-excluding a "
    + "poisoned member) and the reject gate, yielding one of three "
    + "verdicts. The layer runs on every flow at line rate and never "
    + "blocks; only ATTACK is escalated to Layers 2 and 3, and REJECT feeds "
    + "drift monitoring."),

  h3("4.2.5. Layer 2: deliberation, single-shot judgement and the "
     + "agentic Investigator"),

  p([
    r("A certified attack is necessary but not sufficient to act: the "
    + "system must still decide "), i("how severe"),
    r(" the event is and "), i("what to do"),
    r(" about it. The Sentinel assembles a compact event summary (fused "
    + "verdict and confidence, top pooled posteriors, per-model decisions, "
    + "recent verdict counts) and submits it to an LLM under a strict "
    + "instruction to return a single structured object: a "), i("severity"),
    r(" (low/medium/high/critical), a technical "), i("rationale"),
    r(", and "), i("recommended actions"),
    r(" from a fixed vocabulary (block, rate-limit, isolate, recalibrate, "
    + "retrain, notify, no-op). Invocation is sparing (on a certified "
    + "attack or a rejection burst) and rate-limited. Two backends sit "
    + "behind one interface (a cloud model via OpenRouter, a local model "
    + "via LM Studio), and if no LLM is reachable a deterministic "),
    b("rule-based fallback"),
    r(" produces a valid deliberation from the same summary: the layer "
    + "degrades gracefully, never blocks autonomy, and remains "
    + "reproducible."),
  ]),

  p([
    r("Whereas the Sentinel’s deliberation is single-shot, the "),
    b("Investigator"),
    r(" embodies agency in the stronger sense: an explicit agent loop ("),
    i("perceive → reason → act (tools) → reflect → conclude"),
    r(") in which the agent itself decides which tools to invoke. Its "
    + "tools query the ledger for recent incidents of the same class and "
    + "correlate them in time to detect bursts indicative of a coordinated "
    + "campaign; an internal memory tracks campaigns already observed. The "
    + "output is a structured incident report plus the full trace of steps "
    + "(exposed verbatim in the supervision console), and the conclusion "
    + "is itself anchored on-chain, so even the agent’s autonomous "
    + "reasoning is auditable. Two boundaries are deliberate: the "
    + "Investigator runs "), i("after"),
    r(" certification and off the critical path, and no quantitative claim "
    + "of Section 6 depends on this non-deterministic layer, a separation "
    + "we regard as methodologically essential when an LLM is placed in an "
    + "otherwise measurable system."),
  ]),

  fig("paper_q1/figures/layer2_deliberation.png", 610),
  caption("Figure 5. The deliberative layer at a glance. A rare, "
    + "rate-limited trigger (a certified attack or a rejection burst) "
    + "invokes either the Sentinel’s single-shot deliberation (A) or the "
    + "Investigator’s multi-step agentic loop (B: perceive → reason → act "
    + "with tools → reflect). Both target the same LLM behind a graceful "
    + "OpenRouter → LM Studio → rules fallback, and their outputs "
    + "(structured severity/actions, and an on-chain-anchored incident "
    + "report) enrich but never alter the deterministic certification, "
    + "so autonomy and reproducibility hold even with no LLM reachable."),

  h3("4.2.6. Layer 3: consensus, identities, votes, and the "
     + "validateVote chaincode"),

  p([
    r("Figure 6 details the deployed Hyperledger Fabric network: two "
    + "organisations, each with its certificate authority and one "
    + "endorsing peer carrying the validateVote chaincode and a full "
    + "ledger copy; an etcdraft ordering service (default 2 s "
    + "BatchTimeout); and the HTTP-to-gRPC gateway through which the "
    + "agents invoke the contract. The endorsement policy requires the "
    + "signatures of both organisations on every transaction, so no "
    + "single organisation can commit state alone. Figure 7 then shows "
    + "the complete consensus sequence for one alert, from the "
    + "Sentinel’s signed alert to the sealed certification, which is "
    + "also the key to reading the latency measurements of Section 6.6."),
  ]),

  fig("paper_q1/figures/fabric_anatomy.png", 580),
  caption("Figure 6. Anatomy of the deployed Hyperledger Fabric network: "
    + "organisations, certificate authorities, endorsing peers with the "
    + "validateVote chaincode, ordering service, replicated ledger, and "
    + "the agents’ HTTP gateway. Both organisations must endorse every "
    + "transaction."),

  fig("paper_q1/figures/consensus_sequence.png", 600),
  caption("Figure 7. Consensus sequence for one alert: signed alert, "
    + "RecordAlert transaction, independent notary re-validation, one "
    + "ValidateVote transaction per vote (with the four chaincode "
    + "invariants), quorum sealing of ALERT_CERTIFIED, and the "
    + "certification event that releases the downstream agents. Each "
    + "transaction follows Fabric’s execute–order–validate path (~2.06 s "
    + "measured, Table 9)."),

  p([
    r("The consensus layer converts a single agent’s alert into a "
    + "collectively certified, tamper-evident record. Every agent holds an "
    + "Ed25519 key pair; the public keys of authorised notaries are "
    + "registered in the ledger state. A notary endorses an alert only "
    + "after re-validating it independently (checking that the verdict "
    + "exceeds τ and that the claimed class is the arg-max of the pooled "
    + "posteriors) and signs its vote over the canonical serialisation of "
    + "the vote payload. The "), i("validateVote"),
    r(" chaincode (Go) enforces four invariants on every submitted vote: "
    + "(i) the signer is an authorised notary; (ii) the Ed25519 signature "
    + "over the canonical payload verifies against the registered key; "
    + "(iii) the notary has not already voted on this alert (defeating "
    + "replay); and (iv) once valid approving votes reach the quorum "
    + "(2 of 3 in our deployment), the contract itself seals an "),
    i("ALERT_CERTIFIED"),
    r(" record. Because these checks run inside the chaincode and are "
    + "endorsed by peers of two independent organisations, a compromised "
    + "agent cannot forge an endorsement, cannot certify alone, and cannot "
    + "tamper with the record afterwards. The identical logic is first "
    + "unit-tested against a hash-chained simulated ledger, then deployed "
    + "unchanged in semantics as Fabric chaincode, which is also what "
    + "lets Section 6.6 isolate the infrastructure cost of Fabric from the "
    + "intrinsic cost of the consensus rule."),
  ]),

  p([
    r("The scope of this re-validation must be stated precisely. Each "
    + "notary checks the "), i("internal consistency"),
    r(" of the alert (threshold and arg-max over the posteriors carried "
    + "in the alert itself) and the authenticity of every signature; it "
    + "does not independently re-classify the underlying flow. The quorum "
    + "therefore guarantees the "), b("authenticity and consistency"),
    r(" of the certified record, and that no single agent can certify "
    + "alone; it does not, by itself, guarantee the "), i("veracity"),
    r(" of an alert whose posteriors were fabricated wholesale by a fully "
    + "compromised Sentinel. Section 7.2 analyses this boundary and the "
    + "compensating controls (behavioural rate monitoring, human review); "
    + "notary-side independent re-classification is an explicit direction "
    + "for future work, with a measurable latency cost."),
  ]),

  p([
    r("A notary may optionally attach an LLM "), b("second opinion"),
    r(" to its endorsement, a brief natural-language judgement of whether "
    + "the alert looks genuine. This is deliberately "), b("advisory only"),
    r(": the endorsement decision remains the deterministic re-validation, "
    + "the signed vote payload does not contain the opinion, and the "
    + "opinion never changes whether the notary approves. The advice is "
    + "logged separately and surfaced for audit, adding contextual "
    + "judgement without introducing a non-deterministic factor into the "
    + "cryptographic consensus."),
  ]),

  h3("4.2.7. Layer 4: governed human-in-the-loop supervision"),

  p([
    r("Figure 8 summarises the human’s role in one view: "),
    b("(a)"),
    r(" the capability ladder of the three operator roles (the reader "
    + "observes, the analyst additionally decides, the administrator "
    + "additionally governs); "), b("(b)"),
    r(" the two operating modes side by side, showing exactly where the "
    + "human sits on the decision path in supervised mode (the approval "
    + "queue for severity-gated remediations) and that no human is on "
    + "the path in autonomous mode; and "), b("(c)"),
    r(" the accountability rule that makes the whole layer trustworthy: "
    + "every human action is itself a signed, on-chain transaction."),
  ]),

  fig("paper_q1/figures/hitl_layer.png", 600),
  caption("Figure 8. Layer 4, the human’s role: (a) the reader ⊂ "
    + "analyst ⊂ admin capability ladder; (b) the supervised versus "
    + "autonomous decision paths (one governed toggle apart, fail-open "
    + "on console failure); (c) every human action is a signed "
    + "transaction anchored on-chain (RecordGovernance)."),

  p([
    r("The supervision console (React front-end, FastAPI back-end, "
    + "trilingual FR/EN/AR) is the operator-facing face of the system, "
    + "with three roles partitioning access: reading is open to all "
    + "authenticated users, incident approval requires the analyst role, "
    + "and governance the administrator role. It aggregates in real time "
    + "the health of the agents, the live verdict stream, the incident "
    + "list, the Investigator’s reasoning traces, and exposes the "
    + "blockchain as a first-class audit view: what the operator sees is "
    + "the immutable record itself, not a mutable application log. When "
    + "supervision is enabled, remediations above a configurable severity "
    + "are held in an approval queue and the Executor acts only on analyst "
    + "approval; when disabled, the queue is bypassed and the agents act "
    + "autonomously. The gate is fail-open with respect to availability: "
    + "if the supervision layer is unreachable, agents fall back to "
    + "autonomous action rather than stalling the response."),
  ]),

  p([
    r("Because a console that can lower τ, shrink the quorum, or disable "
    + "oversight is itself a high-value target, every administrative "
    + "action is a "), b("first-class, signed transaction"),
    r(": toggling supervision, changing a governed parameter, and every "
    + "manual approval are serialised, signed by a registered governance "
    + "identity, and anchored on-chain via a "), i("RecordGovernance"),
    r(" contract call that verifies the signature before committing. The "
    + "chaincode distinguishes the human actor (recorded as metadata) from "
    + "the cryptographic signer, binding the human chain of responsibility "
    + "to an unforgeable record: the ledger holds not only what the agents "
    + "decided, but every human intervention that shaped their behaviour."),
  ]),

  h3("4.2.8. Deployment topology and reproducibility summary"),

  p([
    r("The deployed topology (ports in Figure 3) is: Sentinel :8001, "
    + "Notary leader :8002 with peers :8012 and :8022, Executor :8003, "
    + "Data Scientist :8004, Investigator :8005, and the supervision "
    + "console :8090, all FastAPI services; the Fabric 2.5 test network "
    + "(one orderer with the default 2 s BatchTimeout, two organisations "
    + "with one peer each, three certificate authorities) runs under WSL2 "
    + "with a native Docker engine. To reproduce the system end to end: "
    + "preprocess as in Section 4.2.1 (down-sampling seed 123, split "
    + "seed 1), train the three detectors of Table 3 (Adam, 30 epochs, "
    + "batch sizes 64 to 512 as in [56]), fit temperatures and fusion "
    + "weights on the validation partition (Sections 4.2.3 and 4.2.4), set "
    + "τ = 0.70 and quorum = 2/3, and deploy the validateVote chaincode "
    + "with the invariants of Section 4.2.6. Every experimental artefact "
    + "of Section 6 (metrics, figures, statistical tests) is regenerated "
    + "by a single script from the released model checkpoints and the "
    + "frozen test partition."),
  ]),

  p([
    r("This layering yields the central operational trade-off of BAg-IDS: "
    + "the reflex layer detects in milliseconds, deliberation adds seconds "
    + "only for genuine attacks, the blockchain adds a bounded, "
    + "quorum-dependent latency in exchange for decentralised, "
    + "cryptographically verifiable trust, and the supervision layer adds "
    + "optional human authority without surrendering auditability. "
    + "Section 6 measures each of these costs subsystem by subsystem; "
    + "Section 7 shows which adversarial behaviours each layer "
    + "neutralises."),
  ]),
];
