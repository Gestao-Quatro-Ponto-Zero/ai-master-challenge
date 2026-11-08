import type { BandKey, Deal, Reason, TabKey } from '../types';
import { MOCK_SUGGESTED_ACTIONS, MOCK_THRESHOLDS, mockConfidenceReason, mockDataQuality, mockPriorityLabel } from './rules';
import { money } from '../../lib/format';

/** Data "de hoje" do exemplo. O dataset é de 2016–2017, então o relógio é simulado. */
export const REFERENCE_DATE = '2017-12-31';

// [id, faixa, produto, estágio, idade em dias (null = sem data), score (null = sem prioridade),
//  chance, efeito do histórico, efeito do momento recente, efeito da carga]
type Row = [string, TabKey, string, string, number | null, number | null, number, number, number, number];

const ROWS: Row[] = [
  ['4SOUOUKH', 'focus', 'GTX Plus Pro', 'Engaging', 92, 94, 0.7, 30, 12, -9],
  ['E2CJIO85', 'focus', 'GTX Plus Pro', 'Engaging', 89, 94, 0.7, 30, 12, -9],
  ['X7MN9ROG', 'focus', 'GTX Plus Pro', 'Engaging', 69, 94, 0.7, 30, 12, -9],
  ['DYYJW46L', 'focus', 'GTX Plus Pro', 'Engaging', 78, 94, 0.69, 30, 12, -9],
  ['6JBM1ZKO', 'focus', 'GTX Pro', 'Engaging', 52, 87, 0.7, 26, 9, -7],

  ['DY8DMZZ9', 'decide', 'GTX Plus Pro', 'Engaging', 106, 95, 0.7, 22, 8, -8],
  ['6SMB6SDY', 'decide', 'GTX Pro', 'Engaging', 138, 87, 0.71, 15, -10, -6],
  ['MAH5U65E', 'decide', 'MG Advanced', 'Engaging', 135, 64, 0.66, 10, 6, -14],
  ['Y3AAS62P', 'decide', 'GTX Plus Basic', 'Engaging', 110, 58, 0.7, 8, -6, -5],
  ['P6NQ2LZK', 'decide', 'GTX Basic', 'Engaging', 130, 40, 0.72, -12, 10, -7],
  ['RTX8ZJXT', 'decide', 'GTX Basic', 'Engaging', 122, 40, 0.72, 8, -6, -5],

  ['2FM8HJDM', 'follow', 'MG Advanced', 'Engaging', 102, 64, 0.65, 12, 8, -12],
  ['3Q15OHQB', 'follow', 'MG Advanced', 'Engaging', 99, 63, 0.65, -14, 8, -12],
  ['31IV2B9O', 'follow', 'GTX Basic', 'Engaging', 66, 39, 0.71, 14, 6, -5],
  ['PV3TH2FF', 'follow', 'MG Special', 'Engaging', 38, 19, 0.72, 8, 6, -4],
  ['D9MZMDOL', 'follow', 'MG Special', 'Engaging', 102, 18, 0.72, 8, -6, -4],
  ['LZ3B174J', 'follow', 'MG Special', 'Engaging', 93, 18, 0.72, 8, 6, -4],

  ['K8P2WQ1A', 'prospecting', 'GTK 500', 'Prospecting', null, null, 0.63, 0, 0, 0],
  ['Z4TN7HXE', 'prospecting', 'GTX Pro', 'Prospecting', null, null, 0.63, 0, 0, 0],
  ['B1VY93MD', 'prospecting', 'MG Advanced', 'Prospecting', null, null, 0.63, 0, 0, 0],

  ['Y6UBZM6P', 'review', 'GTX Plus Pro', 'Engaging', 356, null, 0.71, -10, -6, -8],
  ['IGHYUSN8', 'review', 'GTX Plus Pro', 'Engaging', 239, null, 0.71, -10, -6, -8],
  ['VMIAO42Z', 'review', 'GTX Plus Pro', 'Engaging', 247, null, 0.71, -10, -6, -8],
  ['ZK4S74FD', 'review', 'GTX Plus Pro', 'Engaging', 220, null, 0.71, -10, -6, -8],
  ['C6TQMD3C', 'review', 'GTX Plus Pro', 'Engaging', 207, null, 0.71, -10, -6, -8],
  ['2FNTCPOU', 'review', 'GTX Plus Pro', 'Engaging', 189, null, 0.71, -10, -6, -8],
];

