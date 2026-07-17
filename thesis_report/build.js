/*
 * BAg-IDS — Rapport de thèse (PhD). Assemblage incrémental des chapitres.
 *   node build.js   ->  BAg-IDS_Thesis.docx
 */
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  LevelFormat, Footer, Header, PageNumber, TableOfContents, PageBreak,
} = require("docx");

const helpers = require("./chapters/_helpers.js");

// Ordre des chapitres. Les modules absents sont ignorés (build progressif).
const CHAPTER_FILES = [
  "ch1_introduction.js",
  "ch2_stateoftheart.js",
  "ch3_background.js",
  "ch4_threatmodel.js",
  "ch5_architecture.js",
  "ch6_implementation.js",
  "ch7_evaluation.js",
  "ch8_security.js",
  "ch9_discussion.js",
  "ch10_conclusion.js",
  "ch11_references.js",
];

function loadChapters() {
  const out = [];
  for (const f of CHAPTER_FILES) {
    const p = path.join(__dirname, "chapters", f);
    if (fs.existsSync(p)) {
      out.push(new Paragraph({ children: [new PageBreak()] }));
      out.push(...require(p)(helpers));
    }
  }
  return out;
}

const center = (text, opts = {}) => new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { after: opts.after ?? 120 },
  children: [new TextRun({ text, bold: opts.bold, italics: opts.italics,
    size: opts.size ?? 24, font: "Arial", color: opts.color ?? "000000" })],
});

// ---------------------------------------------------------------- title page
const titlePage = [
  center("Université — Faculté des Sciences", { size: 24, after: 40 }),
  center("Doctorat en Informatique / Cybersécurité", { size: 22, italics: true,
    after: 600 }),
  center("BAg-IDS", { bold: true, size: 52, color: "1F3864", after: 80 }),
  center("A Blockchain-Enabled Agentic AI Architecture for Trustworthy "
    + "Intrusion Detection with Conscious Weighted Consensus and Governed "
    + "Human Oversight", { bold: true, size: 28, after: 700 }),
  center("Thèse de doctorat", { italics: true, size: 24, after: 60 }),
  center("présentée et soutenue publiquement par", { size: 22, after: 60 }),
  center("Ala Bahri", { bold: true, size: 30, after: 500 }),
  center("Sous la direction de", { size: 22, after: 40 }),
  center("Pr. Farah Jemili   ·   Pr. Ouajdi Korbaa", { size: 24, after: 800 }),
  center("Année universitaire 2025–2026", { size: 22 }),
  new Paragraph({ children: [new PageBreak()] }),
];

// ---------------------------------------------------------------- abstracts
const abstracts = [
  helpers.h1("Abstract"),
  helpers.p(
    "Deep-learning intrusion detection systems are accurate but "
  + "operationally fragile: a single model on a single host emits verdicts "
  + "that a security operations centre must trust, the record of those "
  + "verdicts is mutable, and the learned detector can be silently corrupted "
  + "by data poisoning. This thesis presents BAg-IDS, a blockchain-enabled "
  + "agentic architecture that co-designs detection, decentralised trust and "
  + "human oversight in four cooperating layers with deliberately asymmetric "
  + "cost. A reflex layer classifies every flow in milliseconds through a "
  + "calibrated neural ensemble fused by a reliability-weighted rule, "
  + "Conscious Weighted Consensus, with a confidence-gated reject option. A "
  + "deliberative layer invokes a large language model only on salient events. "
  + "A consensus layer certifies each remediation-triggering verdict through "
  + "multi-party, cryptographically signed voting on a Hyperledger Fabric "
  + "smart contract. An optional, governed human-in-the-loop layer lets an "
  + "operator supervise or cede autonomy, with every administrative action "
  + "signed and anchored on-chain. The system is implemented in full and "
  + "evaluated on commodity hardware; every reported number is measured. On "
  + "CICIDS2017 the calibrated ensemble reaches 88.2% accuracy overall and "
  + "97.1% on the certified subset; the consensus cost grows linearly with "
  + "the quorum; and under a label-flipping adversary that reduces the "
  + "strongest detector to 1.9% accuracy the ensemble loses only about one "
  + "accuracy point."),
  helpers.p([
    helpers.b("Keywords: "),
    helpers.r("intrusion detection; blockchain; Hyperledger Fabric; agentic "
    + "AI; large language models; ensemble learning; calibration; adversarial "
    + "robustness; data poisoning; human-in-the-loop."),
  ]),
  helpers.h1("Résumé"),
  helpers.p(
    "Les systèmes de détection d'intrusion fondés sur l'apprentissage profond "
  + "sont précis mais fragiles en exploitation : un modèle unique sur une "
  + "machine unique émet des verdicts que le centre opérationnel de sécurité "
  + "doit croire, la trace de ces verdicts est modifiable, et le détecteur "
  + "appris peut être silencieusement corrompu par empoisonnement des "
  + "données. Cette thèse présente BAg-IDS, une architecture agentique "
  + "adossée à une blockchain qui conçoit conjointement la détection, la "
  + "confiance décentralisée et la supervision humaine en quatre couches "
  + "coopérantes au coût volontairement asymétrique. Une couche réflexe "
  + "classe chaque flux en millisecondes via un ensemble neuronal calibré "
  + "fusionné par une règle pondérée par la fiabilité (Conscious Weighted "
  + "Consensus), avec une région de rejet. Une couche délibérative sollicite "
  + "un grand modèle de langage uniquement sur les événements saillants. Une "
  + "couche de consensus certifie chaque verdict déclenchant une remédiation "
  + "par un vote multipartite signé sur un contrat intelligent Hyperledger "
  + "Fabric. Une couche de supervision humaine, optionnelle et gouvernée, "
  + "permet à un opérateur de superviser ou de céder l'autonomie, chaque "
  + "action d'administration étant signée et ancrée sur la chaîne. Le système "
  + "est entièrement implémenté et évalué sur matériel courant ; chaque "
  + "chiffre rapporté est mesuré."),
  helpers.p([
    helpers.b("Mots-clés : "),
    helpers.r("détection d'intrusion ; blockchain ; Hyperledger Fabric ; IA "
    + "agentique ; grands modèles de langage ; apprentissage d'ensemble ; "
    + "calibration ; robustesse adversariale ; empoisonnement ; supervision "
    + "humaine."),
  ]),
  new Paragraph({ children: [new PageBreak()] }),
];

