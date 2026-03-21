export function buildMockOpportunityDetail(item) {
  return {
    id: item.id,
    title: item.title,
    seller: item.seller,
    manager: item.manager,
    region: item.region,
    deal_stage: item.deal_stage,
    amount: item.amount,
    account: item.account ?? item.title,
    product: item.product ?? "",
    sales_agent: item.sales_agent ?? item.seller,
    regional_office: item.regional_office ?? item.region,
    close_value: item.close_value ?? item.amount,
    engage_date: "",
    close_date: null,
    product_series: "GTX",
    scoreExplanation: {
      score: item.score,
      priority_band: "medium",
      positive_factors: ["modo mock ativo — use a API real para dados do challenge."],
      negative_factors: [],
      risk_flags: [],
      next_action: "agendar contato",
    },
  };
}
