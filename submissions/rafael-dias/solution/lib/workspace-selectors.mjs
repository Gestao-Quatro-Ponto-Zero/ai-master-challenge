import { evidenceEvents } from "./evidence.mjs";
import { isClosed, prioritize } from "./workflow.mjs";
import { dailyProgress, localDay } from "./sales-guide.mjs";
import { sameDay } from "./format.mjs";

/** Pure projections; no React, browser, mutation or persistence. */
export function selectSellerWorkspace(all, agent, events, plans, now) {
  const mine = all.filter((d) => d.sales_agent === agent);
  const open = mine.filter((d) => !isClosed(d));
  const agenda = open
    .filter((d) => d.nextTask)
    .sort((a, b) => a.nextTask.dueAt.localeCompare(b.nextTask.dueAt));
  const due = agenda.filter((d) => d.overdue || sameDay(d.nextTask.dueAt, now));
  const planKey = `${localDay(now)}|${agent}`;
  const progress = dailyProgress(plans[planKey], events, now);
  const activeBatch = progress.batches[progress.activeBatch];
  // Urgent actions bypass fixed rounds; future commitments and pauses stay out.
  const ranked = prioritize(open, now);
  const batchIds = new Set(
    activeBatch?.tasks.filter((t) => !t.done).map((t) => t.opportunityId) || [],
  );
  const batch = ranked.filter((d) => batchIds.has(d.opportunity_id));
  const attention = ranked.filter(
    (d) =>
      d.overdue ||
      d.priority?.rank === 1 ||
      d.healthDetails?.risks.some((r) => r.code === "financial_block"),
  );
  const source =
    activeBatch && batch.length
      ? batch
      : ranked.filter(
          (d) =>
            d.account &&
            !progress.tasks.some(
              (t) => t.opportunityId === d.opportunity_id && t.done,
            ),
        );
  const top = [
    ...new Map(
      [...attention, ...source].map((d) => [d.opportunity_id, d]),
    ).values(),
  ].slice(0, 5);
  const contactsToday = mine
    .flatMap((d) => evidenceEvents(events, d.opportunity_id, now))
    .filter(
      (e) => e.type === "contact" && sameDay(e.occurredAt || e.at, now),
    ).length;
  const qualified = mine.filter((d) => d.qualification && !isClosed(d));
  return {
    mine,
    open,
    agenda,
    due,
    planKey,
    progress,
    top,
    contactsToday,
    qualified,
  };
}

export function selectResultsScope(all, { scope, agent, manager, region }) {
  return all.filter(
    (d) =>
      (scope === "company" || d.sales_agent === agent) &&
      (!manager || d.manager === manager) &&
      (!region || d.regional_office === region),
  );
}