const PRICE: Record<string, number> = {
  'GTK 500': 26768,
  'GTX Plus Pro': 5482,
  'GTX Pro': 4821,
  'MG Advanced': 3393,
  'GTX Plus Basic': 1096,
  'GTX Basic': 550,
  'MG Special': 55,
};

const ACCOUNTS = [
  'Nordwind Ltda',
  'Kestrel Systems',
  'Bluepeak Co.',
  'Orion Retail',
  'Lumen Foods',
  'Tallis Group',
  'Verde Logística',
  'Pallas Health',
];

export function hash(s: string): number {
  let h = 7;
  for (let i = 0; i < s.length; i++) h = (h * 31 + s.charCodeAt(i)) >>> 0;
  return h;
}

function buildReasons(row: Row, price: number): Reason[] {
  const [, , , stage, age, , , hist, recent, load] = row;
  const ticket: Reason = {
    long: 'Ticket do produto: ' + money(price),
    short: price >= 3000 ? 'Alto ticket' : price >= 1000 ? 'Ticket médio' : 'Ticket baixo',
    direction: price >= 1000 ? 'pos' : 'neg',
    weight: Math.max(4, Math.min(95, Math.round(price / 300))),
  };
  if (stage === 'Prospecting') {
    const base: Reason = {
      long: 'Taxa de vitória do produto',
      short: 'Sem histórico do deal: usa a taxa do produto',
      direction: 'neu',
      weight: 60,
    };
    return [base, ticket].sort((a, b) => b.weight - a.weight);
  }
  const out: Reason[] = [ticket];
  if (hist) {
    out.push({
      long: 'Histórico do vendedor com este produto',
      short: hist > 0 ? 'Bom histórico com o produto' : 'Histórico fraco com o produto',
      direction: hist > 0 ? 'pos' : 'neg',
      weight: Math.abs(hist),
    });
  }
  if (recent) {
    out.push({
      long: 'Desempenho recente do vendedor (90 dias)',
      short: recent > 0 ? 'Bom momento recente' : 'Momento recente fraco',
      direction: recent > 0 ? 'pos' : 'neg',
      weight: Math.abs(recent),
    });
  }
  if (load) {
    out.push({
      long: 'Quantidade de deals abertos ao mesmo tempo',
      short: 'Pipeline muito cheio',
      direction: 'neg',
      weight: Math.abs(load),
    });
  }
  if (age !== null) {
    const long = 'Tempo no funil: ' + age + ' dias';
    if (age <= 30) out.push({ long, short: 'Deal recente', direction: 'pos', weight: 12 });
    else if (age <= MOCK_THRESHOLDS.staleDays) {
      out.push({ long, short: 'Há ' + age + ' dias no funil', direction: 'neu', weight: 6 });
    } else if (age <= MOCK_THRESHOLDS.reviewDays) {
      out.push({ long, short: 'Passou do prazo típico', direction: 'warn', weight: 22 });
    } else {
      out.push({ long, short: 'Mais antigo que todo deal fechado', direction: 'warn', weight: 40 });
    }
  }
  return out.sort((a, b) => b.weight - a.weight);
}

function buildDeal(row: Row): Deal {
  const [id, tab, product, stage, age, score, probability, hist] = row;
  const price = PRICE[product];
  const prospecting = stage === 'Prospecting';
  const band: BandKey =
    tab === 'decide'
      ? 'stale_risk'
      : tab === 'follow'
        ? score !== null && score >= MOCK_THRESHOLDS.followUpScore
          ? 'follow_up'
          : 'low'
        : tab;

  const h = hash(id);
  // A conta é exemplo: só ~32% dos deals reais têm conta.
  const account = prospecting || (age ?? 0) % 2 === 0 ? null : ACCOUNTS[h % ACCOUNTS.length];

  const lowConfidence = prospecting || hist < 0;

  return {
    id,
    tab,
    band,
    product,
    stage,
    ageDays: age,
    score,
    priorityLevel: mockPriorityLabel(score),
    probability,
    price,
    expectedValue: probability * price,
    account,
    suggestedAction: MOCK_SUGGESTED_ACTIONS[band],
    confidence: lowConfidence ? 'low' : 'medium',
    confidenceReason: mockConfidenceReason(lowConfidence ? 'low' : 'medium', prospecting),
    dataQuality: mockDataQuality(account),
    reasons: buildReasons(row, price),
  };
}

export function buildSeedDeals(): Deal[] {
  return ROWS.map(buildDeal);
}
