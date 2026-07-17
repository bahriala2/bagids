/* Section 9 — Conclusion. */
module.exports = ({ h1, h2, h3, p, r, b, i, eq, li, caption, table, fig }) => [

  h1("9. Conclusion"),

  p([
    r("We presented BAg-IDS, a blockchain-enabled agentic architecture that "
    + "treats intrusion detection, decentralised trust, and human oversight "
    + "as a single design rather than three separate concerns. Its four "
    + "layers are joined by a deliberate asymmetry of cost: a calibrated "
    + "neural ensemble detects every flow in milliseconds and fuses the "
    + "detectors through the reliability-weighted Conscious Weighted "
    + "Consensus fusion; an LLM deliberates only "
    + "on salient events; a permissioned-blockchain smart contract certifies "
    + "each remediation-triggering verdict through multi-party signed voting "
    + "with quorum, anti-replay and tamper-evident audit; and an optional, "
    + "governed human-in-the-loop layer places a supervising operator above "
    + "the autonomous machinery, recording even its own administrative "
    + "actions on-chain."),
  ]),

  p([
    r("The system is implemented in full and evaluated on commodity hardware, "
    + "so every reported figure is measured rather than projected. On "
    + "CICIDS2017 the calibrated ensemble reaches 96.6% accuracy over all "
    + "decisions and 99.7% on the certified subset at the selected operating "
    + "threshold. The blockchain’s cost is quantified and shown to grow "
    + "linearly with the quorum while being dominated by ledger block "
    + "formation rather than cryptography, which keeps it a tunable "
    + "infrastructure parameter rather than an intrinsic barrier. Most "
    + "importantly, the reliability-weighted fusion is shown to be a "
    + "structural defence against detector corruption: when a simulated "
    + "worst-case output corruption "
    + "reduces the strongest detector to 0.6% accuracy, the ensemble loses "
    + "only 0.6 accuracy point as the corrupted detector’s weight is "
    + "automatically suppressed, and the consensus and governance contracts "
    + "reject forged signatures on-chain."),
  ]),

  p([
    r("Taken together, these results support a practical claim: an intrusion "
    + "detection system can be simultaneously accurate, robust to a corrupted "
    + "component, decentralised in whom it trusts, tamper-evident in what it "
    + "records, and answerable to a human, without sacrificing real-time "
    + "detection. The limitations we stated, chiefly the class-balanced "
    + "evaluation testbed of the original protocol and the single-host ledger "
    + "deployment, bound the "
    + "absolute numbers but not the architectural conclusions, and they map "
    + "directly onto the future work we outlined: true training-set poisoning "
    + "with retraining, "
    + "a geographically distributed multi-organisation deployment, a "
    + "closed-loop drift-to-recalibration defence, and generalisation to "
    + "modern cloud and encrypted-traffic threat corpora."),
  ]),

  p([
    r("Beyond these direct extensions, the architecture generalises past "
    + "intrusion detection. The pattern it implements, autonomous agents "
    + "whose action-triggering decisions are co-signed by a quorum and "
    + "whose governance is itself on-chain, applies wherever an automated "
    + "security decision must be trusted by parties who do not fully trust "
    + "each other: certified malware triage verdicts, phishing takedown "
    + "decisions, cross-organisation cyber-threat-intelligence sharing in "
    + "which each indicator carries a quorum signature, or SOAR playbooks "
    + "whose every automated step is notarised. Two deployment horizons "
    + "seem particularly promising. In a Zero Trust environment, where no "
    + "verdict is accepted on the authority of a single component, the "
    + "certified alerts of BAg-IDS are exactly the continuously verified, "
    + "cryptographically attributable signals a policy engine expects, "
    + "making the consensus layer a natural trust anchor for "
    + "micro-segmentation and access decisions. And a validation campaign "
    + "in a production SOC, measuring how certified, deferred and "
    + "LLM-annotated alerts change analyst workload and time-to-respond, "
    + "would test the human side of the design at the scale it was built "
    + "for. We believe the "
    + "co-design of learning, decentralised trust, and governed human "
    + "oversight is a productive direction for trustworthy security "
    + "automation, and we offer BAg-IDS as a concrete, measured step along "
    + "it."),
  ]),
];
