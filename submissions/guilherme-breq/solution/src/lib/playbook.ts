/**
 * Playbook: transforma o que o motor já sabe de cada deal (status, valor, idade, dias restantes)
 * na próxima ação do vendedor. Puro e sem I/O; `scoring.ts` não muda.
 *
 * Por que existe: `scoring.action` devolve só 5 rótulos e ignora o valor, então um deal de US$ 55
 * pedia a mesma ligação que um de US$ 26 mil. Aqui o ticket baixo vira "lote" (um e-mail resolve)
 * e a ação ganha números concretos (dias até a fase de decisão, dias que faltam).
 */
import { WINDOW_ALERT_DAYS, type ScoredDeal } from "./scoring";

export type Verb = "Ligar" | "Decidir" | "Reengajar" | "Preparar" | "Lote" | "Encerrar" | "Abrir";
export type StepTone = "gold" | "risk" | "warm" | "calm";

export interface Step {
  verb: Verb;
  text: string;
  tone: StepTone;
}

/** Faixa de idades (dias) da fase de decisão, de `decisionWindow(curve)`. */
export interface Window {
  start: number;
  end: number;
}

/** Abaixo disto (de 60) o ticket é baixo: no CRM atual, só o MG Special (US$ 55). */
export const LOTE_BELOW_VALUE_PTS = 10;
/** A partir disto (de 60) o ticket é alto e a ligação pede data de fechamento. */
export const HIGH_TICKET_VALUE_PTS = 40;

type StepInput = Pick<ScoredDeal, "status" | "valuePts" | "ageDays" | "daysLeft">;

export type CyclePhase = "antes" | "decisao" | "depois";

export function cyclePhase(age: number, win: Window): CyclePhase {
  if (age < win.start) return "antes";
  return age <= win.end ? "decisao" : "depois";
}

export const isLote = (d: Pick<ScoredDeal, "status" | "valuePts">) => d.status === "ativo" && d.valuePts < LOTE_BELOW_VALUE_PTS;

const days = (n: number) => `${n} ${n === 1 ? "dia" : "dias"}`;
const remaining = (n: number) => (n <= 0 ? "hoje é o último dia" : n === 1 ? "falta 1 dia" : `faltam ${n} dias`);

export function nextStep(d: StepInput, win: Window): Step {
  if (d.status === "zumbi") return { verb: "Encerrar", text: "Confirmar se está vivo ou marcar como perdido", tone: "risk" };
  if (d.status === "prospeccao") return { verb: "Abrir", text: "Agendar o primeiro contato", tone: "calm" };

  const age = d.ageDays ?? 0;
  const left = d.daysLeft ?? Infinity;
  const closing = left <= WINDOW_ALERT_DAYS;

  if (isLote(d)) {
    return closing
      ? { verb: "Lote", text: `E-mail de sim ou não: ${remaining(left)}`, tone: "calm" }
      : { verb: "Lote", text: "Resolver por e-mail, sem ligação", tone: "calm" };
  }
  if (closing) return { verb: "Decidir", text: `Forçar o sim ou o não: ${remaining(left)}`, tone: "risk" };

  switch (cyclePhase(age, win)) {
    case "decisao":
      return d.valuePts >= HIGH_TICKET_VALUE_PTS
        ? { verb: "Ligar", text: "Ligar hoje e propor data de fechamento", tone: "gold" }
        : { verb: "Ligar", text: "Ligar esta semana: está na fase de decisão", tone: "gold" };
    case "antes":
      return { verb: "Preparar", text: `Proposta pronta: entra na fase de decisão em ${days(win.start - age)}`, tone: "calm" };
    case "depois":
      return { verb: "Reengajar", text: `Reengajar: saiu da fase de decisão há ${days(age - win.end)}`, tone: "warm" };
  }
}

export interface WorkItem<D extends ScoredDeal> {
  deal: D;
  step: Step;
}

export interface WorkGroup<D extends ScoredDeal> {
  verb: Verb;
  items: WorkItem<D>[];
}

export interface Queue<D extends ScoredDeal> {
  /** Vivos de ticket não baixo, na ordem do ranking. */
  work: WorkItem<D>[];
  /** O mesmo trabalho, agrupado por verbo na ordem em que o vendedor deve lê-lo. */
  groups: WorkGroup<D>[];
  lote: D[];
  zombies: D[];
  prospects: D[];
}

const GROUP_ORDER: Verb[] = ["Ligar", "Decidir", "Reengajar", "Preparar"];

/** `deals` já vem ordenado por prioridade (rankPipeline); a ordem é preservada dentro de cada pilha, exceto o lote (por urgência). */
export function buildQueue<D extends ScoredDeal>(deals: D[], win: Window): Queue<D> {
  const work: WorkItem<D>[] = [];
  const lote: D[] = [];
  const zombies: D[] = [];
  const prospects: D[] = [];
  for (const deal of deals) {
    if (deal.status === "zumbi") zombies.push(deal);
    else if (deal.status === "prospeccao") prospects.push(deal);
    else if (isLote(deal)) lote.push(deal);
    else work.push({ deal, step: nextStep(deal, win) });
  }
  // Lote por urgência: quem tem menos dias até o limite vem primeiro (sort estável: o ranking desempata).
  lote.sort((a, b) => (a.daysLeft ?? Infinity) - (b.daysLeft ?? Infinity));
  const groups = GROUP_ORDER.map((verb) => ({ verb, items: work.filter((i) => i.step.verb === verb) })).filter((g) => g.items.length > 0);
  return { work, groups, lote, zombies, prospects };
}
