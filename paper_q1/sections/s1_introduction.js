/* Section 1 — Introduction. */
module.exports = ({ h1, h2, h3, p, r, b, i, eq, li, caption, table, fig }) => [

  h1("1. Introduction"),

  p([
    r("Modern networks are defended by intrusion detection systems (IDS) that "
    + "increasingly rely on deep learning to recognise attacks in high-volume "
    + "traffic. These learned detectors are accurate, but they are also "
    + "opaque, brittle under adversarial pressure, and, most importantly for "
    + "operations, they produce decisions that a security operations centre "
    + "(SOC) must simply trust. In practice a single model, running on a "
    + "single host, emits a verdict that may trigger an automated response "
    + "such as blocking a host or throttling a link. Three weaknesses follow "
    + "from this arrangement, and they compound one another."),
  ]),

  p([
    r("First, "), b("the decision rests on a single point of trust"),
    r(". If the model is wrong, poisoned, or the host that runs it is "
    + "compromised, there is nothing between a bad verdict and a harmful "
    + "action. Second, "), b("the record of the decision is mutable"),
    r(". A conventional log can be altered or deleted, so after an incident "
    + "there is no tamper-evident account of what was detected, who agreed, "
    + "and what was done. This is an increasing liability as automated "
    + "response and regulatory accountability grow. Third, "),
    b("learned detectors are attackable"),
    r(". Poisoning attacks that corrupt training data can silently degrade a "
    + "deployed model, and defences that add an explicit poisoning detector "
    + "merely move the problem to another fragile component. Each weakness has "
    + "been studied in isolation; what is missing is an architecture in which "
    + "detection, trust, and human oversight are designed together."),
  ]),

  p([
    r("Two research currents each address part of the problem but not the "
    + "whole. Blockchain-based collaborative IDS bring decentralised, "
    + "tamper-evident trust, yet they use the ledger mainly to share detection "
    + "data or model updates and leave the detector itself a single, "
    + "unhardened model. In parallel, large language models (LLMs) are being "
    + "cast as autonomous agents for security operations, bringing contextual "
    + "reasoning and human-readable rationale, yet an LLM can neither "
    + "adjudicate every packet at line rate nor be trusted without oversight, "
    + "and agentic proposals rarely provide any decentralised trust guarantee "
    + "beneath the reasoning. Neither current, on its own, yields a detector "
    + "that is simultaneously robust, trustworthy, auditable, and supervisable."),
  ]),

  p([
    r("This paper presents "), b("BAg-IDS"),
    r(", a Blockchain-enabled Agentic AI architecture for intrusion "
    + "detection that unifies these currents into a single, measured "
    + "system. Its central claim is deliberately singular: "),
    b("a trustworthy IDS can be built as an agentic architecture whose "
    + "decisions are secured by a blockchain consensus"),
    r(". Everything else in the system, ensemble calibration, weighted "
    + "fusion, selective rejection, LLM deliberation, and governed human "
    + "oversight, is a mechanism in the service of that goal rather than a "
    + "standalone contribution. BAg-IDS is "
    + "organised as four cooperating layers with deliberately asymmetric cost. "
    + "A "), i("reflex"), r(" detection layer classifies every flow in "
    + "milliseconds through a calibrated ensemble of neural detectors fused "
    + "by a reliability-weighted strategy we refer to as "),
    b("Conscious Weighted Consensus"),
    r(" (a fusion of standard, well-understood components whose value here "
    + "is architectural, Section 4.2.4), and gates low-confidence decisions "
    + "with a reject option. A "),
    i("deliberative"), r(" layer invokes an LLM only on salient events, "
    + "namely a certified attack or a burst of rejections, to reason about "
    + "severity and remediation. A "), i("consensus"),
    r(" layer converts a single agent’s alert into a collectively certified, "
    + "tamper-evident record: independent notary agents re-validate the alert "
    + "and cast cryptographically signed votes to a permissioned-blockchain "
    + "smart contract that certifies the decision only on reaching a quorum. "
    + "Finally, an optional "), i("human-in-the-loop"),
    r(" supervision layer gives an operator a governed, auditable point of "
    + "control, and can be switched off to cede full autonomy to the agents, "
    + "with every administrative action itself signed and anchored on-chain."),
  ]),

  p([
    r("The design principle that makes an agentic, blockchain-backed IDS "
    + "operationally viable is the asymmetry between the layers: thousands of "
    + "flows per second traverse the reflex path, but only the small fraction "
    + "that yield a certified attack incur the cost of LLM deliberation and "
    + "on-chain consensus. Detection therefore remains real-time while trust "
    + "and oversight are applied precisely where they matter, on the decisions "
    + "that trigger action."),
  ]),

  p([b("Contributions. "), r("This paper makes four contributions:")]),

  li([b("A hybrid reflex/deliberative agentic architecture "),
    r("for intrusion detection that combines a real-time calibrated ensemble "
    + "with event-triggered LLM reasoning, so that autonomous contextual "
    + "judgement is applied without placing a language model on the per-flow "
    + "critical path.")]),
  li([b("A reliability-weighted fusion strategy integrated in the trust "
    + "architecture (Conscious Weighted Consensus), "),
    r("in which detectors are weighted by their calibrated, recent "
    + "reliability. The strategy is assembled from established components; "
    + "its contribution is the role it plays in the architecture. We show "
    + "that this same mechanism yields structural "
    + "robustness to detector corruption: evaluated under simulated output "
    + "corruption as a worst-case poisoning proxy, a fully corrupted detector "
    + "is auto-excluded without any explicit attack detection.")]),
  li([b("A blockchain consensus layer on the decision path, "),
    r("realised as a Hyperledger Fabric smart contract that certifies each "
    + "remediation-triggering verdict through multi-party signed voting with "
    + "quorum, anti-replay and tamper-evident audit. Distinctively, it also "
    + "anchors human governance actions, so that even the administrator is "
    + "auditable.")]),
  li([b("A complete, measured implementation and evaluation "),
    r("of the full stack on commodity hardware, including a "
    + "component-by-component ablation (individual detectors, uniform "
    + "ensemble, calibrated weighted fusion, fusion with rejection) that "
    + "quantifies the contribution of each mechanism, the rejection-threshold "
    + "trade-off, the real latency cost of the "
    + "blockchain and its scaling with the quorum, the reflex-path "
    + "throughput, and corruption robustness, with every number produced by "
    + "the running system rather than projected.")]),

  p([
    r("Our evaluation on CICIDS2017 shows that the calibrated ensemble reaches "
    + "96.6% accuracy over all decisions, significantly above its best "
    + "member, and 99.7% at 0.04% false-positive rate on the certified subset; "
    + "that the consensus cost of our sequential-submission implementation "
    + "grows linearly with the quorum and is dominated by ledger block "
    + "formation rather than cryptography; and that, under a simulated output "
    + "corruption that reduces the strongest detector to 0.6% accuracy, the "
    + "ensemble loses only 0.6 accuracy point while the corrupted "
    + "detector’s influence is automatically suppressed. Section 6.9 "
    + "positions these figures against the results reported by recent "
    + "blockchain-based, federated, and agentic IDS."),
  ]),

  p([b("Paper organisation. "),
    r("Section 2 reviews related work and positions our contribution. "
    + "Section 3 states the threat model and design goals. Section 4 presents "
    + "the four-layer architecture. Section 5 describes the implementation. "
    + "Section 6 reports the experimental evaluation. Section 7 analyses "
    + "security threat by threat. Section 8 discusses limitations and Section 9 "
    + "concludes."),
  ]),

  fig("paper_q1/figures/architecture_overview.png", 470),
  caption("Figure 1. Overview of the four-layer BAg-IDS architecture and the "
    + "path of a certified attack (detailed in Section 4)."),
];
