// O "disjuntor" do banco (app em somente leitura por alguns segundos) só pode abrir em falha de
// DISPONIBILIDADE. Entrada mal formada nunca abre: senão uma pessoa travaria as escritas de todos.
// E o "Desfazer" recusa token fora do formato (400) antes de qualquer chamada ao banco.
import { beforeEach, describe, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";
import { tokenDesfazerValido } from "@/lib/desfazer";
import type { Usuario } from "@/lib/tipos";

const desfazerNoRepositorio = vi.hoisted(() => vi.fn<(u: unknown, token: string) => Promise<void>>(async () => undefined));

vi.mock("@/server/sessao", () => ({
  usuarioAtual: async () => ({ id: 3, nome: "Anna Snelling", papel: "vendedor" }) as Usuario,
}));
vi.mock("@/server/repositorio", async () => {
  const { ErroCRM } = await import("@/server/banco");
  return { ErroCRM, desfazer: desfazerNoRepositorio };
});

const g = globalThis as { __g4BancoForaAte?: number };
const resposta = (erro: { code?: string; message?: string } | null, status: number) => Promise.resolve({ data: null, error: erro, status });

beforeEach(() => {
  // Endereço reservado que nunca responde; nenhum teste chega a abrir conexão.
  process.env.SUPABASE_URL = "http://banco.invalid";
  process.env.SUPABASE_SERVICE_ROLE_KEY = "chave-de-teste";
  g.__g4BancoForaAte = 0;
  desfazerNoRepositorio.mockClear();
  vi.spyOn(console, "error").mockImplementation(() => undefined);
  vi.spyOn(console, "log").mockImplementation(() => undefined);
});

describe("disjuntor do banco", () => {
  const ENTRADAS: [string, number, string][] = [
    ["22P02", 400, "GS400"], // texto onde o banco espera número ou uuid
    ["22003", 400, "GS400"], // número fora da faixa
    ["42883", 404, "GS400"], // function inexistente para aqueles argumentos
    ["PGRST100", 400, "GS400"], // filtro mal formado
    ["PGRST202", 404, "GS400"], // function não encontrada
    ["23505", 409, "GS422"], // chave repetida
    ["23514", 400, "GS422"], // check recusou
    ["P0001", 400, "GS422"], // recusa de uma function sem código próprio
    ["XX999", 400, "GS400"], // código desconhecido com 4xx
  ];

  it.each(ENTRADAS)("entrada inválida (%s) vira frase simples e NÃO abre o disjuntor", async (codigo, status, esperado) => {
    const { ler, ErroCRM, bancoAtivo } = await import("@/server/banco");
    const erro = await ler(resposta({ code: codigo, message: "invalid input: segredo digitado" }, status)).catch((e: unknown) => e);
    expect(erro).toBeInstanceOf(ErroCRM);
    expect((erro as InstanceType<typeof ErroCRM>).codigo).toBe(esperado);
    expect((erro as Error).message).not.toContain("segredo digitado"); // a mensagem crua do banco não vai para a tela
    expect(bancoAtivo()).toBe(true);
  });

  it("regra de negócio (GS4xx) mantém a frase do banco e não abre o disjuntor", async () => {
    const { ler, ErroCRM, bancoAtivo } = await import("@/server/banco");
    const erro = await ler(resposta({ code: "GS403", message: "Este deal é de outro vendedor." }, 400)).catch((e: unknown) => e);
    expect(erro).toBeInstanceOf(ErroCRM);
    expect((erro as Error).message).toBe("Este deal é de outro vendedor.");
    expect(bancoAtivo()).toBe(true);
  });

  it("muitas entradas inválidas seguidas continuam sem abrir o disjuntor", async () => {
    const { ler, bancoAtivo, estadoBanco } = await import("@/server/banco");
    for (let i = 0; i < 50; i++) await ler(resposta({ code: "22P02" }, 400)).catch(() => undefined);
    expect(bancoAtivo()).toBe(true);
    expect(estadoBanco()).toBe("ok");
  });

  it("falha de rede (exceção lançada) abre o disjuntor", async () => {
    const { ler, BancoFora, bancoAtivo, estadoBanco } = await import("@/server/banco");
    const erro = await ler(Promise.reject(new TypeError("fetch failed"))).catch((e: unknown) => e);
    expect(erro).toBeInstanceOf(BancoFora);
    expect(bancoAtivo()).toBe(false);
    expect(estadoBanco()).toBe("indisponivel");
  });

  const QUEDAS: [string, string, number][] = [
    ["rede, como o supabase-js devolve", "", 0],
    ["HTTP 5xx sem código", "", 503],
    ["conexão recusada", "08006", 500],
    ["banco reiniciando", "57P01", 500],
    ["conexões esgotadas", "53300", 500],
    ["PostgREST sem conexão com o banco", "PGRST000", 503],
    ["código desconhecido com 5xx", "XX000", 500],
  ];

  it.each(QUEDAS)("falha de disponibilidade (%s) abre o disjuntor", async (_nome, codigo, status) => {
    const { ler, BancoFora, bancoAtivo } = await import("@/server/banco");
    const erro = await ler(resposta({ code: codigo, message: "falhou" }, status)).catch((e: unknown) => e);
    expect(erro).toBeInstanceOf(BancoFora);
    expect(bancoAtivo()).toBe(false);
  });

  it("consulta que passou do tempo limite (57014) falha só aquele pedido, sem abrir o disjuntor", async () => {
    const { ler, BancoFora, bancoAtivo } = await import("@/server/banco");
    const erro = await ler(resposta({ code: "57014", message: "canceling statement due to statement timeout" }, 500)).catch((e: unknown) => e);
    expect(erro).toBeInstanceOf(BancoFora);
    expect(bancoAtivo()).toBe(true);
  });

  it("a leitura paginada segue a mesma regra", async () => {
    const { lerTudo, ErroCRM, BancoFora, bancoAtivo } = await import("@/server/banco");
    const invalida = await lerTudo(() => resposta({ code: "PGRST100" }, 400)).catch((e: unknown) => e);
    expect(invalida).toBeInstanceOf(ErroCRM);
    expect(bancoAtivo()).toBe(true);
    const rede = await lerTudo(() => Promise.reject(new Error("timeout"))).catch((e: unknown) => e);
    expect(rede).toBeInstanceOf(BancoFora);
    expect(bancoAtivo()).toBe(false);
  });
});

describe("token do Desfazer", () => {
  const VALIDOS = [
    "deal:3f2b8c1e-9a4d-4e6f-8b1a-0c2d3e4f5a6b",
    "acao:12",
    "comentario:7",
    "lote:3",
    "tagmais:88UBTBQ8:4",
    "tagmenos:B08R55ET:15",
    "d42",
  ];
  const INVALIDOS = [
    "deal:abc",
    "deal:3f2b8c1e-9a4d-4e6f-8b1a-0c2d3e4f5a6", // uuid curto
    "deal:3f2b8c1e-9a4d-4e6f-8b1a-0c2d3e4f5a6b:x",
    "acao:1e5",
    "acao:-1",
    "acao:99999999999999999999",
    "comentario:abc",
    "lote:",
    "lote:1:2",
    "tagmais:88UBTBQ8",
    "tagmais:88UBTBQ8:x",
    "tagmenos:curto:1",
    "outro:1",
    "d",
    "dx",
    "",
  ];

  it.each(VALIDOS)("aceita %s", (token) => expect(tokenDesfazerValido(token)).toBe(true));
  it.each(INVALIDOS)("recusa [%s]", (token) => expect(tokenDesfazerValido(token)).toBe(false));

  let ip = 0;
  async function pedir(corpo: unknown) {
    const { POST } = await import("@/app/api/desfazer/route");
    const req = new NextRequest("http://localhost/api/desfazer", {
      method: "POST",
      headers: { "content-type": "application/json", "x-forwarded-for": `10.0.${Math.floor(ip / 250)}.${ip++ % 250}` },
      body: JSON.stringify(corpo),
    });
    const r = await POST(req);
    return { status: r.status, corpo: (await r.json()) as { erro?: string; ok?: boolean } };
  }

  it.each(INVALIDOS)("POST /api/desfazer com [%s] devolve 400 sem chamar o banco", async (token) => {
    const r = await pedir({ token });
    expect(r.status).toBe(400);
    expect(r.corpo.erro).toBe("Não entendi o pedido. Recarregue a página e tente de novo.");
    expect(desfazerNoRepositorio).not.toHaveBeenCalled();
    expect(g.__g4BancoForaAte).toBe(0);
  });

  it("POST /api/desfazer sem token ou com outro tipo devolve 400", async () => {
    for (const corpo of [{}, { token: 12 }, { token: ["acao:1"] }, null]) {
      expect((await pedir(corpo)).status).toBe(400);
    }
    expect(desfazerNoRepositorio).not.toHaveBeenCalled();
  });

  it("POST /api/desfazer com token bem formado segue para o repositório", async () => {
    const r = await pedir({ token: "acao:12" });
    expect(r.status).toBe(200);
    expect(desfazerNoRepositorio).toHaveBeenCalledTimes(1);
    expect(desfazerNoRepositorio.mock.calls[0]?.[1]).toBe("acao:12");
  });
});
