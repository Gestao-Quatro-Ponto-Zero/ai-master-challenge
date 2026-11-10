/**
 * Paridade do motor em TS com o regra.py (referência): mesma entrada, mesma data, mesma saída deal a deal.
 * Fixtures: a entrada lida do banco e a carga JSON da execução 9 (sha256 de9f5962…), gerada pelo Python.
 */
import { readFileSync } from "node:fs";
import { gunzipSync } from "node:zlib";
import { describe, expect, it } from "vitest";
import { arredondar, calcular, type LinhaConta, type LinhaDeal, type LinhaProduto } from "@/lib/score/regra";

const ler = (nome: string) =>
  JSON.parse(gunzipSync(readFileSync(new URL(`./fixtures/score/${nome}`, import.meta.url))).toString("utf-8"));

const entrada = ler("entrada_2017-12-31.json.gz") as { deals: LinhaDeal[]; contas: LinhaConta[]; produtos: LinhaProduto[] };
const esperado = ler("score_exec9_2017-12-31.json.gz");
/** JSON com chaves em ordem (a carga do Python sai com sort_keys). */
const canonico = (v: unknown): string =>
  JSON.stringify(v, (_k, x) => (x && typeof x === "object" && !Array.isArray(x)
    ? Object.fromEntries(Object.keys(x).sort().map((k) => [k, (x as Record<string, unknown>)[k]])) : x));
const r = calcular(entrada.deals, entrada.contas, entrada.produtos, esperado.reference_date);

describe("paridade com o regra.py (execução 9)", () => {
  it("mesmos deals", () => {
    expect(r.deals.map((d) => d.opportunity_id)).toEqual(esperado.deals.map((d: { opportunity_id: string }) => d.opportunity_id));
  });

  it("notas, componentes e motivos iguais deal a deal", () => {
    const dif: string[] = [];
    esperado.deals.forEach((e: Record<string, unknown>, i: number) => {
      const t = r.deals[i]! as unknown as Record<string, unknown>;
      for (const k of ["vendedor_nome", "cohort", "fit", "heat", "bonus", "score", "nota_exata", "acao_sugerida", "dias_no_pipeline",
        "valor_esperado", "marcadores", "componentes", "motivos"]) {
        if (canonico(t[k]) !== canonico(e[k])) dif.push(`${e.opportunity_id}.${k}: ${canonico(t[k])} ≠ ${canonico(e[k])}`);
      }
    });
    expect(dif.length, dif.slice(0, 5).join("\n")).toBe(0);
    expect(r.deals.length).toBe(2089);
  });

  it("FIT por vendedor e padrões de conta iguais", () => {
    const chave = (f: { vendedor_nome: string; cohort: string }) => `${f.vendedor_nome}|${f.cohort}`;
    const ordenar = <T extends { vendedor_nome: string; cohort: string }>(a: T[]) => [...a].sort((x, y) => (chave(x) < chave(y) ? -1 : 1));
    expect(ordenar(r.fit_vendedores)).toEqual(ordenar(esperado.fit_vendedores));
    expect(r.padroes_conta).toEqual(esperado.padroes_conta);
  });
});

describe("round do Python", () => {
  it("meio para o par sobre o valor exato", () => {
    expect([arredondar(0.5), arredondar(1.5), arredondar(2.5), arredondar(72.8153)]).toEqual([0, 2, 2, 73]);
    expect([arredondar(0.125, 2), arredondar(0.375, 2), arredondar(2.675, 2), arredondar(1.005, 2)]).toEqual([0.12, 0.38, 2.67, 1]);
  });
});
