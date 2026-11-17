/**
 * Shared x-axis label layout + value-domain helpers for the categorical charts
 * (column, bar, combo, line).
 *
 * Every chart draws into a fixed 640-unit viewBox scaled to fill its container, so a
 * label that fits its slot *in viewBox units* never overlaps regardless of how wide it
 * renders — the fit is scale-invariant.
 *
 * LABELS — two strategies. `axisTicks` (the categorical default) NEVER truncates: when
 * a label is too wide for its slot it tilts the whole tick row onto a diagonal and
 * renders the FULL name (Ronaldo's rule: never end a category label in "…"). It only
 * thins ticks out (`step`) for pure density caps (time-series). `xAxisLabels` is the
 * legacy horizontal-fit path still used by the line chart, whose x is short ordered
 * dates that always fit.
 */
const CHAR_W = 0.58; // mean glyph advance as a fraction of font size (latin + digits, sans)
const MIN_FONT = 7;
const MAX_FONT = 10;
const TARGET_CHARS = 9; // size the font so ~this many chars fit one slot
const MIN_STUB_CHARS = 4; // a label needs at least this many chars (incl. "…") to be worth showing

function clamp(value: number, lo: number, hi: number): number {
  return Math.max(lo, Math.min(hi, value));
}

function densityStep(count: number, targetVisible: number): number {
  if (count <= targetVisible) return 1;
  return Math.max(1, Math.ceil((count - 1) / Math.max(1, targetVisible - 1)));
}

// ── Value domain ────────────────────────────────────────────────────────────

/** Round a positive magnitude up to a clean 1/2/5 × 10ⁿ axis bound. */
export function niceCeil(value: number): number {
  if (!(value > 0)) return 1;
  const magnitude = 10 ** Math.floor(Math.log10(value));
  const normalized = value / magnitude;
  if (normalized <= 1) return magnitude;
  if (normalized <= 2) return 2 * magnitude;
  if (normalized <= 5) return 5 * magnitude;
  return 10 * magnitude;
}

/**
 * A signed value domain that always includes zero, so bars anchor to a real
 * baseline and NEGATIVE values render as bars on the other side of it (instead of
 * silently clamping to zero — the "empty bar" bug). `lo ≤ 0 ≤ hi`, both rounded to
 * clean bounds; a degenerate all-zero set falls back to [0, 1].
 */
export function niceDomain(values: number[]): { lo: number; hi: number; span: number } {
  let mn = 0;
  let mx = 0;
  for (const v of values) {
    if (typeof v === "number" && Number.isFinite(v)) {
      if (v < mn) mn = v;
      if (v > mx) mx = v;
    }
  }
  const hi = mx > 0 ? niceCeil(mx) : 0;
  const lo = mn < 0 ? -niceCeil(-mn) : 0;
  if (hi === 0 && lo === 0) return { lo: 0, hi: 1, span: 1 };
  return { lo, hi, span: hi - lo || 1 };
}

// ── X-axis tick labels (diagonal-capable, never truncated) ────────────────────

export interface AxisTicks {
  /** Show a label only every `step` categories (index 0 and the last are always shown). */
  step: number;
  /** Font size in viewBox units. */
  fontSize: number;
  /** When true, render each label on a diagonal so its FULL text is legible. */
  rotate: boolean;
  /** Rotation in degrees (negative = descends to the left under the tick). */
  angle: number;
  /** Extra vertical room the rotated labels need below the axis (viewBox units, 0 when horizontal). */
  bottomPad: number;
  /** Horizontal footprint of the longest rotated label (viewBox units) — for left-gutter sizing so the first label never clips. 0 when horizontal. */
  labelSpanX: number;
}

/**
 * Decide how to lay out the x-axis labels for `labels` given the horizontal room
 * each gets (`slotPerCategory`, in viewBox units). Returns full labels always — the
 * caller renders the raw string, never a truncated one. Rotates onto a diagonal when
 * the widest visible label can't fit its slot horizontally.
 *
 * @param opts.maxVisible cap on how many labels to show (time-series density); omit to show every category.
 */
export function axisTicks(labels: string[], slotPerCategory: number, opts?: { maxVisible?: number }): AxisTicks {
  const count = labels.length;
  const slot = Math.max(0, slotPerCategory);

  // Only thin for an explicit density cap — rotation (not dropping) handles width.
  let step = 1;
  if (opts?.maxVisible && count > 1) step = densityStep(count, opts.maxVisible);

  const shownSlot = slot * step;
  const longest = labels.reduce((m, l) => Math.max(m, (l ?? "").length), 0);

  // Would the widest label fit horizontally in one slot at a readable font?
  const horizFont = clamp(shownSlot / (CHAR_W * Math.max(TARGET_CHARS, longest)), MIN_FONT, MAX_FONT);
  const fitsHorizontal = longest * horizFont * CHAR_W <= shownSlot;

  if (fitsHorizontal) {
    return { step, fontSize: Math.round(horizFont * 10) / 10, rotate: false, angle: 0, bottomPad: 0, labelSpanX: 0 };
  }

  // Diagonal: pick a compact font, render the full label, reserve vertical + left room.
  const fontSize = count > 14 ? 7 : count > 8 ? 8 : 9;
  const angle = -32;
  const rad = (-angle * Math.PI) / 180;
  const labelWidth = longest * fontSize * CHAR_W;
  const bottomPad = Math.min(96, Math.round(Math.sin(rad) * labelWidth + fontSize + 6));
  const labelSpanX = Math.round(Math.cos(rad) * labelWidth);
  return { step, fontSize, rotate: true, angle, bottomPad, labelSpanX };
}

// ── Legacy horizontal-fit path (line chart only) ─────────────────────────────

export interface XAxisLabels {
  step: number;
  fontSize: number;
  fit: (label: string) => string;
}

export function xAxisLabels(count: number, slotPerCategory: number, opts?: { maxVisible?: number }): XAxisLabels {
  const slot = Math.max(0, slotPerCategory);
  let step = 1;
  if (count > 1) {
    const minSlot = MIN_FONT * CHAR_W * MIN_STUB_CHARS;
    while (slot * step < minSlot) step += 1;
  }
  if (opts?.maxVisible && count > 1) {
    step = Math.max(step, densityStep(count, opts.maxVisible));
  }

  const shownSlot = slot * step;
  const fontSize = Math.round(clamp(shownSlot / (CHAR_W * TARGET_CHARS), MIN_FONT, MAX_FONT) * 10) / 10;
  const maxChars = Math.max(3, Math.floor(shownSlot / (fontSize * CHAR_W)));

  return {
    step,
    fontSize,
    fit: (label: string) => (label.length <= maxChars ? label : `${label.slice(0, Math.max(1, maxChars - 1))}…`),
  };
}

/**
 * Whether to render the label for `index` given the computed `step` (edges always shown).
 * A stepped label too close to the last one is dropped so the two never collide
 * (24 months at step 3 used to print "2024-10" on top of "2024-12").
 */
export function showLabelAt(index: number, count: number, step: number): boolean {
  if (count <= 0) return false;
  if (index === 0 || index === count - 1) return true;
  if (index % step !== 0) return false;
  return count - 1 - index >= step * 0.75;
}

/** Render one diagonal (or horizontal) tick label as an SVG <text>. Shared by the categorical charts. */
export function tickAnchor(rotate: boolean): "middle" | "end" {
  return rotate ? "end" : "middle";
}
