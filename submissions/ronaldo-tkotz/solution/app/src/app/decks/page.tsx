import Link from "next/link";
import { getStoredDeck, listStoredDecks } from "@/engine/deck";
import { DeckLibrary } from "@/app/components/deck/DeckLibrary";
import { requireUser } from "@/app/lib/auth";

// The library reads the app DB (better-sqlite3) at request time — never prerender.
export const runtime = "nodejs";
export const dynamic = "force-dynamic";

/**
 * The Deck Library (SP6 / the gallery): every deck the user built from pinned
 * insights, persisted and reopenable after the conversation ends. The autonomous
 * "Veta Executive Deck" is NOT here — it lives on the left nav and rebuilds live
 * from current data, so it has no frozen snapshot to archive.
 */
export default async function DecksPage() {
  const user = await requireUser();
  // Enrich each summary with its draft/published state (DeckSummary predates the
  // artifact layer and its owner module is frozen this stream — read the stored
  // spec's status here instead; absent status = legacy = published).
  const decks = listStoredDecks(user.id).map((d) => ({
    ...d,
    status: getStoredDeck(user.id, d.id)?.status ?? ("published" as const),
  }));

  return (
    <div className="min-h-dvh bg-background">
      <header className="sticky top-0 z-10 flex items-center gap-4 border-b border-edge bg-background/90 px-6 py-3.5 backdrop-blur">
        <Link href="/" className="text-[12px] font-medium text-faint transition-colors hover:text-foreground">
          ← Veta
        </Link>
        <div className="flex items-center gap-2.5">
          <span className="grid h-6 w-6 place-items-center rounded-md bg-accent-soft text-accent">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" className="h-3.5 w-3.5">
              <path d="M3 7l9-4 9 4-9 4-9-4Z" /><path d="M3 12l9 4 9-4" /><path d="M3 17l9 4 9-4" />
            </svg>
          </span>
          <h1 className="text-[14px] font-semibold tracking-tight text-foreground">Deck Library</h1>
        </div>
        <span className="text-[11px] text-faint">
          {decks.length} {decks.length === 1 ? "deck" : "decks"} you built
        </span>
      </header>

      <main className="mx-auto max-w-6xl px-6 py-8">
        <DeckLibrary initialDecks={decks} />
      </main>
    </div>
  );
}
