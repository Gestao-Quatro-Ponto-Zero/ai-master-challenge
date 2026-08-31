export const REFERENCE_DATE = new Date('2017-12-31T00:00:00Z');

const PRODUCT_CLOCK_MIN_SAMPLE = 30;
const REGIONAL_HISTORY_MIN_SAMPLE = 30;
const RECOVERY_REGION_MIN_SAMPLE = 30;
const RECOVERY_SELLER_MIN_SAMPLE = 15;
const clamp = (value, min = 0, max = 100) => Math.min(max, Math.max(min, value));
const round = (value, digits = 0) => Number(value.toFixed(digits));
const dateValue = (value) => {
  if (!value) return null;
  if (value instanceof Date) return new Date(Date.UTC(value.getUTCFullYear(), value.getUTCMonth(), value.getUTCDate()));
  return new Date(`${String(value).slice(0, 10)}T00:00:00Z`);
};
const dayDifference = (later, earlier) => Math.round((later - earlier) / 86_400_000);

function percentile(values, ratio) {
  if (!values.length) return null;
  const sorted = [...values].sort((a, b) => a - b);
  const position = (sorted.length - 1) * ratio;
  const lower = Math.floor(position);
  const upper = Math.ceil(position);
  if (lower === upper) return sorted[lower];
  return sorted[lower] + (sorted[upper] - sorted[lower]) * (position - lower);
}

function buildProductClocks(wins) {
  const allDurations = [];
  const durationsByProduct = new Map();
  wins.forEach((row) => {
    const engageDate = dateValue(row.engage_date);
    const closeDate = dateValue(row.close_date);
    if (!engageDate || !closeDate) return;
    const duration = dayDifference(closeDate, engageDate);
    if (duration < 0) return;
    allDurations.push(duration);
    const current = durationsByProduct.get(row.product) ?? [];
    current.push(duration);
    durationsByProduct.set(row.product, current);
  });

  const fallback = {
    sampleSize: allDurations.length,
    medianDays: Math.round(percentile(allDurations, .5) ?? 60),
    p90Days: Math.round(percentile(allDurations, .9) ?? 106),
    usedFallback: true,
    sourceScope: 'global',
  };
  const clocks = new Map();
  durationsByProduct.forEach((durations, product) => {
    clocks.set(product, durations.length >= PRODUCT_CLOCK_MIN_SAMPLE ? {
      sampleSize: durations.length,
      medianDays: Math.round(percentile(durations, .5)),
      p90Days: Math.round(percentile(durations, .9)),
      usedFallback: false,
      sourceScope: 'product',
    } : { ...fallback, sourceSampleSize: durations.length });
  });
  return { clocks, fallback };
}

function buildRegionalProductClocks(wins, productClocks, fallbackClock) {
  const durationsByContext = new Map();
  wins.forEach((row) => {
    const engageDate = dateValue(row.engage_date);
    const closeDate = dateValue(row.close_date);
    if (!engageDate || !closeDate) return;
    const duration = dayDifference(closeDate, engageDate);
    if (duration < 0) return;
    const key = `${row.product}||${row.regional_office}`;
    const current = durationsByContext.get(key) ?? { product: row.product, regional_office: row.regional_office, durations: [] };
    current.durations.push(duration);
    durationsByContext.set(key, current);
  });

  const clocks = new Map();
  durationsByContext.forEach(({ product, regional_office: region, durations }, key) => {
    if (durations.length >= PRODUCT_CLOCK_MIN_SAMPLE) {
      clocks.set(key, {
        product,
        regional_office: region,
        sampleSize: durations.length,
        regionalSampleSize: durations.length,
        medianDays: Math.round(percentile(durations, .5)),
        p90Days: Math.round(percentile(durations, .9)),
        usedFallback: false,
        sourceScope: 'region',
      });
      return;
    }
    const fallback = productClocks.get(product) ?? fallbackClock;
    clocks.set(key, { ...fallback, product, regional_office: region, regionalSampleSize: durations.length, usedFallback: true });
  });
  return clocks;
}

function buildProductHistory(closed, baseline) {
  const groups = new Map();
  closed.forEach((row) => {
    const current = groups.get(row.product) ?? { wins: 0, total: 0 };
    current.total += 1;
    if (row.deal_stage === 'Won') current.wins += 1;
    groups.set(row.product, current);
  });
  return new Map([...groups].map(([product, group]) => [product, {
    ...group,
    rate: group.total ? group.wins / group.total : baseline,
  }]));
}

function buildPerformanceHistory(closed, fields) {
  const groups = new Map();
  closed.forEach((row) => {
    const key = fields.map((field) => row[field]).join('||');
    const current = groups.get(key) ?? { total: 0, wins: 0, ...Object.fromEntries(fields.map((field) => [field, row[field]])) };
    current.total += 1;
    if (row.deal_stage === 'Won') current.wins += 1;
    groups.set(key, current);
  });
  groups.forEach((group) => { group.rate = group.total ? group.wins / group.total : 0; });
  return groups;
}

