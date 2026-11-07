export function sortAgentsByOpen(agents, counts) {
  return [...agents].sort(
    (a, b) => (counts[b] || 0) - (counts[a] || 0) || a.localeCompare(b),
  );
}
export function portfolioSummary(data) {
  const owners = [
    ...new Set([
      ...(data.historicalByAgent || []).map((t) => t.sales_agent),
      ...data.opportunities.map((d) => d.sales_agent),
    ]),
  ];
  const rows = owners.map((agent) => {
    const history = (data.historicalByAgent || []).find(
      (t) => t.sales_agent === agent,
    );
    return {
      agent,
      open: data.opportunities.filter((d) => d.sales_agent === agent).length,
      closed: (history?.won || 0) + (history?.lost || 0),
    };
  });
  const active = rows.filter((r) => r.open > 0),
    empty = rows.filter((r) => r.open === 0);
  return {
    total: rows.length,
    active: active.length,
    empty: empty.length,
    min: active.length ? Math.min(...active.map((r) => r.open)) : 0,
    max: active.length ? Math.max(...active.map((r) => r.open)) : 0,
    closedOnly: empty.filter((r) => r.closed > 0).length,
    withoutPipeline: empty.filter((r) => r.closed === 0).length,
  };
}
