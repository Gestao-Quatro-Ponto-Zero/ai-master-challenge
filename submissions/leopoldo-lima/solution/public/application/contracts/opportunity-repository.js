/**
 * @typedef {Object} OpportunityRepository
 * @property {(filters?: {region?: string, manager?: string, deal_stage?: string, q?: string, priority_band?: string, limit?: number}) => Promise<{total: number, items: Array<Record<string, unknown>>}>} listOpportunities
 * @property {(id: string, options?: {signal?: AbortSignal}) => Promise<Record<string, unknown>>} getOpportunity
 * @property {(options?: {signal?: AbortSignal}) => Promise<Record<string, unknown>>} getDashboardKpis
 * @property {(options?: {signal?: AbortSignal}) => Promise<Record<string, unknown>>} getDashboardFilterOptions
 */

/**
 * Valida se um objeto atende ao contrato mínimo de repositório.
 * @param {unknown} value
 * @returns {asserts value is OpportunityRepository}
 */
export function assertOpportunityRepository(value) {
  if (
    !value ||
    typeof value !== "object" ||
    typeof value.listOpportunities !== "function" ||
    typeof value.getOpportunity !== "function" ||
    typeof value.getDashboardKpis !== "function" ||
    typeof value.getDashboardFilterOptions !== "function"
  ) {
    throw new Error("Invalid OpportunityRepository implementation.");
  }
}
