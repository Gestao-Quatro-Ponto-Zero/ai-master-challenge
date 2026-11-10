// O-24 — Prioridades do dia seguem a nota.
//   Ordem (a mesma da migration 0030): atendimento atrasado > lead novo (até 1 dia, sem contato) com FIT >= 75
//   > nota > HEAT > código. O valor esperado não entra.
//   Cartão: a linha de explicação é o 1º motivo da nota; ícone só como alerta (em risco, esfriou).
//   Super hot sem critério de ticket.
import { beforeEach, describe, expect, it, vi } from "vitest";
import { createElement } from "react";
import { renderToStaticMarkup } from "react-dom/server";
import { fraseIcone, icone } from "@/lib/calculos";
import { CONFIG } from "@/lib/config";
import { compararPrioridade, entraNaListaDoGestor, explicacaoDoItem, grupoPrioridade, type ItemOrdem } from "@/lib/prioridades";
import type { DealVisao, Prioridade, Usuario } from "@/lib/tipos";

vi.mock("next/link", () => ({
  default: ({ href, children, ...resto }: { href: string; children: unknown }) => createElement("a", { href, ...resto }, children as never),
}));

const HOJE = "2026-11-10";
const agora = (diasAtras: number) => new Date(Date.parse(`${HOJE}T15:00:00Z`) - diasAtras * 86_400_000).toISOString();
const item = (id: string, x: Partial<ItemOrdem> = {}): ItemOrdem => ({
  id, score: null, heat: null, fit: null, criadoEm: null, comContato: false, marcadores: [], ...x,
});

// Mesmo cenário do validar_0030.mjs (banco): as duas ordens têm de bater.
const CENARIO: ItemOrdem[] = [
  item("B0000001", { fit: 80, heat: 30, score: 50, criadoEm: agora(3) }),
  item("B0000002", { fit: 76, heat: 10, score: 40, marcadores: ["atendimento_atrasado"] }),
  item("B0000003", { fit: 82, criadoEm: agora(0) }),
  item("B0000004", { fit: 70, heat: 10, score: 90 }),
  item("B0000005", { fit: 70, heat: 50, score: 90 }),
  item("B0000006", { fit: 70, heat: 90, score: 70 }),
  item("B0000007", { fit: 60, heat: 90, score: 95, criadoEm: agora(0) }),
  item("B0000008", { fit: 90, heat: 10, score: 20, criadoEm: agora(0), comContato: true }),
  item("B0000009", { fit: 50, heat: 10, score: 10, marcadores: ["risco_esfriar"] }),
  item("B0000010", { fit: 50, heat: 50, score: 30 }),
];

