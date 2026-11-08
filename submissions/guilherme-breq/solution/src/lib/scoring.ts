/**
 * Motor de priorização do pipeline. Puro: sem I/O, testável e reaproveitável fora do app.
 *
 * Por que este desenho (detalhes em docs/scoring.md e analysis/04-06):
 * - Chance de ganhar NÃO entra no score: no backtest temporal, vendedor, produto, setor e
 *   idade tiveram AUC ~0,50 (igual a moeda). Fingir que diferenciam seria pontuar ruído.
 * - Valor (0-60): o preço é o que mais separa deals; escala log porque vai de US$ 55 a 26 mil.
 * - Momento (0-40): p(o deal se decidir nos próximos 30 dias | idade), estimada por Kaplan-Meier
 *   (deals ainda abertos entram como censurados). AUC média 0,65 fora da amostra, bem calibrada.
 *   Normalizada pelo pico da curva: 40 pts = a idade em que mais deals se decidem.
 * - Zumbi: aberto há mais tempo que o maior ciclo que já fechou (corte heurístico). Dos 411 deals
 *   que estavam nessa situação em datas passadas, nenhum fechou até o fim dos dados.
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
  /** decideCurve[idade] = p(decisão nos próximos HORIZON_DAYS dias | deal ainda aberto nessa idade) */
  decideCurve: number[];
  /** Maior valor da curva e a idade em que ele ocorre. */
  peakDecide: number;
  peakAge: number;
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
/** Faixas do momento relativo ao pico (p / pico). */
const HOT = 0.75;
const WARM = 0.4;

const DAY_MS = 86_400_000;
const PRODUCT_ALIASES: Record<string, string> = { GTXPro: "GTX Pro" };

export function normalizeProduct(name: string): string {
  return PRODUCT_ALIASES[name] ?? name;
}

/** Dias entre duas datas ISO; NaN se alguma for inválida. */
export function daysBetween(from: string, to: string): number {
  return Math.round((Date.parse(to) - Date.parse(from)) / DAY_MS);
}

const isValidDate = (s: string | null): s is string => !!s && /^\d{4}-\d{2}-\d{2}$/.test(s) && !Number.isNaN(Date.parse(s));
const isClosed = (d: RawDeal) => (d.stage === "Won" || d.stage === "Lost") && isValidDate(d.engageDate) && isValidDate(d.closeDate);

/**
 * Kaplan-Meier: S[t] = P(duração > t). Eventos = fechados; censurados = abertos (em risco até a idade atual).
 */
function kaplanMeier(events: number[], censored: number[], tmax: number): number[] {
  const S: number[] = [];
  let s = 1;
  for (let t = 0; t <= tmax; t++) {
    const atRisk = events.filter((x) => x >= t).length + censored.filter((x) => x >= t).length;
    const d = events.filter((x) => x === t).length;
    if (atRisk > 0) s *= 1 - d / atRisk;
    S.push(s);
  }
  return S;
}

