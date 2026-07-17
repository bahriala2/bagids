/* Section 0 — Abstract and keywords (placé juste après le bloc titre).
 * Raccourci (~215 mots) et requalifié (corruption simulée, pas
 * label-flipping d'entraînement) suite à la revue interne. */
const { Paragraph, TextRun, AlignmentType } = require("docx");

module.exports = ({ h1, h2, h3, p, r, b, i, eq, li, caption, table, fig }) => [
  new Paragraph({
    spacing: { after: 80 },
    children: [new TextRun({ text: "Abstract", bold: true, size: 24 })],
  }),
  new Paragraph({
    alignment: AlignmentType.JUSTIFIED,
    spacing: { after: 160, line: 276 },
    children: [new TextRun({ size: 20, text:
      "Learning-based intrusion detection systems emit verdicts that "
    + "operators must simply trust: the record is mutable, the model can be "
    + "corrupted, and no one co-signs the decision. We present BAg-IDS, "
    + "whose central contribution is a trustworthy intrusion detection "
    + "system built on an agentic architecture secured by blockchain "
    + "consensus: autonomous agents detect, independently re-validate, and "
    + "co-sign every remediation-triggering verdict by quorum of "
    + "cryptographically signed notary votes on a Hyperledger Fabric smart "
    + "contract. The remaining mechanisms serve this goal, in four layers of "
    + "deliberately asymmetric cost. A reflex layer classifies flows through "
    + "a calibrated, reliability-weighted ensemble fusion with a "
    + "confidence-gated reject option. A deliberative layer invokes a large "
    + "language model only on salient events. Finally, a "
    + "governed human-in-the-loop layer makes every administrative action, "
    + "including the act of ceding autonomy, a signed on-chain transaction. "
    + "The system is fully implemented, every reported number is measured, "
    + "and a component-by-component ablation quantifies what each mechanism "
    + "contributes. "
    + "On CICIDS2017, under the exact preprocessing of the detectors' "
    + "published training pipeline, selective certification raises accuracy "
    + "from 96.6% to 99.7% (false-positive rate 0.04%) on the 87.3% of flows "
    + "it accepts, with a zero-false-positive option at 60.6% coverage, at "
    + "37,500 flows per second on commodity hardware. Consensus adds about "
    + "two seconds per signed vote, a cost dominated by block formation. "
    + "Under simulated corruption of the strongest detector's outputs, a "
    + "worst-case proxy for poisoning, the reliability-weighted fusion loses "
    + "only 0.6 accuracy point while down-weighting the corrupted member from "
    + "0.332 to 0.014.",
    })],
  }),
  new Paragraph({
    spacing: { after: 240 },
    children: [
      new TextRun({ text: "Keywords: ", bold: true, size: 20 }),
      new TextRun({ size: 20, text:
        "intrusion detection; blockchain; Hyperledger Fabric; agentic AI; "
      + "large language models; ensemble learning; model calibration; "
      + "selective classification; adversarial robustness; "
      + "human-in-the-loop." }),
    ],
  }),
];
