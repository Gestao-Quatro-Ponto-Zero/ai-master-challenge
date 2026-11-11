/**
 * Redistribuição de domingo e repasse diário: paridade com o redistribuir.py (FIT absoluto, O-51).
 * - estado de antes (donos revertidos), estado da foto e com os 35 vendedores: o plano do TS é o mesmo do Python;
 * - repasse diário: regras e travas.
 * O lead novo é roteado só pela função do banco (core_rotear_lead), sem regra própria aqui.
 */
import { readFileSync } from "node:fs";
import { gunzipSync } from "node:zlib";
import { describe, expect, it } from "vitest";
import {
  arredondar, calcular, chamadasRedistribuicao, fitDoLead, motivos, notaDoDeal, planejarRedistribuicao, planejarRepasses,
  type LinhaConta, type LinhaDeal, type LinhaProduto,
} from "@/lib/score";

const ler = (nome: string) =>
  JSON.parse(gunzipSync(readFileSync(new URL(`./fixtures/score/${nome}`, import.meta.url))).toString("utf-8"));
const entrada = ler("entrada_2017-12-31.json.gz") as { deals: LinhaDeal[]; contas: LinhaConta[]; produtos: LinhaProduto[] };
const REF = "2017-12-31";
type Troca = { opportunity_id: string; de: string; para: string; fit_dono: number; fit_novo: number; muda: boolean };
const ordem = (a: { opportunity_id: string }[]) => [...a].sort((x, y) => (x.opportunity_id < y.opportunity_id ? -1 : 1));

function plano(deals: LinhaDeal[], vendedores?: string[]) {
  const r = calcular(deals, entrada.contas, entrada.produtos, REF);
  return planejarRedistribuicao(r.leads, r.notas, r.celulas, new Set(), vendedores);
}

describe("redistribuição de domingo", () => {
  it("estado de antes (donos revertidos): mesmo plano do Python", () => {
    const aplicada = ler("redistribuicao_aplicada_2017-12-31.json.gz") as { trocas: Troca[] };
    const esperado = ler("plano_antes_2017-12-31.json.gz") as { limite: number; trocas: Troca[] };
    const de = new Map(aplicada.trocas.filter((t) => t.muda).map((t) => [t.opportunity_id, t.de]));
    const antes = entrada.deals.map((d) => (de.has(d.opportunity_id) ? { ...d, vendedor_nome: de.get(d.opportunity_id)! } : d));
    const p = plano(antes);
    expect(p.limite).toBe(esperado.limite);
    expect(p.elegiveis).toHaveLength(30);
    expect(ordem(p.trocas)).toEqual(ordem(esperado.trocas));
    expect(chamadasRedistribuicao(p.trocas, 9)).toHaveLength(esperado.trocas.filter((t) => t.muda).length);
  });

  it("estado da foto: mesmo plano do Python", () => {
    const esperado = ler("plano_redistribuicao_2017-12-31.json.gz") as { limite: number; trocas: Troca[] };
    const p = plano(entrada.deals);
    expect(p.limite).toBe(esperado.limite);
    expect(ordem(p.trocas)).toEqual(ordem(esperado.trocas));
  });
});

describe("redistribuição com os 35 vendedores ativos (decisão 49)", () => {
  const sem = ["Carl Lin", "Carol Thompson", "Elizabeth Anderson", "Mei-Mei Johns", "Natalya Ivanova"];

  it("os sem histórico entram com a conversão do time, recebem leads e o plano é igual ao do Python", () => {
    const esperado = ler("plano_35_vendedores_2017-12-31.json.gz") as { trocas: Troca[]; resumo: { limite: number } };
    const r = calcular(entrada.deals, entrada.contas, entrada.produtos, REF);
    const vendedores = [...new Set([...r.celulas.taxaVendedor.keys(), ...sem])];
    expect(vendedores).toHaveLength(35);
    const p = planejarRedistribuicao(r.leads, r.notas, r.celulas, new Set(), vendedores);
    expect(p.limite).toBe(esperado.resumo.limite);
    expect(ordem(p.trocas)).toEqual(ordem(esperado.trocas));
    for (const v of sem) expect(p.trocas.filter((t) => t.muda && t.para === v).length).toBeGreaterThan(0);
    for (const t of p.trocas.filter((x) => sem.includes(x.para))) expect(t.fit_novo).toBe(arredondar(100 * r.celulas.taxaTime, 2));
  });

  it("FIT e motivo do vendedor sem histórico", () => {
    const r = calcular(entrada.deals, entrada.contas, entrada.produtos, REF);
    const l = r.leads.find((x) => x.estagio === "Prospecting")!;
    expect(fitDoLead(r.celulas, "Carl Lin", l)).toMatchObject({ fit: 100 * r.celulas.taxaTime, sem_historico: true });
    const n = notaDoDeal(l, "Carl Lin", r.celulas, r.padroes, REF);
    expect(motivos(n)[0]![1]).toBe(`Vendedor sem histórico nos últimos 3 meses: o encaixe usa a conversão do time (${arredondar(100 * r.celulas.taxaTime)}%).`);
  });
});

describe("FIT absoluto", () => {
  const r = calcular(entrada.deals, entrada.contas, entrada.produtos, REF);
  it("é a conversão do vendedor no perfil, de 0 a 100", () => {
    for (const n of r.notas) {
      const f = n.detalhe_fit;
      const esperado = f.usadas.length
        ? 100 * (f.usadas.reduce((s, u) => s + u.taxa_encolhida!, 0) / f.usadas.length)
        : f.sem_historico ? 100 * r.celulas.taxaTime : 100 * r.celulas.taxaVendedor.get(n.vendedor_nome)!;
      expect(n.fit).toBeCloseTo(esperado, 9);
      expect(n.fit).toBeGreaterThanOrEqual(0);
      expect(n.fit).toBeLessThanOrEqual(100);
    }
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
      expect(r.leads.find((x) => x.opportunity_id === c.p_opportunity_id)!.ultimo_contato_em).toBeNull();
    }
  });

  it("quem atingiu o máximo de repasses vai à fila do manager; lead travado não é repassado", () => {
    const novo: LinhaDeal = { opportunity_id: "TESTE001", vendedor_nome: "Garret Kinder", produto_nome: "MG Special", conta_nome: null,
      estagio: "Engaging", data_abertura: "2017-12-23", close_date: null, close_value: null, ultimo_contato_em: null, criado_em: null };
    const r2 = calcular([...entrada.deals, novo], entrada.contas, entrada.produtos, REF);
    const preso = planejarRepasses(r2.leads, r2.notas, r2.celulas, REF, 9, { repassesPorLead: new Map([["TESTE001", 2]]) });
    expect(preso.filaManager).toContain("TESTE001");
    expect(preso.chamadas.find((c) => c.p_opportunity_id === "TESTE001")).toBeUndefined();
    const travado = planejarRepasses(r2.leads, r2.notas, r2.celulas, REF, 9, { travados: new Set(["TESTE001"]) });
    expect(travado.chamadas.find((c) => c.p_opportunity_id === "TESTE001")).toBeUndefined();
  });
});
