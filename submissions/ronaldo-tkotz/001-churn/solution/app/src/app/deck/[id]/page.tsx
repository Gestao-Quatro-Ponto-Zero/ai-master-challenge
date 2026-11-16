import { notFound } from "next/navigation";
import { buildExecutiveReview, getStoredDeck } from "@/engine/deck";
import { DeckViewer } from "@/app/components/deck/DeckViewer";
import { requireUser } from "@/app/lib/auth";

// The warehouse is read at request time (better-sqlite3) — never prerender.
export const dynamic = "force-dynamic";

/**
 * The in-app deck — rendered by the app at runtime (SP4 / ISC-21), never an
 * off-stage export. Two kinds resolve here:
 *  - the autonomous exec review (`exec-review*`) rebuilds live — deterministic + cheap;
 *  - a user-built pin-deck (any other id) loads its frozen, grounded snapshot.
 */
export default async function DeckPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const user = id.startsWith("exec-review") ? null : await requireUser();
  const spec = id.startsWith("exec-review") ? await buildExecutiveReview() : getStoredDeck(user!.id, id);
  if (!spec) notFound();
  return <DeckViewer spec={spec} />;
}
