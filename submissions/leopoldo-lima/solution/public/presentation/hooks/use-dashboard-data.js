import { DASHBOARD_QUERY_KEYS } from "../../shared/query/query-keys.js";

/**
 * @param {{ listOpportunities: Function, getOpportunity: Function }} repository
 */
export function createDashboardDataHook(repository) {
  let rankingAbortController = null;
  let detailAbortController = null;

  async function _withRetry(operation, retries = 1) {
    let lastError = null;
    for (let attempt = 0; attempt <= retries; attempt += 1) {
      try {
        return await operation();
      } catch (error) {
        lastError = error;
        if (attempt === retries) break;
      }
    }
    throw lastError ?? new Error("Unknown dashboard data error.");
  }

  return {
    queryKeys: DASHBOARD_QUERY_KEYS,

    async loadRanking(filters) {
      if (rankingAbortController) rankingAbortController.abort();
      rankingAbortController = new AbortController();
      const queryKey = DASHBOARD_QUERY_KEYS.ranking(filters);
      const payload = await _withRetry(
        () =>
          repository.listOpportunities(filters, {
            signal: rankingAbortController.signal,
          }),
        1
      );
      return { queryKey, payload };
    },

    async loadDetail(id) {
      if (detailAbortController) detailAbortController.abort();
      detailAbortController = new AbortController();
      const queryKey = DASHBOARD_QUERY_KEYS.detail(id);
      const payload = await _withRetry(
        () =>
          repository.getOpportunity(id, {
            signal: detailAbortController.signal,
          }),
        1
      );
      return { queryKey, payload };
    },
  };
}
