/* Chapitre 7 — Experimental Evaluation. */
module.exports = ({ h1, h2, h3, p, r, b, i, eq, li, caption, table, fig }) => [

  h1("Chapter 7. Experimental Evaluation"),

  p([
    r("This chapter evaluates BAg-IDS along four axes that mirror its design "
    + "and its goals: the "), b("detection quality"),
    r(" of the calibrated ensemble (Section 7.2), the effect of the "),
    b("rejection threshold"), r(" (Section 7.3), the "), b("latency cost"),
    r(" of the consensus layer and its scaling with the quorum "
    + "(Section 7.4), and the "), b("robustness"),
    r(" of Conscious Weighted Consensus to label-flipping poisoning "
    + "(Section 7.5). Every number reported below is measured on a real run "
    + "of the implemented system; none is projected."),
  ]),

  // ---------------------------------------------------------------- 7.1
  h2("7.1. Experimental setup"),

  p("Experiments use the CICIDS2017 dataset in its 15-class form (benign "
  + "traffic plus fourteen attack families). After removing non-finite "
  + "records, the data are split 70/15/15 into training, validation and test "
  + "partitions with a fixed seed and class stratification; the test "
  + "partition contains 363,860 flows. The ensemble comprises the RNN, CNN "
  + "and DNN of Chapter 3, each producing a posterior over the 15 classes "
  + "from the same 78-feature representation. Temperature scaling and the "
  + "fusion weights are fitted on the validation split. The agent layer runs "
  + "as four FastAPI services; the consensus layer is evaluated in two "
  + "configurations — the simulated ledger and a Fabric 2.5 test network with "
  + "one orderer, two organisations and their certificate authorities. Unless "
  + "stated otherwise, τ = 0.70 and the quorum is two of three notaries."),

  // ---------------------------------------------------------------- 7.2
  h2("7.2. Detection quality and calibration"),

  p("Table 7.1 reports per-model and ensemble performance on the test "
  + "partition. Two observations stand out. First, the three detectors are of "
  + "very unequal quality: the RNN and DNN are strong (89.06% and 85.74% "
  + "accuracy), whereas the CNN, under the reconstructed preprocessing, is "
  + "weak (31.81% accuracy). Second, despite this heterogeneity, the "
  + "calibrated weighted ensemble reaches 88.21% accuracy at an operational "
  + "false-positive rate of 2.49% over all decisions — close to the best "
  + "single model and far above the weak one. The reliability-proportional "
  + "weighting prevents the weak detector from dominating, a behaviour that "
  + "becomes critical under adversarial conditions (Section 7.5)."),

  table(
    ["Model", "Acc. (%)", "F1 (%)", "FPR (%)"],
    [
      ["RNN (measured)", "89.06", "87.27", "1.766"],
      ["CNN (measured)", "31.81", "42.49", "69.033"],
      ["DNN (measured)", "85.74", "86.34", "9.109"],
      ["BAg-IDS ensemble, all decisions", "88.21", "86.55", "2.494"],
      ["BAg-IDS ensemble, certified (tau=0.70)", "97.10", "96.14", "0.791"],
    ],
    [3400, 1980, 1980, 2000],
    { boldLastRows: 2 }),
  caption("Table 7.1. Measured detection performance on the CICIDS2017 test "
    + "partition (363,860 flows). The certified row reports accepted "
    + "decisions only, at coverage 61.4%."),

  p("When the reject region is applied at τ = 0.70, the ensemble certifies "
  + "61.4% of the flows and, on those accepted decisions, reaches 97.10% "
  + "accuracy, 96.14% F1 and an operational FPR of 0.79%. The confidence gate "
  + "thus trades coverage for a substantial gain in the reliability of the "
  + "decisions actually forwarded to consensus and remediation — precisely "
  + "the decisions whose cost the blockchain will pay."),

  p("Calibration behaves as expected on the two detectors whose confidences "
  + "were poorly scaled: temperature scaling reduces the DNN’s Expected "
  + "Calibration Error from 0.135 to 0.030 and the CNN’s from 0.476 to 0.232. "
  + "The reliability diagram (Figure 7.1) shows the ensemble curve moving "
  + "toward the diagonal after scaling. We note candidly that the "
  + "fused-ensemble ECE does not improve monotonically with per-model "
  + "calibration — a point discussed in Chapter 9; the operational benefit of "
  + "calibration here is the well-ordered confidence that the rejection rule "
  + "and the fusion weights exploit."),

  fig("results/fusion_experiment/figures/reliability_diagram.png", 360),
  caption("Figure 7.1. Reliability diagram of the BAg-IDS ensemble before and "
    + "after temperature scaling (15 bins)."),

  // ---------------------------------------------------------------- 7.3
  h2("7.3. Ablation of the rejection threshold"),

  p("The threshold τ governs the coverage–reliability trade-off. Table 7.2 "
  + "sweeps τ and reports, over the accepted flows, the coverage, accuracy, "
  + "F1 and operational FPR. As τ rises from 0.50 to 0.70, coverage falls "
  + "from 91.1% to 61.4% while accuracy climbs from 90.14% to 97.10% and the "
  + "FPR drops to 0.79%. Beyond τ = 0.70 the picture inverts sharply: at "
  + "τ = 0.80 coverage collapses to 4.5% and the FPR paradoxically rises, "
  + "because only a small, unrepresentative set of over-confident flows "
  + "survives the gate. This identifies τ ≈ 0.70 as the knee of the operating "
  + "curve for this deployment and justifies it as the default."),

  table(
    ["tau", "Coverage (%)", "Acc. (%)", "F1 (%)", "FPR (%)"],
    [
      ["0.50", "91.1", "90.14", "88.25", "1.051"],
      ["0.60", "80.7", "94.55", "92.93", "0.835"],
      ["0.70", "61.4", "97.10", "96.14", "0.791"],
      ["0.80", "4.5", "89.86", "89.91", "17.849"],
    ],
    [1560, 2200, 1900, 1900, 1800],
    { boldRow: 2 }),
  caption("Table 7.2. Ablation of the rejection threshold on accepted "
    + "decisions. τ = 0.70 (bold) is the selected operating point."),

  fig("results/fusion_experiment/figures/tau_sweep.png", 420),
  caption("Figure 7.2. Coverage, accuracy and operational FPR of the accepted "
    + "decisions as a function of the rejection threshold τ."),

  // ---------------------------------------------------------------- 7.4
  h2("7.4. Latency of the consensus layer"),

  p("We now quantify the price of decentralised trust. For each of 40 "
  + "certified attacks we measure the consensus time — recording the alert "
  + "and collecting the signed votes up to certification — under both "
  + "consensus backends and for quorums of one, two and three notaries. "
  + "Table 7.3 reports the median and 95th-percentile consensus latency."),

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
  caption("Table 7.3. Consensus latency per certified alert (40 alerts), by "
    + "backend and quorum. Overhead is the median Fabric-minus-simulated gap."),

  p([
    r("Three findings follow. "), b("(i) The overhead is linear in the "
    + "quorum: "), r("each additional signed vote adds a near-constant "
    + "~2.06 s, so consensus latency is well approximated by "
    + "(1 + quorum) × 2.06 s. "), b("(ii) The cost is dominated by block "
    + "formation, not cryptography: "),
    r("the simulated backend performs the identical signature verification, "
    + "anti-replay and quorum logic in about two milliseconds, so the "
    + "multi-second Fabric figure is the orderer’s block-cutting interval — an "
    + "infrastructure parameter — rather than an intrinsic cost of the "
    + "consensus rule. "), b("(iii) The reflex path is unaffected: "),
    r("detection remains in the millisecond range and only certified attacks "
    + "incur the consensus cost, so the system stays viable for real-time "
    + "monitoring while still certifying decisions within seconds. Design "
    + "goal G6 is thereby met."),
  ]),

  fig("results/phase2/figures/latency_quorum.png", 380),
  caption("Figure 7.3. Median consensus latency per certified alert versus "
    + "quorum, for the simulated and Fabric backends (log scale)."),

  // ---------------------------------------------------------------- 7.5
  h2("7.5. Robustness to label-flipping poisoning"),

  p([
    r("Finally we test the security claim at the heart of the architecture: "
    + "that precision-weighted fusion neutralises a corrupted detector. We "
    + "simulate a poisoning adversary that flips a fraction "), i("p"),
    r(" of one detector’s decisions — inverting attack into benign (evasion) "
    + "and benign into a random attack — on both the validation and test "
    + "data, so that the corruption is reflected in the statistics the "
    + "weights are computed from. We target the strongest detector, the RNN, "
    + "as the worst case, and compare three responses as "), i("p"),
    r(" grows: the poisoned model alone, the ensemble with static (clean) "
    + "weights, and the ensemble with adaptive precision weights (BAg-IDS)."),
  ]),

  table(
    ["p", "RNN alone Acc/FPR (%)", "Static ens. Acc (%)",
     "Adaptive ens. Acc/FPR (%)", "RNN weight"],
    [
      ["0.0", "89.1 / 1.8", "88.2", "88.2 / 2.5", "0.334"],
      ["0.3", "62.9 / 30.7", "85.3", "85.6 / 6.7", "0.316"],
      ["0.5", "45.5 / 50.0", "83.4", "84.4 / 8.9", "0.300"],
      ["0.9", "10.6 / 88.6", "79.6", "87.1 / 7.4", "0.196"],
      ["1.0", "1.9 / 98.2", "78.6", "87.2 / 7.3", "0.058"],
    ],
    [900, 2500, 2000, 2400, 1560],
    { boldLastRows: 1 }),
  caption("Table 7.4. Robustness to label-flipping of the RNN. As the "
    + "poisoned model collapses, the adaptive ensemble loses about one "
    + "accuracy point and auto-excludes the corrupted detector "
    + "(weight 0.334 → 0.058)."),

  p("The result is decisive. A fully poisoned RNN is destroyed as a "
  + "standalone detector — accuracy 1.9%, FPR 98.2% at p = 1.0 — yet the "
  + "BAg-IDS ensemble loses only about one accuracy point (88.2% → 87.2%). "
  + "The mechanism is visible in the last column: the adaptive weight of the "
  + "corrupted detector falls from 0.334 to 0.058 as its validation precision "
  + "collapses, so its influence on the fused decision is automatically "
  + "suppressed without any explicit attack detection. The comparison with "
  + "static weights isolates the effect: at p = 1.0 the static ensemble "
  + "degrades to 78.6% while the adaptive ensemble holds at 87.2%, an "
  + "eight-point gap attributable purely to weight adaptation. Design goal G1 "
  + "is thereby met."),

  p("The worst degradation of the adaptive ensemble occurs not at full "
  + "poisoning but around p = 0.5 (84.4%): a partially corrupted detector is "
  + "more insidious than a fully corrupted one, because it retains enough "
  + "precision to keep a non-negligible weight. This U-shaped response "
  + "(Figure 7.4) is an argument for the complementary drift monitoring "
  + "performed by the Data Scientist agent, which flags the elevated "
  + "rejection rate that partial poisoning induces and can trigger "
  + "recalibration before the weights fully adapt."),

  fig("results/phase2/figures/label_flipping.png", 420),
  caption("Figure 7.4. Accuracy under label-flipping of the RNN: poisoned "
    + "model alone versus ensemble with static and adaptive weights."),

  fig("results/phase2/figures/poisoned_weight.png", 380),
  caption("Figure 7.5. Adaptive fusion weight of the poisoned detector versus "
    + "poisoning fraction, for a strong (RNN) and a weak (CNN) target."),
];
