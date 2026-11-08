import { describe, expect, it } from "vitest";
import {
  buildModel,
  normalizeProduct,
  scoreDeal,
  rankPipeline,
  decisionWindow,
  type RawDeal,
} from "./scoring";

const PRICES = { "GTK 500": 26768, "GTX Pro": 4821, "MG Special": 55 };

function closed(id: string, days: number, won: boolean, agent = "Ana", product = "GTX Pro"): RawDeal {
  const engage = new Date(Date.UTC(2017, 0, 1));
  const close = new Date(engage.getTime() + days * 86_400_000);
  return {
    id,
    agent,
    product,
    account: "Acme",
    stage: won ? "Won" : "Lost",
    engageDate: engage.toISOString().slice(0, 10),
    closeDate: close.toISOString().slice(0, 10),
    closeValue: won ? PRICES[product as keyof typeof PRICES] : 0,
  };
}

function open(id: string, ageDays: number, today: string, product = "GTX Pro", account: string | null = "Acme"): RawDeal {
  const engage = new Date(new Date(today).getTime() - ageDays * 86_400_000);
  return {
    id,
    agent: "Ana",
    product,
    account,
    stage: "Engaging",
    engageDate: engage.toISOString().slice(0, 10),
    closeDate: null,
    closeValue: null,
  };
}

// Histórico sintético: metade decide em 10 dias, metade em 100 dias; ciclo máximo = 100.
const history: RawDeal[] = [
  ...Array.from({ length: 10 }, (_, i) => closed(`a${i}`, 10, i % 2 === 0)),
  ...Array.from({ length: 10 }, (_, i) => closed(`b${i}`, 100, i % 3 !== 0)),
];
const TODAY = "2017-12-31";
const model = buildModel(history, PRICES, { today: TODAY, minSample: 1 });

describe("normalizeProduct", () => {
  it("corrige o nome divergente entre pipeline e catálogo", () => {
    expect(normalizeProduct("GTXPro")).toBe("GTX Pro");
    expect(normalizeProduct("MG Special")).toBe("MG Special");
  });
});

describe("buildModel", () => {
  it("usa a maior duração histórica como ciclo máximo", () => {
    expect(model.maxCycleDays).toBe(100);
  });

  it("calcula p(decisão em 30 dias | idade) só com deals ainda vivos naquela idade", () => {
    // Com 0 dias: 20 vivos, 10 decidem até o dia 30 → 0.5
    expect(model.decideCurve[0]).toBeCloseTo(0.5);
    // Com 50 dias: só os 10 de 100 dias seguem vivos; nenhum decide até o dia 80
    expect(model.decideCurve[50]).toBeCloseTo(0);
    // Com 80 dias: os 10 restantes decidem até o dia 110 → 1
    expect(model.decideCurve[80]).toBeCloseTo(1);
  });

  it("guarda a taxa de vitória global e por vendedor como contexto", () => {
    expect(model.globalWinRate).toBeCloseTo(11 / 20);
    expect(model.agentWinRate.get("Ana")).toBeCloseTo(11 / 20);
  });

  it("usa a última data de fechamento como 'hoje' quando não informada", () => {
    const m = buildModel(history, PRICES, { minSample: 1 });
    expect(m.today).toBe("2017-04-11");
  });
});

