/* Chapitre 1 — General Introduction. */
module.exports = ({ h1, h2, h3, p, r, b, i, eq, li, caption, table, fig }) => [

  h1("Chapter 1. General Introduction"),

  // ---------------------------------------------------------------- 1.1
  h2("1.1. Context and Motivation"),

  p("Contemporary information systems operate under a level of adversarial "
  + "pressure that has no precedent. Enterprises, cloud providers and critical "
  + "infrastructures are targeted continuously by automated reconnaissance, "
  + "distributed denial-of-service campaigns, credential-stuffing bots, web "
  + "exploitation and lateral-movement techniques that evolve faster than "
  + "signatures can be written. In this environment the intrusion detection "
  + "system (IDS) is a cornerstone of the defensive posture: it is the sensor "
  + "and, increasingly, the decision-maker that decides whether a stream of "
  + "network activity is benign or hostile, and whether an automated response "
  + "should be triggered."),

  p("Over the past decade the internal machinery of the IDS has shifted "
  + "decisively from hand-crafted rules toward machine learning, and within "
  + "machine learning toward deep neural networks. Recurrent, convolutional "
  + "and fully-connected architectures now routinely outperform classical "
  + "detectors on the public benchmarks, learning discriminative "
  + "representations of traffic that no human analyst could enumerate. This "
  + "progress is real and valuable. Yet it has concentrated the security of "
  + "the network into a component that is, paradoxically, itself insecure in "
  + "three distinct and compounding ways — and it is this paradox that "
  + "motivates the present thesis."),

  p([
    r("First, the modern IDS is a "), b("single point of trust"),
    r(". A verdict is produced by one model, executing on one host, and is "
    + "then acted upon — a host is blocked, a connection is throttled, an "
    + "account is suspended. There is nothing between an erroneous or "
    + "manipulated verdict and a consequential, sometimes irreversible, "
    + "action. Second, the "), b("record of the decision is mutable"),
    r(". Conventional logs can be altered or deleted by whoever controls the "
    + "host, so that after an incident there is no independently verifiable "
    + "account of what was detected, who concurred, and what was done. As "
    + "automated response and regulatory accountability both grow, this "
    + "absence of a tamper-evident decision trail becomes a serious "
    + "liability. Third, the "), b("learned detector is itself attackable"),
    r(". A decade of adversarial machine-learning research has shown that "
    + "models can be evaded at inference time and, more insidiously, poisoned "
    + "at training time, so that a deployed detector is silently corrupted "
    + "and misclassifies precisely the traffic an adversary cares about."),
  ]),

  p("Each of these weaknesses has attracted a substantial and largely "
  + "separate research literature. Robustness to poisoning is studied within "
  + "adversarial machine learning; tamper-evident records are studied within "
  + "blockchain and distributed-ledger research; and the decentralisation of "
  + "trust across cooperating monitors is studied within collaborative and "
  + "multi-agent intrusion detection. In parallel, a fourth and very recent "
  + "current has emerged: the use of large language models (LLMs) as "
  + "autonomous, reasoning agents for security operations, promising "
  + "contextual judgement and human-readable explanations that pure "
  + "classifiers cannot provide. What is conspicuously missing is an "
  + "architecture in which these concerns are addressed not in isolation but "
  + "together — where detection, the robustness of detection, the trust placed "
  + "in a decision, the immutability of its record, and the possibility of "
  + "human oversight are co-designed as facets of one system."),

  // ---------------------------------------------------------------- 1.2
  h2("1.2. Problem Statement"),

  p("The problem this thesis addresses can be stated compactly. A network "
  + "intrusion detection system that relies on deep learning is, in current "
  + "practice, accurate but untrustworthy in a precise technical sense: its "
  + "decisions rest on a single, corruptible model; its decision record is "
  + "mutable; and it offers no principled way to combine autonomous machine "
  + "speed with accountable human oversight. Existing approaches mitigate "
  + "individual facets of this problem but not their conjunction. "
  + "Blockchain-based collaborative IDS bring decentralised, tamper-evident "
  + "trust, yet they typically use the ledger only to share detection data or "
  + "model updates and leave the detector a single, unhardened model. Agentic "
  + "LLM proposals bring contextual reasoning, yet a language model can "
  + "neither adjudicate every packet at line rate nor be trusted without "
  + "oversight, and such proposals rarely provide any decentralised trust "
  + "guarantee beneath the reasoning. Ensemble and calibration techniques "
  + "improve accuracy and confidence quality, yet they are not, on their own, "
  + "a defence against a corrupted member or a substitute for an auditable "
  + "decision. No existing system delivers a detector that is simultaneously "
  + "robust to poisoning, decentralised in whom it trusts, tamper-evident in "
  + "what it records, and answerable to a human — without sacrificing "
  + "real-time detection."),

  // ---------------------------------------------------------------- 1.3
  h2("1.3. Research Questions"),

  p("From this problem statement we derive the research questions that "
  + "structure the thesis:"),

  li([b("RQ1. "), r("Can an ensemble of heterogeneous neural detectors be "
    + "fused in a way that is not merely more accurate than its members but "
    + "structurally robust to the corruption of one member, without relying "
    + "on an explicit poisoning detector?")]),
  li([b("RQ2. "), r("Can the decision of an IDS be certified by a "
    + "decentralised, cryptographically enforced consensus among independent "
    + "parties, so that no single agent — or compromised host — can "
    + "unilaterally trigger a remediation or forge the record of one?")]),
  li([b("RQ3. "), r("Can autonomous contextual reasoning, provided by a large "
    + "language model, be integrated into the detection pipeline without "
    + "placing the model on the per-flow critical path or making the system "
    + "depend on its availability?")]),
  li([b("RQ4. "), r("Can human oversight be added as an optional, governed "
    + "control surface such that the exercise of administrative authority is "
    + "itself auditable, without reintroducing a single point of trust?")]),
  li([b("RQ5. "), r("What is the real operational cost — in latency and "
    + "engineering complexity — of combining these mechanisms, and is that "
    + "cost compatible with real-time network monitoring on commodity "
    + "hardware?")]),

  // ---------------------------------------------------------------- 1.4
  h2("1.4. Objectives"),

  p("The overarching objective of this thesis is to design, implement and "
  + "empirically evaluate an intrusion detection architecture that answers "
  + "the research questions above within a single coherent system. This "
  + "general objective decomposes into the following specific objectives:"),

  li([b("O1. "), r("Design a calibrated, reliability-weighted ensemble fusion "
    + "rule and characterise its behaviour under data poisoning.")]),
  li([b("O2. "), r("Design and implement a permissioned-blockchain consensus "
    + "mechanism, expressed as a smart contract, that certifies "
    + "remediation-triggering verdicts through multi-party signed voting with "
    + "quorum, anti-replay and tamper-evident audit.")]),
  li([b("O3. "), r("Integrate an LLM-based deliberative layer that is "
    + "event-triggered, rate-limited and gracefully degradable, so that "
    + "autonomy and reproducibility are preserved.")]),
  li([b("O4. "), r("Design a governed human-in-the-loop supervision layer "
    + "whose administrative actions are cryptographically signed and anchored "
    + "on the same ledger, and which can be enabled or disabled at run time.")]),
  li([b("O5. "), r("Implement the full system on commodity hardware and "
    + "measure — rather than project — its detection quality, the "
    + "coverage–reliability trade-off, the latency cost of the consensus "
    + "layer, and its robustness to a label-flipping poisoning attack.")]),

  // ---------------------------------------------------------------- 1.5
  h2("1.5. Contributions"),

  p("The thesis makes four principal contributions, each developed and "
  + "evaluated in the chapters that follow:"),

  li([b("A hybrid reflex/deliberative agentic architecture "),
    r("for intrusion detection (Chapter 5) that couples a real-time "
    + "calibrated ensemble with event-triggered LLM reasoning, so that "
    + "autonomous contextual judgement is applied without placing a language "
    + "model on the per-flow critical path.")]),
  li([b("The Conscious Weighted Consensus fusion rule "),
    r("(Chapter 5), in which detectors are weighted by their calibrated, "
    + "recent reliability, together with the empirical demonstration "
    + "(Chapter 7) that this same mechanism yields structural robustness to "
    + "label-flipping poisoning — a fully corrupted detector is auto-excluded "
    + "with no explicit attack detection.")]),
  li([b("A blockchain consensus layer placed on the decision path "),
    r("(Chapters 5–6), realised as a Hyperledger Fabric smart contract that "
    + "certifies each remediation-triggering verdict through multi-party "
    + "signed voting, and extended — distinctively — to anchor human "
    + "governance actions so that even the administrator is auditable.")]),
  li([b("A complete, measured implementation and evaluation "),
    r("(Chapters 6–7) of the entire stack on commodity hardware, with every "
    + "reported figure produced by the running system, including a "
    + "quantification of the blockchain’s latency cost and its scaling with "
    + "the consensus quorum.")]),

  // ---------------------------------------------------------------- 1.6
  h2("1.6. Research Methodology"),

  p("The thesis follows a constructive, design-science methodology: it builds "
  + "an artefact — the BAg-IDS system — and evaluates it empirically against "
  + "the objectives above. The methodology proceeds in three phases. The "
  + "first phase establishes an executable, measured detection core: the "
  + "calibrated ensemble is reconstructed from trained detectors, its "
  + "behaviour is characterised, and the fusion and rejection mechanisms are "
  + "specified and instrumented. The second phase builds the surrounding "
  + "agentic and trust machinery incrementally — the autonomous agents, the "
  + "consensus logic first as a hash-chained simulation and then as deployed "
  + "blockchain chaincode, and the human-in-the-loop layer — validating each "
  + "component against explicit tests before composing them. The third phase "
  + "conducts a measurement campaign that treats each design goal as an "
  + "evaluation criterion, producing the tables and figures reported in "
  + "Chapter 7. Throughout, a deliberate emphasis is placed on "
  + "reproducibility and on the honest separation of what is measured from "
  + "what is argued."),

  // ---------------------------------------------------------------- 1.7
  h2("1.7. Thesis Organization"),

  p("The remainder of this thesis is organised as follows. "),
  li([b("Chapter 2 "), r("surveys the state of the art across the four "
    + "research threads the thesis unifies, and positions the contribution.")]),
  li([b("Chapter 3 "), r("presents the technical background — deep learning "
    + "for detection, confidence calibration, permissioned blockchain and "
    + "Hyperledger Fabric, and large language models as agents — needed to "
    + "follow the design.")]),
  li([b("Chapter 4 "), r("states the threat model, the trust assumptions and "
    + "the design goals that the architecture must satisfy.")]),
  li([b("Chapter 5 "), r("presents the four-layer BAg-IDS architecture in "
    + "detail, including the Conscious Weighted Consensus fusion rule and the "
    + "consensus and supervision layers.")]),
  li([b("Chapter 6 "), r("describes the implementation, the deployment "
    + "environment and the reproducibility provisions.")]),
  li([b("Chapter 7 "), r("reports the experimental evaluation: detection "
    + "quality and calibration, the rejection-threshold ablation, the "
    + "consensus latency study, and the poisoning-robustness experiment.")]),
  li([b("Chapter 8 "), r("analyses the security of the system threat by "
    + "threat, grounding each claim in the mechanisms and measurements.")]),
  li([b("Chapter 9 "), r("discusses the implications, states the limitations "
    + "candidly, and outlines directions for future work.")]),
  li([b("Chapter 10 "), r("concludes the thesis.")]),
];
