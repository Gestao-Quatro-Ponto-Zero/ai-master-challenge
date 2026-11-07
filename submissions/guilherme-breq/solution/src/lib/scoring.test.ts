import { describe, expect, it } from "vitest";
import {
  buildModel,
  normalizeProduct,
  scoreDeal,
  rankPipeline,
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
