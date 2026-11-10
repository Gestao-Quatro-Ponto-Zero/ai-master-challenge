// Reproduz os dois bloqueadores achados no teste da versão publicada (várias instâncias do servidor):
//   B1 — ✓/✗ das Prioridades respondia 404 "não está na sua lista de hoje" com o deal na lista;
//   B2 — mudar o estágio respondia 409 "alterado por outra pessoa" sem ninguém ter mexido.
// Causa: cada instância guardava a própria memória (a lista do dia e a "versão" do deal).
// Aqui a troca de instância é simulada limpando a memória entre a leitura e a escrita.
import { beforeEach, describe, expect, it } from "vitest";
import type { Usuario } from "@/lib/tipos";

const g = globalThis as { __g4Estado?: unknown };
const novaInstancia = () => {
  g.__g4Estado = undefined;
};

async function repo() {
  return import("@/server/repositorio");
}

async function usuario(papel: Usuario["papel"], nome?: string): Promise<Usuario> {
  const { listarUsuarios } = await repo();
  const u = (await listarUsuarios()).find((x) => x.papel === papel && (!nome || x.nome === nome));
  if (!u) throw new Error(`usuário de teste não encontrado: ${papel} ${nome ?? ""}`);
  return u;
}

beforeEach(() => {
  delete process.env.SUPABASE_URL;
  delete process.env.SUPABASE_SERVICE_ROLE_KEY;
  delete process.env.G4_SOMENTE_LEITURA;
  process.env.G4_ESCRITA_EM_MEMORIA = "1";
  novaInstancia();
});

describe("reserva em arquivo com várias instâncias do servidor", () => {
  it("B2: a versão lida numa instância vale em outra (mudar estágio não dá 409)", async () => {
    const { colunasPipeline, escopoDe, mudarEstagio } = await repo();
    const anna = await usuario("vendedor", "Anna Snelling");
    const colunas = await colunasPipeline(escopoDe(anna), {}, "nota", 5);
    const deal = colunas.find((c) => c.estagio === "Engaging")?.cartoes[0];
    expect(deal).toBeDefined();

    novaInstancia();
    const r = await mudarEstagio(anna, deal!.id, deal!.atualizadoEm, "Lost", { motivo: "sem_resposta" });
    expect(r.deal?.estagio).toBe("Lost");
  });

  it("B2: versão realmente antiga continua dando conflito (409)", async () => {
    const { colunasPipeline, escopoDe, mudarEstagio } = await repo();
    const anna = await usuario("vendedor", "Anna Snelling");
    const deal = (await colunasPipeline(escopoDe(anna), {}, "nota", 5)).find((c) => c.estagio === "Prospecting")!.cartoes[0]!;
    await mudarEstagio(anna, deal.id, deal.atualizadoEm, "Engaging");
    await expect(mudarEstagio(anna, deal.id, deal.atualizadoEm, "Lost")).rejects.toMatchObject({ codigo: "GS409" });
  });

  it("B1: marcar ✗ e ✓ funciona mesmo quando a lista do dia foi montada em outra instância", async () => {
    const { marcarPrioridade, prioridadesDoDia } = await repo();
    const anna = await usuario("vendedor", "Anna Snelling");
    const lista = await prioridadesDoDia(anna);
    expect(lista.length).toBeGreaterThan(2);

    novaInstancia();
    await expect(marcarPrioridade(anna, lista[0]!.deal.id, "pulada")).resolves.toBeDefined();

    novaInstancia();
    await expect(marcarPrioridade(anna, lista[1]!.deal.id, "feita", { tipoAtividade: "ligacao", comentario: "Pediu a proposta." })).resolves.toBeDefined();
  });

  it("decisão 37: ✓ sem tipo de atividade ou sem comentário é recusado", async () => {
    const { marcarPrioridade, prioridadesDoDia } = await repo();
    const anna = await usuario("vendedor", "Anna Snelling");
    const [item] = await prioridadesDoDia(anna);
    await expect(marcarPrioridade(anna, item!.deal.id, "feita", { comentario: "sem tipo" })).rejects.toMatchObject({ codigo: "GS400" });
    await expect(marcarPrioridade(anna, item!.deal.id, "feita", { tipoAtividade: "ligacao" })).rejects.toMatchObject({ codigo: "GS400" });
  });

  it("os ids dos usuários seguem o banco: 2 = admin, vendedores em ordem alfabética, depois os managers", async () => {
    const { listarUsuarios } = await repo();
    const us = await listarUsuarios();
    expect(us.find((u) => u.id === 2)?.papel).toBe("admin");
    expect(us.find((u) => u.id === 3)).toMatchObject({ papel: "vendedor", nome: "Anna Snelling" });
    expect(us.filter((u) => u.papel === "vendedor").every((u) => u.id >= 3 && u.id <= 37)).toBe(true);
    expect(us.filter((u) => u.papel === "manager").every((u) => u.id >= 38 && u.id <= 43)).toBe(true);
    expect(us.some((u) => u.id === 1)).toBe(false);
  });
});

describe("ficha da empresa", () => {
  it("os deals abertos seguem o escopo do perfil; os totais históricos são gerais", async () => {
    const { detalheConta } = await repo();
    const anna = await usuario("vendedor", "Anna Snelling");
    const admin = await usuario("admin");
    const dela = await detalheConta("Hottechi", anna);
    const geral = await detalheConta("Hottechi", admin);
    expect(dela.abertos.every((d) => d.vendedor === "Anna Snelling")).toBe(true);
    expect(geral.abertos.length).toBeGreaterThan(dela.abertos.length);
    expect(dela.conta.compras).toBe(geral.conta.compras);
    expect(dela.conta.receitaGanha).toBe(geral.conta.receitaGanha);
  });
});

describe("sem banco e sem a opção de memória", () => {
  it("o app fica somente leitura e recusa a escrita com frase simples", async () => {
    delete process.env.G4_ESCRITA_EM_MEMORIA;
    const { comentar, somenteLeitura } = await repo();
    const anna = await usuario("vendedor", "Anna Snelling");
    expect(somenteLeitura()).toBe(true);
    await expect(comentar(anna, "1C1I7A6R", "teste")).rejects.toMatchObject({ codigo: "GS503" });
  });
});
