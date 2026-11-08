import { describe, expect, it, vi } from "vitest";

vi.mock("next/cache", () => ({ cacheLife: () => {} }));

import { getPipeline } from "./data";
import { buildQueue, cyclePhase, isLote, nextStep } from "./playbook";
import { decisionWindow, type ScoredDeal } from "./scoring";

// Janela real do CRM (analysis/06): decisão entre os dias 57 e 101, limite em 138.
const WIN = { start: 57, end: 101 };

function live(over: Partial<ScoredDeal> = {}): ScoredDeal {
  return {
    id: "X1",
    agent: "A",
    product: "GTX Pro",
    account: "Acme",
    status: "ativo",
    ageDays: 80,
    daysLeft: 58,
    daysOverCycle: null,
    price: 4821,
    pDecide: 0.43,
    valuePts: 45,
    momentumPts: 39,
    score: 84,
    reasons: [],
    action: "",
    ...over,
  };
}

describe("cyclePhase", () => {
  it("separa antes, dentro e depois da fase de decisão, com os limites incluídos", () => {
    expect(cyclePhase(56, WIN)).toBe("antes");
    expect(cyclePhase(57, WIN)).toBe("decisao");
    expect(cyclePhase(101, WIN)).toBe("decisao");
    expect(cyclePhase(102, WIN)).toBe("depois");
  });
});

describe("isLote", () => {
  it("só é lote o deal vivo de ticket baixo (< 10 pts de valor)", () => {
    expect(isLote(live({ valuePts: 0 }))).toBe(true);
    expect(isLote(live({ valuePts: 9 }))).toBe(true);
    expect(isLote(live({ valuePts: 10 }))).toBe(false);
    expect(isLote(live({ status: "zumbi", valuePts: 0 }))).toBe(false);
  });
});

describe("nextStep", () => {
  it("lote: resolve por e-mail, sem ligação", () => {
    const s = nextStep(live({ valuePts: 0, price: 55, ageDays: 80, daysLeft: 58 }), WIN);
    expect(s.verb).toBe("Lote");
    expect(s.text).toBe("Resolver por e-mail, sem ligação");
  });

  it("lote a 20 dias ou menos do limite: e-mail de sim ou não com a contagem", () => {
    const s = nextStep(live({ valuePts: 0, ageDays: 120, daysLeft: 18 }), WIN);
    expect(s.verb).toBe("Lote");
    expect(s.text).toBe("E-mail de sim ou não: faltam 18 dias");
  });

  it("20 dias ou menos do limite (ticket não baixo): forçar o sim ou o não", () => {
    const s = nextStep(live({ ageDays: 120, daysLeft: 18 }), WIN);
    expect(s.verb).toBe("Decidir");
    expect(s.text).toBe("Forçar o sim ou o não: faltam 18 dias");
    expect(s.tone).toBe("risk");
  });

  it("o limite de 20 dias é inclusivo e a contagem usa singular", () => {
    expect(nextStep(live({ ageDays: 118, daysLeft: 20 }), WIN).verb).toBe("Decidir");
    expect(nextStep(live({ ageDays: 119, daysLeft: 19 }), WIN).verb).toBe("Decidir");
    expect(nextStep(live({ ageDays: 137, daysLeft: 1 }), WIN).text).toBe("Forçar o sim ou o não: falta 1 dia");
    expect(nextStep(live({ ageDays: 138, daysLeft: 0 }), WIN).text).toBe("Forçar o sim ou o não: hoje é o último dia");
  });

  it("decisão com ticket alto (≥ 40 pts): ligar hoje e propor data de fechamento", () => {
    const s = nextStep(live({ valuePts: 60, ageDays: 95, daysLeft: 43 }), WIN);
    expect(s.verb).toBe("Ligar");
    expect(s.text).toBe("Ligar hoje e propor data de fechamento");
  });

  it("decisão com ticket médio (10 a 39 pts): ligar esta semana", () => {
    const s = nextStep(live({ valuePts: 39, ageDays: 70, daysLeft: 68 }), WIN);
    expect(s.verb).toBe("Ligar");
    expect(s.text).toBe("Ligar esta semana: está na fase de decisão");
  });

  it("antes da fase de decisão: preparar, com os dias até entrar nela", () => {
    const s = nextStep(live({ ageDays: 50, daysLeft: 88 }), WIN);
    expect(s.verb).toBe("Preparar");
    expect(s.text).toBe("Proposta pronta: entra na fase de decisão em 7 dias");
    expect(nextStep(live({ ageDays: 56, daysLeft: 82 }), WIN).text).toBe("Proposta pronta: entra na fase de decisão em 1 dia");
  });

  it("depois da fase de decisão: reengajar, com os dias desde que saiu dela", () => {
    const s = nextStep(live({ ageDays: 110, daysLeft: 28 }), WIN);
    expect(s.verb).toBe("Reengajar");
    expect(s.text).toBe("Reengajar: saiu da fase de decisão há 9 dias");
    expect(nextStep(live({ ageDays: 102, daysLeft: 36 }), WIN).text).toBe("Reengajar: saiu da fase de decisão há 1 dia");
  });

  it("zumbi: encerrar (confirmar se está vivo ou marcar como perdido)", () => {
    const s = nextStep(live({ status: "zumbi", valuePts: 60, ageDays: 200, daysLeft: 0 }), WIN);
    expect(s.verb).toBe("Encerrar");
    expect(s.text).toBe("Confirmar se está vivo ou marcar como perdido");
  });

  it("prospecção: abrir o primeiro contato", () => {
    const s = nextStep(live({ status: "prospeccao", ageDays: null, daysLeft: null }), WIN);
    expect(s.verb).toBe("Abrir");
    expect(s.text).toBe("Agendar o primeiro contato");
  });
});

