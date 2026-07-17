/* Chapitre 9 — Discussion and Limitations. */
module.exports = ({ h1, h2, h3, p, r, b, i, eq, li, caption, table, fig }) => [

  h1("Chapter 9. Discussion, Limitations and Future Work"),

  p("The results support the central thesis — that detection, decentralised "
  + "trust and human oversight can be co-designed into one operational system "
  + "— but they also delimit where the approach applies and where it must be "
  + "extended. This chapter discusses the main implications (Section 9.1), "
  + "states the limitations candidly (Section 9.2), and outlines future work "
  + "(Section 9.3)."),

  h2("9.1. Implications"),
  h3("9.1.1. The trust–latency trade-off in perspective"),
  p("Section 7.4 measured a consensus cost of several seconds per certified "
  + "alert, orders of magnitude slower than the millisecond reflex path, and "
  + "prohibitive if it fell on every flow. The architecture’s asymmetry is "
  + "therefore not a convenience but a necessity: it makes decentralised "
  + "trust affordable by charging its cost only to the traffic that triggers "
  + "action. Two points temper the apparent slowness. First, the cost is "
  + "dominated by the ledger’s block-formation interval — an infrastructure "
  + "parameter — rather than by cryptography, so it can be reduced by tuning "
  + "the orderer, batching votes or adopting a faster finality protocol "
  + "without changing the security argument. Second, in a SOC the relevant "
  + "deadline for a certified, audit-bearing decision is human-scale; a few "
  + "seconds to obtain a tamper-evident, multi-party-endorsed record is a "
  + "reasonable price for the accountability it buys, particularly as the "
  + "alert is already queued for the operator while consensus proceeds."),

  h3("9.1.2. Interpreting the poisoning result"),
  p("The label-flipping experiment shows a strong, structural defence, but "
  + "its guarantees are majority-trust guarantees and should not be "
  + "over-read. The ensemble absorbs the corruption of a single detector "
  + "because the remaining detectors outweigh it; simultaneous corruption of "
  + "a majority would defeat the mechanism, exactly as a colluding majority "
  + "would defeat the notary quorum. The U-shaped response also matters "
  + "operationally: a partially poisoned detector is more damaging than a "
  + "fully poisoned one, which argues against treating the weighting as a "
  + "complete defence and in favour of the layered response the thesis "
  + "advocates."),

  h2("9.2. Limitations"),
  h3("9.2.1. Preprocessing provenance and absolute accuracy"),
  p("The most important caveat concerns the detection numbers. The original "
  + "training-time feature scaler was not preserved with the released models, "
  + "so the pipeline refits a scaler on the training split. This is adequate "
  + "for the relative comparisons that carry the thesis’s claims, but it "
  + "means the absolute per-detector accuracies characterise this "
  + "reconstructed pipeline rather than the detectors’ peak reported "
  + "performance; the weak measured accuracy of the CNN is best read in this "
  + "light. This limitation also bounds the accuracy of the system on "
  + "arbitrary operator-supplied flows, whose preprocessing must match the "
  + "training pipeline for detection to be reliable. Re-establishing the "
  + "exact preprocessing, or retraining the detectors under a controlled "
  + "pipeline, would sharpen the absolute figures without affecting the "
  + "architectural conclusions."),

  h3("9.2.2. Single-host test network"),
  p("The blockchain is evaluated on a Fabric test network on a single "
  + "workstation. This suffices to measure the real cost of the "
  + "execute–order–validate path and to demonstrate the full stack on "
  + "commodity hardware, but it does not capture wide-area latency, "
  + "geographic distribution of organisations, or a larger notary set under "
  + "contention. A multi-site deployment would raise absolute latencies; the "
  + "linear quorum scaling should, however, carry over."),

  h3("9.2.3. Calibration of the fused ensemble"),
  p("Temperature scaling improves per-model calibration, yet the calibration "
  + "error of the fused ensemble does not improve monotonically, because "
  + "scaling is applied per model before a linear opinion pool that does not "
  + "preserve calibration in general. A joint or post-fusion calibration step "
  + "would likely tighten the ensemble’s reliability; the simpler per-model "
  + "scheme was kept because the operational role of calibration here is the "
  + "well-ordered confidence that the rejection rule and the weights consume."),

  h3("9.2.4. Dependence on the deliberative model"),
  p("The deliberative layer relies on an external LLM. The design mitigates "
  + "the dependence — the model is off the per-flow path, rate-limited, and "
  + "degrades to a rule-based fallback — but the quality of the severity "
  + "assessments tracks the quality of the model used. A systematic study of "
  + "how different LLMs affect downstream decisions, and of prompt-level "
  + "robustness, is beyond this thesis; the LLM never sees raw traffic and "
  + "only annotates already-certified alerts, which bounds its influence on "
  + "detection itself."),

  h3("9.2.5. Scope of the empirical security evaluation"),
  p("We measured robustness against label-flipping poisoning and verified the "
  + "cryptographic invariants of the consensus and governance contracts "
  + "on-chain. We did not empirically evaluate every adversary of Chapter 4 — "
  + "adaptive evasion against the feature extractor, or coordinated "
  + "multi-agent compromise, for instance — some of which are out of scope "
  + "and others of which warrant dedicated study. The security analysis of "
  + "Chapter 8 is therefore part argument, part measurement, and the thesis "
  + "is explicit about which is which."),

  h2("9.3. Future work"),
  p("Several directions follow. Beyond addressing the limitations above, the "
  + "architecture invites evaluation on more recent and more specialised "
  + "threat corpora — modern cloud-DDoS and encrypted-traffic (QUIC) datasets "
  + "— to test whether the calibrated ensemble and the trust machinery "
  + "generalise beyond the CICIDS family; this requires retraining detectors "
  + "on the new feature schemas but leaves the consensus and supervision "
  + "layers unchanged. On the systems side, a geographically distributed, "
  + "multi-organisation Fabric deployment would turn the latency study into a "
  + "genuine scalability study, and alternative finality protocols could "
  + "shrink the consensus cost. On the learning side, closing the "
  + "drift-to-recalibration loop through the Data Scientist agent, and "
  + "studying online Dirichlet weight adaptation under sustained partial "
  + "poisoning, would strengthen the poisoning defence into an adaptive one. "
  + "Finally, the human-in-the-loop layer opens a line of work on usable, "
  + "accountable autonomy: how much oversight operators actually exercise, "
  + "and how the on-chain governance record supports post-incident review and "
  + "regulatory compliance."),
];
