/* Chapitre 10 — General Conclusion. */
module.exports = ({ h1, h2, h3, p, r, b, i, eq, li, caption, table, fig }) => [

  h1("Chapter 10. General Conclusion"),

  p("This thesis set out to answer a single question: whether a "
  + "deep-learning intrusion detection system can be made trustworthy in a "
  + "precise technical sense — robust to a corrupted model, decentralised in "
  + "whom it trusts, tamper-evident in what it records, and answerable to a "
  + "human — without sacrificing real-time detection. The answer, developed "
  + "across the preceding chapters, is affirmative, and it takes the form of "
  + "a concrete, measured system: BAg-IDS."),

  p("BAg-IDS treats detection, decentralised trust and human oversight as a "
  + "single design rather than three separate concerns. Its four layers are "
  + "joined by a deliberate asymmetry of cost: a calibrated neural ensemble "
  + "detects every flow in milliseconds and fuses the detectors through "
  + "Conscious Weighted Consensus; an LLM deliberates only on salient events; "
  + "a permissioned-blockchain smart contract certifies each "
  + "remediation-triggering verdict through multi-party signed voting with "
  + "quorum, anti-replay and tamper-evident audit; and an optional, governed "
  + "human-in-the-loop layer places a supervising operator above the "
  + "autonomous machinery — recording even its own administrative actions "
  + "on-chain."),

  p("The system was implemented in full and evaluated on commodity hardware, "
  + "so every reported figure is measured rather than projected. Returning to "
  + "the research questions of Chapter 1: reliability-weighted fusion answers "
  + "RQ1, providing structural robustness to poisoning — a fully corrupted "
  + "detector costs the ensemble about one accuracy point as its weight is "
  + "automatically suppressed. The multi-notary chaincode answers RQ2, "
  + "certifying decisions through cryptographic quorum and rejecting forged "
  + "signatures on-chain. The event-triggered, gracefully degrading "
  + "deliberative layer answers RQ3, adding contextual reasoning off the "
  + "per-flow path. The governed, on-chain human-in-the-loop layer answers "
  + "RQ4, making even the administrator auditable. And the latency study "
  + "answers RQ5, showing the consensus cost to be linear in the quorum, "
  + "dominated by ledger block formation rather than cryptography, and "
  + "confined to the small fraction of certified events."),

  p("Taken together, these results support a practical claim: an intrusion "
  + "detection system can be simultaneously accurate, robust to a corrupted "
  + "component, decentralised in whom it trusts, tamper-evident in what it "
  + "records, and answerable to a human, without sacrificing real-time "
  + "detection. The limitations stated in Chapter 9 — chiefly the "
  + "reconstructed preprocessing pipeline and the single-host ledger "
  + "deployment — bound the absolute numbers but not the architectural "
  + "conclusions, and they map directly onto the future work outlined there: "
  + "sharper detector training, a distributed multi-organisation deployment, "
  + "a closed-loop drift-to-recalibration defence, and generalisation to "
  + "modern cloud and encrypted-traffic threats. The co-design of learning, "
  + "decentralised trust and governed human oversight is, we believe, a "
  + "productive direction for trustworthy security automation, and BAg-IDS is "
  + "offered as a concrete, measured step along it."),
];
