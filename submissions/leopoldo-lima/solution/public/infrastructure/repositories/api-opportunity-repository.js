export class ApiOpportunityRepository {
  /**
   * @param {string} basePath
   */
  constructor(basePath = "/api") {
    this.basePath = basePath;
  }

  /**
   * @param {{
   *   region?: string,
   *   manager?: string,
   *   deal_stage?: string,
   *   q?: string,
   *   priority_band?: string,
   *   limit?: number
   * }} filters
   * @param {{signal?: AbortSignal}} options
   */
  async listOpportunities(filters = {}, options = {}) {
    const params = new URLSearchParams();
    if (filters.region) params.set("region", filters.region);
    if (filters.manager) params.set("manager", filters.manager);
    if (filters.deal_stage) params.set("deal_stage", filters.deal_stage);
    if (filters.q) params.set("q", filters.q);
    if (filters.priority_band) params.set("priority_band", filters.priority_band);
    params.set("limit", String(filters.limit ?? 20));

    const response = await fetch(`${this.basePath}/opportunities?${params.toString()}`, {
      signal: options.signal,
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }

  /**
   * @param {string} id
   * @param {{signal?: AbortSignal}} options
   */
  async getOpportunity(id, options = {}) {
    const response = await fetch(`${this.basePath}/opportunities/${id}`, {
      signal: options.signal,
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }

  /**
   * @param {{signal?: AbortSignal}} options
   */
  async getDashboardKpis(options = {}) {
    const response = await fetch(`${this.basePath}/dashboard/kpis`, {
      signal: options.signal,
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }

  /**
   * @param {{signal?: AbortSignal}} options
   */
  async getDashboardFilterOptions(options = {}) {
    const response = await fetch(`${this.basePath}/dashboard/filter-options`, {
      signal: options.signal,
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    return response.json();
  }
}