describe("scoreDeal", () => {
  it("marca como zumbi o deal mais velho que o ciclo máximo", () => {
    const s = scoreDeal(open("z", 150, TODAY), model);
    expect(s.status).toBe("zumbi");
    expect(s.daysOverCycle).toBe(50);
    expect(s.action).toMatch(/perdido/i);
  });

  it("soma valor (0-60) e momento (0-40) no score", () => {
    const s = scoreDeal(open("x", 85, TODAY, "GTK 500"), model);
    expect(s.status).toBe("ativo");
    expect(s.valuePts).toBe(60);
    expect(s.momentumPts).toBe(40);
    expect(s.score).toBe(100);
  });

  it("dá 0 de valor para o produto mais barato do catálogo", () => {
    const s = scoreDeal(open("y", 50, TODAY, "MG Special"), model);
    expect(s.valuePts).toBe(0);
    expect(s.momentumPts).toBe(0);
    expect(s.score).toBe(0);
  });

  it("explica o score com motivos em linguagem de vendedor", () => {
    const s = scoreDeal(open("x", 85, TODAY, "GTK 500"), model);
    expect(s.reasons.length).toBeGreaterThanOrEqual(2);
    expect(s.reasons.some((r) => r.kind === "valor")).toBe(true);
    expect(s.reasons.some((r) => r.kind === "momento")).toBe(true);
  });

  it("avisa quando a janela do ciclo está fechando", () => {
    const s = scoreDeal(open("w", 90, TODAY), model);
    expect(s.daysLeft).toBe(10);
    expect(s.reasons.some((r) => r.kind === "janela")).toBe(true);
  });

  it("sinaliza deal sem conta vinculada", () => {
    const s = scoreDeal(open("n", 20, TODAY, "GTX Pro", null), model);
    expect(s.reasons.some((r) => r.kind === "dados")).toBe(true);
  });

  it("trata prospecção sem data de engajamento: só valor, sem idade", () => {
    const d: RawDeal = { ...open("p", 0, TODAY), stage: "Prospecting", engageDate: null };
    const s = scoreDeal(d, model);
    expect(s.status).toBe("prospeccao");
    expect(s.ageDays).toBeNull();
    expect(s.momentumPts).toBe(0);
  });
});

describe("rankPipeline", () => {
  it("ignora fechados; ativos por score, depois zumbis e prospecção por valor", () => {
    const prosp: RawDeal = { ...open("prosp", 0, TODAY, "GTK 500"), stage: "Prospecting", engageDate: null };
    const deals = [
      ...history,
      prosp,
      open("baixo", 50, TODAY, "MG Special"),
      open("zumbi", 300, TODAY, "GTK 500"),
      open("alto", 85, TODAY, "GTK 500"),
    ];
    const ranked = rankPipeline(deals, model);
    expect(ranked.map((d) => d.id)).toEqual(["alto", "baixo", "zumbi", "prosp"]);
  });

  it("no empate de score, prioriza quem tem menos dias restantes no ciclo", () => {
    // 85 e 90 dias caem no mesmo platô da curva (p=1) → mesmo score
    const ranked = rankPipeline([open("mais-tempo", 85, TODAY), open("menos-tempo", 90, TODAY)], model);
    expect(ranked[0].score).toBe(ranked[1].score);
    expect(ranked.map((d) => d.id)).toEqual(["menos-tempo", "mais-tempo"]);
  });

  it("zumbi não recebe score: não compete com deal vivo", () => {
    const s = scoreDeal(open("z", 300, TODAY, "GTK 500"), model);
    expect(s.score).toBe(0);
    expect(s.price).toBe(26768);
  });
});

describe("Kaplan-Meier: deals ainda abertos contam como censurados (revisão Esquadro #2)", () => {
  // Mesmo histórico + 10 deals abertos há 200 dias que nunca se decidiram (zumbis).
  const zombies = Array.from({ length: 10 }, (_, i) => open(`zz${i}`, 200, "2017-04-11"));
  const km = buildModel([...history, ...zombies], PRICES, { minSample: 1 });

  it("sem censura, coincide com a taxa empírica", () => {
    expect(model.decideCurve[80]).toBeCloseTo(1);
  });

  it("com censura, a chance de decidir cai: os zumbis estavam em risco e não decidiram", () => {
    // Em risco aos 80 dias: 10 que fecham aos 100 + 10 abertos há 200 → metade decide em 30 dias
    expect(km.decideCurve[80]).toBeCloseTo(0.5);
    expect(km.maxCycleDays).toBe(100); // o ciclo máximo continua vindo só dos fechados
  });
});

