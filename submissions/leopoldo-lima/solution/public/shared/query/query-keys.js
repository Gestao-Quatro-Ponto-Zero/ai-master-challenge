export const DASHBOARD_QUERY_KEYS = {
  ranking: (filters) => ["dashboard", "ranking", JSON.stringify(filters ?? {})],
  detail: (id) => ["dashboard", "detail", String(id)],
};
