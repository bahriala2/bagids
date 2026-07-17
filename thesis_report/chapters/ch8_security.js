/* Chapitre 8 — Security Analysis. */
module.exports = ({ h1, h2, h3, p, r, b, i, eq, li, caption, table, fig }) => [

  h1("Chapter 8. Security Analysis"),

  p("This chapter revisits the adversary of Chapter 4 and argues, threat by "
  + "threat, which architectural property neutralises it — grounding each "
  + "claim in the mechanisms of Chapter 5 and the measurements of Chapter 7. "
  + "The analysis assumes the threat model stated earlier, in particular the "
  + "honest-majority assumptions on the detector ensemble and the notary "
  + "quorum. Table 8.1 summarises the mapping; the sections develop each "
  + "entry."),

  table(
    ["Threat", "Neutralising property", "Evidence"],
    [
      ["Detector poisoning (label-flipping)",
       "Precision-weighted fusion auto-excludes the corrupted model",
       "Sec. 7.5"],
      ["Compromised Sentinel (forged alerts)",
       "Independent notary re-validation before certification", "Sec. 5.5.1"],
      ["Malicious/forged vote",
       "On-chain Ed25519 signature check against the signer registry",
       "Sec. 8.2, measured"],
      ["Vote replay / double vote",
       "One-vote-per-notary invariant in the chaincode", "Sec. 5.5.2"],
      ["Single rogue notary", "Quorum requirement (k of n)", "Sec. 8.3"],
      ["Record tampering",
       "Replicated, hash-linked ledger endorsed by two organisations",
       "Sec. 8.4"],
      ["Console/admin subversion",
       "Governance actions signed and anchored on-chain", "Sec. 8.5, measured"],
    ],
    [2760, 4200, 1800],
    {}),
  caption("Table 8.1. Threats and the BAg-IDS properties that neutralise "
    + "them."),

  h2("8.1. Resilience to detector poisoning"),
  p("Section 7.5 measured BAg-IDS under a label-flipping adversary that fully "
  + "inverts the strongest detector: as a standalone classifier the poisoned "
  + "RNN drops to 1.9% accuracy, yet the ensemble retains 87.2%. The defence "
  + "is structural rather than reactive. Because the fusion weight of each "
  + "detector is proportional to its recent validation precision, a detector "
  + "whose reliability collapses sees its weight decay automatically — from "
  + "0.334 to 0.058 in the measured worst case — so its vote is discounted "
  + "without the system ever having to detect that an attack is underway. The "
  + "guarantee is a majority-trust one: it holds while a majority of the "
  + "ensemble remains honest, and the worst leverage is at partial poisoning "
  + "(p ≈ 0.5), which the drift monitor of Section 5.4 is intended to catch."),

  h2("8.2. Authenticity of votes and alerts"),
  p([
    r("A compromised Sentinel could fabricate alerts, and a compromised host "
    + "could attempt to inject votes on behalf of a notary. BAg-IDS blocks "
    + "both at the consensus boundary. Every notary independently re-validates "
    + "an alert before endorsing it, so a Sentinel cannot manufacture "
    + "consensus merely by asserting a verdict. And every vote is an Ed25519 "
    + "signature over the canonical payload, verified inside the chaincode "
    + "against the registered public key. We verified this empirically: "
    + "submitting a vote whose signature does not match the registered key is "
    + "rejected at endorsement time by the peers of both organisations, with "
    + "the contract returning an explicit "), i("invalid signature"),
    r(" error. Because verification runs in the smart contract and not in any "
    + "single agent, subverting one host does not let an attacker forge an "
    + "endorsement — satisfying goal G3."),
  ]),

  h2("8.3. Anti-replay and the quorum barrier"),
  p("Two further invariants defend the vote-counting itself. First, the "
  + "chaincode records at most one vote per notary per alert, so a captured "
  + "vote cannot be replayed to inflate an approval count. Second, no alert "
  + "is certified — and no remediation authorised — until a quorum of k "
  + "valid, distinct approvals is reached. A single rogue notary can neither "
  + "certify an alert alone nor block one its peers approve; it is reduced to "
  + "one vote among n. The quorum is a tunable security/latency dial: "
  + "Section 7.4 showed the consensus cost growing linearly with k, so an "
  + "operator trades a higher collusion threshold against a few seconds of "
  + "latency. This satisfies goal G2."),

  h2("8.4. Integrity and non-repudiation of the record"),
  p("Once certified, a decision must be impossible to alter or disown. The "
  + "simulated ledger provides tamper-evidence through hash-linking — the "
  + "property tests confirm that altering any past entry breaks the chain — "
  + "and the Fabric deployment strengthens this to tamper-resistance: the "
  + "ledger is replicated across the peers of two independent organisations, "
  + "and each transaction is endorsed and ordered before commitment, so "
  + "rewriting history would require colluding across organisational "
  + "boundaries. Every alert, signed vote and certification is therefore a "
  + "non-repudiable record whose signatures bind each decision to the "
  + "specific notaries that endorsed it — satisfying goal G4 and giving the "
  + "audit trail evidentiary value a single-host log cannot offer."),

  h2("8.5. Auditability of human authority"),
  p([
    r("Adding a human supervision layer creates a new target: an attacker who "
    + "subverts the console could lower the rejection threshold, shrink the "
    + "quorum, or disable oversight, quietly weakening the system. BAg-IDS "
    + "answers this by refusing to treat administrative power as implicit. "
    + "Every governance action is serialised, signed by the governance "
    + "identity, and anchored on the same blockchain through a dedicated "
    + "contract call whose signature is verified before commitment. We "
    + "confirmed on-chain that a governance record with an invalid signature "
    + "is rejected and that valid records are readable back from the ledger in "
    + "order. The contract separates the human actor from the cryptographic "
    + "signer, binding the human chain of responsibility to an unforgeable "
    + "record. The administrator is thus auditable — the ledger holds every "
    + "human intervention that shaped the agents’ behaviour, including the "
    + "decision to remove oversight itself. This satisfies goal G5."),
  ]),

  h2("8.6. Defence in depth"),
  p("The properties above are layered rather than independent, and their "
  + "value lies in composition. A poisoning attack that the weighting absorbs "
  + "also raises the rejection rate, which the Data Scientist surfaces as "
  + "drift and can escalate to recalibration. An adversary who compromises a "
  + "Sentinel still faces independent notary validation; one who compromises "
  + "a notary still faces the quorum; one who reaches the ledger still faces "
  + "cross-organisation replication; and one who reaches the console still "
  + "faces on-chain, signed governance. No single compromise collapses the "
  + "system, and the human-in-the-loop layer provides an out-of-band control "
  + "surface that can tighten the posture precisely when the autonomous "
  + "layers report anomalies. The residual assumptions are explicit and "
  + "conventional: soundness of the cryptographic primitives, an honest "
  + "majority of notaries, and a correct initial registration of identities."),
];
