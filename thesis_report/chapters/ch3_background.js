/* Chapitre 3 — Technical Background. */
module.exports = ({ h1, h2, h3, p, r, b, i, eq, li, caption, table, fig }) => [

  h1("Chapter 3. Technical Background"),

  p("This chapter provides the technical background needed to follow the "
  + "design of BAg-IDS. It is deliberately self-contained: a reader familiar "
  + "with one area may skip the corresponding section. Section 3.1 recalls the "
  + "neural architectures used as detectors and the flow-feature "
  + "representation of network traffic. Section 3.2 covers confidence "
  + "calibration and the reject option. Section 3.3 introduces probabilistic "
  + "opinion pooling, the basis of the fusion rule. Section 3.4 presents "
  + "permissioned blockchains and Hyperledger Fabric. Section 3.5 introduces "
  + "digital signatures and the Ed25519 scheme. Section 3.6 outlines large "
  + "language models and the agent abstraction."),

  // ---------------------------------------------------------------- 3.1
  h2("3.1. Neural detectors and flow features"),

  p([
    r("Network traffic is represented, throughout this thesis, as a set of "),
    b("bidirectional flows"),
    r(". A flow aggregates the packets exchanged between two endpoints over a "
    + "connection and is summarised by a fixed-length vector of statistical "
    + "features — durations, packet and byte counts, inter-arrival-time "
    + "statistics, flag counts and so on — computed by a flow meter. The "
    + "CICIDS datasets provide on the order of eighty such features per flow; "
    + "after cleaning, the detectors in this work consume a 78-feature "
    + "vector. Each flow carries a label identifying benign traffic or one of "
    + "several attack families."),
  ]),

  p([
    r("Three complementary neural architectures are used as base detectors. A "),
    b("deep neural network (DNN)"),
    r(", a stack of fully connected layers with non-linear activations, "
    + "learns a direct mapping from the feature vector to a class "
    + "distribution. A "), b("convolutional neural network (CNN)"),
    r(" applies one-dimensional convolutions over the feature vector to "
    + "capture local combinations of features. A "),
    b("recurrent neural network (RNN)"),
    r(", here a simple recurrent network, processes the features as a short "
    + "sequence and maintains a hidden state that summarises context. Each "
    + "network ends in a softmax layer producing a posterior distribution "),
    i("P(c | x, M)"), r(" over the classes for input flow "), i("x"),
    r(" under model "), i("M"),
    r(". The three architectures are chosen for their complementary inductive "
    + "biases: they tend to fail on different inputs, which is what makes "
    + "their combination worthwhile."),
  ]),

  // ---------------------------------------------------------------- 3.2
  h2("3.2. Confidence calibration and the reject option"),

  p([
    r("A classifier is "), b("calibrated"),
    r(" when its stated confidence matches its empirical accuracy: among all "
    + "predictions made with confidence 0.8, about 80% should be correct. "
    + "Deep networks are frequently over-confident, which is problematic when "
    + "a downstream mechanism thresholds confidence. The standard measure of "
    + "miscalibration is the "), b("Expected Calibration Error (ECE)"),
    r(", which partitions predictions into confidence bins and averages, over "
    + "bins, the absolute gap between mean confidence and accuracy:"),
  ]),

  eq("ECE = Σ_b (|B_b| / N) · | acc(B_b) − conf(B_b) |"),

  p([
    r("where "), i("B_b"), r(" is the set of predictions in bin "), i("b"),
    r(", and acc and conf are the accuracy and mean confidence within the "
    + "bin. "), b("Temperature scaling"),
    r(" reduces the ECE by dividing the pre-softmax logits by a single "
    + "positive scalar "), i("T"),
    r(" learnt on a validation set by minimising the negative log-likelihood. "
    + "Because a single scalar cannot change which class has the largest "
    + "logit, temperature scaling improves calibration without altering "
    + "accuracy. Given calibrated posteriors, a "), b("reject option"),
    r(" abstains whenever the maximum posterior falls below a threshold "),
    i("τ"), r(", trading coverage (the fraction of inputs on which the system "
    + "commits) for higher reliability on the accepted inputs."),
  ]),

  // ---------------------------------------------------------------- 3.3
  h2("3.3. Opinion pooling and weighted fusion"),

  p([
    r("Combining several probabilistic classifiers is an instance of "),
    b("opinion pooling"), r(". The "), i("linear opinion pool"),
    r(" forms the fused posterior as a convex combination of the individual "
    + "posteriors:"),
  ]),

  eq("P̃(c | x) = Σ_m w_m · P(c | x, M_m),   with   Σ_m w_m = 1,  w_m ≥ 0."),

  p([
    r("The weights "), i("w_m"),
    r(" express how much each model is trusted. In many ensembles they are "
    + "uniform or tuned once for accuracy. The scheme used in this thesis, "
    + "detailed in Chapter 5, sets each weight proportional to the model’s "
    + "recent, calibrated "), b("precision"),
    r(" on a validation stream, so that a model whose reliability degrades — "
    + "for any reason, including poisoning — sees its weight, and hence its "
    + "influence on the fused decision, decay automatically. The final "
    + "decision is the arg-max of the pooled posterior, and its confidence is "
    + "the corresponding maximum, to which the reject threshold of "
    + "Section 3.2 is applied."),
  ]),

  // ---------------------------------------------------------------- 3.4
  h2("3.4. Permissioned blockchain and Hyperledger Fabric"),

  p([
    r("A "), b("blockchain"), r(" is an append-only ledger replicated across "
    + "a set of nodes, in which records are grouped into blocks and each "
    + "block is cryptographically linked to its predecessor by a hash, so "
    + "that altering any past record invalidates every subsequent block. This "
    + "hash-linking provides "), b("tamper-evidence"),
    r(": modification is detectable by anyone holding the chain. In a "),
    b("permissioned"), r(" blockchain, participation is restricted to "
    + "identified members admitted by a membership authority, in contrast to "
    + "the open, pseudonymous participation of public blockchains. "
    + "Permissioned ledgers suit enterprise security settings because they "
    + "combine tamper-evidence and decentralised trust with known identities "
    + "and without the energy cost of proof-of-work."),
  ]),

  p([
    r("Hyperledger Fabric is the permissioned platform used in this thesis. "
    + "Its distinctive "), b("execute–order–validate"),
    r(" architecture separates three phases. In the "), i("execute"),
    r(" phase, a transaction proposal is sent to endorsing peers, which run "
    + "the smart contract (the "), b("chaincode"),
    r(") and return signed endorsements without yet committing any state. In "
    + "the "), i("order"), r(" phase, an ordering service sequences endorsed "
    + "transactions into blocks. In the "), i("validate"),
    r(" phase, every peer checks that each transaction carries endorsements "
    + "satisfying the required policy and applies it to the ledger. "
    + "Identities are issued as X.509 certificates by each organisation’s "
    + "Membership Service Provider. Two properties of this model are central "
    + "to BAg-IDS: an endorsement policy can require signatures from multiple "
    + "independent organisations before a transaction commits, and the "
    + "chaincode can enforce arbitrary application logic — including "
    + "signature verification and quorum counting — as a precondition of "
    + "commitment."),
  ]),

  // ---------------------------------------------------------------- 3.5
  h2("3.5. Digital signatures and Ed25519"),

  p([
    r("A "), b("digital signature"),
    r(" scheme lets a signer, holding a private key, produce a signature over "
    + "a message that anyone holding the corresponding public key can verify, "
    + "and that no one lacking the private key can forge. Signatures provide "),
    b("authenticity"), r(" (the message came from the holder of the key), "),
    b("integrity"), r(" (it was not altered) and "), b("non-repudiation"),
    r(" (the signer cannot later disown it). BAg-IDS uses "),
    b("Ed25519"), r(", an elliptic-curve signature scheme over the twisted "
    + "Edwards curve Curve25519, chosen for its short keys and signatures, "
    + "fast verification and resistance to common implementation pitfalls. "
    + "Each agent holds an Ed25519 key pair; votes and governance actions are "
    + "signed over a canonical serialisation of their payload, and the "
    + "verification is performed inside the chaincode against a registry of "
    + "authorised public keys, so that authenticity is enforced by the "
    + "decentralised ledger rather than by any single host."),
  ]),

  // ---------------------------------------------------------------- 3.6
  h2("3.6. Large language models and the agent abstraction"),

  p([
    r("A "), b("large language model (LLM)"),
    r(" is a neural network, typically a transformer, trained on large text "
    + "corpora to predict tokens and, through instruction tuning, to follow "
    + "natural-language instructions. Beyond text generation, an LLM can be "
    + "prompted to reason about a structured situation and to emit a "
    + "structured response — for instance a JSON object with a severity "
    + "rating and a list of recommended actions — which is how the "
    + "deliberative layer of BAg-IDS uses it. Because LLM inference is "
    + "comparatively slow and, for hosted models, subject to rate limits and "
    + "availability, an LLM is unsuitable for per-flow decisions and is best "
    + "reserved for infrequent, high-level judgements."),
  ]),

  p([
    r("An "), b("agent"),
    r(", in the sense used throughout this thesis, is an autonomous software "
    + "entity that perceives its environment, maintains internal state, and "
    + "acts to pursue an objective without being externally driven. This "
    + "classical notion predates LLMs; what LLMs add is a capacity for "
    + "flexible, contextual "), i("deliberation"),
    r(". A long-standing design pattern in agent architectures separates a "
    + "fast, reactive "), i("reflex"), r(" component from a slower, "
    + "deliberative one. BAg-IDS adopts this hybrid explicitly: its agents "
    + "act autonomously on a reflex path in the millisecond range, and invoke "
    + "LLM deliberation only on salient events, so that contextual reasoning "
    + "is available without compromising real-time operation. The four agents "
    + "— Sentinel, Notary, Executor and Data Scientist — and the messages "
    + "that flow between them are the subject of Chapter 5."),
  ]),
];