describe("buildQueue", () => {
  const a = live({ id: "a", valuePts: 60, ageDays: 95, daysLeft: 43, score: 95 });
  const b = live({ id: "b", valuePts: 20, ageDays: 110, daysLeft: 28, score: 50 });
  const c = live({ id: "c", valuePts: 0, price: 55, score: 30 });
  const z = live({ id: "z", status: "zumbi", ageDays: 200, daysLeft: 0 });
  const p = live({ id: "p", status: "prospeccao", ageDays: null, daysLeft: null });

  it("separa trabalho, lote, zumbis e prospecção, mantendo a ordem do ranking", () => {
    const q = buildQueue([a, b, c, z, p], WIN);
    expect(q.work.map((i) => i.deal.id)).toEqual(["a", "b"]);
    expect(q.work.map((i) => i.step.verb)).toEqual(["Ligar", "Reengajar"]);
    expect(q.lote.map((d) => d.id)).toEqual(["c"]);
    expect(q.zombies.map((d) => d.id)).toEqual(["z"]);
    expect(q.prospects.map((d) => d.id)).toEqual(["p"]);
  });

  it("agrupa por verbo na ordem Ligar, Decidir, Reengajar, Preparar e omite grupos vazios", () => {
    const prep = live({ id: "prep", ageDays: 40, daysLeft: 98, score: 40 });
    const dec = live({ id: "dec", ageDays: 125, daysLeft: 13, score: 35 });
    const q = buildQueue([b, prep, dec, a], WIN);
    expect(q.groups.map((g) => g.verb)).toEqual(["Ligar", "Decidir", "Reengajar", "Preparar"]);
    expect(q.groups.map((g) => g.items.map((i) => i.deal.id))).toEqual([["a"], ["dec"], ["b"], ["prep"]]);
    expect(buildQueue([a], WIN).groups.map((g) => g.verb)).toEqual(["Ligar"]);
  });

  it("o lote vem por urgência: menos dias até o limite primeiro, e o ranking desempata", () => {
    const l = (id: string, daysLeft: number) => live({ id, valuePts: 0, price: 55, ageDays: 138 - daysLeft, daysLeft });
    const q = buildQueue([l("a", 60), l("b", 15), l("c", 60), l("d", 3), l("e", 20)], WIN);
    expect(q.lote.map((d) => d.id)).toEqual(["d", "b", "e", "a", "c"]);
  });

  it("vendedor sem nada aberto devolve tudo vazio", () => {
    const q = buildQueue([], WIN);
    expect(q.work).toEqual([]);
    expect(q.groups).toEqual([]);
    expect(q.lote).toEqual([]);
    expect(q.zombies).toEqual([]);
    expect(q.prospects).toEqual([]);
  });
});

describe("playbook com os dados reais do CRM", async () => {
  const data = await getPipeline();
  const win = decisionWindow(data.decideCurve);

  it("a janela de decisão do CRM vai do dia 57 ao 101", () => {
    expect(win.start).toBe(57);
    expect(win.end).toBe(101);
  });

  it("distribui os 298 vivos por verbo conforme o relatório do Design", () => {
    const counts: Record<string, number> = {};
    for (const d of data.deals) {
      if (d.status !== "ativo") continue;
      const v = nextStep(d, win).verb;
      counts[v] = (counts[v] ?? 0) + 1;
    }
    expect(counts).toEqual({ Ligar: 72, Decidir: 76, Reengajar: 53, Preparar: 35, Lote: 62 });
    expect(Object.values(counts).reduce((s, n) => s + n, 0)).toBe(298);
  });

  it("todo vivo cai em exatamente uma pilha da fila", () => {
    const q = buildQueue(data.deals, win);
    expect(q.work.length + q.lote.length).toBe(298);
    expect(q.zombies).toHaveLength(1291);
    expect(q.prospects).toHaveLength(500);
  });
});