const performanceKey = (...values) => values.join('||');

function buildValuePoints(rows) {
  const prices = [...new Set(rows.map((row) => Number(row.sales_price)))].sort((a, b) => a - b);
  return new Map(prices.map((price, index) => [price, Math.round(10 + (prices.length === 1 ? .5 : index / (prices.length - 1)) * 30)]));
}

function momentFor(row, ageDays, clock) {
  if (row.deal_stage === 'Prospecting') return { points: 10, status: 'Em Prospecting', detail: 'A oportunidade está em Prospecting. Como não há informação de tempo nesse estágio, recebe 10 de 20 pontos de Momento.' };
  if (ageDays === null) return { points: 0, status: 'Sem data', detail: 'Sem data de Engaging, o momento recebe 0 de 20 pontos.' };
  const sourceDetail = clock.sourceScope === 'region'
    ? `Referência calculada com ${clock.sampleSize} vendas realizadas de ${row.product} na região ${row.regional_office}.`
    : `Há apenas ${clock.regionalSampleSize ?? 0} vendas realizadas de ${row.product} com datas válidas na região ${row.regional_office}; por isso, usamos ${clock.sourceScope === 'product' ? 'o ciclo geral do produto' : 'o ciclo geral de vendas'}.`;
  if (ageDays <= clock.medianDays) return { points: 20, status: 'No melhor momento', detail: `Está em negociação há ${ageDays} dias. Metade das vendas realizadas acontece em até ${clock.medianDays} dias. ${sourceDetail}` };
  if (ageDays <= clock.p90Days) return { points: 10, status: 'Mais lento que o normal', detail: `Está em negociação há ${ageDays} dias. Normalmente, 90% das vendas realizadas acontecem em até ${clock.p90Days} dias. ${sourceDetail}` };
  return { points: 0, status: 'Fora do tempo esperado', detail: `Está em negociação há ${ageDays} dias. Normalmente, 90% das vendas realizadas acontecem em até ${clock.p90Days} dias. Esse tempo já foi ultrapassado. ${sourceDetail}` };
}

function actionFor(row, ageDays, clock) {
  if (row.deal_stage === 'Prospecting') return {
    key: 'Definir próximo passo',
    label: 'Definir próximo passo',
    instruction: 'Revisar a oportunidade, confirmar o estágio atual e registrar o próximo passo comercial',
  };
  if (ageDays === null) return { key: 'Completar dados', label: 'Completar dados', instruction: 'Corrigir a data de Engaging e validar se a oportunidade continua ativa' };
  const accountStep = row.account ? '' : 'Identificar a conta e ';
  if (ageDays > clock.p90Days * 1.3) return { key: 'Requalificar ou encerrar', label: 'Requalificar ou encerrar', instruction: `${accountStep}confirmar intenção e prazo; sem compromisso real, corrigir o estágio ou encerrar` };
  if (ageDays > clock.p90Days) return { key: 'Reengajar hoje', label: 'Reengajar hoje', instruction: `${accountStep}retomar o contato hoje e registrar um compromisso com data` };
  return { key: 'Avançar agora', label: 'Avançar agora', instruction: `${accountStep}confirmar o próximo compromisso e avançar a oportunidade` };
}

function scoreBand(score) {
  if (score >= 70) return 'Alto';
  if (score >= 50) return 'Médio';
  return 'Baixo';
}

function accountHistoryFor(wins) {
  const history = new Map();
  wins.forEach((row) => {
    if (!row.account) return;
    const current = history.get(row.account) ?? { wins: 0, lastWin: null, series: new Set(), value: 0 };
    const closedAt = dateValue(row.close_date);
    current.wins += 1;
    current.value += Number(row.close_value ?? 0);
    current.series.add(row.series);
    if (closedAt && (!current.lastWin || closedAt > current.lastWin)) current.lastWin = closedAt;
    history.set(row.account, current);
  });
  return history;
}