describe("ordem das Prioridades do dia", () => {
  it("grupos: atrasado (0), lead novo com FIT alto (1), os demais (2)", () => {
    const g = Object.fromEntries(CENARIO.map((c) => [c.id, grupoPrioridade(c, HOJE)]));
    expect(g).toMatchObject({ B0000001: 0, B0000002: 0, B0000003: 1, B0000007: 2, B0000008: 2, B0000004: 2 });
  });

  it("lead novo: até 1 dia é novo; passou de 1 dia sem contato vira atendimento atrasado", () => {
    expect(grupoPrioridade(item("X", { fit: 75, criadoEm: agora(1) }), HOJE)).toBe(1);
    expect(grupoPrioridade(item("X", { fit: 75, criadoEm: agora(2) }), HOJE)).toBe(0);
    expect(grupoPrioridade(item("X", { fit: 74, criadoEm: agora(2) }), HOJE)).toBe(2);
    expect(grupoPrioridade(item("X", { fit: 90, criadoEm: agora(5), comContato: true }), HOJE)).toBe(2);
    // a marca da execução não vale mais depois do primeiro contato
    expect(grupoPrioridade(item("X", { marcadores: ["atendimento_atrasado"], comContato: true }), HOJE)).toBe(2);
  });

  it("ordem completa = a do banco: grupo, nota, HEAT no empate, código; valor esperado não entra", () => {
    const ordem = [...CENARIO].sort((a, b) => compararPrioridade(a, b, HOJE)).map((c) => c.id);
    expect(ordem).toEqual(["B0000001", "B0000002", "B0000003", "B0000007", "B0000005", "B0000004", "B0000006", "B0000010", "B0000008", "B0000009"]);
  });

  it("empate total cai no código do deal", () => {
    const [a, b] = [item("ZZ000001", { score: 50, heat: 50 }), item("AA000001", { score: 50, heat: 50 })];
    expect([a, b].sort((x, y) => compararPrioridade(x, y, HOJE)).map((c) => c.id)).toEqual(["AA000001", "ZZ000001"]);
  });

  it("manager e admin: filtro 'atencao' (padrão), 'icone' e 'todos'", () => {
    expect(CONFIG.prioridadesGestor).toBe("atencao");
    expect(entraNaListaDoGestor({ icone: "super_hot" }, 2, "icone")).toBe(true);
    expect(entraNaListaDoGestor({ icone: "em_risco" }, 2, "icone")).toBe(true);
    expect(entraNaListaDoGestor({ icone: null }, 0, "icone")).toBe(false);
    expect(entraNaListaDoGestor({ icone: null }, 0, "atencao")).toBe(true);
    expect(entraNaListaDoGestor({ icone: "em_risco" }, 2, "atencao")).toBe(true);
    expect(entraNaListaDoGestor({ icone: "super_hot" }, 2, "atencao")).toBe(false);
    expect(entraNaListaDoGestor({ icone: "esfriou" }, 2, "todos")).toBe(true);
  });
});

describe("super hot sem ticket", () => {
  it("produto barato na janela de 15 a 106 dias é super hot; a frase não fala em ticket", () => {
    expect(icone("Engaging", 47, 55, null)).toBe("super_hot");
    expect(icone("Engaging", 14, 5000, null)).toBeNull();
    expect(icone("Engaging", 107, 5000, null)).toBe("em_risco");
    expect(fraseIcone("super_hot", 47)).toBe("Na fase em que mais deals viram ganho.");
  });
});

describe("cartão da lista do dia", () => {
  const deal = (x: Partial<DealVisao>): DealVisao => ({
    id: "B0000001", nome: "Hottechi · GTX Pro", estagio: "Engaging", vendedor: "Anna Snelling", manager: "Dustin Brinkmann", regiao: "Central",
    produto: "GTX Pro", serie: "GTX", preco: 4821, conta: "Hottechi", setor: "technology", porte: "grande", contato: null,
    dataAbertura: "2017-11-14", diasDesdeAbertura: 47, ultimoContato: null, closeDate: null, closeValue: null, motivoPerda: null,
    fit: 80, heat: 70, bonus: 0, score: 46, faixaNota: "media", acaoSugerida: "focar", marcadores: [], valorEsperado: 4821,
    valorPeloPrecoDeTabela: false, icone: "super_hot", tags: [], qtdComentarios: 0, atualizadoDepoisDaNota: false, criadoEm: null,
    atualizadoEm: "2026-11-10T00:00:00Z", ...x,
  });
  const prioridade = (x: Partial<Prioridade>): Prioridade => ({
    posicao: 1, deal: deal({}), marcada: null, puladoDiasSeguidos: 0, motivo: null, atendimentoAtrasado: false, ...x,
  });
  const html = async (itens: Prioridade[], papel: Usuario["papel"] = "vendedor") => {
    const { Prioridades } = await import("@/components/Prioridades");
    return renderToStaticMarkup(createElement(Prioridades, { itens, papel, somenteLeitura: false }));
  };

  it("manager com a lista vazia vê uma frase, não um quadro em branco", async () => {
    const h = await html([], "manager");
    expect(h).toContain("Deals do time que pedem ação");
    expect(h).toContain("Nenhum deal do time pede ação hoje");
    expect(h).toContain("Ir para o Pipeline");
    expect(h).not.toContain("super hot");
  });

  it("mostra o 1º motivo da nota no lugar da frase do super hot", async () => {
    const h = await html([prioridade({ motivo: "Encaixe acima da sua média: série GTX (27 de 41 ganhos nos últimos 3 meses)." })]);
    expect(h).toContain("Encaixe acima da sua média: série GTX (27 de 41 ganhos nos últimos 3 meses).");
    expect(h).not.toContain("Super hot");
    expect(h).not.toContain("ticket");
  });

  it("os alertas Em risco de esfriar e Esfriou continuam, junto com o motivo", async () => {
    const risco = await html([prioridade({ deal: deal({ icone: "em_risco", diasDesdeAbertura: 120 }), motivo: "Aberto há 120 dias: em risco de esfriar." })]);
    expect(risco).toContain("Em risco");
    expect(risco).toContain("Aberto há 120 dias: em risco de esfriar.");
    const frio = await html([prioridade({ deal: deal({ icone: "esfriou", diasDesdeAbertura: 210 }) })]);
    expect(frio).toContain("Esfriou");
  });

  it("marca o atendimento atrasado", async () => {
    expect(await html([prioridade({ atendimentoAtrasado: true })])).toContain("Atendimento atrasado");
    expect(await html([prioridade({})])).not.toContain("Atendimento atrasado");
  });
});

