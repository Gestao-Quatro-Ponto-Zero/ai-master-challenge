import path from "node:path";
import PptxGenJS from "pptxgenjs";

import type { DeckChart, DeckSpec, DeckTable, Evidence, Slide } from "@/engine/deck";

const GOLD = "E3B341";
const OBSIDIAN = "0E0E10";
const PAPER = "FAF8F4";
const WHITE = "FFFFFF";
const NEUTRAL_200 = "E5E5E5";
const NEUTRAL_300 = "D4D4D4";
const NEUTRAL_400 = "A3A3A3";
const NEUTRAL_500 = "737373";
const NEUTRAL_600 = "525252";
const NEUTRAL_700 = "404040";
const NEUTRAL_900 = "171717";

const LEFT = 0.7;
const CONTENT_W = 11.9;

function texturePath(file: string): string {
  return path.join(process.cwd(), "public/deck-textures", file);
}

function addParagraphs(
  lines: string[],
  paraSpaceAfter: number,
): { text: string; options: { paraSpaceAfter: number; breakLine: true } }[] {
  return lines.map((line, index) => ({
    text: line,
    // breakLine puts each line on its own paragraph; paraSpaceAfter alone renders
    // them as inline runs (sentences run together — "Enterprise.$21.9M…").
    options: { paraSpaceAfter: index === lines.length - 1 ? 0 : paraSpaceAfter, breakLine: true },
  }));
}

/**
 * Honest number formatting for the export face — inferred from the plotted FIELD
 * names, matching ChartView.makeFormatter exactly: money fields get $, percent-ish
 * fields (incl. score — an NPS chart must NOT export with $ labels) and plain
 * counts stay unprefixed. Never assume "bar = currency".
 */
function chartFormatCode(chart: DeckChart): string {
  const fields = chart.series.map((s) => s.name);
  if (fields.some((f) => /usd|arr|mrr|revenue|amount|spend|cost|price|\$/i.test(f))) return "$#,##0";
  if (fields.some((f) => /pct|percent|rate|ratio|share|score/i.test(f))) return "#,##0.#";
  return "#,##0"; // plain counts — thousands-separated
}

