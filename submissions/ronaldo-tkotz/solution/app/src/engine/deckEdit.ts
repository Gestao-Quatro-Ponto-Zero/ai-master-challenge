/**
 * Draft-deck editing — the PATCH surface behind /api/deck/{id}.
 *
 * The invariant this module encodes: editing touches PROSE ONLY. A draft deck's
 * titles, subtitles, body lines, slide order, and slide count are the user's;
 * the grounded material — evidence values, chart data/specs, tables, citedSql,
 * lineage — is immutable BY CONSTRUCTION. No op in the vocabulary below can
 * even express a write to a grounded field: every op copies the stored spec and
 * mutates only prose/order, so an illegal edit is unrepresentable, not merely
 * rejected. Publishing flips status to "published" and freezes the deck — from
 * then on (and for legacy decks with no status at all) every op 409s.
 *
 * Structure rules: a pin-deck is cover · context · [divider+argument]* ·
 * recommendation. Move/remove operate on divider+argument PAIRS as one unit and
 * never touch the frame slides; dividers renumber after any reorder.
 *
 * Pure + storage-free (deck.ts owns persistence) — headlessly testable.
 */
import type { DeckSpec, Slide } from "./deck";

export const DECK_TITLE_MAX = 160;
export const SLIDE_TITLE_MAX = 160;
export const SUBTITLE_MAX = 300;
export const BODY_LINE_MAX = 300;

/** The complete edit vocabulary — nothing here can name a grounded field. */
export type DeckEditOp =
  | { op: "editText"; slideIndex: number; field: "title" | "subtitle"; value: string }
  | { op: "editBody"; slideIndex: number; lineIndex: number; value: string }
  | { op: "move"; from: number; to: number }
  | { op: "remove"; slideIndex: number }
  | { op: "publish" }
  | { op: "editDeckTitle"; value: string };

export type DeckEditResult =
  | { ok: true; spec: DeckSpec }
  | { ok: false; status: number; error: string };

const fail = (status: number, error: string): DeckEditResult => ({ ok: false, status, error });

/** Parse an untrusted request body into an edit op, or null when malformed. */
export function parseDeckEditOp(body: unknown): DeckEditOp | null {
  if (!body || typeof body !== "object") return null;
  const b = body as Record<string, unknown>;
  const int = (v: unknown): v is number => Number.isInteger(v);
  switch (b.op) {
    case "editText":
      if (int(b.slideIndex) && (b.field === "title" || b.field === "subtitle") && typeof b.value === "string")
        return { op: "editText", slideIndex: b.slideIndex, field: b.field, value: b.value };
      return null;
    case "editBody":
      if (int(b.slideIndex) && int(b.lineIndex) && typeof b.value === "string")
        return { op: "editBody", slideIndex: b.slideIndex, lineIndex: b.lineIndex, value: b.value };
      return null;
    case "move":
      if (int(b.from) && int(b.to)) return { op: "move", from: b.from, to: b.to };
      return null;
    case "remove":
      if (int(b.slideIndex)) return { op: "remove", slideIndex: b.slideIndex };
      return null;
    case "publish":
      return { op: "publish" };
    case "editDeckTitle":
      if (typeof b.value === "string") return { op: "editDeckTitle", value: b.value };
      return null;
    default:
      return null;
  }
}

// ── Pair structure: [divider, argument] blocks between the frame slides ───────

/** Start indices of every divider+argument pair, in slide order. */
export function pairStarts(slides: Slide[]): number[] {
  const starts: number[] = [];
  for (let i = 0; i < slides.length - 1; i++) {
    if (slides[i].layout === "divider" && slides[i + 1].layout === "argument") {
      starts.push(i);
      i++; // the argument belongs to this pair — don't re-scan it
    }
  }
  return starts;
}

/** The pair (by ordinal) a slide index belongs to, or -1 for frame slides. */
export function pairOfSlide(slides: Slide[], slideIndex: number): number {
  return pairStarts(slides).findIndex((s) => slideIndex === s || slideIndex === s + 1);
}

