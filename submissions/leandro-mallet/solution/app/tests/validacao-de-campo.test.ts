// N4 — erro de campo na API volta com frase específica (e o nome do campo), não com "Não entendi o pedido".
import { beforeEach, describe, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";
import { z } from "zod";
import type { Usuario } from "@/lib/tipos";
import { EMAIL, FRASE_GENERICA, fraseDeValidacao, TELEFONE, type ErroDeCampo } from "@/lib/validacao";

const salvarContato = vi.hoisted(() => vi.fn(async () => ({ id: 1 })));
const comentar = vi.hoisted(() => vi.fn(async () => ({ id: 1 })));

vi.mock("@/server/sessao", () => ({
  usuarioAtual: async () => ({ id: 3, nome: "Anna Snelling", papel: "vendedor" }) as Usuario,
}));
vi.mock("@/server/repositorio", async () => {
  const { ErroCRM } = await import("@/server/banco");
  return { ErroCRM, salvarContato, comentar, detalheDeal: async () => ({ deal: { id: "ABCD1234", conta: "Acme", atualizadoEm: null } }) };
});

beforeEach(() => {
  salvarContato.mockClear();
  comentar.mockClear();
  vi.spyOn(console, "log").mockImplementation(() => undefined);
});

const frase = (esquema: z.ZodType, corpo: unknown) => {
  const r = esquema.safeParse(corpo);
  if (r.success) throw new Error("o corpo deveria ser inválido");
  return fraseDeValidacao(r.error.issues as unknown as ErroDeCampo[], corpo);
};

describe("frase de validação por campo", () => {
  const contato = z.object({
    nome: z.string().min(1).max(120),
    email: z.string().trim().max(160).refine((v) => v === "" || EMAIL.test(v)).nullish(),
    telefone: z.string().trim().max(25).refine((v) => v === "" || TELEFONE.test(v)).nullish(),
  });

  it("e-mail inválido", () => {
    expect(frase(contato, { nome: "Ana", email: "ana@" })).toEqual({ campo: "email", frase: "E-mail inválido. Confira o endereço (exemplo: nome@empresa.com)." });
  });

  it("telefone inválido", () => {
    expect(frase(contato, { nome: "Ana", telefone: "ligar depois" }).frase).toMatch(/^Telefone inválido\./);
  });

  it("campo obrigatório vazio ou ausente", () => {
    expect(frase(contato, { nome: "" })).toEqual({ campo: "nome", frase: "Preencha o nome." });
    expect(frase(contato, { email: "a@b.co" })).toEqual({ campo: "nome", frase: "Preencha o nome." });
  });

  it("texto longo demais diz o limite", () => {
    expect(frase(contato, { nome: "x".repeat(121) }).frase).toBe("O nome pode ter no máximo 120 caracteres.");
    expect(frase(z.object({ texto: z.string().min(1).max(1000) }), { texto: "x".repeat(1001) }).frase).toBe("O comentário pode ter no máximo 1000 caracteres.");
  });

  it("opção fora da lista, número fora da faixa e tipo errado", () => {
    expect(frase(z.object({ motivo: z.enum(["preco", "outro"]) }), { motivo: "sei la" }).frase).toBe("Escolha uma opção válida para o motivo da perda.");
    expect(frase(z.object({ valor: z.number().int().positive().max(100_000_000) }), { valor: 200_000_000 }).frase).toBe("O valor não pode passar de 100.000.000.");
    expect(frase(z.object({ anoFundacao: z.number().int().min(1800) }), { anoFundacao: 1500 }).frase).toBe("O ano de fundação não pode ser menor que 1.800.");
    expect(frase(z.object({ valor: z.number() }), { valor: "mil" }).frase).toBe("Confira o valor: o valor não é aceito.");
  });

  it("lote: sem leads ou leads demais", () => {
    const lote = z.object({ ids: z.array(z.string().min(1)).min(1).max(2) });
    expect(frase(lote, { ids: ["a", "b", "c"] }).frase).toBe("Selecione até 2 leads por vez; refine o filtro.");
    expect(frase(lote, { ids: [] }).frase).toBe("Selecione pelo menos um lead.");
  });

  it("a frase nunca repete o que foi digitado", () => {
    const digitado = "segredo<script>@x";
    expect(frase(contato, { nome: "Ana", email: digitado }).frase).not.toContain("segredo");
  });

  it("campo desconhecido ou corpo que não é objeto: frase genérica, sem nome de campo", () => {
    expect(frase(z.object({ token: z.string().min(2) }), { token: "" })).toEqual({ campo: null, frase: FRASE_GENERICA });
    expect(frase(contato, null)).toEqual({ campo: null, frase: FRASE_GENERICA });
    expect(frase(contato, "texto solto")).toEqual({ campo: null, frase: FRASE_GENERICA });
  });
});

describe("rotas devolvem 400 com a frase do campo", () => {
  let ip = 0;
  const pedido = (url: string, corpo: unknown) =>
    new NextRequest(`http://localhost${url}`, {
      method: "POST",
      headers: { "content-type": "application/json", "x-forwarded-for": `10.1.0.${ip++ % 250}` },
      body: JSON.stringify(corpo),
    });

  it("POST /api/deals/[id]/contato com e-mail inválido", async () => {
    const { POST } = await import("@/app/api/deals/[id]/contato/route");
    const r = await POST(pedido("/api/deals/ABCD1234/contato", { versao: null, nome: "Ana Souza", email: "ana.souza" }));
    expect(r.status).toBe(400);
    expect(await r.json()).toMatchObject({ erro: "E-mail inválido. Confira o endereço (exemplo: nome@empresa.com).", detalhe: { campo: "email" } });
    expect(salvarContato).not.toHaveBeenCalled();
  });

  it("POST /api/deals/[id]/contato com e-mail válido, vazio ou ausente segue para salvar", async () => {
    const { POST } = await import("@/app/api/deals/[id]/contato/route");
    for (const email of ["ana@empresa.com", "", null, undefined]) {
      const r = await POST(pedido("/api/deals/ABCD1234/contato", { versao: null, nome: "Ana Souza", email }));
      expect(r.status).toBe(200);
    }
    expect(salvarContato).toHaveBeenCalledTimes(4);
  });

  it("POST /api/deals/[id]/comentarios com texto vazio", async () => {
    const { POST } = await import("@/app/api/deals/[id]/comentarios/route");
    const r = await POST(pedido("/api/deals/ABCD1234/comentarios", { texto: "" }));
    expect(r.status).toBe(400);
    expect(await r.json()).toMatchObject({ erro: "Preencha o comentário.", detalhe: { campo: "texto" } });
    expect(comentar).not.toHaveBeenCalled();
  });

  it("corpo que não é JSON continua com a frase genérica", async () => {
    const { POST } = await import("@/app/api/deals/[id]/comentarios/route");
    const req = new NextRequest("http://localhost/api/deals/ABCD1234/comentarios", { method: "POST", headers: { "x-forwarded-for": "10.1.1.1" }, body: "{quebrado" });
    const r = await POST(req);
    expect(r.status).toBe(400);
    expect((await r.json()).erro).toBe(FRASE_GENERICA);
  });
});
