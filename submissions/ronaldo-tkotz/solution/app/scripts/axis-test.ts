/**
 * axis-test — the contract of the shared x-axis label layout (charts/axis.ts).
 *
 * The charts render into a fixed 640-unit viewBox, so "no overlap" reduces to a
 * scale-invariant property: a shown label's width in viewBox units must fit its slot.
 * We assert exactly that, plus the behaviours the layout promises:
 *   • wide bands → show every category (step 1) at a comfortable font,
 *   • crowded bands → thin labels out rather than overlap, font floored (still readable),
 *   • a density cap (time-series) limits visible ticks without shrinking needlessly,
 *   • truncation keeps each shown label inside its slot,
 *   • edges are always shown.
 */
import { showLabelAt, xAxisLabels } from "../src/app/components/charts/axis";

const CHAR_W = 0.58; // must mirror axis.ts — the width model the fit guarantees
let checks = 0;
const ok = (cond: boolean, msg: string) => {
  if (!cond) {
    console.error(`✗ ${msg}`);
    process.exit(1);
  }
  checks++;
  console.log(`✓ ${msg}`);
};

/** Worst-case rendered width (viewBox units) of the longest fitted label among shown indices. */
function widestShown(labels: string[], slotPerCategory: number, opts?: { maxVisible?: number }): number {
  const layout = xAxisLabels(labels.length, slotPerCategory, opts);
  let widest = 0;
  labels.forEach((label, i) => {
    if (!showLabelAt(i, labels.length, layout.step)) return;
    widest = Math.max(widest, layout.fit(label).length * layout.fontSize * CHAR_W);
  });
  return widest;
}

// — Image #3 reproduction: ~12 industry names in a chat-width column chart.
const industries = [
  "Building Products", "Marine Engineering", "Aerospace & Defense", "Construction",
  "Media & Entertainment", "Architecture", "Energy & Utilities", "Logistics",
  "Manufacturing", "Healthcare", "Retail", "Education",
];
const band12 = (640 - 50 - 16) / industries.length; // ColumnChart plot geometry
const l12 = xAxisLabels(industries.length, band12);
ok(l12.step === 1, "12 wide bands → every category shown (no every-other dropping)");
ok(widestShown(industries, band12) <= band12 + 0.01, "12-category labels each fit their band (no overlap)");
ok(l12.fontSize >= 7 && l12.fontSize <= 10, "12-category font stays in the readable 7–10 range");

// — Crowded: 40 categories, narrow bands → must thin out, not overlap, font floored at 7.
const many = Array.from({ length: 40 }, (_, i) => `Category ${i + 1}`);
const band40 = (640 - 50 - 16) / many.length;
const l40 = xAxisLabels(many.length, band40);
ok(l40.step > 1, "40 narrow bands → labels thinned (step > 1) instead of overlapping");
ok(l40.fontSize >= 7, "40-category font floored at the readable minimum (7)");
ok(widestShown(many, band40) <= band40 * l40.step + 0.01, "thinned labels still fit their (wider) slot");

// — Density cap (line/time-series): 18 months, capped at 9 visible.
const months = Array.from({ length: 18 }, (_, i) => `2025-${String((i % 12) + 1).padStart(2, "0")}`);
const spacing18 = (640 - 52 - 18) / (months.length - 1);
const capped = xAxisLabels(months.length, spacing18, { maxVisible: 9 });
const shownCount = months.filter((_, i) => showLabelAt(i, months.length, capped.step)).length;
ok(capped.step > 1 && shownCount <= 9, "time-series density cap keeps visible ticks ≤ 9");
ok(capped.fontSize === 10, "capped time-series keeps full font (wide slots, no shrink needed)");
ok(capped.fit("2025-01") === "2025-01", "7-char date label is not truncated in a capped line chart");

// — Edges always shown.
ok(showLabelAt(0, 18, capped.step) && showLabelAt(17, 18, capped.step), "first and last labels always shown");

// — Truncation adds an ellipsis and respects the slot for a single very long label.
const tiny = xAxisLabels(20, 18); // narrow-ish band
const fitted = tiny.fit("Telecommunications Infrastructure");
ok(fitted.endsWith("…") && fitted.length * tiny.fontSize * CHAR_W <= 18 * tiny.step + 0.01, "long label truncated to fit its slot");

console.log(`\nAXIS OK — ${checks} checks`);