describe("reserva em memória segue a mesma ordem", () => {
  const g = globalThis as { __g4Estado?: unknown };
  beforeEach(() => {
    delete process.env.SUPABASE_URL;
    delete process.env.SUPABASE_SERVICE_ROLE_KEY;
    delete process.env.G4_SOMENTE_LEITURA;
    process.env.G4_ESCRITA_EM_MEMORIA = "1";
    g.__g4Estado = undefined;
  });

  const repo = () => import("@/server/repositorio");
  const usuario = async (papel: Usuario["papel"], nome?: string) => {
    const u = (await (await repo()).listarUsuarios()).find((x) => x.papel === papel && (!nome || x.nome === nome));
    if (!u) throw new Error(`sem usuário ${papel}`);
    return u;
  };
  const ordenada = (lista: Prioridade[]) => {
    const hoje = new Date().toLocaleDateString("sv-SE", { timeZone: CONFIG.fusoHorario });
    const chaves = lista.map((p) => ({ ...p.deal, comContato: false }));
    return [...chaves].sort((a, b) => compararPrioridade(a, b, hoje)).map((d) => d.id);
  };

  it("vendedor: lista pela nota, cada item com o 1º motivo da nota quando houver", async () => {
    const lista = await (await repo()).prioridadesDoDia(await usuario("vendedor", "Anna Snelling"));
    expect(lista.length).toBeGreaterThan(2);
    expect(lista.map((p) => p.deal.id)).toEqual(ordenada(lista));
    for (const p of lista) expect(p.motivo === null || p.motivo.length > 0).toBe(true);
  });

  it("manager: só o que pede ação (atrasado, lead novo com FIT alto, em risco), pela nota; super hot fora", async () => {
    const manager = await usuario("manager");
    const lista = await (await repo()).prioridadesDoDia(manager);
    expect(lista.length).toBeGreaterThan(0);
    expect(lista.every((p) => p.deal.manager === manager.manager && (p.atendimentoAtrasado || p.deal.icone === "em_risco" || p.deal.criadoEm !== null))).toBe(true);
    expect(lista.some((p) => p.deal.icone === "super_hot")).toBe(false);
    expect(lista.map((p) => p.deal.id)).toEqual(ordenada(lista));
  });

  it("explicação do item: o 1º motivo, sem espaços; sem motivo, nada", () => {
    expect(explicacaoDoItem(["  Encaixe alto.  ", "outro"])).toBe("Encaixe alto.");
    expect(explicacaoDoItem([])).toBeNull();
    expect(explicacaoDoItem(undefined)).toBeNull();
  });
});
