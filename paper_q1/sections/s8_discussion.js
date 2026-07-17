/* Section 8 — Discussion and Limitations. */
module.exports = ({ h1, h2, h3, p, r, b, i, eq, li, caption, table, fig }) => [

  h1("8. Discussion and Limitations"),

  p([
    r("The results support the central thesis of the paper (that detection, "
    + "decentralised trust, and human oversight can be co-designed into a "
    + "single operational system), but they also delimit where the approach "
    + "applies and where it must be extended. We discuss the main "
    + "implications and state the limitations candidly, since several bound "
    + "the interpretation of the numbers in Section 6."),
  ]),

  // ---------------------------------------------------------------- 8.1
  h2("8.1. The trust–latency trade-off in perspective"),

  p([
    r("Section 6.6 measured a consensus cost of several seconds per certified "
    + "alert, growing linearly with the quorum. This is orders of magnitude "
    + "slower than the millisecond reflex path, and it would be prohibitive if "
    + "it fell on every flow. The architecture’s asymmetry is therefore not a "
    + "convenience but a necessity: it is what makes decentralised trust "
    + "affordable, by charging its cost only to the small fraction of traffic "
    + "that triggers action. Two points temper the apparent slowness. First, "
    + "the cost is dominated by the ledger’s block-formation interval, an "
    + "infrastructure parameter, rather than by the cryptographic verification "
    + "(the identical logic runs in about two milliseconds on the simulated "
    + "backend), and, as Section 6.6 makes explicit, the observed linear "
    + "growth with the quorum is a property of our sequential vote "
    + "submission, not of the consensus rule: with concurrent submission by "
    + "independent notaries the expected cost is about two block intervals "
    + "irrespective of the quorum. Parallelising the submission path, tuning "
    + "the BatchTimeout, and re-measuring over several hundred certified "
    + "alerts is scheduled revision work; both levers reduce latency without "
    + "changing the security argument. Second, in a SOC the relevant deadline for a certified, "
    + "audit-bearing decision is human-scale; a few seconds to obtain a "
    + "tamper-evident, multi-party-endorsed record is a reasonable price for "
    + "the accountability it buys, particularly as the alert is already queued "
    + "for the operator while consensus proceeds."),
  ]),

  // ---------------------------------------------------------------- 8.2
  h2("8.2. Interpreting the corruption result"),

  p([
    r("The corruption experiment shows a strong, structural defence, but "
    + "its guarantees are majority-trust guarantees and should not be "
    + "over-read. The ensemble absorbs the corruption of a single detector "
    + "because the remaining detectors outweigh it; simultaneous corruption of "
    + "a majority of the ensemble is outside the model and would defeat the "
    + "mechanism, exactly as a colluding majority would defeat the notary "
    + "quorum. The residual dip at partial corruption (Section 6.7) also matters "
    + "operationally: a partially corrupted detector (around p ≈ 0.3) is more "
    + "damaging than a fully poisoned one, because it retains enough precision "
    + "to keep a non-negligible weight. This argues against treating the "
    + "weighting as a complete defence and in favour of the layered response "
    + "we advocate: the Data Scientist agent’s drift monitoring is intended "
    + "precisely to catch the elevated rejection rate that partial poisoning "
    + "induces and to escalate to recalibration before the weights fully "
    + "adapt. Quantifying that escalation loop end-to-end is left to future "
    + "work."),
  ]),

  // ---------------------------------------------------------------- 8.3
  h2("8.3. Limitations"),

  h3("8.3.1. Preprocessing provenance: a resolved threat to validity, "
     + "and a cautionary tale"),
  p([
    r("The detectors originate from our prior published study [56], and "
    + "all results in this paper are measured under that study’s exact "
    + "preprocessing, which we recovered from the original training "
    + "notebook and reproduce seed for seed (Section 4.2.1). We report "
    + "the episode openly because it is instructive. An earlier draft "
    + "evaluated the same released checkpoints under a plausible but "
    + "mismatched reconstruction (a different scaler, no class "
    + "rebalancing, a different split): every model degraded, one "
    + "severely (the CNN fell to 31.8% accuracy with a 69% FPR), and "
    + "the miscalibration induced by the out-of-distribution inputs "
    + "mechanically inflated the apparent benefit of calibration and "
    + "rejection. Recovering the original pipeline restored all three "
    + "detectors (Table 3) and eliminated the artefact. The lesson "
    + "generalises: released model weights without their exact "
    + "preprocessing are not a reproducible artefact, and evaluation "
    + "results on them can be dominated by the reconstruction rather "
    + "than the models. We therefore release the full preprocessing "
    + "specification alongside the models. Two properties of the "
    + "original protocol remain as caveats, stated in Section 6.1: the "
    + "scaler is fitted before splitting (negligible but non-zero "
    + "leakage) and the evaluation testbed is class-balanced, so "
    + "operational rates on raw traffic will differ."),
  ]),

  h3("8.3.2. Single-host test network"),
  p([
    r("The blockchain is evaluated on a Fabric test network (one orderer, "
    + "two organisations with one peer each) running on a single workstation. "
    + "This is sufficient to measure the real cost of the "
    + "execute–order–validate path and to demonstrate the full stack on "
    + "commodity hardware, but it does not capture wide-area network latency, "
    + "geographic distribution of organisations, or the behaviour of a larger "
    + "notary set under contention. A multi-site deployment would raise "
    + "absolute latencies and is the natural next step for a scalability "
    + "study; the linear quorum scaling we observe should, however, carry "
    + "over."),
  ]),

  h3("8.3.3. Calibration of the fused ensemble"),
  p([
    r("Temperature scaling improves per-model calibration substantially, yet "
    + "the calibration error of the fused ensemble does not improve "
    + "monotonically. Post-hoc scaling is applied per model before fusion, and "
    + "the linear opinion pool does not preserve calibration in general; a "
    + "joint or post-fusion calibration step would likely tighten the "
    + "ensemble’s reliability. We deliberately kept the simpler per-model "
    + "scheme because the operational role of calibration here is the "
    + "well-ordered confidence that the rejection rule and the fusion weights "
    + "consume, which it provides; refining fused calibration is an orthogonal "
    + "improvement."),
  ]),

  h3("8.3.4. Dependence on the deliberative model"),
  p([
    r("The deliberative layer relies on an external LLM. Our design mitigates "
    + "the dependence (the language model is off the per-flow path, is "
    + "rate-limited, and degrades to a deterministic rule-based fallback when "
    + "unavailable, so autonomy and reproducibility are preserved), but the "
    + "quality of the severity assessments and remediation suggestions "
    + "ultimately tracks the quality of the model used. A systematic study of "
    + "how different LLMs affect downstream decisions, and of prompt-level "
    + "robustness, is beyond this paper’s scope. We note that the LLM never "
    + "sees raw traffic and only annotates already-certified alerts, which "
    + "bounds its influence on detection itself."),
  ]),

  h3("8.3.5. Scope of the empirical security evaluation"),
  p([
    r("We measured robustness against label-flipping poisoning and verified "
    + "the cryptographic invariants of the consensus and governance contracts "
    + "on-chain. We did not empirically evaluate every adversary of Section 3 "
    + "(for example, adaptive evasion crafted against the feature extractor, "
    + "or coordinated multi-agent compromise), some of which are out of scope "
    + "and others of which warrant dedicated study. The security analysis of "
    + "Section 7 is therefore part argument, part measurement, and we have "
    + "been explicit about which is which."),
  ]),

  h3("8.3.6. The cost of on-decision trust: latency and energy"),
  p([
    r("Placing consensus on the decision path is not free, and we state "
    + "the bill explicitly. Each certified alert pays roughly two seconds "
    + "per signed vote (Section 6.6), a cost dominated by ledger block "
    + "formation and growing linearly with the quorum under our "
    + "sequential-submission implementation. The architecture confines "
    + "this cost to the rare certified decisions, so the per-flow reflex "
    + "path is unaffected, but the price is real for any deployment whose "
    + "certified-alert rate approaches the ledger's transaction budget, "
    + "and it caps how large a notary set one can afford before batching "
    + "or parallel submission becomes necessary. On energy, a permissioned "
    + "Fabric network involves no proof-of-work: the overhead is that of "
    + "a handful of CPU-bound endorsement, ordering and validation "
    + "processes, orders of magnitude below public-chain mining and small "
    + "next to the GPU cost of training the detectors. We did not meter "
    + "consumption, however, so we make no quantitative energy claim; a "
    + "joules-per-certified-alert measurement across quorum sizes is a "
    + "straightforward and worthwhile extension."),
  ]),

  h3("8.3.7. Dependence on a single evaluation corpus"),
  p([
    r("Every detection figure in this paper is measured on CICIDS2017, "
    + "whose documented generation and labelling flaws we discuss in "
    + "Section 6.1 and partially mitigate, but cannot eliminate, by "
    + "protocol choices. The trust machinery (consensus, governance, "
    + "supervision) is dataset-agnostic by construction, and the "
    + "corruption experiment of Section 6.7 stresses the fusion under "
    + "conditions no benchmark provides; the detectors and the reported "
    + "operating points, in contrast, are corpus-specific, and the "
    + "comparison of Section 6.9 shows how protocol differences dominate "
    + "cross-paper deltas. Validation on a second, independently "
    + "generated corpus (and ultimately on live traffic behind a SOC) is "
    + "the single most valuable next measurement."),
  ]),

  // ---------------------------------------------------------------- 8.4
  h2("8.4. Generalisation and future work"),

  p([
    r("Several directions follow naturally. Beyond addressing the limitations "
    + "above, the architecture invites evaluation on more recent and more "
    + "specialised threat corpora, for instance modern cloud-DDoS and "
    + "encrypted-traffic (QUIC) datasets, to test whether the calibrated "
    + "ensemble and the trust machinery generalise beyond the CICIDS family; "
    + "this requires retraining detectors on the new feature schemas but "
    + "leaves the consensus and supervision layers unchanged. On the systems "
    + "side, a geographically distributed, multi-organisation Fabric "
    + "deployment would turn the latency study into a genuine scalability "
    + "study, and alternative finality protocols could shrink the consensus "
    + "cost. On the learning side, closing the drift-to-recalibration loop "
    + "through the Data Scientist agent, and studying online Dirichlet weight "
    + "adaptation under sustained partial poisoning, would strengthen the "
    + "poisoning defence into an adaptive one. Finally, the human-in-the-loop "
    + "layer opens a line of work on usable, accountable autonomy: how much "
    + "oversight operators actually exercise, and how the on-chain governance "
    + "record supports post-incident review and compliance. A natural "
    + "extension of that layer is faithful explainability at the approval "
    + "surface: because remediations awaiting human approval are rare by "
    + "construction, per-decision feature attributions (for example "
    + "model-agnostic Shapley-value estimates over the fused ensemble) can "
    + "be afforded exactly where an analyst must decide, following the same "
    + "asymmetric-cost principle as deliberation and consensus."),
  ]),

  p([
    r("On the deployment side, the natural insertion point for BAg-IDS in "
    + "an operational environment is as a certification tier behind an "
    + "existing SOC pipeline: the reflex ensemble subscribes to the same "
    + "flow telemetry as the incumbent IDS, certified verdicts reach the "
    + "SIEM as co-signed, replay-proof alerts rather than raw model "
    + "outputs, and the supervision console becomes the analyst's approval "
    + "surface for high-impact remediations. Because Fabric is "
    + "permissioned, the notary set can be mapped onto trust domains an "
    + "organisation already operates (subsidiaries, security providers, "
    + "regulators) without any public chain, and the measured costs of "
    + "Sections 6.2.2 and 6.6 give an operator the two numbers needed to "
    + "size such a deployment: reflex throughput per core and certified "
    + "alerts per minute per quorum."),
  ]),
];
