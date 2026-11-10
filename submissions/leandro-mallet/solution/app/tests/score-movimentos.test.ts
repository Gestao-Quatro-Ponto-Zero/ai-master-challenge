/**
 * Redistribuição de domingo: paridade com o redistribuir.py.
 * - estado de antes (donos revertidos): o plano do TS é o mesmo que o Python gravou e aplicou (475 trocas);
 * - estado de agora: o plano não mexe em ninguém (estável).
 * Repasse diário e roteamento de lead novo: regras e travas.
 */
import { readFileSync } from "node:fs";
import { gunzipSync } from "node:zlib";
import { describe, expect, it } from "vitest";
import {
  calcular, chamadasRedistribuicao, planejarRedistribuicao, planejarRepasses, preparar, rotearLeadNovo,
  type LinhaConta, type LinhaDeal, type LinhaProduto,
} from "@/lib/score";

const ler = (nome: string) =>
  JSON.parse(gunzipSync(readFileSync(new URL(`./fixtures/score/${nome}`, import.meta.url))).toString("utf-8"));
const entrada = ler("entrada_2017-12-31.json.gz") as { deals: LinhaDeal[]; contas: LinhaConta[]; produtos: LinhaProduto[] };
const REF = "2017-12-31";

function plano(deals: LinhaDeal[]) {
  const r = calcular(deals, entrada.contas, entrada.produtos, REF);
  return planejarRedistribuicao(r.leads, r.notas, r.celulas);
}

describe("redistribuição de domingo", () => {
  it("antes da troca: mesmo plano do Python (475 trocas, limite 27)", () => {
    const aplicada = ler("redistribuicao_aplicada_2017-12-31.json.gz") as { trocas: { opportunity_id: string; de: string; para: string; fit_dono: number; fit_novo: number; muda: boolean }[] };
    const de = new Map(aplicada.trocas.filter((t) => t.muda).map((t) => [t.opportunity_id, t.de]));
    const antes = entrada.deals.map((d) => (de.has(d.opportunity_id) ? { ...d, vendedor_nome: de.get(d.opportunity_id)! } : d));
    const p = plano(antes);
    expect(p.limite).toBe(27);
    expect(p.elegiveis).toHaveLength(30);
    const ordem = (a: { opportunity_id: string }[]) => [...a].sort((x, y) => (x.opportunity_id < y.opportunity_id ? -1 : 1));
    expect(ordem(p.trocas)).toEqual(ordem(aplicada.trocas));
    expect(chamadasRedistribuicao(p.trocas, 9)).toHaveLength(475);
  });

  it("depois da troca: estável e igual ao Python", () => {
    const esperado = ler("plano_redistribuicao_2017-12-31.json.gz");
    const p = plano(entrada.deals);
    expect(p.trocas.filter((t) => t.muda)).toHaveLength(0);
    const ordem = (a: { opportunity_id: string }[]) => [...a].sort((x, y) => (x.opportunity_id < y.opportunity_id ? -1 : 1));
    expect(ordem(p.trocas)).toEqual(ordem(esperado.trocas));
  });
});

describe("redistribuição com os 35 vendedores ativos (decisão 49)", () => {
  it("os sem histórico entram com FIT 50, recebem leads e o plano é igual ao do Python", () => {
    const esperado = ler("plano_35_vendedores_2017-12-31.json.gz") as { trocas: { opportunity_id: string; para: string; muda: boolean }[]; resumo: { limite: number } };
    const sem = ["Carl Lin", "Carol Thompson", "Elizabeth Anderson", "Mei-Mei Johns", "Natalya Ivanova"];
    const r = calcular(entrada.deals, entrada.contas, entrada.produtos, REF);
    const vendedores = [...new Set([...r.celulas.taxaVendedor.keys(), ...sem])];
    expect(vendedores).toHaveLength(35);
    const p = planejarRedistribuicao(r.leads, r.notas, r.celulas, new Set(), vendedores);
    expect(p.limite).toBe(esperado.resumo.limite);
    const ordem = (a: { opportunity_id: string }[]) => [...a].sort((x, y) => (x.opportunity_id < y.opportunity_id ? -1 : 1));
    expect(ordem(p.trocas)).toEqual(ordem(esperado.trocas));
    for (const v of sem) expect(p.trocas.filter((t) => t.muda && t.para === v).length).toBeGreaterThan(0);
    for (const t of p.trocas.filter((x) => sem.includes(x.para))) expect(t.fit_novo).toBe(50);
  });

  it("motivo do vendedor sem histórico", async () => {
    const { fitDoLead, motivos, notaDoDeal } = await import("@/lib/score");
    const r = calcular(entrada.deals, entrada.contas, entrada.produtos, REF);
    const l = r.leads.find((x) => x.estagio === "Prospecting")!;
    expect(fitDoLead(r.celulas, "Carl Lin", l)).toMatchObject({ fit: 50, sem_historico: true });
    const n = notaDoDeal(l, "Carl Lin", r.celulas, r.padroes, REF);
    expect(motivos(n)[0]![1]).toBe("Vendedor sem histórico: encaixe neutro (50).");
  });
});

