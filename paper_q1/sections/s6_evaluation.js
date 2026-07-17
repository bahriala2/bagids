/* Section 6 — Experimental Evaluation.
 * PROTOCOLE D'ORIGINE [56] : RobustScaler fit sur le jeu équilibré,
 * benign sous-échantillonné à 390 222, split 60/20/20 (rs=1).
 * Valeurs : results/paper_analytics_original/analytics.json +
 * results/original_pipeline/results.json (inférence réelle). */
module.exports = ({ h1, h2, h3, p, r, b, i, eq, li, caption, table, fig }) => [

  h1("6. Experimental Evaluation"),

  p([
    r("We evaluate BAg-IDS "), b("subsystem by subsystem"),
    r(", mirroring the pipeline of Figure 3: the three individual detectors "
    + "(Section 6.2), the calibration stage (6.3), the CWC fusion (6.4), the "
    + "rejection gate and the load it offers to the deliberative layer "
    + "(6.5), the consensus layer (6.6), the robustness to detector "
    + "corruption that the fusion weights provide (6.7), and a functional "
    + "validation of the deliberative/agentic layer (6.8). Each subsection "
    + "isolates one subsystem, reports its measured behaviour, and "
    + "quantifies the "),
    b("impact of its output on the subsystem that consumes it"),
    r(". Section 6.9 assembles the chain. Every number and every curve below "
    + "is measured on a real run of the implemented system (no value is "
    + "projected or simulated), and the key comparisons are accompanied by "
    + "a statistical analysis (95% bootstrap confidence intervals and "
    + "McNemar tests)."),
  ]),

  // ---------------------------------------------------------------- 6.1
  h2("6.1. Experimental setup and statistical methodology"),

  p([
    r("Experiments use CICIDS2017 in its 15-class form under the "),
    b("exact preprocessing of the detectors’ original training pipeline"),
    r(" [56], which we recovered from the training notebook and reproduce "
    + "seed for seed (Section 4.2.1): the cleaned corpus is balanced by "
    + "down-sampling benign traffic to the 390,222 attack flows, features "
    + "are scaled with a RobustScaler, and the data are split 60/20/20 "
    + "into training, validation and test partitions; the frozen test "
    + "partition contains 156,089 flows. The detectors are those of "
    + "Table 3, reused exactly as released by [56]; temperatures and "
    + "fusion weights are fitted on the validation partition only. The "
    + "agent layer runs as FastAPI services on a single Windows "
    + "workstation; the consensus layer is evaluated both on a local "
    + "hash-chained ledger and on a Hyperledger Fabric 2.5 test network "
    + "(one orderer, two organisations with one peer each, three CAs) "
    + "under WSL2 with a native Docker engine. Unless stated otherwise, "
    + "τ = 0.70 and the quorum is 2 of 3 notaries."),
  ]),

  p([
    r("Two conventions apply throughout. First, besides the 15-class "
    + "metrics we report "), b("operational binary metrics"),
    r(" (BENIGN versus ATTACK, the decision that actually triggers "
    + "remediation) with the attack class as positive; the operational "
    + "FPR is the fraction of benign flows raised as attacks, and is "
    + "measured on the balanced evaluation set of the original protocol. "
    + "Second, all headline metrics carry a "),
    b("95% bootstrap confidence interval"),
    r(" (1,000 resamples of the test partition, percentile method), and "
    + "pairwise model differences are tested with "), b("McNemar’s test"),
    r(" (χ² with continuity correction) on per-flow correctness, the "
    + "appropriate paired test when two classifiers are evaluated on the "
    + "same test set."),
  ]),

  p([
    b("Known limitations of the benchmarks and of the protocol. "),
    r("CICIDS2017 remains the community reference, but its generation "
    + "tooling and labelling have documented flaws: Engelen et al. "
    + "identified errors in the CICFlowMeter feature extractor and in the "
    + "labels themselves [50], and subsequent studies quantified their "
    + "material effect on reported performance [51, 52]. These flaws "
    + "particularly affect the minority attack classes, and we interpret "
    + "per-class figures accordingly. Two properties of the original "
    + "protocol [56] are likewise stated openly: the scaler is fitted on "
    + "the full balanced corpus before splitting (its statistics are "
    + "label-free medians and quantiles over 780K flows, so the induced "
    + "leakage is negligible but non-zero), and evaluation is on a "
    + "class-balanced testbed, so operational rates on raw, benign-"
    + "dominated traffic will differ. We keep both choices for strict "
    + "fidelity to the published detectors. Consensus-latency results "
    + "(Section 6.6) rest on 40 certified alerts and should be read as a "
    + "characterisation of this deployment; a larger-scale re-measurement "
    + "with concurrent vote submission is planned (Section 8.1)."),
  ]),

  // ---------------------------------------------------------------- 6.2
  h2("6.2. Subsystem 1: the individual detectors"),

  p([
    r("We first evaluate each detector in isolation, exactly as it enters "
    + "the pipeline. Table 4 reports the 15-class metrics, the operational "
    + "binary metrics with confidence intervals, and the "
    + "threshold-independent ROC-AUC and average precision; Figure 10 shows "
    + "the operational ROC and precision–recall curves; Figure 11 the "
    + "per-class F1; Figure 12 the row-normalised confusion matrices."),
  ]),

  table(
    ["Model", "Acc-15 (%)", "F1-w (%)", "Oper. F1 [95% CI]", "ROC-AUC",
     "AP", "FPR (%)"],
    [
      ["RNN", "90.68", "90.50", "0.903 [0.901, 0.905]", "0.998", "0.998",
       "0.05"],
      ["CNN", "89.10", "88.29", "0.906 [0.904, 0.908]", "0.985", "0.977",
       "1.01"],
      ["DNN", "95.27", "94.74", "0.952 [0.951, 0.953]", "0.985", "0.985",
       "0.17"],
      ["CWC ensemble (all decisions)", "96.60", "96.39",
       "0.967 [0.966, 0.968]", "0.999", "0.999", "0.09"],
      ["CWC + reject, certified only (τ=0.70)", "99.65", "99.62",
       "0.996", "n/a", "n/a", "0.04"],
    ],
    [2450, 1150, 1050, 2100, 950, 850, 810],
    { boldLastRows: 1 }),
  caption("Table 4. Measured performance on the CICIDS2017 test partition "
    + "of the original protocol (156,089 flows, balanced). Acc-15/F1-w: "
    + "15-class accuracy and weighted F1. Oper. F1, ROC-AUC, AP, FPR: "
    + "operational BENIGN-vs-ATTACK metrics; CIs from 1,000 bootstrap "
    + "resamples."),

  fig("paper_q1/figures/fig_roc_pr.png", 560),
  caption("Figure 10. Operational ROC (a) and precision–recall (b) curves of "
    + "the three detectors and the CWC ensemble on the test partition."),

  p([
    r("Three findings emerge. "),
    b("(i) All three detectors are operationally strong but "
    + "complementary"),
    r(": the DNN has the best 15-class accuracy (95.27%), the RNN the "
    + "best ranking quality (AUC 0.998) and an extremely low FPR (0.05%), "
    + "and the CNN, the weakest at the arg-max, still contributes "
    + "high-quality ranking (AUC 0.985). Their error sets differ enough "
    + "for fusion to profit, which Section 6.4 confirms. "),
    b("(ii) The per-class picture is strong on the operationally "
    + "dominant families"),
    r(" (Figure 11): DDoS 0.975, DoS Hulk 0.973, PortScan 0.993, "
    + "FTP/SSH-Patator 0.99/0.98 ensemble F1. "),
    b("(iii) The residual weaknesses are the rare classes"),
    r(": Bot (F1 0.52, 380 test flows), DoS slowloris (0.53), the web "
    + "attacks, and the vanishing classes Heartbleed (1 flow) and "
    + "Infiltration (9 flows) are missed or unstable, the region where "
    + "the labelling flaws of the benchmark [50–52] are also "
    + "concentrated. We report this candidly; it is exactly the "
    + "low-confidence region that the rejection gate (Section 6.5) is "
    + "designed to withhold from automated remediation."),
  ]),

  fig("paper_q1/figures/fig_f1_per_class.png", 600),
  caption("Figure 11. Per-class F1 of the three detectors and the CWC "
    + "ensemble (test partition, 15 classes)."),

  fig("paper_q1/figures/fig_confusion.png", 540),
  caption("Figure 12. Row-normalised confusion matrices of the three "
    + "detectors and the ensemble."),

  h3("6.2.1. Statistical analysis"),

  p([
    r("Figure 13 plots the operational F1 of each model with its 95% "
    + "bootstrap interval; the intervals are narrow (± ~0.002) and the "
    + "ensemble’s interval is disjoint from every detector’s. Table 5 "
    + "reports McNemar’s test on per-flow 15-class correctness for every "
    + "pair: all differences are significant, and, unlike a weaker "
    + "regime where fusion merely averages, "),
    b("the ensemble is statistically superior to each of its members"),
    r(" (χ² = 709 against the strong DNN, p ≈ 10⁻¹⁵⁶). The model ranking "
    + "of Table 4 is not a sampling accident, and every downstream "
    + "comparison rests on statistically separated baselines."),
  ]),

  fig("paper_q1/figures/fig_bootstrap_ci.png", 420),
  caption("Figure 13. Operational F1 with 95% bootstrap confidence "
    + "intervals (1,000 resamples)."),

  table(
    ["Pair", "χ² (McNemar)", "p-value", "Interpretation"],
    [
      ["RNN vs CNN", "296", "2.2 × 10⁻⁶⁶", "RNN > CNN (15-class)"],
      ["RNN vs DNN", "2,900", "< 10⁻³⁰⁰", "DNN > RNN"],
      ["CNN vs DNN", "6,359", "< 10⁻³⁰⁰", "DNN ≫ CNN"],
      ["Ensemble vs RNN", "7,113", "< 10⁻³⁰⁰", "ensemble ≫ RNN"],
      ["Ensemble vs DNN", "709", "2.9 × 10⁻¹⁵⁶", "ensemble > DNN"],
      ["Ensemble vs CNN", "9,562", "< 10⁻³⁰⁰", "ensemble ≫ CNN"],
    ],
    [2300, 1800, 1800, 3460],
    {}),
  caption("Table 5. McNemar tests (χ², continuity-corrected) on per-flow "
    + "correctness over the 156,089-flow test partition. The ensemble "
    + "significantly outperforms every individual detector."),

  h3("6.2.2. Reflex-path cost and context with the state of the art"),

  p([
    r("Because Table 1 uses line-rate viability (C8) as a discriminating "
    + "criterion, we measure it rather than assert it. On the evaluation "
    + "workstation (CPU only), the complete reflex pipeline (three "
    + "detector inferences, temperature scaling, CWC fusion and the "
    + "reject decision) sustains "), b("37,524 flows/s"),
    r(" in batched operation (measured over 363,860 flows), i.e. an "
    + "amortised cost of 0.027 ms per flow. Latency for an isolated "
    + "single flow is framework-bound rather than model-bound: an eager "
    + "single-flow pass measures 199 ms (median; p95 407 ms), dominated "
    + "by per-call TensorFlow overhead, which is why the Sentinel "
    + "processes flows in micro-batches. The reflex layer is comfortably "
    + "line-rate for the flow volumes of the evaluated corpus on "
    + "commodity hardware."),
  ]),

  p([
    r("For context, recent deep and Transformer-based systems report "
    + "97–99.9% accuracy on CICIDS2017-family benchmarks [2, 5, 9, 10]. "
    + "Under the original training protocol our measurements sit in the "
    + "same regime: 96.60% for the ungated ensemble and 99.65–99.97% on "
    + "the certified stream (Section 6.5). Cross-paper comparison "
    + "nevertheless remains indicative at best (published protocols "
    + "differ in class sets, rebalancing and splits [51]), which is why "
    + "our claims rest on within-pipeline comparisons and on the "
    + "selective operating point evaluated against a selective-"
    + "classification baseline in Section 6.5. We note for transparency "
    + "that an earlier draft of this work evaluated the same released "
    + "checkpoints under a reconstructed (mismatched) preprocessing and "
    + "measured substantially lower absolute figures; recovering the "
    + "original pipeline of [56] closed that gap entirely, a cautionary "
    + "tale about preprocessing provenance that we discuss in "
    + "Section 8.3.1."),
  ]),

  p([
    i("Impact on the next subsystem. "),
    r("The detector stage hands three posterior vectors per flow to the "
    + "calibration stage: one detector strong at ranking (RNN), one "
    + "strong at the arg-max (DNN), and one weaker but complementary "
    + "member (CNN). What the downstream fusion and rejection can achieve "
    + "depends on making these three confidence scales comparable, "
    + "measured next."),
  ]),

  // ---------------------------------------------------------------- 6.3
  h2("6.3. Subsystem 2: confidence calibration"),

  p([
    r("Table 6 gives, per model, the fitted temperature and the Expected "
    + "Calibration Error before and after scaling; Figure 14 shows the "
    + "reliability diagrams. In-distribution, the detectors are only "
    + "mildly over-confident (the fitted temperatures are moderate, "
    + "1.63–1.99, and the raw ECEs small, 0.018–0.051), in sharp "
    + "contrast with the pathological miscalibration they exhibit under "
    + "a mismatched preprocessing (Section 8.3.1)."),
  ]),

  table(
    ["Model", "Fitted T", "ECE before", "ECE after", "Effect"],
    [
      ["RNN", "1.93", "0.051", "0.024", "−53% (largest repair)"],
      ["CNN", "1.63", "0.040", "0.053", "≈ neutral"],
      ["DNN", "1.99", "0.018", "0.039", "slightly degraded"],
      ["CWC ensemble", "n/a", "0.047", "0.092", "see discussion"],
    ],
    [1700, 1200, 1500, 1500, 3460],
    {}),
  caption("Table 6. Temperature scaling per detector: fitted temperature "
    + "and Expected Calibration Error (15 bins) before/after, on the test "
    + "partition."),

  fig("paper_q1/figures/fig_reliability.png", 620),
  caption("Figure 14. Reliability diagrams of each detector and of the "
    + "ensemble, before (grey) and after (colour) temperature scaling."),

  p([
    r("We report the calibration stage with complete candour, because "
    + "its headline metric and its operational value diverge. Measured "
    + "by ECE, temperature scaling only clearly repairs the RNN "
    + "(0.051 → 0.024); the CNN and DNN were already near-calibrated, a "
    + "one-parameter correction cannot improve them further, and the "
    + "fused ensemble’s ECE worsens (0.047 → 0.092): averaging "
    + "individually calibrated posteriors does not guarantee a "
    + "calibrated average, a known property of opinion pools. What "
    + "calibration measurably buys the pipeline is "),
    b("better decisions downstream"),
    r(": the ablation of Section 6.4 (Table 7) shows that removing it "
    + "from the CWC costs 0.7 point of operational F1 (0.9666 → 0.9595) "
    + "and raises the FPR by a fifth (0.09% → 0.11%), because the fusion "
    + "weights and, above all, the rejection threshold consume the "
    + "confidence ordering that scaling homogenises across members."),
  ]),

  p([
    i("Impact on the next subsystem. "),
    r("Calibration hands the fusion three confidence-comparable "
    + "posteriors. The measured effect is small in the clean regime "
    + "precisely because the detectors are healthy in-distribution; its "
    + "insurance value, repairing a member whose confidence scale "
    + "drifts, is what the corruption experiment of Section 6.7 "
    + "stresses."),
  ]),

  // ---------------------------------------------------------------- 6.4
  h2("6.4. Subsystem 3: Conscious Weighted Consensus fusion"),

  p([
    r("We ablate the fusion rule itself: Table 7 and Figure 15 compare, "
    + "on identical inputs, the best single detector, a uniform-weight "
    + "opinion pool, per-model majority voting, the CWC (precision "
    + "weights + calibration), the CWC without calibration, and finally "
    + "the CWC followed by the rejection gate."),
  ]),

  table(
    ["Fusion strategy", "Oper. F1", "Oper. FPR (%)", "Acc-15 (%)"],
    [
      ["DNN alone (best single)", "0.952", "0.17", "95.27"],
      ["Uniform mean (calibrated)", "0.965", "0.09", "96.48"],
      ["Majority vote", "0.950", "0.11", "95.08"],
      ["CWC (precision weights, calibrated)", "0.967", "0.09", "96.60"],
      ["CWC without calibration", "0.960", "0.11", "95.95"],
      ["CWC + reject (τ=0.70), certified only", "0.996", "0.04", "99.65"],
    ],
    [3900, 1500, 1800, 1660],
    { boldLastRows: 1 }),
  caption("Table 7. Ablation of the fusion strategy on identical detector "
    + "outputs. The last row evaluates the accepted (certified) decisions "
    + "only, at coverage 87.3%."),

  fig("paper_q1/figures/fig_ablation_fusion.png", 560),
  caption("Figure 15. Operational F1 and FPR of the fusion strategies of "
    + "Table 7."),

  p([
    r("The ordering is now unambiguous. "),
    b("Fusion beats the best single model"),
    r(": the CWC gains 1.3 accuracy points over the DNN (96.60% vs "
    + "95.27%), halves its FPR, and the McNemar test of Table 5 makes "
    + "the difference decisive. In addition, "),
    b("soft pooling beats hard voting"),
    r(" (majority vote loses the probabilistic information and lands "
    + "below the best single model). Within soft pooling, the precision "
    + "weights add a small but consistent margin over the uniform pool "
    + "(96.60% vs 96.48%): with three healthy detectors the weights are "
    + "nearly uniform by construction (0.332/0.323/0.345), so their "
    + "clean-regime contribution is modest; their decisive role is "
    + "adversarial, measured in Section 6.7. Calibration inside the "
    + "fusion is worth 0.65 accuracy point (Table 7, row 5), consistent "
    + "with Section 6.3."),
  ]),

  p([
    i("Impact on the next subsystem. "),
    r("The fusion emits one pooled posterior per flow whose confidence "
    + "separates correct from incorrect decisions markedly better than "
    + "any single member (AUC 0.999). That separation is the raw "
    + "material of the rejection gate, quantified next by the "
    + "risk–coverage curve."),
  ]),

  // ---------------------------------------------------------------- 6.5
  h2("6.5. Subsystem 4: the rejection gate and the load it routes to "
     + "deliberation"),

  p([
    r("The reject threshold τ turns the fused posterior into a ternary "
    + "decision, and in doing so couples two quantities: the reliability "
    + "of what is "), i("certified"),
    r(" (and will therefore reach the consensus layer and possibly the "
    + "Executor) and the volume of what is "), i("deferred"),
    r(" (and will therefore load the Data Scientist’s drift monitor and "
    + "the deliberative layer). Figure 16(a) gives the risk–coverage "
    + "curve of the CWC ensemble against the standard softmax-response "
    + "selective baseline applied to the best single detector [16, 17]; "
    + "Figure 16(b) shows the two coupled fractions as τ sweeps; Table 8 "
    + "tabulates the operating points."),
  ]),

  table(
    ["τ", "Coverage (%)", "Deferred (%)", "Acc. accepted (%)",
     "F1 accepted", "FPR accepted (%)"],
    [
      ["0.50", "96.8", "3.2", "97.32", "0.973", "0.093"],
      ["0.60", "92.1", "7.9", "98.80", "0.987", "0.050"],
      ["0.70", "87.3", "12.7", "99.65", "0.996", "0.040"],
      ["0.75", "82.6", "17.4", "99.72", "0.997", "0.040"],
      ["0.80", "73.2", "26.8", "99.77", "0.997", "0.034"],
      ["0.90", "60.6", "39.4", "99.97", "0.9995", "0.000"],
    ],
    [900, 1700, 1600, 1900, 1400, 1760],
    { boldRow: 2 }),
  caption("Table 8. Sweep of the rejection threshold τ: coverage, "
    + "deferred fraction (routed to drift monitoring/deliberation), and "
    + "quality of the accepted decisions. τ = 0.70 (bold) is the "
    + "operating point."),

  fig("paper_q1/figures/fig_risk_coverage.png", 560),
  caption("Figure 16. (a) Risk–coverage curves of the CWC ensemble and of "
    + "the best single detector under the softmax-response selective "
    + "baseline, with the τ = 0.70 operating point. (b) Fraction of flows "
    + "deferred to the deliberative layer and FPR of the accepted "
    + "decisions, as functions of τ."),

  p([
    r("The gate delivers the certified stream the architecture is built "
    + "around. At τ = 0.70 the ensemble certifies 87.3% of flows and, on "
    + "those, reaches 99.65% 15-class accuracy, 0.996 operational F1 and "
    + "0.04% FPR, versus 96.60%, 0.967 and 0.09% ungated (Table 7). "
    + "The trade-off degrades gracefully across the whole sweep: "
    + "coverage falls smoothly (96.8% → 60.6% between τ = 0.5 and 0.9) "
    + "while the FPR of the accepted set decreases monotonically to "
    + "zero at τ = 0.90, an operating point that certifies 60.6% of "
    + "traffic at 99.97% accuracy with no false positives on the test "
    + "partition. We select τ = 0.70 as the default because it is the "
    + "knee where accepted accuracy saturates (99.65 → 99.77% costs 14 "
    + "coverage points), but the whole curve of Figure 16 is available "
    + "to the operator as a governed, on-chain-audited parameter. "
    + "Figure 16(a) also situates the design in the selective-"
    + "classification literature: at every coverage level the fused "
    + "curve dominates the single-best-model softmax-response baseline "
    + "[16, 17], so the gate’s benefit is not merely that of "
    + "thresholding any confident model."),
  ]),

  p([
    i("Impact on the next subsystems. "),
    r("Downstream, the gate is a load-shaping contract. To Layer 3 it "
    + "promises that only 0.04%-FPR decisions are worth the cost of "
    + "multi-party consensus, which is what keeps the multi-second "
    + "Fabric latency of Section 6.6 off the reflex path. To Layer 2 it "
    + "delivers the 12.7% deferred stream whose rolling rate is the "
    + "Data Scientist’s drift signal, and whose bursts trigger "
    + "deliberation. Raising τ trades certified reliability against "
    + "deliberative load along the measured curve of Figure 16(b), an "
    + "explicit, tunable coupling between the reflex and deliberative "
    + "subsystems."),
  ]),

  // ---------------------------------------------------------------- 6.6
  h2("6.6. Subsystem 5: the consensus layer, latency versus quorum"),

  p([
    r("We now quantify the price of decentralised trust for exactly the "
    + "decisions the gate certifies. For each of 40 certified attacks we "
    + "measure the consensus time (recording the alert and collecting "
    + "the signed votes up to certification) under both consensus "
    + "backends and for quorums of one, two and three notaries "
    + "(Table 9, Figure 17)."),
  ]),

  table(
    ["Quorum", "Simulated (ms)", "Fabric median (ms)", "Fabric p95 (ms)",
     "Overhead (ms)"],
    [
      ["1", "1.8", "4,130", "4,151", "4,128"],
      ["2", "2.2", "6,185", "6,395", "6,183"],
      ["3", "2.8", "8,212", "8,229", "8,209"],
    ],
    [1400, 2100, 2200, 1900, 1760],
    {}),
  caption("Table 9. Consensus latency per certified alert (40 alerts), "
    + "by backend and quorum. Overhead is the median Fabric-minus-"
    + "simulated gap."),

  fig("paper_q1/figures/latency_quorum.png", 460),
  caption("Figure 17. Median consensus latency per certified alert "
    + "versus quorum, simulated and Fabric backends (log scale)."),

  p([
    b("(i) The linearity is an implementation property, not a "
    + "consensus property: "),
    r("in the evaluated implementation the leader submits the alert and "
    + "the votes sequentially, one transaction each, and each "
    + "transaction waits for its block (the sequence of Figure 7), "
    + "hence the observed (1 + quorum) × 2.06 s. Three independent notaries could submit "
    + "concurrently, in which case the expected latency is on the order "
    + "of two block intervals (~4 s with the default cut interval) "
    + "regardless of the quorum; parallelising the submission path and "
    + "re-measuring at larger scale is scheduled revision work "
    + "(Section 8.1). "),
    b("(ii) The cost is infrastructure, not cryptography: "),
    r("the simulated backend performs the identical signature "
    + "verification, anti-replay and quorum logic in ~2 ms, so the "
    + "multi-second Fabric figure is dominated by the orderer’s "
    + "block-cutting interval (the default 2 s BatchTimeout, deliberately "
    + "left untuned here), a deployment parameter rather than an "
    + "intrinsic cost of the consensus rule. "),
    b("(iii) The reflex path is unaffected: "),
    r("detection continues at the throughput of Section 6.2.2; only "
    + "certified attacks pay for consensus. With 40 alerts, these "
    + "figures characterise the deployment; they are not presented as "
    + "population estimates."),
  ]),

  p([
    i("Impact on the next subsystem. "),
    r("Certification is the event that awakens the remaining agents: it "
    + "releases the Executor (directly, or through the operator’s "
    + "approval queue when supervision is on) and opens an Investigator "
    + "case. The ~2 s per vote is thus the end-to-end reaction-time "
    + "floor of the autonomous remediation path, and the reason "
    + "high-severity actions can afford a human gate: the human decides "
    + "in parallel with, not in addition to, an already multi-second "
    + "consensus."),
  ]),

  // ---------------------------------------------------------------- 6.7
  h2("6.7. Subsystem 6: robustness of the CWC weights to detector "
     + "corruption (a worst-case poisoning proxy)"),

  p([
    r("We finally test the security claim that motivates the CWC: that "
    + "precision-weighted fusion neutralises a corrupted member. The "
    + "experimental model must be stated precisely, because it is "),
    b("not training-set label-flipping in the sense of the poisoning "
    + "literature"),
    r(" [21, 22]: rather than corrupting training data and retraining, "
    + "we directly invert a fraction p of one detector’s "), i("output"),
    r(" decisions (attack into benign, i.e. evasion, and benign into a "
    + "random attack) on both the validation and test data, so the "
    + "corruption is reflected in the very statistics the weights are "
    + "computed from. This "), b("simulated output corruption"),
    r(" is a worst-case proxy: it upper-bounds the damage any "
    + "training-time attack on that detector could inflict at rate p, "
    + "while abstracting away the structured error patterns a genuinely "
    + "retrained-on-poisoned-data model would exhibit. A companion "
    + "experiment with true training-set poisoning and retraining is "
    + "scheduled revision work (Section 8.2). We target the strongest "
    + "ranking detector (RNN) and compare, as p grows, the corrupted "
    + "model alone, the ensemble with static (clean) weights, the "
    + "ensemble with adaptive precision weights (BAg-IDS), and, as a "
    + "robust-aggregation baseline from the literature, the coordinate-"
    + "wise "), b("median pool"),
    r(", which for M = 3 members coincides with the trimmed mean. "
    + "(Krum and TRIM-style defences operate on gradient or training "
    + "aggregation in federated settings and do not apply directly to "
    + "posterior fusion.)"),
  ]),

  table(
    ["p", "RNN alone Acc (%)", "Static ens. Acc (%)",
     "Median pool Acc (%)", "Adaptive ens. Acc (%)", "RNN weight"],
    [
      ["0.0", "90.7", "96.6", "95.1", "96.6", "0.332"],
      ["0.3", "63.6", "94.9", "93.9", "94.7", "0.286"],
      ["0.5", "45.6", "93.8", "93.1", "95.0", "0.247"],
      ["0.9", "9.6", "91.5", "91.5", "95.9", "0.098"],
      ["1.0", "0.6", "90.9", "91.1", "96.0", "0.014"],
    ],
    [700, 1900, 1900, 1900, 2000, 1260],
    { boldLastRows: 1 }),
  caption("Table 10. Robustness to simulated output corruption of the "
    + "RNN. The adaptive ensemble loses at most 1.9 accuracy points at "
    + "any corruption level and only 0.6 at full corruption, while the "
    + "corrupted detector's weight decays 0.332 → 0.014."),

  p([
    r("The result is clear-cut, and stronger than under any static "
    + "alternative. A fully corrupted RNN is destroyed as a standalone "
    + "detector (0.6% accuracy at p = 1.0), yet the adaptive ensemble "
    + "retains 96.0% of its clean 96.6%: the corrupted member’s weight "
    + "decays from 0.332 to 0.014 (Figure 19), so its influence is "),
    b("automatically suppressed without any explicit attack "
    + "detection"),
    r(". The baselines isolate the mechanism (Figure 18): static "
    + "weights degrade steadily to 90.9% (a 5.1-point gap to adaptive "
    + "at p = 1.0), and the median pool, which needs no validation "
    + "statistics, tracks the static ensemble rather than the "
    + "adaptive one, ending at 91.1%. Across the entire corruption "
    + "range the adaptive weights dominate both baselines; their worst "
    + "point is a shallow dip to 94.7% around p ≈ 0.3, where the "
    + "corrupted detector retains enough validation precision to keep "
    + "a meaningful weight. This is where the fusion subsystem of "
    + "Section 6.4 earns its place: the near-uniform clean-regime "
    + "weights and the corrupted-regime exclusion are the same "
    + "mechanism observed in its two regimes."),
  ]),

  fig("paper_q1/figures/fig_robust_fusion.png", 560),
  caption("Figure 18. Accuracy (a) and operational FPR (b) under "
    + "simulated corruption of the RNN: corrupted model alone, static "
    + "weights, median pool (= trimmed mean for M = 3), and adaptive "
    + "CWC weights."),

  fig("paper_q1/figures/fig_corruption_weight.png", 440),
  caption("Figure 19. Adaptive fusion weight of the corrupted detector "
    + "versus corruption fraction, for the RNN and CNN targets."),

  h3("6.7.1. The adaptive adversary"),

  p([
    r("We state the adaptive-adversary limitation explicitly rather "
    + "than leaving it implicit. Eq. 2 is public, so an informed "
    + "attacker will not corrupt uniformly at random: a targeted "
    + "backdoor that "), b("preserves validation precision"),
    r(" (for instance one that only misclassifies a minority attack "
    + "class contributing little to the weighted precision, or that "
    + "activates on a trigger absent from the validation distribution) "
    + "would keep the corrupted detector’s weight intact and defeat "
    + "the weighting entirely. The residual dip around p ≈ 0.3 marks "
    + "the region such an adversary would target. Within the "
    + "architecture, the compensating controls are the median baseline "
    + "(insensitive to validation statistics and only ~5 points behind "
    + "in the worst case), the rejection-rate drift signal consumed by "
    + "the Data Scientist, and the human audit of certified incidents; "
    + "a systematic evaluation against precision-preserving poisoning "
    + "is future work (Section 8.2)."),
  ]),

  // ---------------------------------------------------------------- 6.8
  h2("6.8. Functional validation of the deliberative and agentic layer"),

  p([
    r("The deliberative layer is deliberately excluded from the "
    + "quantitative claims above (Section 4.2.5); what follows is a "),
    b("functional validation"),
    r(" (evidence that the full five-agent system operates end to end "
    + "as specified) and is presented as such, not as a statistical "
    + "evaluation of deliberation quality (assessing severity "
    + "assignments against ground truth, inter-model agreement and cost "
    + "is future work). In a live session with attack injection, "
    + "the Sentinel processed 224 flows and "
    + "emitted 8 signed alerts; all 8 were certified by the 2-of-3 "
    + "notary quorum; the notaries attached 7 advisory second opinions; "
    + "and the Investigator autonomously opened 7 investigations, "
    + "correlating ledger history to flag 3 of them as multi-incident "
    + "campaigns, each with its full perceive-reason-act-reflect trace "
    + "recorded and displayed in the supervision console. Consistent "
    + "with the design boundaries, disabling the LLM backends changed "
    + "none of the certified verdicts: deliberation and advisories fell "
    + "back to the deterministic rules, and detection, consensus and "
    + "remediation continued unchanged. A failure mode we fixed and "
    + "report for reproducibility: a synchronous advisory call on the "
    + "endorsement path initially exceeded the 5 s endorsement timeout "
    + "and stalled certification; advisory opinions must be strictly "
    + "asynchronous to preserve the latency budget of Section 6.6."),
  ]),

  // ---------------------------------------------------------------- 6.9
  h2("6.9. Positioning against recently reported blockchain, federated "
     + "and agentic IDS results"),

  p([
    r("A controlled quantitative comparison with the systems of Section 2 "
    + "is not possible: no two of them share a dataset, a class "
    + "granularity, a preprocessing protocol, or a notion of operating "
    + "point, and none releases an artefact we could rerun under our "
    + "protocol. What we can do honestly is place our measured figures "
    + "next to the figures those papers report for themselves, under "
    + "their own protocols, and be explicit about what is and is not "
    + "comparable. Table 11 does this for the closest recent "
    + "blockchain-based, federated, and agentic systems whose sources "
    + "state concrete numbers."),
  ]),

  table(
    ["System (ref.)", "Category", "Dataset (protocol of the source)",
     "Reported performance"],
    [
      ["Liang et al. [57]", "Blockchain + multi-agent (IoT)",
       "NSL-KDD (binary)", "83.2% acc, F1 0.839 (test set)"],
      ["Soltani et al. [58]", "Multi-agent adaptive DL",
       "CIC-IDS2017/2018", "detection rate > 95% (online, CNN)"],
      ["Begum et al. [60]", "Federated + blockchain (IoMT)",
       "Edge-IIoTSet / TON_IoT", "97.4% acc, F1 0.97 / 98.2% acc, F1 0.98"],
      ["Ali et al. [59]", "Federated + blockchain (IIoT)",
       "ToN-IoT, N-BaIoT", "97.3% acc"],
      ["H. Li et al. [63]", "LLM-enhanced agentic IDS",
       "unnamed benchmarks", "> 90% acc"],
      ["BAg-IDS (this work)", "Agentic + blockchain consensus + HITL",
       "CICIDS2017 (15 classes)",
       "96.60% acc, F1 0.967, FPR 0.09% (all decisions); "
       + "99.65% acc, FPR 0.04% at 87.3% coverage (certified)"],
    ],
    [1700, 2300, 2300, 3060],
    { boldLastRows: 1 }),
  caption("Table 11. Our measured results next to the self-reported "
    + "results of recent blockchain, federated, and agentic IDS. Each row "
    + "is measured by its own authors under their own protocol; the rows "
    + "are indicative context, not a controlled benchmark."),

  p([
    r("Three observations survive the protocol differences. First, "
    + "BAg-IDS's all-decisions accuracy (96.60% over 15 classes) sits in "
    + "the same band as the best federated-blockchain systems report on "
    + "easier, coarser-grained corpora (97-98% on IoT datasets with fewer "
    + "classes), and its certified operating point (99.65% at 0.04% FPR) "
    + "exceeds every figure in the table, at the explicit and quantified "
    + "cost of deferring 12.7% of flows. Second, the compared systems "
    + "report detection quality only; none reports a selective/certified "
    + "operating point, a false-positive rate at that point, or a "
    + "measured on-chain cost per decision, which are precisely the "
    + "quantities an operator needs to act on a verdict. Third, in all "
    + "of the blockchain-based rows the ledger stores alerts or model "
    + "updates after the fact, so their reported accuracy is that of an "
    + "unhardened detector; BAg-IDS is, to our knowledge, the only "
    + "system in the table whose reported figures are produced through "
    + "the consensus path itself."),
  ]),

  // ---------------------------------------------------------------- 6.10
  h2("6.10. Synthesis: the measured chain of impacts"),

  p([
    r("Reading Sections 6.2–6.8 as one chain: three strong but "
    + "complementary detectors (90.7–95.3% accuracy) are made "
    + "confidence-comparable by calibration (worth 0.65 accuracy point "
    + "inside the fusion); the CWC pools them into one posterior that "
    + "beats the best single member by 1.3 points (96.60%, McNemar "
    + "p ≈ 10⁻¹⁵⁶) and withstands the total corruption of its "
    + "strongest-ranking member at a cost of 0.6 point (versus 5.7 for "
    + "static weights and 5.5 for the median pool); the rejection gate "
    + "converts that pooled confidence into a 99.65%-accurate, "
    + "0.04%-FPR certified stream covering 87.3% of traffic (at "
    + "37,500 flows/s, with a zero-FPR option at τ = 0.90) while "
    + "routing the deferred remainder to drift monitoring; the "
    + "consensus layer certifies that stream at ~2 s per vote without "
    + "touching the reflex path; and the agentic layer enriches "
    + "certified incidents into campaign-aware, human-auditable "
    + "reports without ever entering the deterministic decision chain. "
    + "Each interface in this chain is backed by a measured curve "
    + "(Figures 10–19) rather than a design argument."),
  ]),
];