export function buildModel(
  deals: RawDeal[],
  prices: Record<string, number>,
  opts: { today?: string; minSample?: number } = {},
): Model {
  const minSample = opts.minSample ?? 30;
  const closed = deals.filter(isClosed);
  if (closed.length < Math.max(1, minSample)) {
    throw new Error(`Histórico insuficiente: ${closed.length} deals fechados (mínimo ${Math.max(1, minSample)}).`);
  }
  const durations = closed.map((d) => daysBetween(d.engageDate!, d.closeDate!)).filter((t) => t >= 0);
  const maxCycleDays = Math.max(...durations);
  const today = opts.today ?? closed.map((d) => d.closeDate!).sort().at(-1)!;

  const openAges = deals
    .filter((d) => d.stage === "Engaging" && isValidDate(d.engageDate))
    .map((d) => daysBetween(d.engageDate!, today))
    .filter((a) => a >= 0);

  const S = kaplanMeier(durations, openAges, maxCycleDays + HORIZON_DAYS);
  const decideCurve: number[] = [];
  for (let age = 0; age <= maxCycleDays; age++) {
    decideCurve.push(S[age] > 0 ? 1 - S[age + HORIZON_DAYS] / S[age] : 0);
  }
  const peakDecide = Math.max(...decideCurve);
  const peakAge = decideCurve.indexOf(peakDecide);

  const wonCount = closed.filter((d) => d.stage === "Won").length;
  const byAgent = new Map<string, { won: number; total: number }>();
  for (const d of closed) {
    const s = byAgent.get(d.agent) ?? { won: 0, total: 0 };
    s.total++;
    if (d.stage === "Won") s.won++;
    byAgent.set(d.agent, s);
  }

  const validPrices = Object.fromEntries(Object.entries(prices).filter(([, v]) => Number.isFinite(v) && v > 0));
  const logs = Object.values(validPrices).map(Math.log);
  if (!logs.length) throw new Error("Catálogo sem nenhum preço válido.");

  return {
    today,
    maxCycleDays,
    decideCurve,
    peakDecide,
    peakAge,
    globalWinRate: wonCount / closed.length,
    agentWinRate: new Map([...byAgent].map(([a, s]) => [a, s.won / s.total])),
    prices: validPrices,
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
  const pts = Math.round((VALUE_WEIGHT * (Math.log(price) - m.minLogPrice)) / span);
  return Math.min(VALUE_WEIGHT, Math.max(0, pts));
}

function valueReason(price: number, product: string, pts: number): Reason {
  if (pts >= 40) return { kind: "valor", tone: "pos", text: `Ticket alto: ${formatUSD(price)} (${product})` };
  if (pts >= 20) return { kind: "valor", tone: "neutro", text: `Ticket médio: ${formatUSD(price)} (${product})` };
  return { kind: "valor", tone: "neg", text: `Ticket baixo: ${formatUSD(price)} (${product}). Só compensa se for rápido` };
}

type Phase = "decisao" | "aproximando" | "cedo" | "esfriando";

/**
 * Fase de decisão = faixa CONTÍNUA ao redor do pico em que a curva fica ≥ 75% do pico.
 * Não usa só o limiar: a curva tem um pico inicial (deals que se decidem nos primeiros dias)
 * que não deve ser confundido com o pico do ciclo.
 */
export function decisionWindow(curve: number[]) {
  const peak = Math.max(...curve);
  const peakAge = curve.indexOf(peak);
  let start = peakAge;
  while (start > 0 && curve[start - 1] >= HOT * peak) start--;
  let end = peakAge;
  while (end < curve.length - 1 && curve[end + 1] >= HOT * peak) end++;
  return { peak, peakAge, start, end };
}

function phaseOf(age: number, p: number, m: Model): Phase {
  const w = decisionWindow(m.decideCurve);
  if (age >= w.start && age <= w.end) return "decisao";
  const rel = m.peakDecide > 0 ? p / m.peakDecide : 0;
  if (age > w.end) return rel >= WARM ? "aproximando" : "esfriando";
  return rel >= WARM ? "aproximando" : "cedo";
}

function momentumReason(age: number, p: number, phase: Phase): Reason {
  const base = `${pct(p)} dos deals com ${age} dias se decidem no mês seguinte`;
  switch (phase) {
    case "decisao":
      return { kind: "momento", tone: "pos", text: `Fase de decisão: ${base}, perto do pico do ciclo` };
    case "aproximando":
      return { kind: "momento", tone: "neutro", text: `Momento razoável: ${base}` };
    case "cedo":
      return { kind: "momento", tone: "neg", text: `Ainda cedo: só ${base}` };
    case "esfriando":
      return { kind: "momento", tone: "neg", text: `Esfriando: só ${base}. Nesta idade, a maioria vira zumbi` };
  }
}

function actionFor(status: Status, daysLeft: number | null, phase: Phase | null): string {
  if (status === "zumbi") return "Confirmar se está vivo ou marcar como perdido";
  if (status === "prospeccao") return "Agendar o primeiro contato";
  // Progressão no fim do ciclo: esfriando → reengajar; perto do limite → forçar o sim ou o não.
  if (daysLeft !== null && daysLeft <= WINDOW_ALERT_DAYS) return "Forçar o sim ou o não esta semana";
  if (phase === "decisao") return "Ligar hoje: fase de decisão";
  if (phase === "esfriando") return "Reengajar antes que esfrie de vez";
  if (phase === "aproximando") return "Preparar a proposta";
  return "Manter a cadência";
}

export function scoreDeal(deal: RawDeal, m: Model): ScoredDeal {
  const product = normalizeProduct(deal.product);
  const known = m.prices[product];
  const price = known ?? 0;
  const valuePts = known ? valuePoints(known, m) : 0;
  const reasons: Reason[] = [];
  const base = { id: deal.id, agent: deal.agent, product, account: deal.account, price, valuePts };

  if (!known) reasons.push({ kind: "dados", tone: "neg", text: `Preço de "${product}" não encontrado no catálogo. Valor considerado zero` });
  if (!deal.account) reasons.push({ kind: "dados", tone: "neg", text: "Sem conta vinculada no CRM. Complete antes do contato" });

  const invalidDate = deal.engageDate !== null && !isValidDate(deal.engageDate);
  if (!deal.engageDate || invalidDate) {
    if (invalidDate) reasons.push({ kind: "dados", tone: "neg", text: `Data de engajamento inválida no CRM (${deal.engageDate})` });
    const pre: Reason[] = [{ kind: "prospeccao", tone: "neutro", text: "Ainda não engajado: sem tempo de ciclo para medir o momento" }];
    if (known) pre.unshift(valueReason(price, product, valuePts));
    reasons.unshift(...pre);
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

  const rawAge = daysBetween(deal.engageDate, m.today);
  if (rawAge < 0) reasons.push({ kind: "dados", tone: "neg", text: "Data de engajamento no futuro em relação aos dados. Confira o CRM" });
  const ageDays = Math.max(0, rawAge);

  if (ageDays > m.maxCycleDays) {
    const over = ageDays - m.maxCycleDays;
    reasons.unshift({
      kind: "zumbi",
      tone: "neg",
      text: `Aberto há ${ageDays} dias, ${over} além do maior ciclo que já fechou (${m.maxCycleDays}d). No histórico, nenhum deal nessa situação fechou`,
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

  const pDecide = m.decideCurve[ageDays] ?? 0;
  const phase = phaseOf(ageDays, pDecide, m);
  const momentumPts = m.peakDecide > 0 ? Math.round((MOMENTUM_WEIGHT * pDecide) / m.peakDecide) : 0;
  const daysLeft = m.maxCycleDays - ageDays;
  const head: Reason[] = [momentumReason(ageDays, pDecide, phase)];
  if (known) head.unshift(valueReason(price, product, valuePts));
  reasons.unshift(...head);
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
    action: actionFor("ativo", daysLeft, phase),
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
