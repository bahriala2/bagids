/* Chapitre 4 — Threat Model and Design Goals. */
module.exports = ({ h1, h2, h3, p, r, b, i, eq, li, caption, table, fig }) => [

  h1("Chapter 4. Threat Model and Design Goals"),

  p("An architecture that claims to make intrusion detection trustworthy must "
  + "state precisely against whom it is trustworthy, and under what "
  + "assumptions. This chapter makes the adversary explicit. Section 4.1 "
  + "records the system and trust assumptions. Section 4.2 enumerates the "
  + "adversary’s capabilities, organised by the front attacked. Section 4.3 "
  + "delimits what is out of scope. Section 4.4 derives the design goals that "
  + "the architecture must meet and that Chapters 7 and 8 evaluate."),

  // ---------------------------------------------------------------- 4.1
  h2("4.1. System model and trust assumptions"),

  p([
    r("The system comprises four cooperating agents — Sentinel, Notary, "
    + "Executor and Data Scientist — a set of trained neural detectors, a "
    + "permissioned ledger operated by two or more organisations, and an "
    + "optional human-in-the-loop console. We assume a "),
    b("permissioned setting"),
    r(": participating organisations are known and admitted through a "
    + "membership authority, and each agent holds a long-lived Ed25519 key "
    + "pair whose public half is registered before operation begins. We take "
    + "the standard cryptographic assumptions as given — signatures are "
    + "unforgeable and hash functions are collision-resistant — and we assume "
    + "the initial registration of identities is carried out correctly by an "
    + "honest administrator."),
  ]),

  p([
    r("The consensus layer inherits the fault model of the underlying ledger. "
    + "In the evaluated configuration, a decision is certified only with the "
    + "agreement of a "), b("quorum"),
    r(" of independent notaries — a majority in the deployed setting. The "
    + "central trust assumption is therefore an "),
    b("honest-majority"), r(" assumption: the adversary is unable to control "
    + "a quorum of notaries simultaneously, just as, for the detection layer, "
    + "it is unable to corrupt a majority of the ensemble simultaneously. "
    + "These two majority assumptions are the backbone of the security "
    + "argument in Chapter 8."),
  ]),

  // ---------------------------------------------------------------- 4.2
  h2("4.2. Adversary capabilities"),

  p("Within these assumptions we grant the adversary a deliberately broad "
  + "repertoire, organised by the front it attacks. The four fronts "
  + "correspond to the four ways in which the current practice of "
  + "deep-learning intrusion detection is fragile, as set out in Chapter 1."),

  h3("4.2.1. Model-level: poisoning"),
  p("The adversary can tamper with the training or update data of one "
  + "detector — for example by flipping the labels of a fraction of samples "
  + "— so that the deployed model misclassifies, typically making attacks "
  + "pass as benign (evasion). Corruption of a single detector is in scope; "
  + "simultaneous corruption of a majority of the ensemble is not."),

  h3("4.2.2. Agent-level: compromise"),
  p("The adversary can take over a single agent host: a Sentinel that then "
  + "emits fabricated or manipulated alerts; one notary that votes "
  + "dishonestly or refuses to vote; or the supervision console, from which "
  + "it may attempt to weaken the system’s posture. Compromise is limited to "
  + "one agent of each kind at a time."),

  h3("4.2.3. Record-level: forgery, replay and tampering"),
  p("The adversary can observe inter-agent messages and attempt to inject a "
  + "vote on behalf of a notary, replay a previously valid vote to inflate an "
  + "approval count, or alter a decision already written to the ledger, in "
  + "order to manufacture or erase a certification."),

  h3("4.2.4. Governance-level: authority abuse"),
  p("Having reached the human-in-the-loop console, the adversary can attempt "
  + "to lower the rejection threshold, reduce the quorum, or disable human "
  + "oversight altogether, so as to quietly degrade the guarantees the "
  + "operator believes are in force."),

  // ---------------------------------------------------------------- 4.3
  h2("4.3. Out of scope"),

  p("We exclude threats that are orthogonal to the contribution or that no "
  + "detection architecture of this kind can address alone. Denial-of-service "
  + "against the network or the ledger infrastructure, side-channel and "
  + "host-level exploits of the operating system, compromise of the "
  + "membership authority or of the initial key registration, and adversarial "
  + "evasion crafted directly against the feature extractor are not treated "
  + "here. We likewise assume the LLM of the deliberative layer is not an "
  + "attack vector for detection decisions, since it never observes raw "
  + "traffic and its output only annotates already-certified alerts with a "
  + "severity and a recommended action; the certification itself does not "
  + "depend on it."),

  // ---------------------------------------------------------------- 4.4
  h2("4.4. Design goals"),

  p("From the threat model we derive the properties the architecture must "
  + "provide. They serve as the criteria against which Chapters 7 and 8 "
  + "evaluate the system, and each is traced to the layer that realises it "
  + "and the point at which it is assessed."),

  li([b("G1 — Poisoning resilience. "), r("The detection decision must degrade "
    + "gracefully when a single detector is corrupted, without relying on an "
    + "explicit poisoning detector. (Conscious Weighted Consensus, "
    + "Section 5.3; measured in Section 7.5.)")]),
  li([b("G2 — No single point of trust. "), r("No individual agent may "
    + "unilaterally cause a remediation; certification must require agreement "
    + "among independent parties. (Multi-notary quorum, Section 5.5.)")]),
  li([b("G3 — Authenticity and non-repudiation. "), r("Every alert, vote and "
    + "certification must be attributable to a registered identity and "
    + "impossible to forge or disown. (Signed votes verified on-chain, "
    + "Sections 5.5 and 8.2.)")]),
  li([b("G4 — Tamper-evident auditability. "), r("The decision record must be "
    + "immutable and independently verifiable after the fact. (Hash-linked, "
    + "replicated ledger, Sections 5.5 and 8.4.)")]),
  li([b("G5 — Governed, auditable oversight. "), r("Human control must be "
    + "possible and optional, and any exercise of administrative authority "
    + "must itself be recorded immutably. (Human-in-the-loop layer, "
    + "Section 5.6; verified in Section 8.5.)")]),
  li([b("G6 — Operational viability. "), r("The trust machinery must not "
    + "compromise real-time detection; its cost must fall only on the small "
    + "fraction of certified events. (Reflex/deliberative asymmetry, "
    + "Section 5.1; measured in Section 7.4.)")]),

  p("The next chapter presents the four-layer architecture that realises "
  + "these goals, after which Chapter 6 describes its implementation, "
  + "Chapter 7 measures the extent to which the goals are met, and Chapter 8 "
  + "argues, threat by threat, why each adversarial capability of Section 4.2 "
  + "is neutralised."),
];
