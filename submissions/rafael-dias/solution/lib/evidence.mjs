/** Read-only event projection: preserve stored history, deduplicate its effects. */
export function evidenceEvents(events, opportunityId, now) {
  const cutoff = Date.parse(now);
  const seen = new Set();
  return events
    .map((event, index) => ({ event, index }))
    .filter(({ event: e }) => {
      if (e.opportunityId !== opportunityId) return false;
      const recorded = Date.parse(e.recordedAt || e.at);
      const occurred = Date.parse(e.occurredAt || e.at);
      if (
        !Number.isFinite(recorded) ||
        !Number.isFinite(occurred) ||
        recorded > cutoff ||
        occurred > cutoff
      )
        return false;
      const key = e.evidenceId || e.id;
      if (key && seen.has(key)) return false;
      if (key) seen.add(key);
      return true;
    })
    .sort(
      (a, b) =>
        Date.parse(a.event.occurredAt || a.event.at) -
          Date.parse(b.event.occurredAt || b.event.at) || a.index - b.index,
    )
    .map(({ event }) => event);
}

export const occurredAt = (event) => event.occurredAt || event.at;
