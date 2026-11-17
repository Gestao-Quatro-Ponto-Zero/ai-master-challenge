"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import type { DeckSpec } from "@/engine/deck";
import { pairOfSlide, pairStarts } from "@/engine/deckEdit";
import { SlideView } from "./SlideView";

/**
 * The in-app deck viewer. Renders a grounded DeckSpec as keyboard-navigable
 * 16:9 slides at runtime — this IS the deck (SP4 / ISC-21), not a screenshot of
 * one. Arrow keys / space / click to move; Esc returns to Veta.
 *
 * Draft decks (status "draft") additionally carry the editor: click-to-edit
 * prose, argument-pair reorder/remove, and a publish button that freezes the
 * deck. Everything keys off `spec.status`, so published and legacy decks render
 * exactly as they always did. Edits are optimistic; the server's PATCH response
 * carries the authoritative spec and reconciles the view.
 */
export function DeckViewer({ spec: initial }: { spec: DeckSpec }) {
  const router = useRouter();
  const [spec, setSpec] = useState(initial);
  const [i, setI] = useState(0);
  const [publishArmed, setPublishArmed] = useState(false);
  const [removeArmed, setRemoveArmed] = useState(false);
  const [busy, setBusy] = useState(false);
  const n = spec.slides.length;
  const draft = spec.status === "draft";
  const go = useCallback((d: number) => setI((x) => Math.min(Math.max(x + d, 0), n - 1)), [n]);

  useEffect(() => {
    function onKey(e: KeyboardEvent) {
      // Never steal keys from an active inline editor.
      const t = e.target as HTMLElement | null;
      if (t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.isContentEditable)) return;
      if (e.key === "ArrowRight" || e.key === " " || e.key === "PageDown") {
        e.preventDefault();
        go(1);
      } else if (e.key === "ArrowLeft" || e.key === "PageUp") {
        e.preventDefault();
        go(-1);
      } else if (e.key === "Escape") {
        router.push("/");
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [go, router]);

  /** PATCH one edit op; reconcile on the server's authoritative spec, revert on failure. */
  const patch = useCallback(
    async (op: Record<string, unknown>, optimistic?: DeckSpec): Promise<boolean> => {
      const prev = spec;
      if (optimistic) setSpec(optimistic);
      setBusy(true);
      try {
        const res = await fetch(`/api/deck/${encodeURIComponent(spec.id)}`, {
          method: "PATCH",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(op),
        });
        const data = (await res.json().catch(() => null)) as { spec?: DeckSpec } | null;
        if (!res.ok || !data?.spec) {
          setSpec(prev); // reconcile: the edit did not land
          return false;
        }
        setSpec(data.spec);
        return true;
      } catch {
        setSpec(prev);
        return false;
      } finally {
        setBusy(false);
      }
    },
    [spec],
  );

  const slide = spec.slides[i];

  // Prose edits are optimistic — apply locally, then reconcile on the response.
  const editText = (field: "title" | "subtitle", value: string) => {
    const next = structuredClone(spec);
    next.slides[i][field] = value.trim();
    void patch({ op: "editText", slideIndex: i, field, value }, next);
  };
  const editBody = (lineIndex: number, value: string) => {
    const next = structuredClone(spec);
    if (next.slides[i].body?.[lineIndex] !== undefined) next.slides[i].body![lineIndex] = value.trim();
    void patch({ op: "editBody", slideIndex: i, lineIndex, value }, next);
  };

  // Pair controls — visible only when the current slide sits inside a divider+argument pair.
  const pairs = pairStarts(spec.slides);
  const pairIdx = draft ? pairOfSlide(spec.slides, i) : -1;
  const movePair = async (dir: -1 | 1) => {
    const target = pairIdx + dir;
    if (target < 0 || target >= pairs.length) return;
    // Keep the eye on the moved pair: it travels 2 slides in `dir`.
    if (await patch({ op: "move", from: pairs[pairIdx], to: pairs[target] })) setI((x) => x + dir * 2);
  };
  const removePair = async () => {
    setRemoveArmed(false);
    if (await patch({ op: "remove", slideIndex: i })) setI((x) => Math.max(0, Math.min(x - 1, spec.slides.length - 3)));
  };

  return (
    <div className="flex h-dvh w-full flex-col bg-[#070708]">
      {/* Top bar — title, position, exits. */}
      <header className="flex items-center gap-4 px-5 py-3 text-[12px]">
        <button onClick={() => router.push("/")} className="font-medium text-neutral-400 transition-colors hover:text-white">
          ← Veta
        </button>
        <span className="font-medium text-neutral-200">{spec.title}</span>
        {spec.status === "published" && (
          <span className="rounded-full border border-emerald-400/30 px-2 py-0.5 text-[10px] font-medium text-emerald-400/90">Published</span>
        )}
        <span className="ml-auto font-mono tabular-nums text-neutral-500">
          {i + 1} / {n}
        </span>
        <a
          href={`/api/deck/${encodeURIComponent(spec.id)}/pptx`}
          download
          title="Download this deck as PowerPoint"
          className="rounded-md border border-white/15 px-2.5 py-1 text-[11px] font-medium text-neutral-200 transition-colors hover:border-[#e3b341]/40 hover:text-[#e3b341]"
        >
          Download .pptx
        </a>
      </header>

      {/* Draft bar — the editing contract, and the one-way door out of it. */}
      {draft && (
        <div className="flex items-center gap-3 border-y border-[#e3b341]/20 bg-[#e3b341]/[0.06] px-5 py-1.5 text-[11px]">
          <span className="flex items-center gap-1.5 font-medium text-[#e3b341]">
            <span className="h-1.5 w-1.5 rounded-full bg-[#e3b341]" />
            Draft — editing enabled
          </span>
          <span className="text-neutral-500">Click any title or line to rewrite it. Numbers, charts and tables stay grounded by SQL.</span>
          <span className="ml-auto flex items-center gap-2">
            {publishArmed && <span className="text-neutral-400">Publishing freezes the deck — no further edits.</span>}
            <button
              onClick={() => (publishArmed ? void patch({ op: "publish" }) : setPublishArmed(true))}
              onBlur={() => setPublishArmed(false)}
              disabled={busy}
              className={`rounded-md px-2.5 py-1 text-[11px] font-medium transition-colors disabled:opacity-50 ${
                publishArmed
                  ? "bg-[#e3b341] text-black hover:opacity-90"
                  : "border border-[#e3b341]/40 text-[#e3b341] hover:bg-[#e3b341]/10"
              }`}
            >
              {publishArmed ? "Confirm publish" : "Publish"}
            </button>
          </span>
        </div>
      )}

      {/* Stage — the slide at 16:9, centred, with prev/next affordances. */}
      <main className="relative flex flex-1 items-center justify-center px-6 pb-4">
        <button
          onClick={() => go(-1)}
          disabled={i === 0}
          aria-label="Previous slide"
          className="absolute left-2 z-10 grid h-10 w-10 place-items-center rounded-full text-[22px] text-neutral-500 transition-colors hover:text-white disabled:opacity-20"
        >
          ‹
        </button>
        <div className="aspect-[16/9] w-full max-w-[1180px] overflow-hidden rounded-xl shadow-2xl ring-1 ring-white/10">
          <SlideView slide={slide} spec={spec} editable={draft} edit={{ onEditText: editText, onEditBody: editBody }} />
        </div>
        <button
          onClick={() => go(1)}
          disabled={i === n - 1}
          aria-label="Next slide"
          className="absolute right-2 z-10 grid h-10 w-10 place-items-center rounded-full text-[22px] text-neutral-500 transition-colors hover:text-white disabled:opacity-20"
        >
          ›
        </button>
      </main>

      {/* Pair controls — reorder/remove the section the current slide belongs to. */}
      {pairIdx >= 0 && (
        <div className="flex items-center justify-center gap-2 pb-1 text-[11px] text-neutral-500">
          <span>
            Section {pairIdx + 1} of {pairs.length}
          </span>
          <button
            onClick={() => void movePair(-1)}
            disabled={busy || pairIdx === 0}
            title="Move this section earlier"
            className="rounded border border-white/10 px-1.5 py-0.5 transition-colors hover:border-white/30 hover:text-white disabled:opacity-25"
          >
            ↑
          </button>
          <button
            onClick={() => void movePair(1)}
            disabled={busy || pairIdx === pairs.length - 1}
            title="Move this section later"
            className="rounded border border-white/10 px-1.5 py-0.5 transition-colors hover:border-white/30 hover:text-white disabled:opacity-25"
          >
            ↓
          </button>
          {removeArmed ? (
            <span className="flex items-center gap-1.5">
              <button onClick={() => void removePair()} disabled={busy} className="font-medium text-red-400 hover:text-red-300">
                Remove section?
              </button>
              <button onClick={() => setRemoveArmed(false)} className="text-neutral-500 hover:text-white">
                Cancel
              </button>
            </span>
          ) : (
            <button
              onClick={() => setRemoveArmed(true)}
              disabled={busy}
              title="Remove this section (divider + slide)"
              className="rounded border border-white/10 px-1.5 py-0.5 transition-colors hover:border-red-400/50 hover:text-red-400 disabled:opacity-25"
            >
              ✕
            </button>
          )}
        </div>
      )}

      {/* Progress — one pip per slide, clickable. */}
      <footer className="flex items-center justify-center gap-1.5 pb-4">
        {spec.slides.map((s, k) => (
          <button
            key={k}
            onClick={() => setI(k)}
            aria-label={`Go to slide ${k + 1}`}
            className={`h-1.5 rounded-full transition-all ${k === i ? "w-6 bg-[#e3b341]" : "w-1.5 bg-white/25 hover:bg-white/50"}`}
          />
        ))}
      </footer>
    </div>
  );
}
