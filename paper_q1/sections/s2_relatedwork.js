/* Section 2 — Related Work.
 * Synthese critique : DL IDS -> ensembles/calibration/selectif ->
 * adversarial -> multi-agents -> blockchain -> agentic AI (3 phases) ->
 * convergence agentic+blockchain -> positionnement (Table 1 biblio +
 * Table 2 criteres C1-C8). Refs alignees sur s10_references.js. */
module.exports = ({ h1, h2, h3, p, r, b, i, eq, li, caption, table, fig }) => [

  h1("2. Related Work"),

  p([
    r("BAg-IDS lies at the intersection of five research threads: deep-"
    + "learning intrusion detection, confidence-aware and selective "
    + "classification, adversarial robustness of learned detectors, "
    + "multi-agent and blockchain-based collaborative security, and the "
    + "rapidly maturing use of large language models (LLMs) as autonomous "
    + "agents in cyber defence. We review each thread critically rather "
    + "than as a catalogue, giving particular attention to the 2023–2026 "
    + "literature, and we organise the agentic line along the three-phase "
    + "evolution that the recent surveys converge on [64, 76]. Two "
    + "synthesis tables close the section: a bibliographic comparison of "
    + "the closest agentic/blockchain/IDS systems (Table 1) and a "
    + "capability matrix that positions BAg-IDS against the whole design "
    + "space along eight criteria (Table 2)."),
  ]),

  // ---------------------------------------------------------------- 2.1
  h2("2.1. Deep learning for network intrusion detection"),

  p([
    r("Learning-based intrusion detection has moved decisively toward deep "
    + "models. Recurrent architectures capture temporal structure in flow "
    + "sequences [1], convolutional and hybrid networks learn "
    + "discriminative spatial features [2], and deep autoencoders and "
    + "self-taught learning cope with high-dimensional, imbalanced traffic "
    + "[3, 4]; systematic studies established deep networks as the state of "
    + "the art across the standard benchmarks [5, 6]. Much of this progress "
    + "rests on realistic public datasets, chiefly CICIDS2017 and "
    + "CSE-CIC-IDS2018 [7, 8], which are now the de facto reference and the "
    + "basis of our own evaluation, although their generation tooling and "
    + "labelling carry documented flaws [50–52] against which any results, "
    + "including ours, must be read (Section 6.1). The most recent wave "
    + "applies attention and Transformer architectures to cloud and "
    + "imbalanced traffic [9, 10] and, increasingly, treats detection as a "
    + "bridge toward language-model-based analysis [11]. Our own prior "
    + "comparative study [56] belongs to this thread: it trained on "
    + "CICIDS2017 the RNN, CNN and DNN detectors reused here as the "
    + "reflex-layer members. The critical limitation common to this entire "
    + "line is architectural rather than statistical: detection is treated "
    + "as a single-model prediction problem that stops at the classifier "
    + "and implicitly trusts its own output, saying nothing about how a "
    + "decision, once made, should be calibrated, trusted, recorded, or "
    + "acted upon. That silence is the gap this paper addresses."),
  ]),

  // ---------------------------------------------------------------- 2.2
  h2("2.2. Ensembles, calibration, and selective detection"),

  p([
    r("To offset the variance and blind spots of any single model, "
    + "ensemble intrusion detection combines heterogeneous classifiers, "
    + "with documented accuracy and robustness benefits over monolithic "
    + "detectors [12, 13]. The tradeoff is well known: ensembles add "
    + "inference and maintenance cost, and, more subtly, most of them fuse "
    + "votes with fixed or accuracy-agnostic weights over raw network "
    + "confidences, which modern neural networks are known to miscalibrate "
    + "[14, 15]. Two complementary correctives have matured. Temperature "
    + "scaling [14] restores confidence reliability without changing the "
    + "arg-max, and selective classification [16] equips the classifier "
    + "with a reject option that abstains on low-confidence inputs; the "
    + "operational relevance of this abstention, where a false alarm has a "
    + "real cost, is increasingly recognised both in the general "
    + "reject-option literature [17] and in uncertainty-aware NIDS [18]. "
    + "These mechanisms are individually standard, yet they are rarely "
    + "combined into a single detector whose fusion weights, calibration "
    + "and reject threshold are co-designed. BAg-IDS makes exactly that "
    + "combination the reflex layer, and it ties the fusion weights to each "
    + "detector’s recent, calibrated reliability so that, as Section 6.7 "
    + "shows, the ensemble becomes a defence against a corrupted member "
    + "rather than merely an accuracy aggregator, while the reject region "
    + "doubles as the explicit coupling that shapes the load offered to the "
    + "deliberative layer (Section 6.5)."),
  ]),

  // ---------------------------------------------------------------- 2.3
  h2("2.3. Adversarial and poisoning threats to learned detectors"),

  p([
    r("A decade of adversarial machine learning has shown that learned "
    + "detectors are attackable at test time and at training time [19, 20]. "
    + "Poisoning attacks, in which an adversary corrupts the training data, "
    + "for instance by flipping labels, to degrade or backdoor the deployed "
    + "model, are especially damaging for continuously retrained IDS "
    + "[21, 22] and have been surveyed in depth [23]. The recent literature "
    + "sharpens the operational picture: realistic-capability models for "
    + "deployed NIDS [24], systematisations of attacks and defences [25], "
    + "and comprehensive surveys of the adversarial-ML landscape [26], "
    + "while poisoning has also been demonstrated against federated IDS "
    + "training [27]. The dominant defensive pattern adds an explicit "
    + "anomaly or poisoning detector, which itself becomes an attack "
    + "surface and a source of false positives, and thus trades one "
    + "fragile component for another. Our approach is complementary and "
    + "structural: rather than detecting poisoning, reliability-weighted "
    + "fusion suppresses a corrupted member automatically, a resilience we "
    + "quantify under simulated output corruption as a worst-case "
    + "poisoning proxy (Section 6.7), and against a robust-aggregation "
    + "baseline (median/trimmed pooling)."),
  ]),

  // ---------------------------------------------------------------- 2.4
  h2("2.4. Multi-agent and collaborative intrusion detection"),

  p([
    r("Decomposing intrusion detection across autonomous, cooperating "
    + "agents dates back to early distributed IDS designs [28] and "
    + "reference architectures for autonomous cyber defence such as AICA "
    + "[72], and it has continued through agent-based and collaborative "
    + "monitors that share evidence across nodes [29]. The paradigm scales "
    + "detection and improves resilience, but it introduces a trust "
    + "problem that repeatedly resurfaces in recent work: a single "
    + "malicious or compromised participant can poison the shared view or "
    + "forge alerts. Liang et al. [57] pair distributed deep-learning "
    + "monitors with a blockchain ledger for tamper-proof alert sharing on "
    + "NSL-KDD, but the agents remain reactive and lack autonomous "
    + "response. Soltani et al. [58] add adaptivity, coupling CNN- and "
    + "LSTM-based detectors with continual and federated learning so that "
    + "agents track concept drift and zero-day patterns, reporting "
    + "detection rates above 95% on CICIDS2017 and CSE-CIC-IDS2018; yet "
    + "their framework provides no trust layer for the inter-agent "
    + "exchange it depends on. Surveys of trust-based collaborative IDS "
    + "[30] and of open multi-agent security challenges [75] identify "
    + "insider threats and the reliance on a trusted aggregation point as "
    + "the central unresolved issues. BAg-IDS retains the multi-agent "
    + "decomposition but removes the trusted aggregator, replacing "
    + "reputation heuristics with a cryptographically enforced, "
    + "quorum-based consensus on the decision itself."),
  ]),

  // ---------------------------------------------------------------- 2.5
  h2("2.5. Blockchain for trustworthy and collaborative security"),

  p([
    r("Blockchain has been proposed as the missing trust substrate for "
    + "collaborative detection. Early position work argued for "
    + "blockchain-based collaborative IDS [31], systems such as CIoTA "
    + "demonstrated blockchain-anchored anomaly detection for IoT devices "
    + "[32], and reviews catalogued the design space [33]. Permissioned "
    + "platforms, notably Hyperledger Fabric, whose execute–order–validate "
    + "architecture underpins our deployment [34], made auditable, "
    + "identity-bound ledgers practical. The most active current sub-line "
    + "fuses federated learning with blockchain so that the chain secures "
    + "the integrity and accountability of shared model updates: Ali et "
    + "al.’s FL-BCID validates federated updates through smart contracts "
    + "on ToN-IoT and N-BaIoT [59]; Begum et al.’s BFLIDS combines CNN and "
    + "BiLSTM classifiers with Ethereum smart contracts for decentralised "
    + "model aggregation, reporting accuracies above 97% on Edge-IIoTSet "
    + "and TON-IoT [60]; Aydin and Aydin target DDoS with a federated, "
    + "blockchain-backed multi-agent design [74]; and consensus-driven "
    + "variants add PBFT-verified alerting on top of gradient-boosted "
    + "detectors [61]. General secure-logging IDS provide immutability and "
    + "decentralised trust for IoT anomaly detection but stop there "
    + "[62]. Two limitations are shared across this category and are "
    + "decisive for our design. First, and with rare exceptions, the "
    + "ledger secures the collaboration, meaning the sharing of data, "
    + "alerts or model updates, while the detection decision itself is "
    + "still produced by a single, implicitly trusted model and merely "
    + "logged after the fact. Second, the multi-second cost of on-chain "
    + "commitment is seldom reconciled with line-rate detection. BAg-IDS "
    + "answers both: it places a smart contract on the decision path, so "
    + "that a quorum of signed notary votes, not a single model, certifies "
    + "each remediation-triggering verdict, and it confines that cost to "
    + "the small certified fraction of traffic through the reflex/"
    + "deliberative asymmetry (Sections 6.5–6.6)."),
  ]),

  // ---------------------------------------------------------------- 2.6
  h2("2.6. Agentic AI in cyber defence: a three-phase evolution"),

  p([
    r("The most recent thread reframes detectors as autonomous, "
    + "goal-driven agents. Recent surveys converge on a three-phase "
    + "reading of this evolution [64, 76], which we adopt as an organising "
    + "device. In the "), b("first phase"),
    r(" (learning-based agents), autonomy came from reinforcement and "
    + "continual learning: deep reinforcement learning let agents adapt "
    + "defensive policies to evolving threats [73], at the cost of "
    + "fragile reward design and unstable policies, and multi-agent RL "
    + "extended this to coordinated response. The "),
    b("second phase"),
    r(" (cognitive, LLM-based agents) added contextual reasoning over "
    + "unstructured evidence: LLMs moved from text assistants to "
    + "orchestrators able to plan investigations and summarise alerts "
    + "[41–46], with the ReAct tool-use loop [45] supplying the "
    + "perceive–reason–act pattern our Investigator instantiates. Concrete "
    + "systems illustrate the range: HuntGPT couples an anomaly detector "
    + "with explainable-AI and a conversational LLM for analyst-facing "
    + "triage [47]; H. Li et al. propose an LLM-enhanced agentic, "
    + "multi-agent collaborative IDS with specialised traffic-analysis, "
    + "classification and response agents, reporting classification "
    + "accuracy above 90% on benchmark IDS data but providing no "
    + "blockchain trust layer for the alerts they exchange [63]; and "
    + "NetMoniAI deploys per-node LLM-empowered agents with a central "
    + "controller for DDoS-style detection, explicitly acknowledging that "
    + "it lacks on-chain immutability and that its central orchestrator is "
    + "a single point of failure [66]. The "),
    b("third phase"),
    r(" (decentralised, resilient agents) is where trust, accountability "
    + "and resilience become first-class: blockchain provides tamper-proof "
    + "records of agent actions and smart contracts encode coordination "
    + "and access-control policies without a central authority. A recurring "
    + "and well-founded conclusion across all three phases, echoed by the "
    + "SOC-automation and analyst-trust literature [48] and by dedicated "
    + "agentic-security surveys [64], is that an LLM cannot and should not "
    + "adjudicate every low-level event at line rate, and that its outputs "
    + "require oversight. This motivates hybrid, human-supervised designs "
    + "that reserve language-model reasoning for high-level decisions, a "
    + "modern instantiation of the classic reflex/deliberative separation "
    + "[49]. BAg-IDS embodies that separation and supplies what phase-two "
    + "agentic IDS still lack: a decentralised trust layer beneath the "
    + "agents and a governed human-in-the-loop layer above them."),
  ]),

  // ---------------------------------------------------------------- 2.7
  h2("2.7. Convergence of agentic AI and blockchain"),

  p([
    r("The closest and most novel context for our work is the emerging "
    + "convergence of agentic AI with blockchain, developed largely "
    + "outside intrusion detection. Beyond security, DeCoAgent lets "
    + "LLM-based agents register on-chain, discover peers and negotiate "
    + "task allocation through smart contracts [67], and Qi et al. extend "
    + "this with reputation tracking and incentive-compatible matching for "
    + "open Web3 ecosystems [68]; both demonstrate feasibility but report "
    + "significant smart-contract overhead and degraded matching when "
    + "agent capabilities overlap, and neither is validated at scale. "
    + "Within collaborative reasoning, BlockAgents introduces a "
    + "Proof-of-Thought consensus that combines reasoning-based evaluation "
    + "with stake-based voting to blunt Byzantine and poisoning behaviour "
    + "among LLM agents, at the price of added latency and computational "
    + "complexity [69], while DAO-AI evaluates agentic voting over more "
    + "than 3,000 real governance proposals and finds strong alignment "
    + "with human outcomes but no collaborative multi-agent reasoning "
    + "[70]. Closer to security, Lad et al. use smart contracts to govern "
    + "inter-agent communication and accountability in cyber-physical MAS "
    + "[71], and Gosmar and Dahl’s Sentinel Agents monitor inter-agent "
    + "communication for coordinated threats using behavioural analytics, "
    + "though validated only on synthetic scenarios and not integrated "
    + "with an IDS [65]. The pattern across this convergence is clear and "
    + "instructive: blockchain and smart contracts are used to coordinate, "
    + "govern or incentivise agents, and their common tradeoff is the "
    + "transaction-latency and complexity cost of frequent on-chain "
    + "interaction. What is missing is a system that turns this "
    + "convergence back onto the detection decision itself, placing "
    + "quorum-based certification on the per-verdict path of an operational "
    + "IDS while keeping that cost off the line-rate path. BAg-IDS is, to "
    + "our knowledge, the first to do so."),
  ]),

  // ---------------------------------------------------------------- 2.8
  h2("2.8. Critical synthesis and positioning"),

  p([
    r("Read as a whole, the literature exhibits a consistent division of "
    + "labour and a consistent blind spot. The detection community "
    + "(Sections 2.1–2.3) perfects the classifier but trusts its output; "
    + "the collaborative and blockchain community (Sections 2.4–2.5) "
    + "secures the sharing of alerts or model updates but leaves the "
    + "decision to a single implicitly trusted model and rarely addresses "
    + "line-rate cost; the agentic community (Section 2.6) adds reasoning "
    + "and autonomy but, in its deployed IDS instances, provides neither "
    + "decentralised trust nor a measured full-stack system; and the "
    + "agentic-blockchain convergence (Section 2.7) demonstrates on-chain "
    + "coordination and governance of agents but has not been brought to "
    + "the intrusion-detection decision itself. Table 1 makes this "
    + "concrete for the closest systems, and Table 2 abstracts it into "
    + "eight capabilities that jointly define trustworthy autonomous "
    + "detection."),
  ]),

  p([
    b("(C1) Calibrated ensemble detection"),
    r(": heterogeneous detectors fused over honest confidences. "),
    b("(C2) Selective classification"),
    r(": an explicit reject region that withholds unreliable decisions "
    + "from automation. "),
    b("(C3) Corruption robustness"),
    r(": graceful degradation when a member model is corrupted (evaluated "
    + "under simulated output corruption, a worst-case poisoning proxy; "
    + "Section 6.7). "),
    b("(C4) Decentralised cryptographic consensus"),
    r(": no single trusted aggregator may certify a decision. "),
    b("(C5) Immutable decision audit"),
    r(": every certified verdict and vote is tamper-evident. "),
    b("(C6) Agentic LLM reasoning"),
    r(": multi-step, tool-using investigation rather than single-shot "
    + "classification. "),
    b("(C7) Governed human oversight"),
    r(": a human gate whose own administrative actions are signed and "
    + "auditable. "),
    b("(C8) Line-rate viability"),
    r(": the expensive machinery is kept off the per-flow path."),
  ]),

  // ---- Table 1 : comparaison bibliographique des systemes proches ----
  table(
    ["Ref. (year)", "Approach", "BC", "Ag", "SC", "Reported result",
     "Gap addressed by BAg-IDS"],
    [
      ["Liang [57] (2020)", "DL monitors + blockchain alert log (IoT)",
       "✓", "±", "✗", "83.2% acc (NSL-KDD)",
       "No autonomy or on-decision consensus"],
      ["Soltani [58] (2023)", "Multi-agent adaptive CNN/LSTM + FL",
       "✗", "✓", "✗", ">95% (CIC-IDS2017/18)",
       "No trust layer for inter-agent exchange"],
      ["Ali [59] (2025)", "FL-BCID: federated IDS + SC validation",
       "✓", "✗", "✓", "97.3% acc (ToN-IoT)",
       "No agent coordination; log-only ledger"],
      ["Begum [60] (2024)", "BFLIDS: FL + Ethereum aggregation (IoMT)",
       "✓", "✗", "✓", "97.4% acc (Edge-IIoTSet)",
       "No autonomy; decision off-chain"],
      ["Nandanwar [61] (2025)", "PBFT consensus + XGBoost IDS",
       "✓", "✗", "±", "n/r (NSL-KDD)",
       "No agent collaboration; dated data"],
      ["Kumar [62] (2025)", "Secure blockchain IDS logging (IoT)",
       "✓", "✗", "✗", "n/r (IoT traffic)",
       "No automated mitigation or agency"],
      ["H. Li [63] (2026)", "LLM-enhanced agentic collaborative IDS",
       "✗", "✓", "✗", ">90% (benchmarks)",
       "No blockchain trust for shared alerts"],
      ["Gosmar [65] (2025)", "Sentinel agents, behavioural MAS monitor",
       "✗", "✓", "✗", "n/r (synthetic)",
       "Not integrated with an IDS"],
      ["Zambare [66] (2025)", "NetMoniAI: per-node LLM agents + controller",
       "✗", "✓", "✗", "n/r",
       "Central SPoF; no on-chain immutability"],
      ["Jin [67] (2024)", "DeCoAgent: on-chain LLM-agent collaboration",
       "✓", "✓", "✓", "n/r (feasibility)",
       "Not a detector; rigid contract logic"],
      ["Qi [68] (2025)", "Blockchain-driven LLM-agent matching (Web3)",
       "✓", "✓", "✓", "n/r (simulation)",
       "High SC overhead; not security"],
      ["X. Li [69] (2024)", "BlockAgents: Proof-of-Thought consensus",
       "✓", "✓", "✓", "qual. (poison ↓)",
       "Latency; not a detector"],
      ["Capponi [70] (2025)", "DAO-AI: agentic on-chain governance voting",
       "✓", "✓", "✓", "3k proposals",
       "No collaborative reasoning; not IDS"],
      ["BAg-IDS (this work)",
       "Calibrated CWC ensemble + reject + LLM + Fabric quorum + HITL",
       "✓", "✓", "✓", "99.7% cert., 0.04% FPR (CICIDS2017)",
       "this work"],
    ],
    [1350, 2350, 360, 360, 360, 1560, 3020],
    { boldLastRows: 1 }),
  caption("Table 1. Bibliographic comparison of the closest agentic, "
    + "blockchain and IDS systems. BC: uses blockchain; Ag: agentic/"
    + "autonomous; SC: smart contracts. ✓ present, ± partial, ✗ absent. "
    + "“n/r”: not reported in the source available to us; “qual.”: "
    + "qualitative only. Reported results are stated by the cited authors "
    + "under their own protocols and are not directly comparable across "
    + "rows; Section 6.9 places our measured results next to these "
    + "reported figures."),

  // ---- Table 2 : matrice de capacites C1-C8 ----
  table(
    ["Approach", "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"],
    [
      ["Deep-learning / Transformer IDS [1–11]",
       "±", "✗", "✗", "✗", "✗", "✗", "✗", "✓"],
      ["Ensemble IDS [12, 13]",
       "±", "✗", "±", "✗", "✗", "✗", "✗", "✓"],
      ["Selective / uncertainty-aware IDS [16–18]",
       "±", "✓", "✗", "✗", "✗", "✗", "✗", "✓"],
      ["Adversarially-defended IDS [24–27]",
       "✗", "✗", "±", "✗", "✗", "✗", "✗", "✓"],
      ["Multi-agent / collaborative IDS [28–30, 57, 58]",
       "±", "✗", "±", "✗", "±", "✗", "±", "✓"],
      ["Blockchain / FL-blockchain IDS [31–40, 59–62, 74]",
       "±", "✗", "±", "✓", "✓", "✗", "✗", "±"],
      ["Agentic / LLM defence [41–47, 63, 65, 66]",
       "✗", "✗", "✗", "✗", "✗", "✓", "±", "±"],
      ["Agentic + blockchain (non-IDS) [67–71]",
       "✗", "✗", "±", "✓", "✓", "✓", "±", "✗"],
      ["BAg-IDS (this work)",
       "✓", "✓", "✓", "✓", "✓", "✓", "✓", "✓"],
    ],
    [3160, 725, 725, 725, 725, 725, 725, 725, 725],
    { boldLastRows: 1 }),
  caption("Table 2. Capability-matrix positioning of BAg-IDS. C1 "
    + "calibrated ensemble; C2 selective classification (reject); C3 "
    + "corruption robustness (poisoning proxy); C4 decentralised "
    + "cryptographic consensus on the decision; C5 immutable decision "
    + "audit; C6 agentic (multi-step, tool-using) LLM reasoning; C7 "
    + "governed, auditable human oversight; C8 line-rate viability. "
    + "✓ intrinsic to the category; ± present in some works, not "
    + "intrinsic; ✗ absent."),

  p([
    r("The two tables converge on the same reading, which is the "
    + "contribution of this paper. Each capability has a mature literature "
    + "behind it, yet no prior system exhibits all eight, and the "
    + "agentic-blockchain convergence that comes closest (row 8 of "
    + "Table 2) has never been applied to the detection decision or shown "
    + "to be line-rate viable. A new approach is therefore necessary not "
    + "because any single mechanism is missing, but because these "
    + "mechanisms live in communities that rarely intersect, and their "
    + "naive composition is not viable: placing an LLM or a blockchain on "
    + "the per-flow path would destroy real-time detection, while logging "
    + "decisions after a single model has made them provides auditability "
    + "without trust. "),
    b("To our knowledge, BAg-IDS is the first measured system to satisfy "
    + "all eight criteria simultaneously"),
    r(": a calibrated, poisoning-resilient selective ensemble on the "
    + "per-flow path; a smart-contract consensus that certifies every "
    + "remediation-triggering verdict through quorum-signed votes; an "
    + "agentic investigator whose multi-step reasoning is itself anchored "
    + "on the ledger; and a governed human-in-the-loop layer whose every "
    + "administrative act, including switching autonomy on or off, is a "
    + "signed on-chain transaction. It resolves the specific limitations "
    + "identified above, namely the single point of trust of "
    + "single-model IDS (C1, C4), the after-the-fact and off-decision role "
    + "of the ledger in blockchain IDS (C4, C5), the absent trust layer of "
    + "agentic IDS (C4–C5), and the line-rate infeasibility of naive "
    + "on-chain or LLM-in-the-loop designs (C8), and it does so as one "
    + "fully implemented artefact whose every reported number is measured "
    + "(Sections 4–6)."),
  ]),
];
