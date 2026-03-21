import { normalizeSortDedupeStrings } from "../../shared/filter-options-utils.js";
import { buildMockOpportunityDetail } from "../mocks/fixtures/opportunity-detail.js";
import { MOCK_OPPORTUNITY_LIST } from "../mocks/fixtures/opportunity-list.js";

export class MockOpportunityRepository {
  constructor() {
    this.items = [...MOCK_OPPORTUNITY_LIST];
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
   * @param {{signal?: AbortSignal}} _options
   */
  async listOpportunities(filters = {}, _options = {}) {
    let items = [...this.items];
    if (filters.region) items = items.filter((item) => item.region === filters.region);
    if (filters.manager) items = items.filter((item) => item.manager === filters.manager);
    if (filters.deal_stage) items = items.filter((item) => item.deal_stage === filters.deal_stage);
    if (filters.priority_band) {
      const b = String(filters.priority_band).toLowerCase();
      items = items.filter((item) => String(item.priority_band || "").toLowerCase() === b);
    }
    if (filters.q) {
      const qn = String(filters.q).toLowerCase();
      items = items.filter((item) => {
        const blob = [item.id, item.title, item.account, item.product]
          .filter(Boolean)
          .join(" ")
          .toLowerCase();
        return blob.includes(qn);
      });
    }
    const limit = filters.limit ?? 20;
    return { total: items.length, items: items.slice(0, limit) };
  }

  /**
   * @param {string} id
   * @param {{signal?: AbortSignal}} _options
   */
  async getOpportunity(id, _options = {}) {
    const item = this.items.find((candidate) => candidate.id === id);
    if (!item) throw new Error("Opportunity not found");
    return buildMockOpportunityDetail(item);
  }

  /**
   * @param {{signal?: AbortSignal}} _options
   */
  /**
   * @param {{signal?: AbortSignal}} _options
   */
  async getDashboardFilterOptions(_options = {}) {
    const offices = normalizeSortDedupeStrings(this.items.map((i) => i.region).filter(Boolean));
    const managers = normalizeSortDedupeStrings(this.items.map((i) => i.manager).filter(Boolean));
    const stages = normalizeSortDedupeStrings(this.items.map((i) => i.deal_stage).filter(Boolean));
    return {
      regional_offices: offices,
      managers,
      deal_stages: stages,
      regions: offices,
    };
  }

  /**
   * @param {{signal?: AbortSignal}} _options
   */
  async getDashboardKpis(_options = {}) {
    const n = this.items.length;
    const scores = this.items.map((i) => i.score);
    const avg = n ? scores.reduce((a, b) => a + b, 0) / n : 0;
    return {
      total_opportunities: n,
      open_opportunities: this.items.filter(
        (i) => i.deal_stage === "Engaging" || i.deal_stage === "Prospecting",
      ).length,
      won_opportunities: this.items.filter((i) => i.deal_stage === "Won").length,
      lost_opportunities: this.items.filter((i) => i.deal_stage === "Lost").length,
      avg_score: Math.round(avg * 100) / 100,
    };
  }
}
