import type { ScoreResult } from '@/types/csv';
import { daysBetween } from './csv-utils';

interface DealForScoring {
  deal_stage: string;
  engage_date: string;
  est_value: number;
  account: string;
}

export function calcPriorityScore(
  deal: DealForScoring,
  referenceDate: Date,
  teamAvgDays: number,
  portfolioMaxValue: number
): ScoreResult {
  const daysInStage = daysBetween(deal.engage_date, referenceDate);

  const CONTACT_THRESHOLD = 14;
  const d1 = Math.min(25, (daysInStage / CONTACT_THRESHOLD) * 25);

  const avg = teamAvgDays > 0 ? teamAvgDays : daysInStage;
  const d2 = Math.min(25, (daysInStage / avg) * 25);

  const p90 = portfolioMaxValue > 0 ? portfolioMaxValue : deal.est_value;
  const d3 = p90 > 0 ? Math.min(20, (deal.est_value / p90) * 20) : 10;

  const d4 = deal.deal_stage === 'Engaging' ? 20 : 10;

  const daysOver = Math.max(0, daysInStage - teamAvgDays);
  const d5 = Math.min(10, (daysOver / 7) * 10);

  const score = Math.min(100, Math.round(d1 + d2 + d3 + d4 + d5));

  const label: ScoreResult['label'] =
    score >= 85 ? 'Crítico' :
    score >= 70 ? 'Alto' :
    score >= 55 ? 'Médio' : 'Baixo';

  const drivers = [
    { value: d1, text: `${daysInStage} dias sem contato` },
    { value: d2, text: `${daysInStage}d no stage` },
    { value: d3, text: 'Alto valor' },
    { value: d4, text: deal.deal_stage },
    { value: d5, text: `${Math.round(daysOver)}d acima da média` },
  ];
  const primaryDriver = drivers.reduce((a, b) => a.value >= b.value ? a : b);
  const valueStr = deal.est_value >= 1000
    ? `$${(deal.est_value / 1000).toFixed(1)}K`
    : `$${deal.est_value.toFixed(0)}`;
  const context_reason = `${primaryDriver.text} · ${deal.deal_stage} · ${valueStr}`;

  return { score, label, context_reason, breakdown: { d1, d2, d3, d4, d5 } };
}
