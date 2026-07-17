/* Section 7 — Security Analysis. */
module.exports = ({ h1, h2, h3, p, r, b, i, eq, li, caption, table, fig }) => [

  h1("7. Security Analysis"),

  p([
    r("This section revisits the adversary of Section 3 and argues, threat by "
    + "threat, which architectural property neutralises it, grounding each "
    + "claim in the mechanisms of Section 4 and, where available, the "
    + "measurements of Section 6. The analysis assumes the threat model stated "
    + "earlier: an adversary may poison a detector, may compromise a single "
    + "agent (a Sentinel, one notary, or the console), and may attempt to "
    + "forge, replay or tamper with decision records, but cannot break the "
    + "underlying cryptographic primitives nor simultaneously control a quorum "
    + "of independent notaries. Table 12 summarises the mapping; the "
    + "subsections develop each entry."),
  ]),

  table(
    ["Threat", "Neutralising property", "Evidence"],
    [
      ["Detector corruption (simulated poisoning proxy)",
       "Precision-weighted fusion auto-excludes the corrupted model",
       "Sec. 6.7, Table 10"],
      ["Compromised Sentinel (forged alerts)",
       "Consistency re-validation + vote authenticity (partial; see §7.2)",
       "Sec. 7.2"],
      ["Malicious/forged vote",
       "On-chain Ed25519 signature check against the signer registry",
       "Sec. 7.2, measured"],
      ["Vote replay / double vote",
       "One-vote-per-notary invariant in the chaincode",
       "Sec. 4.2.6"],
      ["Single rogue notary",
       "Quorum requirement (k of n) before any remediation",
       "Sec. 7.3"],
      ["Record tampering",
       "Replicated, hash-linked ledger endorsed by two organisations",
       "Sec. 7.4"],
      ["Console/admin subversion",
       "Governance actions signed and anchored on-chain (auditable admin)",
       "Sec. 7.5, measured"],
    ],
    [2760, 4200, 1800],
    {}),
  caption("Table 12. Threats and the BAg-IDS properties that neutralise them."),

  // ---------------------------------------------------------------- 7.1
  h2("7.1. Resilience to detector corruption"),

  p([
    r("The most insidious attack against a learning-based IDS is one that "
    + "corrupts the model itself. Section 6.7 measured BAg-IDS under "
    + "simulated output corruption, a worst-case proxy for poisoning, that "
    + "fully inverts the strongest detector: as "
    + "a standalone classifier the corrupted RNN drops to 0.6% accuracy, yet "
    + "the ensemble retains 96.0% of its clean 96.6% accuracy. The "
    + "defence is structural rather than reactive. Because the fusion weight "
    + "of each detector is proportional to its recent validation precision "
    + "(Eq. 2), a detector whose reliability collapses sees its weight decay "
    + "automatically, from 0.332 to 0.014 in the measured worst case, so its "
    + "vote is discounted "), b("without the system ever having to detect that "
    + "an attack is underway"),
    r(". This is a valuable property: it degrades gracefully against an "
    + "adversary the system cannot see, and it requires no poisoning detector "
    + "that could itself be evaded."),
  ]),

  p([
    r("The analysis is honest about the attack’s residual leverage. The "
    + "ensemble’s worst degradation is a shallow dip at partial corruption "
    + "(p ≈ 0.3, −1.9 accuracy points), where the corrupted detector keeps "
    + "enough precision to retain a meaningful weight; and the guarantee is "
    + "a majority-trust one: it holds "
    + "while a majority of the ensemble remains honest, exactly as the "
    + "consensus layer assumes a majority of honest notaries. Simultaneous "
    + "poisoning of two of the three detectors is outside the threat model, "
    + "and the complementary drift monitor (Section 7.6) is the intended "
    + "second line of defence against slow, partial corruption."),
  ]),

  // ---------------------------------------------------------------- 7.2
  h2("7.2. Authenticity of votes and alerts"),

  p([
    r("A compromised Sentinel could fabricate alerts, and a compromised host "
    + "could attempt to inject votes on behalf of a notary. BAg-IDS blocks "
    + "both at the consensus boundary. Every notary independently re-validates "
    + "an alert before endorsing it (checking that an attack verdict truly "
    + "exceeds τ and that the claimed class is the arg-max of the pooled "
    + "posteriors), so a Sentinel cannot manufacture consensus merely by "
    + "asserting a verdict. And every vote is an Ed25519 signature over the "
    + "canonical vote payload, verified "), b("inside the chaincode"),
    r(" against the public key registered for that notary. We verified this "
    + "empirically: submitting a vote whose signature does not match the "
    + "registered key is rejected at endorsement time by the peers of both "
    + "organisations, with the contract returning an explicit "),
    i("invalid signature"),
    r(" error. Because verification runs in the smart contract and not in any "
    + "single agent, subverting one host does not let an attacker forge an "
    + "endorsement."),
  ]),

  p([
    b("Scope of the re-validation: an honest boundary. "),
    r("The notaries’ re-validation is a "), i("consistency"),
    r(" check: it recomputes threshold and arg-max over the posteriors "
    + "carried in the alert, but it does not independently re-classify "
    + "the underlying flow. A fully compromised Sentinel can therefore "
    + "fabricate an internally consistent alert (posteriors included) "
    + "that all notaries will endorse. What the consensus layer "
    + "guarantees against this adversary is accountability, not "
    + "prevention: the forged alert is signed by the Sentinel’s "
    + "registered identity, immutably recorded, rate-visible to the "
    + "supervision layer, and attributable in post-incident review: a "
    + "compromised Sentinel cannot lie "), i("quietly"),
    r(" or deniably. Prevention would require notaries to re-run "
    + "detection on the raw flow themselves, which is architecturally "
    + "straightforward (each notary can hold the model bundle) but "
    + "multiplies inference cost and consensus payloads; we scope it as "
    + "future work and, accordingly, temper the corresponding row of "
    + "Table 12."),
  ]),

  // ---------------------------------------------------------------- 7.3
  h2("7.3. Anti-replay and the quorum barrier"),

  p([
    r("Two further invariants defend the vote-counting itself. First, the "
    + "chaincode records at most one vote per notary per alert, so a captured "
    + "vote cannot be replayed to inflate an approval count. Second, and "
    + "centrally, no alert is certified, and therefore no remediation is "
    + "authorised, until a quorum of k valid, distinct approvals is reached. "
    + "A single rogue notary can neither certify an alert alone nor block one "
    + "that its peers approve; it is reduced to one vote among n. The quorum k "
    + "is a tunable security/latency dial: Section 6.6 showed the consensus "
    + "cost growing linearly with k, so an operator trades a higher collusion "
    + "threshold against a few seconds of additional latency. In the evaluated "
    + "configuration (k = 2 of n = 3), certification requires the cooperation "
    + "of a majority of the notaries, which the threat model assumes an "
    + "adversary cannot achieve."),
  ]),

  // ---------------------------------------------------------------- 7.4
  h2("7.4. Integrity and non-repudiation of the record"),

  p([
    r("Once certified, a decision must be impossible to alter or disown. The "
    + "simulated ledger already provides tamper-evidence through hash-linking "
    + "(our unit tests confirm that altering any past entry breaks the chain) "
    + "and the Fabric deployment strengthens this to tamper-resistance: the "
    + "ledger is replicated across the peers of two independent organisations, "
    + "and each transaction is endorsed and ordered before commitment, so "
    + "rewriting history would require colluding across organisational "
    + "boundaries. Every alert, every signed vote and every certification is "
    + "therefore a non-repudiable record: the signatures bind each decision to "
    + "the specific notaries that endorsed it, giving the audit trail "
    + "evidentiary value that a single-host log cannot offer."),
  ]),

  // ---------------------------------------------------------------- 7.5
  h2("7.5. Auditability of human authority"),

  p([
    r("Adding a human supervision layer creates a new target: an attacker who "
    + "subverts the console could lower the rejection threshold, shrink the "
    + "quorum, or simply switch off oversight, quietly weakening the whole "
    + "system. BAg-IDS answers this by refusing to treat administrative power "
    + "as implicit. Every governance action (toggling supervision, changing a "
    + "governed parameter, and every manual approval) is serialised, signed "
    + "by the governance identity, and anchored on the same blockchain through "
    + "a dedicated contract call whose signature is verified before "
    + "commitment. We confirmed on-chain that a governance record with an "
    + "invalid signature is rejected, and that valid records are readable back "
    + "from the ledger in order. The contract deliberately separates the "),
    b("human actor"), r(" (the operator account, stored as metadata) from the "),
    b("cryptographic signer"),
    r(" (the registered governance identity), binding the human chain of "
    + "responsibility to an unforgeable record. The consequence is a system in "
    + "which the administrator is auditable: the ledger holds not only what "
    + "the agents decided, but every human intervention that shaped their "
    + "behaviour, including the decision to remove human oversight itself."),
  ]),

  // ---------------------------------------------------------------- 7.6
  h2("7.6. Defence in depth"),

  p([
    r("The properties above are layered rather than independent, and their "
    + "value lies in composition. A poisoning attack that the weighting "
    + "absorbs also raises the rejection rate, which the Data Scientist agent "
    + "surfaces as drift and can escalate to recalibration, a second line "
    + "behind the first. An adversary who compromises a Sentinel still faces "
    + "independent notary validation; one who compromises a notary still faces "
    + "the quorum; one who reaches the ledger still faces cross-organisation "
    + "replication; and one who reaches the console still faces on-chain, "
    + "signed governance. No single compromise collapses the system, and the "
    + "human-in-the-loop layer provides an out-of-band control surface that "
    + "can tighten the posture (raising τ or the quorum, or re-enabling "
    + "supervision) precisely when the autonomous layers report anomalies. "
    + "The residual assumptions are explicit and conventional: soundness of "
    + "the cryptographic primitives, an honest majority of notaries, and a "
    + "correct initial registration of identities."),
  ]),
];