const pad2 = (n: number): string => String(n).padStart(2, "0");

/** Renumber divider sectionNumbers to match the current pair order. */
function renumber(slides: Slide[]): void {
  pairStarts(slides).forEach((s, k) => {
    slides[s].sectionNumber = pad2(k + 1);
  });
}

// ── The op interpreter ─────────────────────────────────────────────────────────

/**
 * Apply one edit op to a stored spec, returning the NEXT spec (a deep copy —
 * the caller re-stores it) or a typed failure. The stored spec is the single
 * source of grounded truth: every chart/table/evidence/citedSql/lineage byte in
 * the result comes from the structuredClone of `stored`, never from the op.
 */
export function applyDeckEdit(stored: DeckSpec, op: DeckEditOp): DeckEditResult {
  // Frozen gate first: published — or legacy status-less — decks accept nothing.
  if (stored.status !== "draft") return fail(409, "This deck is published and frozen — no edits accepted.");

  const spec = structuredClone(stored); // grounded fields ride through untouched
  const slides = spec.slides;

  switch (op.op) {
    case "publish": {
      spec.status = "published";
      return { ok: true, spec };
    }

    case "editDeckTitle": {
      const value = op.value.trim().slice(0, DECK_TITLE_MAX);
      if (!value) return fail(400, "The deck title cannot be empty.");
      spec.title = value;
      return { ok: true, spec };
    }

    case "editText": {
      const slide = slides[op.slideIndex];
      if (!slide) return fail(400, `No slide at index ${op.slideIndex}.`);
      if (op.field === "title") {
        const value = op.value.trim().slice(0, SLIDE_TITLE_MAX);
        if (!value) return fail(400, "A slide title cannot be empty.");
        slide.title = value;
      } else {
        // An emptied subtitle is a deletion — the renderers already skip falsy subtitles.
        slide.subtitle = op.value.trim().slice(0, SUBTITLE_MAX);
      }
      return { ok: true, spec };
    }

    case "editBody": {
      const slide = slides[op.slideIndex];
      if (!slide) return fail(400, `No slide at index ${op.slideIndex}.`);
      if (!slide.body || op.lineIndex < 0 || op.lineIndex >= slide.body.length)
        return fail(400, `No body line ${op.lineIndex} on slide ${op.slideIndex}.`);
      const value = op.value.trim().slice(0, BODY_LINE_MAX);
      if (!value) return fail(400, "A body line cannot be empty.");
      slide.body[op.lineIndex] = value;
      return { ok: true, spec };
    }

    case "move": {
      const fromPair = pairOfSlide(slides, op.from);
      const toPair = pairOfSlide(slides, op.to);
      if (fromPair === -1 || toPair === -1)
        return fail(400, "Move targets must both sit inside a divider+argument pair — frame slides don't move.");
      if (fromPair === toPair) return { ok: true, spec }; // no-op, but not an error
      const starts = pairStarts(slides);
      const pair = slides.splice(starts[fromPair], 2); // the unit travels whole
      // Remove-then-insert at the ORIGINAL target ordinal — classic list reorder:
      // the moved pair ends up at ordinal `toPair` whichever direction it travelled.
      const newStarts = pairStarts(slides);
      const j = Math.min(toPair, newStarts.length);
      const insertAt = j < newStarts.length ? newStarts[j] : newStarts[newStarts.length - 1] + 2;
      slides.splice(insertAt, 0, ...pair);
      renumber(slides);
      return { ok: true, spec };
    }

    case "remove": {
      const k = pairOfSlide(slides, op.slideIndex);
      if (k === -1)
        return fail(400, "Only divider+argument pairs can be removed — the frame slides stay.");
      slides.splice(pairStarts(slides)[k], 2);
      renumber(slides);
      return { ok: true, spec };
    }
  }
}