// ---------------------------------------------------------------- TOC + lists
const frontLists = [
  helpers.h1("Table of Contents"),
  new TableOfContents("Table of Contents", {
    hyperlink: true, headingStyleRange: "1-3" }),
  new Paragraph({ children: [new PageBreak()] }),
  helpers.h1("List of Abbreviations"),
  ...[
    ["IDS", "Intrusion Detection System"],
    ["SOC", "Security Operations Centre"],
    ["RNN / CNN / DNN", "Recurrent / Convolutional / Deep Neural Network"],
    ["ECE", "Expected Calibration Error"],
    ["LLM", "Large Language Model"],
    ["CWC", "Conscious Weighted Consensus"],
    ["FPR", "False-Positive Rate"],
    ["HITL", "Human-in-the-Loop"],
    ["MSP", "Membership Service Provider (Hyperledger Fabric)"],
    ["RBAC", "Role-Based Access Control"],
  ].map(([a, d]) => helpers.p([helpers.b(a + "  —  "), helpers.r(d)])),
  new Paragraph({ children: [new PageBreak()] }),
];

const doc = new Document({
  creator: "Ala Bahri",
  title: "BAg-IDS — PhD Thesis",
  features: { updateFields: true },   // demande à Word de recalculer la TOC
  styles: {
    default: { document: { run: { font: "Arial", size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal",
        quickFormat: true,
        run: { size: 32, bold: true, font: "Arial", color: "1F3864" },
        paragraph: { spacing: { before: 320, after: 180 }, outlineLevel: 0,
          keepNext: true } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal",
        quickFormat: true,
        run: { size: 27, bold: true, font: "Arial", color: "2E5496" },
        paragraph: { spacing: { before: 220, after: 120 }, outlineLevel: 1,
          keepNext: true } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal",
        quickFormat: true,
        run: { size: 23, bold: true, italics: true, font: "Arial" },
        paragraph: { spacing: { before: 160, after: 100 }, outlineLevel: 2,
          keepNext: true } },
    ],
  },
  numbering: {
    config: [
      { reference: "bullets", levels: [{ level: 0, format: LevelFormat.BULLET,
        text: "•", alignment: AlignmentType.LEFT,
        style: { paragraph: { indent: { left: 720, hanging: 360 } } } }] },
    ],
  },
  sections: [{
    properties: {
      page: {
        size: { width: 12240, height: 15840 },
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1620 },
      },
    },
    footers: {
      default: new Footer({ children: [new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [new TextRun({ children: [PageNumber.CURRENT], size: 18 })] })] }),
    },
    headers: {
      default: new Header({ children: [new Paragraph({
        alignment: AlignmentType.RIGHT,
        children: [new TextRun({ text: "BAg-IDS — PhD Thesis", size: 16,
          color: "8090A8" })] })] }),
    },
    children: [
      ...titlePage,
      ...abstracts,
      ...frontLists,
      ...loadChapters(),
    ],
  }],
});

Packer.toBuffer(doc).then((buf) => {
  const out = path.join(__dirname, "BAg-IDS_Thesis.docx");
  fs.writeFileSync(out, buf);
  console.log("Écrit :", out);
});
