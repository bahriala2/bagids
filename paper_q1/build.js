/*
 * BAg-IDS — Manuscrit Computers & Security (Elsevier).
 * Script de construction incrémental : chaque section validée est ajoutée
 * dans son propre module (sections/*.js) et assemblée ici.
 *
 *   node build.js
 * -> BAg-IDS_ComputersSecurity.docx
 */
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  LevelFormat, Footer, PageNumber, TableOfContents,
} = require("docx");

// --- styles communs (réutilisés par les modules de section) -------------
const helpers = require("./sections/_helpers.js");

// Ordre de rédaction : cœur technique d'abord. Les modules absents sont
// ignorés (permet de construire au fur et à mesure de la validation).
const SECTION_FILES = [
  "s0_abstract.js",
  "s1_introduction.js",
  "s2_relatedwork.js",
  "s3_threatmodel.js",
  "s4_architecture.js",
  "s5_implementation.js",
  "s6_evaluation.js",
  "s7_security.js",
  "s8_discussion.js",
  "s9_conclusion.js",
  "s10_references.js",
  // "s3_threatmodel.js",
  // "s5_implementation.js",
  // "s8_discussion.js",
  // "s2_relatedwork.js",
  // "s1_introduction.js",
  // "s9_conclusion.js",
  // "s0_abstract.js",
];

function loadSections() {
  const out = [];
  for (const f of SECTION_FILES) {
    const p = path.join(__dirname, "sections", f);
    if (fs.existsSync(p)) out.push(...require(p)(helpers));
  }
  return out;
}

const titleBlock = [
  new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { after: 120 },
    children: [new TextRun({
      text: "BAg-IDS: A Blockchain-Enabled Agentic AI Architecture for "
          + "Trustworthy Intrusion Detection with Conscious Weighted Consensus",
      bold: true, size: 36, font: "Arial",
    })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { after: 60 },
    children: [new TextRun({
      text: "Ala Bahri, Farah Jemili, Ouajdi Korbaa", size: 24, font: "Arial" })],
  }),
  new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { after: 240 },
    children: [new TextRun({
      text: "Manuscript prepared for submission to Computers & Security "
          + "(Elsevier)", italics: true, size: 20, font: "Arial" })],
  }),
];

const doc = new Document({
  creator: "Ala Bahri",
  title: "BAg-IDS",
  styles: {
    default: { document: { run: { font: "Arial", size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal",
        quickFormat: true,
        run: { size: 30, bold: true, font: "Arial", color: "1F3864" },
        paragraph: { spacing: { before: 280, after: 160 }, outlineLevel: 0 } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal",
        quickFormat: true,
        run: { size: 26, bold: true, font: "Arial", color: "2E5496" },
        paragraph: { spacing: { before: 200, after: 120 }, outlineLevel: 1 } },
      { id: "Heading3", name: "Heading 3", basedOn: "Normal", next: "Normal",
        quickFormat: true,
        run: { size: 23, bold: true, italics: true, font: "Arial" },
        paragraph: { spacing: { before: 160, after: 100 }, outlineLevel: 2 } },
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
        margin: { top: 1440, right: 1440, bottom: 1440, left: 1440 },
      },
    },
    footers: {
      default: new Footer({ children: [new Paragraph({
        alignment: AlignmentType.CENTER,
        children: [new TextRun("Page "),
                   new TextRun({ children: [PageNumber.CURRENT] }),
                   new TextRun(" — BAg-IDS (Computers & Security)")] })] }),
    },
    children: [...titleBlock, ...loadSections()],
  }],
});

Packer.toBuffer(doc).then((buf) => {
  const out = path.join(__dirname, "BAg-IDS_ComputersSecurity.docx");
  fs.writeFileSync(out, buf);
  console.log("Écrit :", out);
});