describe("repasse diário por mudança de faixa", () => {
  const r = calcular(entrada.deals, entrada.contas, entrada.produtos, REF);

  it("só lead sem contato que mudou de faixa hoje, com as 3 travas", () => {
    const { chamadas } = planejarRepasses(r.leads, r.notas, r.celulas, REF, 9);
    const notaPor = new Map(r.notas.map((n) => [n.opportunity_id, n]));
    for (const c of chamadas) {
      const n = notaPor.get(c.p_opportunity_id)!;
      expect(c.p_origem).toBe("repasse_janela");
      expect(c.p_fit_novo).toBeGreaterThanOrEqual(75);
      expect(c.p_fit_novo).toBeGreaterThanOrEqual((c.p_fit_dono ?? 0) - 3);
      expect(c.p_posicao_top).toBeLessThanOrEqual(5);
      expect(c.p_para_vendedor).not.toBe(n.vendedor_nome);
      const l = r.leads.find((x) => x.opportunity_id === c.p_opportunity_id)!;
      expect(l.ultimo_contato_em).toBeNull();
    }
  });

  it("lead que mudou de faixa vira candidato; quem atingiu o máximo vai à fila do manager", () => {
    // lead de teste aberto ontem há 7 dias (faixa 2–7) e hoje com 8 (faixa 8–15)
    const novo: LinhaDeal = { opportunity_id: "TESTE001", vendedor_nome: "Garret Kinder", produto_nome: "MG Special", conta_nome: null,
      estagio: "Engaging", data_abertura: "2017-12-23", close_date: null, close_value: null, ultimo_contato_em: null, criado_em: null };
    const r2 = calcular([...entrada.deals, novo], entrada.contas, entrada.produtos, REF);
    const livre = planejarRepasses(r2.leads, r2.notas, r2.celulas, REF, 9);
    const preso = planejarRepasses(r2.leads, r2.notas, r2.celulas, REF, 9, { repassesPorLead: new Map([["TESTE001", 2]]) });
    expect(preso.filaManager).toContain("TESTE001");
    expect(preso.chamadas.find((c) => c.p_opportunity_id === "TESTE001")).toBeUndefined();
    const travado = planejarRepasses(r2.leads, r2.notas, r2.celulas, REF, 9, { travados: new Set(["TESTE001"]) });
    expect(travado.chamadas.find((c) => c.p_opportunity_id === "TESTE001")).toBeUndefined();
    void livre;
  });
});

describe("roteamento de lead novo", () => {
  const r = calcular(entrada.deals, entrada.contas, entrada.produtos, REF);
  const ativos = new Map<string, number>();
  for (const n of r.notas) if (n.ativo) ativos.set(n.vendedor_nome, (ativos.get(n.vendedor_nome) ?? 0) + 1);
  const lead = preparar([{ opportunity_id: "NOVO0001", vendedor_nome: "", produto_nome: "GTX Pro", conta_nome: null, estagio: "Prospecting",
    data_abertura: null, close_date: null, close_value: null, ultimo_contato_em: null, criado_em: null }], entrada.contas, entrada.produtos)[0]!;

  it("vai a quem converte mais, abaixo do limite, com FIT ≥ 50", () => {
    const rota = rotearLeadNovo(lead, r.celulas, ativos, 40);
    expect(rota.vendedor).not.toBeNull();
    expect(rota.fit!).toBeGreaterThanOrEqual(50);
  });

  it("penalidade tira a vez; todos no limite = fila do manager", () => {
    const rota = rotearLeadNovo(lead, r.celulas, ativos, 40);
    const pen = rotearLeadNovo(lead, r.celulas, ativos, 40, new Map([[rota.vendedor!, 50]]));
    expect(pen.vendedor).not.toBe(rota.vendedor);
    expect(rotearLeadNovo(lead, r.celulas, ativos, 0).vendedor).toBeNull();
  });
});
