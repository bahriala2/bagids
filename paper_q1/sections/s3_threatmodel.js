/* Section 3 — Threat Model and Design Goals. */
module.exports = ({ h1, h2, h3, p, r, b, i, eq, li, caption, table, fig }) => [

  h1("3. Threat Model and Design Goals"),

  p([
    r("Before presenting the architecture we make explicit the adversary it is "
    + "designed to withstand and the properties it aims to guarantee. A "
    + "learning-based intrusion detector operating inside a security operations "
    + "workflow is exposed on three fronts at once: its models can be "
    + "corrupted, the software agents that run it can be subverted, and the "
    + "record of what it decided can be forged or repudiated. BAg-IDS is "
    + "designed against an adversary that operates on all three, under "
    + "assumptions we state below."),
  ]),

  // ---------------------------------------------------------------- 3.1
  h2("3.1. System and trust assumptions"),

  p([
    r("The system consists of five cooperating agents (Sentinel, Notary, "
    + "Executor, Data Scientist, Investigator), a set of trained detectors, and a "
    + "permissioned ledger operated by two or more organisations. We assume a "),
    b("permissioned"), r(" setting: participating organisations are known and "
    + "admitted through a membership authority, and each agent holds a "
    + "long-lived key pair whose public half is registered before operation. "
    + "We take the standard cryptographic assumptions (that signatures cannot "
    + "be forged and hash functions are collision-resistant) as given, and we "
    + "assume the initial registration of identities is performed correctly by "
    + "an honest administrator. The consensus layer inherits the fault model "
    + "of the underlying ledger; in the evaluated configuration a decision is "
    + "certified only with the agreement of a "), b("majority of independent "
    + "notaries"), r(", so the adversary is assumed unable to control that "
    + "majority simultaneously."),
  ]),

  // ---------------------------------------------------------------- 3.2
  h2("3.2. Adversary capabilities"),

  p([
    r("Within these assumptions, we grant the adversary a deliberately broad "
    + "repertoire, organised by the front it attacks:"),
  ]),

  li([b("Model-level (poisoning). "), r("The adversary can tamper with the "
    + "training or update data of one detector, for example by flipping a "
    + "fraction of its labels, so that the deployed model misclassifies, "
    + "typically making attacks pass as benign (evasion). Corruption of a "
    + "single detector is in scope; simultaneous corruption of a majority of "
    + "the ensemble is not.")]),
  li([b("Agent-level (compromise). "), r("The adversary can take over a single "
    + "agent host: a Sentinel that then emits fabricated or manipulated "
    + "alerts, one notary that votes dishonestly, or the supervision console "
    + "from which it may attempt to weaken the system’s posture. Compromise is "
    + "limited to one agent of each kind at a time.")]),
  li([b("Record-level (forgery, replay, tampering). "), r("The adversary can "
    + "observe messages and attempt to inject a vote on behalf of a notary, "
    + "replay a previously valid vote, or alter a decision already written to "
    + "the ledger, in order to manufacture or erase a certification.")]),
  li([b("Governance-level (authority abuse). "), r("Having reached the console, "
    + "the adversary can attempt to lower the rejection threshold, reduce the "
    + "quorum, or disable human oversight, so as to quietly degrade the "
    + "guarantees the operator believes are in force.")]),

  // ---------------------------------------------------------------- 3.3
  h2("3.3. Out of scope"),

  p([
    r("We exclude threats that are orthogonal to the contribution or that no "
    + "detection architecture of this kind can address alone. Denial-of-"
    + "service against the network or the ledger infrastructure, side-channel "
    + "and host-level exploits of the operating system, compromise of the "
    + "membership authority or of the initial key registration, and "
    + "adversarial evasion crafted against the feature extractor itself are "
    + "not treated here. We likewise assume the LLM used by the deliberative "
    + "layer is not an attack vector for detection decisions, since it never "
    + "sees raw traffic and its output only annotates already-certified "
    + "alerts with a severity and a recommended action."),
  ]),

  // ---------------------------------------------------------------- 3.4
  h2("3.4. Design goals"),

  p([
    r("From this threat model we derive the properties the architecture must "
    + "provide. They double as the criteria against which Sections 6 and 7 "
    + "evaluate the system:"),
  ]),

  li([b("G1. Poisoning resilience. "), r("The detection decision must degrade "
    + "gracefully when a single detector is corrupted, without relying on an "
    + "explicit poisoning detector. (Addressed by the Conscious Weighted "
    + "Consensus, Section 4.2.4; measured in Section 6.7.)")]),
  li([b("G2. No single point of trust. "), r("No individual agent may "
    + "unilaterally cause a remediation; certification must require agreement "
    + "among independent parties. (Multi-notary quorum, Section 4.2.6.)")]),
  li([b("G3. Authenticity and non-repudiation. "), r("Every alert, vote and "
    + "certification must be attributable to a registered identity and "
    + "impossible to forge or disown. (Signed votes verified on-chain, "
    + "Section 4.2.6.)")]),
  li([b("G4. Tamper-evident auditability. "), r("The decision record must be "
    + "immutable and independently verifiable after the fact. (Hash-linked, "
    + "replicated ledger, Section 4.2.6.)")]),
  li([b("G5. Governed, auditable oversight. "), r("Human control must be "
    + "possible and optional, and any exercise of administrative authority "
    + "must itself be recorded immutably. (Human-in-the-loop layer, "
    + "Section 4.2.7; verified in Section 7.5.)")]),
  li([b("G6. Operational viability. "), r("The trust machinery must not "
    + "compromise real-time detection; its cost must fall only on the small "
    + "fraction of certified events. (Reflex/deliberative asymmetry, "
    + "Section 4.1.1; measured in Section 6.6.)")]),

  p([
    r("The remainder of the paper is organised around these goals: Section 4 "
    + "presents the architecture that realises them, Section 6 measures the "
    + "extent to which they are met, and Section 7 argues, threat by threat, "
    + "why each adversarial capability of Section 3.2 is neutralised."),
  ]),
];
