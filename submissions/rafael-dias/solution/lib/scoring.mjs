export const REFERENCE_DATE = "2017-12-31";
export const normalizeProduct = (value) =>
  value === "GTXPro" ? "GTX Pro" : value;
export function daysBetween(start, end) {
  return Math.floor((Date.parse(end) - Date.parse(start)) / 86400000);
}
export function median(values) {
  if (!values.length) return null;
  const sorted = [...values].sort((a, b) => a - b),
    middle = Math.floor(sorted.length / 2);
  return sorted.length % 2
    ? sorted[middle]
    : (sorted[middle - 1] + sorted[middle]) / 2;
}
// Outcomes are used only for reference durations; never for deal-level points.
export function buildReferences(pipeline, asOf = REFERENCE_DATE) {
  const history = pipeline.filter(
    (d) =>
      ["Won", "Lost"].includes(d.deal_stage) &&
      d.close_date &&
      d.close_date <= asOf &&
      d.engage_date &&
      daysBetween(d.engage_date, d.close_date) >= 0,
  );
  const globalMedian = median(
    history.map((d) => daysBetween(d.engage_date, d.close_date)),
  );
  return Object.fromEntries(
    [...new Set(pipeline.map((d) => normalizeProduct(d.product)))].map(
      (product) => {
        const rows = history.filter(
          (d) => normalizeProduct(d.product) === product,
        );
        return [
          product,
          {
            days:
              rows.length >= 30
                ? median(
                    rows.map((d) => daysBetween(d.engage_date, d.close_date)),
                  )
                : globalMedian,
            count: rows.length,
            fallback: rows.length < 30,
          },
        ];
      },
    ),
  );
}
export function scoreDeal(deal, product, reference, asOf = REFERENCE_DATE) {
  if (!["Engaging", "Prospecting"].includes(deal.deal_stage)) return null;
  if (deal.engage_date && deal.engage_date > asOf) return null;
  const age = deal.engage_date ? daysBetween(deal.engage_date, asOf) : null;
  const stagePoints = deal.deal_stage === "Engaging" ? 40 : 20;
  // Log scale limits the dominance of the most expensive catalog item.
  const potentialPoints =
    product?.sales_price > 0
      ? Math.round(
          30 * Math.min(1, Math.log1p(product.sales_price) / Math.log1p(26768)),
        )
      : 0;
  const ratio =
    age !== null && reference?.days > 0 ? age / reference.days : null;
  // Long-running deals enter a review queue; they are not assigned a probability of loss.
  const timingPoints =
    ratio === null ? 0 : ratio <= 1 ? 30 : ratio <= 2 ? 20 : 10;
  const review = ratio !== null && ratio > 2;
  const action = !deal.account
    ? "Identificar a conta e validar o contexto"
    : deal.deal_stage === "Prospecting"
      ? "Qualificar necessidade e próximo passo"
      : review
        ? "Revisar viabilidade e combinar próximo passo"
        : "Confirmar próximo passo da negociação";
  return {
    score: stagePoints + potentialPoints + timingPoints,
    age,
    review,
    action,
    factors: [
      {
        label:
          deal.deal_stage === "Engaging"
            ? "Negociação iniciada"
            : "Em prospecção",
        points: stagePoints,
        max: 40,
      },
      {
        label: "Potencial pelo preço de catálogo",
        points: potentialPoints,
        max: 30,
      },
      {
        label:
          ratio === null
            ? "Sem data de negociação"
            : review
              ? "Ciclo longo: requer revisão"
              : ratio > 1
                ? "Acima do ciclo típico"
                : "Dentro do ciclo típico",
        points: timingPoints,
        max: 30,
      },
    ],
    warnings: [
      ...(!deal.account
        ? ["Conta não informada; isso não reduz os pontos."]
        : []),
      ...(age === null ? ["Sem data para avaliar o tempo de negociação."] : []),
      ...(reference?.fallback
        ? ["Pouco histórico do produto; referência geral utilizada."]
        : []),
    ],
  };
}
