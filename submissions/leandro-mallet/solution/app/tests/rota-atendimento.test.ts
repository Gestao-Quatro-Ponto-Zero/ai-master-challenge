// O-31 — rota POST /api/deals/[id]/atendimento: tipo que conta como contato e comentário obrigatórios.
import { beforeEach, describe, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";
import type { Usuario } from "@/lib/tipos";

type Chamada = (...args: unknown[]) => Promise<unknown>;
const repo = vi.hoisted(() => ({ registrarAtendimento: vi.fn<Chamada>(async () => ({ desfazer: "acao:9" })) }));

vi.mock("@/server/sessao", () => ({ usuarioAtual: async () => ({ id: 3, nome: "Anna Snelling", papel: "vendedor", vendedor: "Anna Snelling" }) as Usuario }));
vi.mock("@/server/repositorio", async () => {
  const { ErroCRM } = await import("@/server/banco");
  return { ErroCRM, ...repo };
});

beforeEach(() => {
  repo.registrarAtendimento.mockClear();
  vi.spyOn(console, "log").mockImplementation(() => undefined);
});

let ip = 0;
async function postar(corpo: unknown) {
  const { POST } = await import("@/app/api/deals/[id]/atendimento/route");
  const r = await POST(
    new NextRequest("http://localhost/api/deals/ABCD1234/atendimento", {
      method: "POST",
      headers: { "content-type": "application/json", "x-forwarded-for": `10.3.0.${ip++}` },
      body: JSON.stringify(corpo),
    }),
  );
  return { status: r.status, corpo: (await r.json()) as { erro?: string; desfazer?: string } };
}

describe("registrar atendimento pela rota", () => {
  it("grava com o tipo e o comentário sem espaços nas pontas", async () => {
    const r = await postar({ tipoAtividade: "ligacao", comentario: "  Pediu a proposta. " });
    expect(r.status).toBe(200);
    expect(repo.registrarAtendimento.mock.calls[0]?.slice(1)).toEqual(["ABCD1234", "ligacao", "Pediu a proposta."]);
  });

  it("sem comentário ou com tipo desconhecido: 400 com frase e sem chamar o banco", async () => {
    expect((await postar({ tipoAtividade: "ligacao", comentario: "  " })).corpo.erro).toBe("Preencha o comentário.");
    expect((await postar({ tipoAtividade: "telepatia", comentario: "x" })).status).toBe(400);
    expect((await postar({ comentario: "x" })).corpo.erro).toBe("Preencha o tipo de atividade.");
    expect(repo.registrarAtendimento).not.toHaveBeenCalled();
  });
});
