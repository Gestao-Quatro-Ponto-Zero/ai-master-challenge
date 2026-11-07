/**
 * Motor de priorização do pipeline. Puro: sem I/O, testável e reaproveitável fora do app.
 *
 * Por que este desenho (detalhes em docs/scoring.md e analysis/04-05):
 * - Chance de ganhar NÃO entra no score: no backtest temporal, vendedor, produto, setor e
 *   idade tiveram AUC ~0,50 (igual a moeda). Fingir que diferenciam seria pontuar ruído.
 * - Valor (0-60): o preço é o que mais separa deals; escala log porque vai de US$ 55 a 26 mil.
 * - Momento (0-40): p(o deal se decidir nos próximos 30 dias | idade). AUC 0,66-0,87 fora da amostra.
 * - Zumbi: aberto há mais tempo que o maior ciclo que já fechou. Em 589 casos testados, 0 fecharam.
 */

export type Stage = "Prospecting" | "Engaging" | "Won" | "Lost";

export interface RawDeal {
  id: string;
  agent: string;
  product: string;
  account: string | null;
  stage: Stage;
  engageDate: string | null; // YYYY-MM-DD
  closeDate: string | null;
  closeValue: number | null;
}

export interface Model {
  today: string;
  maxCycleDays: number;
  /** decideCurve[idade] = p(decisão nos próximos HORIZON dias | deal ainda aberto nessa idade) */
  decideCurve: number[];
  globalWinRate: number;
  agentWinRate: Map<string, number>;
  prices: Record<string, number>;
  minLogPrice: number;
  maxLogPrice: number;
}

export type Status = "ativo" | "zumbi" | "prospeccao";
export type ReasonKind = "valor" | "momento" | "janela" | "zumbi" | "dados" | "prospeccao";
export type Tone = "pos" | "neg" | "neutro";

export interface Reason {
  kind: ReasonKind;
  tone: Tone;
  text: string;
}

export interface ScoredDeal {
  id: string;
  agent: string;
  product: string;
  account: string | null;
  status: Status;
  ageDays: number | null;
  daysLeft: number | null;
  daysOverCycle: number | null;
  price: number;
  pDecide: number | null;
  valuePts: number;
  momentumPts: number;
  score: number;
  reasons: Reason[];
  action: string;
}

export const HORIZON_DAYS = 30;
export const VALUE_WEIGHT = 60;
export const MOMENTUM_WEIGHT = 40;
/** A partir de quantos dias restantes no ciclo o deal entra em "janela fechando". */
export const WINDOW_ALERT_DAYS = 20;

const DAY_MS = 86_400_000;
const PRODUCT_ALIASES: Record<string, string> = { GTXPro: "GTX Pro" };

export function normalizeProduct(name: string): string {
  return PRODUCT_ALIASES[name] ?? name;
}

export function daysBetween(from: string, to: string): number {
  return Math.round((Date.parse(to) - Date.parse(from)) / DAY_MS);
}

const isClosed = (d: RawDeal) => (d.stage === "Won" || d.stage === "Lost") && d.engageDate && d.closeDate;

export function buildModel(
  deals: RawDeal[],
  prices: Record<string, number>,
  opts: { today?: string; minSample?: number } = {},
): Model {
  const minSample = opts.minSample ?? 30;
  const closed = deals.filter(isClosed);
  const durations = closed.map((d) => daysBetween(d.engageDate!, d.closeDate!));
  const maxCycleDays = Math.max(...durations);
  const today = opts.today ?? closed.map((d) => d.closeDate!).sort().at(-1)!;

  const decideCurve: number[] = [];
  let last = 0;
  for (let age = 0; age <= maxCycleDays; age++) {
    const alive = durations.filter((t) => t > age);
    if (alive.length >= minSample) {
      last = alive.filter((t) => t <= age + HORIZON_DAYS).length / alive.length;
    }
    decideCurve.push(last);
  }

  const wonCount = closed.filter((d) => d.stage === "Won").length;
  const byAgent = new Map<string, { won: number; total: number }>();
  for (const d of closed) {
    const s = byAgent.get(d.agent) ?? { won: 0, total: 0 };
    s.total++;
    if (d.stage === "Won") s.won++;
    byAgent.set(d.agent, s);
  }

  const logs = Object.values(prices).map(Math.log);
  return {
    today,
    maxCycleDays,
    decideCurve,
    globalWinRate: wonCount / closed.length,
    agentWinRate: new Map([...byAgent].map(([a, s]) => [a, s.won / s.total])),
    prices,
    minLogPrice: Math.min(...logs),
    maxLogPrice: Math.max(...logs),
  };
}

const usd = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "USD", maximumFractionDigits: 0 });
export const formatUSD = (v: number) => usd.format(v);
const pct = (p: number) => `${Math.round(p * 100)}%`;

function valuePoints(price: number, m: Model): number {
  const span = m.maxLogPrice - m.minLogPrice;
  if (span <= 0) return VALUE_WEIGHT;
  return Math.round((VALUE_WEIGHT * (Math.log(price) - m.minLogPrice)) / span);
}