function addDarkChartPanel(
  pptx: PptxGenJS,
  slide: ReturnType<PptxGenJS["addSlide"]>,
  chart: DeckChart,
  box: { x: number; y: number; w: number; h: number },
): void {
  slide.addShape(pptx.ShapeType.roundRect, {
    x: box.x,
    y: box.y,
    w: box.w,
    h: box.h,
    fill: { color: OBSIDIAN },
    line: { type: "none" },
    rectRadius: 0.08,
  });

  slide.addText(chart.title.toUpperCase(), {
    x: box.x + 0.24,
    y: box.y + 0.18,
    w: box.w - 0.48,
    h: 0.22,
    fontSize: 9,
    bold: true,
    color: NEUTRAL_400,
    fontFace: "Arial",
    charSpacing: 1.6,
    margin: 0,
  });

  const chartSeries = chart.series.map((series) => ({
    name: series.name,
    labels: chart.categories,
    values: series.values,
  }));

  const chartType = chart.kind === "bar" ? pptx.ChartType.bar : pptx.ChartType.line;
  slide.addChart(chartType, chartSeries, {
    x: box.x + 0.22,
    y: box.y + 0.5,
    w: box.w - 0.44,
    h: box.h - 0.72,
    ...(chart.kind === "bar" ? { barDir: "bar" as const } : { lineDataSymbol: "circle" as const }),
    chartColors: chart.series.map((series) => (series.color ?? GOLD).replace(/^#/, "")),
    showLegend: chart.series.length > 1,
    legendColor: NEUTRAL_300,
    showTitle: false,
    showValue: chart.kind === "bar",
    dataLabelColor: PAPER,
    dataLabelFontSize: 8,
    // Field-name-inferred formatting (see chartFormatCode) — currency only when the
    // plotted fields say money, never "bar chart therefore dollars".
    valAxisLabelFormatCode: chartFormatCode(chart),
    dataLabelFormatCode: chartFormatCode(chart),
    valGridLine: { color: "3A3A3A" },
    chartArea: { fill: { color: OBSIDIAN } },
    plotArea: { fill: { color: OBSIDIAN } },
    catAxisLabelColor: "C9C9C9",
    valAxisLabelColor: "C9C9C9",
    catAxisLineColor: "3A3A3A",
    valAxisLineColor: "3A3A3A",
  });
}

function columnWidths(table: DeckTable, totalWidth: number): number[] {
  const weights = table.columns.map((_, index) => (table.numericColumns.includes(index) ? 0.9 : 1.35));
  const weightTotal = weights.reduce((sum, weight) => sum + weight, 0);
  return weights.map((weight) => (totalWidth * weight) / weightTotal);
}

function addTableBlock(
  slide: ReturnType<PptxGenJS["addSlide"]>,
  table: DeckTable,
  box: { x: number; y: number; w: number },
): void {
  const rows = [
    table.columns.map((column, index) => ({
      text: column.toUpperCase(),
      options: {
        bold: true,
        color: NEUTRAL_500,
        fontSize: 9,
        align: table.numericColumns.includes(index) ? ("right" as const) : ("left" as const),
        fill: { color: PAPER },
      },
    })),
    ...table.rows.map((row) =>
      row.map((cell, index) =>
        table.numericColumns.includes(index)
          ? {
              // Money columns are already string-formatted by the deck (usd()); count/score/percent
              // columns must show their raw grounded value. Match SlideView, which renders String(cell).
              text: String(cell),
              options: { align: "right" as const, fontFace: "Courier New", color: NEUTRAL_900 },
            }
          : { text: String(cell), options: { color: NEUTRAL_700 } },
      ),
    ),
  ];

  slide.addTable(rows, {
    x: box.x,
    y: box.y,
    w: box.w,
    colW: columnWidths(table, box.w),
    border: { type: "solid", color: "E5E0D8", pt: 0.5 },
    autoPage: false,
    fontFace: "Arial",
    fontSize: 11,
    valign: "middle",
    margin: 0.08,
  });
}

function addCoverSlide(pptx: PptxGenJS, spec: DeckSpec, slideSpec: Slide): void {
  const slide = pptx.addSlide();
  slide.background = { path: texturePath("ore-cover.png") };

  slide.addText("RAVENSTACK", {
    x: LEFT,
    y: 1.45,
    w: 4.8,
    h: 0.24,
    fontSize: 13,
    bold: true,
    color: GOLD,
    fontFace: "Arial",
    charSpacing: 3,
    margin: 0,
  });

  // Title box reserves two lines (h:1.3 at 36pt) so a wrapping title — quarter
  // labels vary with the dataset — never collides with the subtitle below it.
  slide.addText(slideSpec.title, {
    x: LEFT,
    y: 1.8,
    w: 9.6,
    h: 1.3,
    fontSize: 36,
    bold: true,
    color: WHITE,
    fontFace: "Arial",
    valign: "top",
    margin: 0,
  });

  if (slideSpec.subtitle) {
    slide.addText(slideSpec.subtitle, {
      x: LEFT,
      y: 3.2,
      w: 8.4,
      h: 0.95,
      fontSize: 15,
      color: NEUTRAL_300,
      fontFace: "Arial",
      valign: "top",
      margin: 0,
    });
  }

  if (slideSpec.evidence) {
    slide.addText(slideSpec.evidence.value, {
      x: LEFT,
      y: 4.2,
      w: 2.5,
      h: 0.42,
      fontSize: 24,
      bold: true,
      color: GOLD,
      fontFace: "Courier New",
      margin: 0,
    });
    slide.addText(slideSpec.evidence.label, {
      x: LEFT + 2.1,
      y: 4.28,
      w: 4.4,
      h: 0.26,
      fontSize: 14,
      color: NEUTRAL_400,
      fontFace: "Arial",
      margin: 0,
    });
  }

  slide.addShape(pptx.ShapeType.rect, {
    x: LEFT,
    y: 4.95,
    w: 2.4,
    h: 0.02,
    fill: { color: GOLD, transparency: 65 },
    line: { type: "none" },
  });

  slide.addText(`Veta · grounded as of ${spec.asOf}`, {
    x: LEFT,
    y: 6.55,
    w: 4.8,
    h: 0.2,
    fontSize: 11.5,
    color: NEUTRAL_500,
    fontFace: "Courier New",
    margin: 0,
  });
}

function addDividerSlide(pptx: PptxGenJS, slideSpec: Slide): void {
  const slide = pptx.addSlide();
  slide.background = { path: texturePath("ore-divider.png") };

  let cursorY = 2.0;
  if (slideSpec.sectionNumber) {
    slide.addText(slideSpec.sectionNumber, {
      x: LEFT,
      y: cursorY,
      w: 2.4,
      h: 0.74,
      fontSize: 54,
      bold: true,
      color: GOLD,
      fontFace: "Courier New",
      margin: 0,
    });
    cursorY += 0.92;
  }

  slide.addText(slideSpec.title, {
    x: LEFT,
    y: cursorY,
    w: 8.4,
    h: 0.6,
    fontSize: 33,
    bold: true,
    color: WHITE,
    fontFace: "Arial",
    margin: 0,
  });

  if (slideSpec.subtitle) {
    slide.addText(slideSpec.subtitle, {
      x: LEFT,
      y: cursorY + 0.72,
      w: 6.8,
      h: 0.34,
      fontSize: 15,
      color: NEUTRAL_400,
      fontFace: "Arial",
      margin: 0,
    });
  }
}

function addContextSlide(pptx: PptxGenJS, slideSpec: Slide): void {
  const slide = pptx.addSlide();
  slide.background = { color: PAPER };

  slide.addText(slideSpec.title, {
    x: LEFT,
    y: 0.62,
    w: CONTENT_W,
    h: 0.45,
    fontSize: 27,
    bold: true,
    color: NEUTRAL_900,
    fontFace: "Arial",
    margin: 0,
  });

  if (slideSpec.body?.length) {
    slide.addText(addParagraphs(slideSpec.body, 10), {
      x: LEFT,
      y: 1.48,
      w: 5.1,
      h: 4.95,
      fontSize: 14,
      color: NEUTRAL_700,
      fontFace: "Arial",
      valign: "middle",
      margin: 0,
    });
  }

  if (slideSpec.chart) {
    addDarkChartPanel(pptx, slide, slideSpec.chart, { x: 6.42, y: 1.42, w: 5.48, h: 4.98 });
  }
}

function addHeroCard(
  pptx: PptxGenJS,
  slide: ReturnType<PptxGenJS["addSlide"]>,
  evidence: Evidence,
  box: { x: number; y: number; w: number; h: number },
): void {
  slide.addShape(pptx.ShapeType.roundRect, {
    x: box.x,
    y: box.y,
    w: box.w,
    h: box.h,
    fill: { color: OBSIDIAN },
    line: { type: "none" },
    rectRadius: 0.08,
  });

  slide.addText(evidence.value, {
    x: box.x + 0.28,
    y: box.y + 0.22,
    w: box.w - 0.56,
    h: 0.42,
    fontSize: 30,
    bold: true,
    color: GOLD,
    fontFace: "Courier New",
    margin: 0,
  });

  slide.addText(`${evidence.label} · ${evidence.rowCount} rows`, {
    x: box.x + 0.28,
    y: box.y + 0.75,
    w: box.w - 0.56,
    h: 0.2,
    fontSize: 11.5,
    color: NEUTRAL_400,
    fontFace: "Arial",
    margin: 0,
  });
}

function addArgumentSlide(pptx: PptxGenJS, slideSpec: Slide): void {
  const slide = pptx.addSlide();
  slide.background = { color: PAPER };

  slide.addText(slideSpec.title, {
    x: LEFT,
    y: 0.62,
    w: CONTENT_W,
    h: 0.4,
    fontSize: 24,
    bold: true,
    color: NEUTRAL_900,
    fontFace: "Arial",
    margin: 0,
  });

  const hasVisual = Boolean(slideSpec.chart) || Boolean(slideSpec.table);
  if (slideSpec.body?.length) {
    // A prose-only (narrative-pin) slide gets the full text column; slides with a
    // chart/table keep the split layout.
    slide.addText(addParagraphs(slideSpec.body, 8), {
      x: LEFT,
      y: 1.42,
      w: hasVisual ? 4.45 : 9.2,
      h: slideSpec.evidence ? 2.85 : 4.95,
      fontSize: hasVisual ? 13 : 15,
      color: NEUTRAL_600,
      fontFace: "Arial",
      margin: 0,
    });
  }

  if (slideSpec.evidence) {
    addHeroCard(pptx, slide, slideSpec.evidence, { x: LEFT, y: 5.2, w: 4.1, h: 1.25 });
  }

  const visualX = 5.35;
  const visualW = 6.55;
  const hasChart = Boolean(slideSpec.chart);
  const hasTable = Boolean(slideSpec.table);

  if (hasChart && slideSpec.chart && hasTable && slideSpec.table) {
    addDarkChartPanel(pptx, slide, slideSpec.chart, { x: visualX, y: 1.38, w: visualW, h: 2.5 });
    addTableBlock(slide, slideSpec.table, { x: visualX, y: 4.18, w: visualW });
    return;
  }

  if (hasChart && slideSpec.chart) {
    addDarkChartPanel(pptx, slide, slideSpec.chart, { x: visualX, y: 1.38, w: visualW, h: 5.08 });
  }

  if (hasTable && slideSpec.table) {
    addTableBlock(slide, slideSpec.table, { x: visualX, y: 1.48, w: visualW });
  }
}

function addRecommendationSlide(pptx: PptxGenJS, slideSpec: Slide): void {
  const slide = pptx.addSlide();
  slide.background = { path: texturePath("ore-closing.png") };

  slide.addText(slideSpec.title, {
    x: LEFT,
    y: 1.52,
    w: 8.8,
    h: 0.52,
    fontSize: 32,
    bold: true,
    color: WHITE,
    fontFace: "Arial",
    margin: 0,
  });

  if (slideSpec.body?.length) {
    slide.addText(
      slideSpec.body.map((item) => ({
        text: item,
        options: { bullet: { code: "25AA" }, color: NEUTRAL_200, breakLine: true, paraSpaceAfter: 10 },
      })),
      {
        x: LEFT,
        y: 2.42,
        w: 8.4,
        h: 2.8,
        fontSize: 16,
        color: NEUTRAL_200,
        fontFace: "Arial",
        margin: 0,
      },
    );
  }

  slide.addShape(pptx.ShapeType.rect, {
    x: LEFT,
    y: 5.72,
    w: 2.4,
    h: 0.02,
    fill: { color: GOLD },
    line: { type: "none" },
  });

  slide.addText("Veta · fundamentado no banco da RavenStack", {
    x: LEFT,
    y: 6.1,
    w: 4.8,
    h: 0.22,
    fontSize: 12.5,
    color: GOLD,
    fontFace: "Arial",
    margin: 0,
  });
}

export async function deckToPptx(spec: DeckSpec): Promise<Buffer> {
  const pptx = new PptxGenJS();
  pptx.layout = "LAYOUT_WIDE";
  pptx.author = "Veta";
  pptx.company = "Veta";
  pptx.subject = spec.subtitle;
  pptx.title = spec.title;

  for (const slide of spec.slides) {
    switch (slide.layout) {
      case "cover":
        addCoverSlide(pptx, spec, slide);
        break;
      case "divider":
        addDividerSlide(pptx, slide);
        break;
      case "context":
        addContextSlide(pptx, slide);
        break;
      case "argument":
        addArgumentSlide(pptx, slide);
        break;
      case "recommendation":
        addRecommendationSlide(pptx, slide);
        break;
      default:
        throw new Error(`unknown slide layout: ${(slide as Slide).layout}`);
    }
  }

  const buffer = await pptx.write({ outputType: "nodebuffer" });
  return buffer as Buffer;
}