export function buildScoringModel(rows) {
  const closed = rows.filter((row) => row.deal_stage === 'Won' || row.deal_stage === 'Lost');
  const wins = closed.filter((row) => row.deal_stage === 'Won');
  const baseline = closed.length ? wins.length / closed.length : .5;
  const productHistory = buildProductHistory(closed, baseline);
  const sellerProductHistory = buildPerformanceHistory(closed, ['product', 'sales_agent']);
  const regionProductHistory = buildPerformanceHistory(closed, ['product', 'regional_office']);
  const valuePointsByPrice = buildValuePoints(rows);
  const { clocks: productClocks, fallback: fallbackClock } = buildProductClocks(wins);
  const regionalProductClocks = buildRegionalProductClocks(wins, productClocks, fallbackClock);
  const accountHistory = accountHistoryFor(wins);
  const agentContext = new Map(rows.map((row) => [row.sales_agent, { manager: row.manager, regional_office: row.regional_office }]));

  function scoreOpen(row) {
    const engageDate = dateValue(row.engage_date);
    const ageDays = engageDate ? dayDifference(REFERENCE_DATE, engageDate) : null;
    const productHistoryItem = productHistory.get(row.product) ?? { wins: 0, total: 0, rate: baseline };
    const regionalHistoryItem = regionProductHistory.get(performanceKey(row.product, row.regional_office));
    const usesRegionalHistory = Boolean(regionalHistoryItem && regionalHistoryItem.total >= REGIONAL_HISTORY_MIN_SAMPLE);
    const history = usesRegionalHistory ? regionalHistoryItem : productHistoryItem;
    const price = Number(row.sales_price);
    const valuePoints = valuePointsByPrice.get(price) ?? 10;
    const historyPoints = Math.round(history.rate * 40);
    const productClock = productClocks.get(row.product) ?? fallbackClock;
    const baseClock = regionalProductClocks.get(performanceKey(row.product, row.regional_office)) ?? { ...productClock, product: row.product, regional_office: row.regional_office, regionalSampleSize: 0, usedFallback: true };
    const clock = { ...baseClock, ageDays };
    const moment = momentFor(row, ageDays, clock);
    const focusScore = valuePoints + historyPoints + moment.points;
    const focusBand = scoreBand(focusScore);
    const action = actionFor(row, ageDays, clock);

    const valueDescription = valuePoints >= 35 ? 'tem alto valor de catálogo' : valuePoints >= 25 ? 'tem valor de catálogo intermediário' : 'tem menor valor de catálogo';
    const scoreExplanation = [
      { key: 'value', label: 'Valor', points: valuePoints, max: 40, detail: `${row.product} ${valueDescription} (US$ ${price.toLocaleString('en-US')}).` },
      { key: 'history', label: 'Histórico', points: historyPoints, max: 40, detail: usesRegionalHistory
        ? `De ${history.total} oportunidades encerradas de ${row.product} na região ${row.regional_office}, ${Math.round(history.rate * 100)}% resultaram em vendas realizadas.`
        : `Há apenas ${regionalHistoryItem?.total ?? 0} oportunidades encerradas de ${row.product} na região ${row.regional_office}. Por isso, usamos o histórico geral do produto: ${Math.round(productHistoryItem.rate * 100)}% de ${productHistoryItem.total} resultaram em vendas realizadas.` },
      { key: 'moment', label: 'Momento', points: moment.points, max: 20, detail: moment.detail },
    ];
    const strongest = [...scoreExplanation].sort((a, b) => (b.points / b.max) - (a.points / a.max))[0];
    const reasons = [
      { tone: moment.points === 0 ? 'warning' : 'data', text: moment.detail },
      { tone: 'positive', text: `${strongest.label} é o principal impulsionador: ${strongest.points} de ${strongest.max} pontos.` },
    ];

    const account = accountHistory.get(row.account);
    return {
      ...row,
      age_days: ageDays,
      focus_score: focusScore,
      focus_band: focusBand,
      priority_score: focusScore,
      potential_score: focusScore,
      potential_band: focusBand,
      chance_score: round(history.rate * 100, 1),
      value_score: valuePoints,
      timing_score: moment.points,
      expected_revenue: round(price * history.rate, 2),
      action_key: action.key,
      action_label: action.label,
      recommended_action: action.instruction,
      timing_status: moment.status,
      product_clock: clock,
      history_scope: usesRegionalHistory ? 'region' : 'product_fallback',
      history_sample: history.total,
      reasons,
      score_explanation: scoreExplanation,
      contributions: { value: valuePoints, history: historyPoints, timing: moment.points },
      account_history: account ? { wins: account.wins, recencyDays: dayDifference(REFERENCE_DATE, account.lastWin), seriesCount: account.series.size, wonValue: round(account.value, 2) } : null,
    };
  }

  const open = rows.filter((row) => row.deal_stage === 'Prospecting' || row.deal_stage === 'Engaging')
    .map(scoreOpen)
    .sort((a, b) => b.focus_score - a.focus_score || b.expected_revenue - a.expected_revenue);
  const byId = new Map(open.map((row) => [row.opportunity_id, row]));

  const recovery = rows.filter((row) => row.deal_stage === 'Lost' && row.account && row.close_date).map((row) => {
    const lossDate = dateValue(row.close_date);
    const daysSinceLoss = dayDifference(REFERENCE_DATE, lossDate);
    const laterSameProductWin = wins.some((won) => won.account === row.account && won.product === row.product && dateValue(won.close_date) > lossDate);
    const history = productHistory.get(row.product) ?? { rate: baseline };
    const price = Number(row.sales_price);
    const valuePoints = valuePointsByPrice.get(price) ?? 10;
    const recencyPoints = Math.round(clamp(40 - (daysSinceLoss / 90) * 40, 0, 40));
    const historyPoints = Math.round(history.rate * 20);
    const currentSeller = sellerProductHistory.get(performanceKey(row.product, row.sales_agent));
    const currentRegion = regionProductHistory.get(performanceKey(row.product, row.regional_office));
    const currentSellerRate = currentSeller?.total >= RECOVERY_SELLER_MIN_SAMPLE ? currentSeller.rate : history.rate;
    const currentRegionRate = currentRegion?.total >= RECOVERY_REGION_MIN_SAMPLE ? currentRegion.rate : history.rate;
    const currentContextRate = currentSellerRate * .7 + currentRegionRate * .3;

    const candidates = [...sellerProductHistory.values()].filter((candidate) => (
      candidate.product === row.product
      && candidate.sales_agent !== row.sales_agent
      && candidate.total >= RECOVERY_SELLER_MIN_SAMPLE
    )).map((candidate) => {
      const context = agentContext.get(candidate.sales_agent);
      const region = context ? regionProductHistory.get(performanceKey(row.product, context.regional_office)) : null;
      if (!context || !region || region.total < RECOVERY_REGION_MIN_SAMPLE) return null;
      if (context.regional_office !== row.regional_office) return null;
      return { ...candidate, ...context, region_rate: region.rate, region_sample: region.total, context_rate: candidate.rate * .7 + region.rate * .3 };
    }).filter(Boolean).sort((a, b) => b.context_rate - a.context_rate || b.total - a.total);

    const bestCandidate = candidates[0];
    const improvement = bestCandidate ? bestCandidate.context_rate - currentContextRate : 0;
    const shouldRedistribute = Boolean(bestCandidate && improvement >= .05);
    const redistribution = shouldRedistribute ? {
      recommended: true,
      seller: bestCandidate.sales_agent,
      manager: bestCandidate.manager,
      region: bestCandidate.regional_office,
      seller_rate: round(bestCandidate.rate * 100, 1),
      seller_sample: bestCandidate.total,
      region_rate: round(bestCandidate.region_rate * 100, 1),
      region_sample: bestCandidate.region_sample,
      improvement_pp: round(improvement * 100, 1),
      action: `Redistribuir para ${bestCandidate.sales_agent}`,
      reason: `${bestCandidate.sales_agent} realizou vendas em ${Math.round(bestCandidate.rate * 100)}% de ${bestCandidate.total} oportunidades de ${row.product}; a região ${bestCandidate.regional_office} realizou vendas em ${Math.round(bestCandidate.region_rate * 100)}% de ${bestCandidate.region_sample}.`,
    } : {
      recommended: false,
      action: 'Reativar com a equipe atual',
      reason: 'Não há outro vendedor com melhora relevante e amostra suficiente para recomendar uma redistribuição.',
    };

    const recoveryExplanation = [
      { key: 'value', label: 'Valor', points: valuePoints, max: 40, detail: `${row.product} vale US$ ${price.toLocaleString('en-US')}.` },
      { key: 'recency', label: 'Recência', points: recencyPoints, max: 40, detail: `A oportunidade foi perdida há ${daysSinceLoss} dias; perdas mais recentes recebem mais pontos.` },
      { key: 'history', label: 'Histórico', points: historyPoints, max: 20, detail: `${Math.round(history.rate * 100)}% das oportunidades encerradas deste produto resultaram em vendas realizadas.` },
    ];
    return {
      ...row,
      days_since_loss: daysSinceLoss,
      later_same_product_win: laterSameProductWin,
      recovery_score: valuePoints + recencyPoints + historyPoints,
      recovery_explanation: recoveryExplanation,
      redistribution,
      action_label: shouldRedistribute ? 'Redistribuir oportunidade' : 'Reativar oportunidade',
      recommended_action: shouldRedistribute ? `${redistribution.action} e revisar a abordagem antes do novo contato` : 'Revisar a perda e validar uma nova abordagem antes de entrar em contato',
    };
  }).filter((row) => row.days_since_loss >= 0 && row.days_since_loss <= 90 && !row.later_same_product_win)
    .sort((a, b) => b.recovery_score - a.recovery_score);

  return { baseline: round(baseline * 100, 1), open, byId, recovery, productClocks, regionalProductClocks };
}

export function applyScope(rows, role, profile) {
  if (role === 'seller') return rows.filter((row) => row.sales_agent === profile);
  if (role === 'manager') return rows.filter((row) => row.manager === profile);
  return rows;
}
