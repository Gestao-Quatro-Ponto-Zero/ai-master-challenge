// R1 — texto obrigatório só com espaços passava pela rota, caía na regra do banco e voltava como 422 genérico.
// Agora o schema tira os espaços das pontas antes de conferir e a rota responde 400 com a frase do campo.
import { beforeEach, describe, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";
import type { Usuario } from "@/lib/tipos";

type Chamada = (...args: unknown[]) => Promise<unknown>;
const repo = vi.hoisted(() => ({
  comentar: vi.fn<Chamada>(async () => ({ id: 1 })),
  marcarPrioridade: vi.fn<Chamada>(async () => ({ desfazer: null })),
  executarLote: vi.fn<Chamada>(async () => ({ loteId: 1, aplicados: 1, pulados: 0 })),
  salvarContato: vi.fn<Chamada>(async () => ({ id: 1 })),
  criarTag: vi.fn<Chamada>(async () => ({ id: 1 })),
  criarDeal: vi.fn<Chamada>(async () => ({ id: "ABCD1234" })),
  registrarAcao: vi.fn<Chamada>(async () => ({ desfazer: "acao:1" })),
}));

vi.mock("@/server/sessao", () => ({
  usuarioAtual: async () => ({ id: 38, nome: "Manager de teste", papel: "manager" }) as Usuario,
}));
vi.mock("@/server/repositorio", async () => {
  const { ErroCRM } = await import("@/server/banco");
  return {
    ErroCRM, ...repo,
    detalheDeal: async () => ({ deal: { id: "ABCD1234", conta: "Acme", atualizadoEm: null } }),
    buscarDeals: async () => ({ total: 0, linhas: [] }),
    escopoDe: () => ({}),
    lotesRecentes: async () => [],
    listarTags: async () => [],
    listarEquipe: async () => [],
  };
});

beforeEach(() => {
  for (const f of Object.values(repo)) f.mockClear();
  vi.spyOn(console, "log").mockImplementation(() => undefined);
});

let ip = 0;
async function postar(caminho: string, corpo: unknown) {
  const rotas: Record<string, () => Promise<{ POST: (req: NextRequest) => Promise<Response> }>> = {
    comentarios: () => import("@/app/api/deals/[id]/comentarios/route"),
    acoes: () => import("@/app/api/deals/[id]/acoes/route"),
    contato: () => import("@/app/api/deals/[id]/contato/route"),
    prioridades: () => import("@/app/api/prioridades/route"),
    lotes: () => import("@/app/api/lotes/route"),
    tags: () => import("@/app/api/tags/route"),
    deals: () => import("@/app/api/deals/route"),
  };
  const url = { comentarios: "/api/deals/ABCD1234/comentarios", acoes: "/api/deals/ABCD1234/acoes", contato: "/api/deals/ABCD1234/contato" }[caminho] ?? `/api/${caminho}`;
  const { POST } = await rotas[caminho]!();
  const r = await POST(
    new NextRequest(`http://localhost${url}`, {
      method: "POST",
      headers: { "content-type": "application/json", "x-forwarded-for": `10.2.${Math.floor(ip / 250)}.${ip++ % 250}` },
      body: JSON.stringify(corpo),
    }),
  );
  return { status: r.status, corpo: (await r.json()) as { erro?: string; detalhe?: { campo?: string } } };
}

const SO_ESPACOS = ["   ", "\n\t ", "  "];

describe("R1: texto obrigatório só com espaços", () => {
  it.each(SO_ESPACOS)("comentário [%j] devolve 400 \"Preencha o comentário.\" sem chamar o banco", async (texto) => {
    const r = await postar("comentarios", { texto });
    expect(r).toEqual({ status: 400, corpo: expect.objectContaining({ erro: "Preencha o comentário.", detalhe: { campo: "texto" } }) });
    expect(repo.comentar).not.toHaveBeenCalled();
  });

  it("comentário com espaços nas pontas é salvo sem eles", async () => {
    expect((await postar("comentarios", { texto: "  Ligar amanhã cedo.  " })).status).toBe(200);
    expect(repo.comentar.mock.calls[0]?.[2]).toBe("Ligar amanhã cedo.");
  });

  it("✓ da prioridade: comentário só com espaços ou ausente devolve \"Preencha o comentário.\"", async () => {
    for (const comentario of [...SO_ESPACOS, "", null, undefined]) {
      const r = await postar("prioridades", { dealId: "ABCD1234", resultado: "feita", tipoAtividade: "ligacao", comentario });
      expect(r.status).toBe(400);
      expect(r.corpo).toMatchObject({ erro: "Preencha o comentário.", detalhe: { campo: "comentario" } });
    }
    expect(repo.marcarPrioridade).not.toHaveBeenCalled();
  });

  it("✓ da prioridade: sem tipo de atividade devolve \"Preencha o tipo de atividade.\"", async () => {
    const r = await postar("prioridades", { dealId: "ABCD1234", resultado: "feita", tipoAtividade: "  ", comentario: "Pediu a proposta." });
    expect(r).toEqual({ status: 400, corpo: expect.objectContaining({ erro: "Preencha o tipo de atividade.", detalhe: { campo: "tipoAtividade" } }) });
    expect(repo.marcarPrioridade).not.toHaveBeenCalled();
  });

  it("✓ completo segue com o comentário sem os espaços das pontas; ✗ não exige comentário", async () => {
    expect((await postar("prioridades", { dealId: "ABCD1234", resultado: "feita", tipoAtividade: "ligacao", comentario: " Pediu a proposta. " })).status).toBe(200);
    expect(repo.marcarPrioridade.mock.calls[0]?.[3]).toEqual({ tipoAtividade: "ligacao", comentario: "Pediu a proposta." });
    expect((await postar("prioridades", { dealId: "ABCD1234", resultado: "pulada" })).status).toBe(200);
    expect(repo.marcarPrioridade).toHaveBeenCalledTimes(2);
  });

  it("lote Comentar: texto só com espaços ou ausente devolve \"Preencha o comentário.\"", async () => {
    for (const texto of [...SO_ESPACOS, "", undefined]) {
      const r = await postar("lotes", { tipo: "comentar", ids: ["ABCD1234"], texto });
      expect(r.status).toBe(400);
      expect(r.corpo).toMatchObject({ erro: "Preencha o comentário.", detalhe: { campo: "texto" } });
    }
    expect(repo.executarLote).not.toHaveBeenCalled();
  });

  it("lote Comentar com texto segue; os outros lotes não exigem texto", async () => {
    expect((await postar("lotes", { tipo: "comentar", ids: ["ABCD1234"], texto: "  Rever na segunda.  " })).status).toBe(200);
    expect(repo.executarLote.mock.calls[0]?.[3]).toMatchObject({ texto: "Rever na segunda." });
    expect((await postar("lotes", { tipo: "avancar_estagio", ids: ["ABCD1234"] })).status).toBe(200);
    expect(repo.executarLote).toHaveBeenCalledTimes(2);
  });

  it("os outros textos obrigatórios seguem a mesma regra (contato, tag, novo lead)", async () => {
    expect((await postar("contato", { versao: null, nome: "   " })).corpo).toMatchObject({ erro: "Preencha o nome.", detalhe: { campo: "nome" } });
    expect((await postar("tags", { nome: "  ", cor: "tag-1" })).corpo).toMatchObject({ erro: "Preencha o nome.", detalhe: { campo: "nome" } });
    expect((await postar("deals", { produto: " ", estagio: "Prospecting" })).corpo).toMatchObject({ erro: "Preencha o produto.", detalhe: { campo: "produto" } });
    expect(repo.salvarContato).not.toHaveBeenCalled();
    expect(repo.criarTag).not.toHaveBeenCalled();
    expect(repo.criarDeal).not.toHaveBeenCalled();
  });

  it("texto opcional só com espaços vira vazio e não bloqueia (observação da ação, nome do lead)", async () => {
    expect((await postar("acoes", { acao: "liguei", nota: "   " })).status).toBe(200);
    expect(repo.registrarAcao.mock.calls[0]?.[3]).toBeNull();
    expect((await postar("deals", { produto: "GTX Basic", estagio: "Prospecting", nome: "   " })).status).toBe(200);
    expect(repo.criarDeal.mock.calls[0]?.[1]).toMatchObject({ produto: "GTX Basic", nome: null });
  });
});
