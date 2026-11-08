import { describe, expect, it } from "vitest";
import { ageNote, modalPattern, nextStep, textPattern } from "./playbook";
import type { ScoredDeal } from "./scoring";

// Janela real do CRM: decisão entre os dias 57 e 101, pico no 75, limite em 138.
const WIN = { start: 57, end: 101, peakAge: 75 };

function deal(over: Partial<ScoredDeal> = {}): ScoredDeal {
  return {
    id: "X1", agent: "A", product: "GTX Pro", account: "Acme", status: "ativo", ageDays: 80, daysLeft: 58, daysOverCycle: null,
    price: 4821, pDecide: 0.43, valuePts: 45, momentumPts: 39, score: 84, reasons: [], action: "", ...over,
  };
}
const note = (over: Partial<ScoredDeal>) => {
  const d = deal(over);
  return ageNote(d, nextStep(d, WIN), WIN);
};

describe("ageNote · o que difere em cada linha da pilha", () => {
  it("Ligar: posição em relação ao pico, a idade e o prazo", () => {
    expect(note({ ageDays: 95, daysLeft: 43, valuePts: 60 })).toBe("20 dias depois do pico · dia 95, faltam 43 dias para o limite");
    expect(note({ ageDays: 73, daysLeft: 65 })).toBe("2 dias até o pico · dia 73, faltam 65 dias para o limite");
    expect(note({ ageDays: 75, daysLeft: 63 })).toBe("no pico · dia 75, faltam 63 dias para o limite");
    expect(note({ ageDays: 76, daysLeft: 62 })).toBe("1 dia depois do pico · dia 76, faltam 62 dias para o limite");
  });

  it("Decidir: só idade e prazo, com singular e o último dia", () => {
    expect(note({ ageDays: 120, daysLeft: 18 })).toBe("dia 120, faltam 18 dias para o limite");
    expect(note({ ageDays: 137, daysLeft: 1 })).toBe("dia 137, falta 1 dia para o limite");
    expect(note({ ageDays: 138, daysLeft: 0 })).toBe("dia 138, hoje é o último dia");
  });

  it("Preparar: quanto falta para entrar na fase de decisão (a informação que a ação carregava)", () => {
    expect(note({ ageDays: 50, daysLeft: 88 })).toBe("entra na fase de decisão em 7 dias · dia 50, faltam 88 dias para o limite");
    expect(note({ ageDays: 56, daysLeft: 82 })).toBe("entra na fase de decisão em 1 dia · dia 56, faltam 82 dias para o limite");
  });

  it("Reengajar: há quanto tempo saiu da fase de decisão", () => {
    expect(note({ ageDays: 110, daysLeft: 28 })).toBe("saiu da fase de decisão há 9 dias · dia 110, faltam 28 dias para o limite");
    expect(note({ ageDays: 102, daysLeft: 36 })).toBe("saiu da fase de decisão há 1 dia · dia 102, faltam 36 dias para o limite");
  });

  it("Lote: idade e prazo, sem posição no ciclo", () => {
    expect(note({ valuePts: 0, price: 55, ageDays: 120, daysLeft: 18 })).toBe("dia 120, faltam 18 dias para o limite");
  });

  it("zumbi e prospecção", () => {
    expect(note({ status: "zumbi", ageDays: 157, daysLeft: 0, daysOverCycle: 19 })).toBe("aberto há 157 dias · 19 além do limite");
    expect(note({ status: "prospeccao", ageDays: null, daysLeft: null })).toBe("ainda sem engajamento");
  });
});

describe("modalPattern · o texto que se repete numa pilha", () => {
  it("devolve o texto mais frequente", () => {
    expect(modalPattern(["Ligar hoje", "Ligar hoje", "Ligar esta semana"])).toBe("Ligar hoje");
  });

  it("números não contam: 'faltam 18 dias' e 'faltam 3 dias' são o mesmo padrão", () => {
    const p = modalPattern(["Forçar o sim ou o não: faltam 18 dias", "Forçar o sim ou o não: faltam 3 dias", "Outro"]);
    expect(p).toBe("Forçar o sim ou o não: faltam N dias");
  });

  it("singular e plural contam como o mesmo padrão ('há 1 dia' e 'há 9 dias'; 'falta 1 dia' e 'faltam 18 dias')", () => {
    expect(modalPattern(["Reengajar: saiu da fase de decisão há 1 dia", "Reengajar: saiu da fase de decisão há 9 dias", "Reengajar: saiu da fase de decisão há 30 dias"])).toBe("Reengajar: saiu da fase de decisão há N dias");
    expect(textPattern("Forçar o sim ou o não: falta 1 dia")).toBe(textPattern("Forçar o sim ou o não: faltam 18 dias"));
  });

  it("empate fica com o que apareceu primeiro; lista vazia dá vazio", () => {
    expect(modalPattern(["A", "B"])).toBe("A");
    expect(modalPattern([])).toBe("");
  });
});
