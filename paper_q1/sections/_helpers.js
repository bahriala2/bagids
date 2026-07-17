/* Fabriques de paragraphes réutilisées par les modules de section. */
const fs = require("fs");
const path = require("path");
const {
  Paragraph, TextRun, HeadingLevel, AlignmentType, Table, TableRow,
  TableCell, WidthType, BorderStyle, ShadingType, ImageRun,
} = require("docx");

const PROJECT_ROOT = path.resolve(__dirname, "..", "..");

// Titre de section niveau 1/2/3
const h1 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_1,
  children: [new TextRun(t)] });
const h2 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_2,
  children: [new TextRun(t)] });
const h3 = (t) => new Paragraph({ heading: HeadingLevel.HEADING_3,
  children: [new TextRun(t)] });

// Paragraphe de corps justifié. Accepte une chaîne ou un tableau de runs.
const p = (content) => new Paragraph({
  alignment: AlignmentType.JUSTIFIED,
  spacing: { after: 120, line: 276 },
  children: typeof content === "string" ? [new TextRun(content)] : content,
});

// Runs de commodité
const r = (t) => new TextRun(t);
const b = (t) => new TextRun({ text: t, bold: true });
const i = (t) => new TextRun({ text: t, italics: true });

// Équation centrée avec numéro à droite
const eq = (expr, num) => new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { before: 80, after: 120 },
  tabStops: [{ type: "right", position: 9360 }],
  children: [new TextRun({ text: expr, italics: true }),
             new TextRun({ text: `\t(${num})` })],
});

// Élément de liste à puces justifié
const li = (content) => new Paragraph({
  numbering: { reference: "bullets", level: 0 },
  alignment: AlignmentType.JUSTIFIED,
  spacing: { after: 80, line: 276 },
  children: typeof content === "string" ? [new TextRun(content)] : content,
});

// Légende de figure/table
const caption = (t) => new Paragraph({
  alignment: AlignmentType.CENTER,
  spacing: { before: 60, after: 160 },
  children: [new TextRun({ text: t, italics: true, size: 20 })],
});

// Tableau : entête + lignes. colWidths en DXA (somme = largeur table).
// opts.boldRow (index 0-based du corps) / opts.boldLastRows (n dernières).
const _border = { style: BorderStyle.SINGLE, size: 1, color: "AAB4C4" };
const _borders = { top: _border, bottom: _border, left: _border, right: _border };
const cell = (text, w, { header = false, bold = false, align } = {}) =>
  new TableCell({
    borders: _borders,
    width: { size: w, type: WidthType.DXA },
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    shading: header ? { fill: "1F3864", type: ShadingType.CLEAR }
                    : { fill: "FFFFFF", type: ShadingType.CLEAR },
    children: [new Paragraph({
      alignment: align || (header ? AlignmentType.CENTER : AlignmentType.LEFT),
      children: [new TextRun({
        text, bold: header || bold, size: 18,
        color: header ? "FFFFFF" : "16223A" })],
    })],
  });

const table = (headers, rows, colWidths, opts = {}) => {
  const total = colWidths.reduce((a, b) => a + b, 0);
  const nBody = rows.length;
  const boldSet = new Set();
  if (typeof opts.boldRow === "number") boldSet.add(opts.boldRow);
  if (opts.boldLastRows) {
    for (let k = 0; k < opts.boldLastRows; k++) boldSet.add(nBody - 1 - k);
  }
  const headerRow = new TableRow({
    tableHeader: true,
    children: headers.map((h, c) => cell(h, colWidths[c], { header: true })),
  });
  const bodyRows = rows.map((row, ri) => new TableRow({
    children: row.map((val, c) => cell(String(val), colWidths[c], {
      bold: boldSet.has(ri),
      align: c === 0 ? AlignmentType.LEFT : AlignmentType.CENTER,
    })),
  }));
  return new Table({
    width: { size: total, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: [headerRow, ...bodyRows],
  });
};

// Figure : insère un PNG (chemin relatif à la racine du projet), centré.
const fig = (relPath, widthPx = 460) => {
  const abs = path.join(PROJECT_ROOT, relPath);
  if (!fs.existsSync(abs)) {
    return new Paragraph({ alignment: AlignmentType.CENTER,
      children: [new TextRun({ text: `[figure manquante : ${relPath}]`,
        italics: true, color: "C00000" })] });
  }
  // Ratio approximatif : on borne la hauteur à partir d'une largeur cible.
  const height = Math.round(widthPx * 0.72);
  return new Paragraph({
    alignment: AlignmentType.CENTER, spacing: { before: 80, after: 40 },
    children: [new ImageRun({
      type: "png", data: fs.readFileSync(abs),
      transformation: { width: widthPx, height },
      altText: { title: relPath, description: relPath, name: relPath },
    })],
  });
};

module.exports = { h1, h2, h3, p, r, b, i, eq, li, caption, table, fig };
