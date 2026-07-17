# Cover Letter — BAg-IDS (Computers & Security)

Dear Editors-in-Chief,

We are pleased to submit our manuscript entitled **"BAg-IDS: A
Blockchain-Enabled Agentic AI Architecture for Trustworthy Intrusion
Detection"** for consideration in *Computers & Security*.

Learning-based intrusion detection systems produce verdicts that operators
must simply trust: the record is mutable, the model can be corrupted, and no
one co-signs the decision. Our manuscript addresses this trust gap with a
single architectural claim: trustworthy intrusion detection can be obtained
by co-designing detection, decentralised trust, and human oversight. BAg-IDS
realises this claim in four layers of deliberately asymmetric cost: a
real-time calibrated ensemble with selective rejection, an LLM-based
deliberative layer invoked only on salient events, a consensus layer in which
independent notary agents certify every remediation-triggering verdict by
quorum of cryptographically signed votes on a Hyperledger Fabric smart
contract, and a governed human-in-the-loop layer whose every administrative
action, including the act of ceding autonomy, is itself signed and anchored
on-chain.

We believe the manuscript is a strong fit for *Computers & Security* for
three reasons:

1. **The system is fully implemented and every reported number is measured**,
   from detection quality (99.65% accuracy at 0.04% false-positive rate on
   the certified subset of CICIDS2017) to the real latency cost of on-chain
   consensus (~2 s per signed vote) and the reflex-path throughput (37,500
   flows/s on commodity hardware).
2. **The evaluation includes a complete ablation** (individual detectors,
   uniform ensemble, majority vote, weighted fusion with and without
   calibration, rejection gate) and a measured robustness study in which the
   reliability-weighted fusion automatically suppresses a fully corrupted
   detector, losing only 0.6 accuracy point.
3. **The limitations are stated candidly**, including the cost of on-decision
   trust, the dependence on the evaluation corpus, and the scope of the
   empirical security analysis, and a quantitative positioning against
   recently reported blockchain, federated and agentic IDS results is
   provided.

This manuscript is original, has not been published previously, and is not
under consideration by any other journal. All authors have approved the
submission. The three neural detectors originate from our previously
published comparative study (IEEE AMCAI 2023,
doi:10.1109/AMCAI59331.2023.10431511), which is cited in the manuscript; all
other material is new. The source code and reproduction scripts are held in a
private repository and will be made publicly available upon acceptance.

We have no conflicts of interest to declare.

Thank you for your consideration.

Sincerely,

Mohamed Ala Eddine Bahri (corresponding author)
On behalf of all authors: Farah Jemili, Ouajdi Korbaa
[Affiliation — à confirmer]