describe("momento relativo ao pico e estado 'esfriando'", () => {
  it("40 pts = idade em que mais deals se decidem, mesmo que o pico seja < 100%", () => {
    const zombies = Array.from({ length: 10 }, (_, i) => open(`zz${i}`, 200, "2017-04-11"));
    const km = buildModel([...history, ...zombies], PRICES, { minSample: 1, today: TODAY });
    const s = scoreDeal(open("x", 80, TODAY), km);
    expect(km.peakDecide).toBeCloseTo(0.5);
    expect(s.momentumPts).toBe(40);
  });

  it("depois do pico, chance baixa vira 'esfriando' com ação de reengajar", () => {
    // Fecham aos 10 e 40 dias (pico cedo), 2 fecham aos 130 e 18 seguem abertos há 200 dias:
    // aos 60 dias, ninguém do grupo em risco decide nos 30 dias seguintes.
    const h = [
      ...Array.from({ length: 10 }, (_, i) => closed(`c${i}`, 10, true)),
      ...Array.from({ length: 10 }, (_, i) => closed(`d${i}`, 40, true)),
      ...Array.from({ length: 2 }, (_, i) => closed(`e${i}`, 130, false)),
      ...Array.from({ length: 18 }, (_, i) => open(`z${i}`, 200, TODAY)),
    ];
    const m = buildModel(h, PRICES, { minSample: 1, today: TODAY });
    const s = scoreDeal(open("frio", 60, TODAY), m);
    expect(s.pDecide).toBeCloseTo(0);
    expect(s.reasons.find((r) => r.kind === "momento")?.text).toMatch(/esfriando/i);
    expect(s.action).toMatch(/reengajar/i);
  });
});

describe("validação de dados (revisão Esquadro #4-#6)", () => {
  it("recusa histórico insuficiente em vez de inventar limites", () => {
    expect(() => buildModel([], PRICES)).toThrow(/histórico insuficiente/i);
    expect(() => buildModel(history, PRICES, { minSample: 50 })).toThrow(/histórico insuficiente/i);
  });

  it("ignora preços inválidos no catálogo e sinaliza produto sem preço", () => {
    const m = buildModel(history, { ...PRICES, Quebrado: Number.NaN, Zero: 0 }, { minSample: 1, today: TODAY });
    expect(Number.isFinite(m.minLogPrice) && Number.isFinite(m.maxLogPrice)).toBe(true);
    const s = scoreDeal(open("np", 50, TODAY, "Produto Fantasma"), m);
    expect(Number.isFinite(s.score)).toBe(true);
    expect(s.valuePts).toBe(0);
    expect(s.reasons.some((r) => r.kind === "dados" && /preço/i.test(r.text))).toBe(true);
  });

  it("data de engajamento no futuro não vira idade negativa", () => {
    const s = scoreDeal(open("fut", -10, TODAY), model);
    expect(s.ageDays).toBe(0);
    expect(s.reasons.some((r) => r.kind === "dados" && /futur/i.test(r.text))).toBe(true);
  });

  it("data de engajamento inválida vai para prospecção com aviso, sem NaN", () => {
    const s = scoreDeal({ ...open("inv", 10, TODAY), engageDate: "2017-13-45" }, model);
    expect(s.status).toBe("prospeccao");
    expect(Number.isFinite(s.score)).toBe(true);
    expect(s.reasons.some((r) => r.kind === "dados" && /data/i.test(r.text))).toBe(true);
  });
});

describe("decisionWindow: a fase de decisão é a faixa contínua ao redor do pico", () => {
  // 10 decidem aos 5 dias (pico inicial), 10 aos 100 (pico verdadeiro, p=1 entre 70 e 99).
  const h = [
    ...Array.from({ length: 10 }, (_, i) => closed(`r${i}`, 5, false)),
    ...Array.from({ length: 10 }, (_, i) => closed(`s${i}`, 100, true)),
  ];
  const m = buildModel(h, PRICES, { minSample: 1, today: TODAY });

  it("não junta o pico inicial com o pico do ciclo", () => {
    expect(decisionWindow(m.decideCurve)).toMatchObject({ peakAge: 70, start: 70, end: 99 });
  });

  it("deal recém-engajado não é rotulado como 'fase de decisão'", () => {
    const s = scoreDeal(open("novo", 0, TODAY), m);
    expect(s.reasons.find((r) => r.kind === "momento")?.text).not.toMatch(/fase de decisão/i);
    expect(s.action).not.toMatch(/fase de decisão/i);
  });
});