function valueReason(price: number, product: string, pts: number): Reason {
  if (pts >= 40) return { kind: "valor", tone: "pos", text: `Ticket alto: ${formatUSD(price)} (${product})` };
  if (pts >= 20) return { kind: "valor", tone: "neutro", text: `Ticket médio: ${formatUSD(price)} (${product})` };
  return { kind: "valor", tone: "neg", text: `Ticket baixo: ${formatUSD(price)} (${product}). Só compensa se for rápido` };
}

function momentumReason(age: number, p: number): Reason {
  if (p >= 0.7)
    return { kind: "momento", tone: "pos", text: `Fase de decisão: ${pct(p)} dos deals com ${age} dias se resolveram no mês seguinte` };
  if (p >= 0.4)
    return { kind: "momento", tone: "neutro", text: `Decisão se aproximando: ${pct(p)} dos deals com ${age} dias se resolveram no mês seguinte` };
  return { kind: "momento", tone: "neg", text: `Ainda cedo: só ${pct(p)} dos deals com ${age} dias se resolveram no mês seguinte` };
}

function actionFor(status: Status, daysLeft: number | null, p: number | null): string {
  if (status === "zumbi") return "Confirmar se está vivo ou marcar como perdido";
  if (status === "prospeccao") return "Agendar o primeiro contato";
  if (daysLeft !== null && daysLeft <= WINDOW_ALERT_DAYS) return "Pedir a decisão esta semana";
  if (p !== null && p >= 0.7) return "Ligar hoje: fase de decisão";
  if (p !== null && p >= 0.4) return "Preparar a proposta";
  return "Manter a cadência";
}

export function scoreDeal(deal: RawDeal, m: Model): ScoredDeal {
  const product = normalizeProduct(deal.product);
  const price = m.prices[product] ?? 0;
  const valuePts = price > 0 ? valuePoints(price, m) : 0;
  const reasons: Reason[] = [];
  const base = { id: deal.id, agent: deal.agent, product, account: deal.account, price, valuePts };

  if (!deal.account) {
    reasons.push({ kind: "dados", tone: "neg", text: "Sem conta vinculada no CRM. Complete antes do contato" });
  }

  if (!deal.engageDate) {
    reasons.unshift(valueReason(price, product, valuePts), {
      kind: "prospeccao",
      tone: "neutro",
      text: "Ainda não engajado: sem tempo de ciclo para medir o momento",
    });
    return {
      ...base,
      status: "prospeccao",
      ageDays: null,
      daysLeft: null,
      daysOverCycle: null,
      pDecide: null,
      momentumPts: 0,
      score: valuePts,
      reasons,
      action: actionFor("prospeccao", null, null),
    };
  }

  const ageDays = daysBetween(deal.engageDate, m.today);

  if (ageDays > m.maxCycleDays) {
    const over = ageDays - m.maxCycleDays;
    reasons.unshift({
      kind: "zumbi",
      tone: "neg",
      text: `Aberto há ${ageDays} dias, ${over} além do maior ciclo que já fechou (${m.maxCycleDays}d). Nenhum deal assim fechou no histórico`,
    });
    return {
      ...base,
      status: "zumbi",
      ageDays,
      daysLeft: 0,
      daysOverCycle: over,
      pDecide: null,
      momentumPts: 0,
      score: 0,
      reasons,
      action: actionFor("zumbi", 0, null),
    };
  }

  const pDecide = m.decideCurve[Math.max(0, ageDays)] ?? 0;
  const momentumPts = Math.round(MOMENTUM_WEIGHT * pDecide);
  const daysLeft = m.maxCycleDays - ageDays;
  reasons.unshift(valueReason(price, product, valuePts), momentumReason(ageDays, pDecide));
  if (daysLeft <= WINDOW_ALERT_DAYS) {
    reasons.push({
      kind: "janela",
      tone: "neg",
      text: `Faltam ${daysLeft} dias para passar do maior ciclo que já fechou (${m.maxCycleDays}d)`,
    });
  }

  return {
    ...base,
    status: "ativo",
    ageDays,
    daysLeft,
    daysOverCycle: null,
    pDecide,
    momentumPts,
    score: valuePts + momentumPts,
    reasons,
    action: actionFor("ativo", daysLeft, pDecide),
  };
}

const STATUS_ORDER: Record<Status, number> = { ativo: 0, zumbi: 1, prospeccao: 2 };

export function rankPipeline(deals: RawDeal[], m: Model): ScoredDeal[] {
  return deals
    .filter((d) => d.stage === "Engaging" || d.stage === "Prospecting")
    .map((d) => scoreDeal(d, m))
    .sort(
      (a, b) =>
        STATUS_ORDER[a.status] - STATUS_ORDER[b.status] ||
        (a.status === "ativo" ? b.score - a.score : b.price - a.price) ||
        // Empate: quem tem menos tempo restante no ciclo vem primeiro (é agora ou nunca).
        (a.daysLeft ?? Infinity) - (b.daysLeft ?? Infinity) ||
        a.id.localeCompare(b.id),
    );
}
