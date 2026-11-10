// Achados leves do teste online com o banco (N1, N2 e N3), reproduzidos na reserva em memória.
//   N1 — "Contém" procurava a frase inteira; agora procura cada palavra.
//   N2 — faltava o "Desfazer este lote" por 24 horas.
//   N3 — o contador "X de 10 feitas" subia também com o ✗.
import { beforeEach, describe, expect, it } from "vitest";
import { atendeDeal, contemTodas } from "@/lib/filtro/aplicar";
import { juntar } from "@/lib/filtro/etiquetas";
import { interpretar } from "@/lib/filtro/interpretar";
import { fraseLoteDesfeito, lotesRecentesPara, type LoteBruto } from "@/lib/lotes";
import { resumoPrioridades } from "@/lib/prioridades";
import type { Usuario } from "@/lib/tipos";

const g = globalThis as { __g4Estado?: unknown };

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
  g.__g4Estado = undefined;
});

describe("N1: filtro livre, etiqueta Contém", () => {
  it("procura cada palavra, em qualquer ordem, sem acento nem maiúscula", () => {
    const nome = "Teste de persistência (pode encerrar)";
    expect(contemTodas(nome, "teste persistencia")).toBe(true);
    expect(contemTodas(nome, "PERSISTÊNCIA teste")).toBe(true);
    expect(contemTodas(nome, "encerrar teste")).toBe(true);
    expect(contemTodas(nome, "teste inexistente")).toBe(false);
    expect(contemTodas(nome, "  ")).toBe(true);
  });

  it("\"Teste de persistência\" acha o lead \"Teste de persistência (pode encerrar)\"", async () => {
    const { buscarDeals, contextoFiltro, criarDeal, escopoDe, listarProdutos } = await repo();
    const anna = await usuario("vendedor", "Anna Snelling");
    const [produto] = await listarProdutos();
    const { id } = await criarDeal(anna, { produto: produto!.nome, estagio: "Prospecting", nome: "Teste de persistência (pode encerrar)" });

    const { etiquetas } = interpretar("Teste de persistência", await contextoFiltro("leads", anna));
    expect(etiquetas.map((e) => e.chave)).toEqual(["contem"]);
    const pagina = await buscarDeals(escopoDe(anna), juntar(etiquetas), "padrao_leads");
    expect(pagina.linhas.map((d) => d.id)).toContain(id);

    // A frase que não bate em todas as palavras continua sem achar.
    const outra = await buscarDeals(escopoDe(anna), juntar(interpretar("Teste de zzzinexistente", await contextoFiltro("leads", anna)).etiquetas), "padrao_leads");
    expect(outra.linhas.map((d) => d.id)).not.toContain(id);
  });

  it("vale também para as outras colunas do lead (produto, empresa, vendedor)", async () => {
    const { buscarDeals, escopoDe } = await repo();
    const anna = await usuario("vendedor", "Anna Snelling");
    const [d] = (await buscarDeals(escopoDe(anna), {}, "padrao_leads", 0, 500)).linhas.filter((x) => x.conta && x.produto);
    expect(d).toBeDefined();
    const palavras = `${d!.produto.split(" ")[0]} ${d!.conta!.split(" ")[0]}`;
    expect(atendeDeal(d!, { contem: palavras }, "2017-12-31")).toBe(true);
    expect(atendeDeal(d!, { contem: `${d!.conta!.split(" ")[0]} ${d!.produto.split(" ")[0]}` }, "2017-12-31")).toBe(true);
  });
});

describe("N3: contador das Prioridades do dia", () => {
  it("\"feitas\" conta só o ✓; pulada e contato por fora não contam", () => {
    const itens = [
      ...Array.from({ length: 2 }, () => ({ marcada: "feita" as const })),
      ...Array.from({ length: 3 }, () => ({ marcada: "pulada" as const })),
      { marcada: "contato" as const },
      ...Array.from({ length: 4 }, () => ({ marcada: null })),
    ];
    expect(resumoPrioridades(itens)).toEqual({ feitas: 2, puladas: 3, pendentes: 4, meta: 10 });
  });

  it("na lista real: ✗ não sobe o contador, ✓ sobe", async () => {
    const { marcarPrioridade, prioridadesDoDia } = await repo();
    const anna = await usuario("vendedor", "Anna Snelling");
    const lista = await prioridadesDoDia(anna);
    expect(lista.length).toBeGreaterThan(2);

    await marcarPrioridade(anna, lista[0]!.deal.id, "pulada");
    expect(resumoPrioridades(await prioridadesDoDia(anna))).toMatchObject({ feitas: 0, puladas: 1 });

    await marcarPrioridade(anna, lista[1]!.deal.id, "feita", { tipoAtividade: "ligacao", comentario: "Pediu a proposta." });
    expect(resumoPrioridades(await prioridadesDoDia(anna))).toMatchObject({ feitas: 1, puladas: 1 });
  });
});

describe("N2: desfazer este lote por 24 horas", () => {
  const AGORA = Date.parse("2026-11-10T12:00:00.000Z");
  const horasAtras = (h: number) => new Date(AGORA - h * 3_600_000).toISOString();
  const pessoas: Usuario[] = [
    { id: 2, papel: "admin", nome: "Admin" },
    { id: 3, papel: "vendedor", nome: "Ana", vendedor: "Ana", manager: "Marta" },
    { id: 4, papel: "vendedor", nome: "Beto", vendedor: "Beto", manager: "Marta" },
    { id: 5, papel: "vendedor", nome: "Caio", vendedor: "Caio", manager: "Nuno" },
    { id: 38, papel: "manager", nome: "Marta", manager: "Marta" },
    { id: 39, papel: "manager", nome: "Nuno", manager: "Nuno" },
  ];
  const pessoa = (id: number) => pessoas.find((p) => p.id === id)!;
  const lote = (id: number, usuarioId: number, horas: number, extra: Partial<LoteBruto> = {}): LoteBruto => ({
    id, tipo: "comentar", usuarioId, criadoEm: horasAtras(horas), aplicados: 3, pulados: 1, desfeitoEm: null, desfeitoPorId: null, ...extra,
  });
  const lotes = [lote(1, 3, 1), lote(2, 4, 2), lote(3, 5, 3), lote(4, 38, 4), lote(5, 3, 25), lote(6, 3, 23.9, { desfeitoEm: horasAtras(1), desfeitoPorId: 38 })];
  const ids = (u: Usuario) => lotesRecentesPara(lotes, u, pessoas, AGORA).map((l) => l.id);

  it("o vendedor vê só os próprios lotes das últimas 24 horas", () => {
    expect(ids(pessoa(3))).toEqual([1, 6]);
    expect(ids(pessoa(4))).toEqual([2]);
  });

  it("o manager vê os próprios e os do seu time; o admin vê todos", () => {
    expect(ids(pessoa(38))).toEqual([1, 2, 4, 6]);
    expect(ids(pessoa(39))).toEqual([3]);
    expect(ids(pessoa(2))).toEqual([1, 2, 3, 4, 6]);
  });

  it("lote com mais de 24 horas não aparece; o desfeito aparece com quem desfez", () => {
    const meus = lotesRecentesPara(lotes, pessoa(3), pessoas, AGORA);
    expect(meus.find((l) => l.id === 5)).toBeUndefined();
    expect(meus.find((l) => l.id === 6)).toMatchObject({ desfeitoPor: "Marta", meu: true, rotulo: "Comentar" });
    expect(meus.find((l) => l.id === 1)).toMatchObject({ desfeitoEm: null, desfazerAte: horasAtras(1 - 24) });
  });

  it("a frase do aviso diz o que voltou e o que ficou", () => {
    expect(fraseLoteDesfeito({ restaurados: 1, pulados: 0 })).toBe("Lote desfeito: 1 mudança desfeita.");
    expect(fraseLoteDesfeito({ restaurados: 12, pulados: 2 })).toBe("Lote desfeito: 12 mudanças desfeitas; 2 ficaram como estão, porque o lead mudou depois.");
  });

  it("na prática: aplica o lote, ele aparece em Lotes recentes e dá para desfazer depois do aviso", async () => {
    const { buscarDeals, desfazer, detalheDeal, escopoDe, executarLote, lotesRecentes } = await repo();
    const anna = await usuario("vendedor", "Anna Snelling");
    const outro = (await (await repo()).listarUsuarios()).find((u) => u.papel === "vendedor" && u.id !== anna.id && u.manager !== anna.manager)!;
    const manager = (await (await repo()).listarUsuarios()).find((u) => u.papel === "manager" && u.manager === anna.manager)!;
    const admin = await usuario("admin");
    const alvo = (await buscarDeals(escopoDe(anna), { estagios: ["Prospecting"] }, "padrao_leads", 0, 2)).linhas.map((d) => d.id);
    expect(alvo).toHaveLength(2);

    const r = await executarLote(anna, "avancar_estagio", alvo, {});
    expect(r).toMatchObject({ aplicados: 2, pulados: 0 });

    // Aparece para quem aplicou, para o manager do time e para o admin; não para outro vendedor.
    expect((await lotesRecentes(anna)).map((l) => l.id)).toEqual([r.loteId]);
    expect((await lotesRecentes(manager)).map((l) => l.id)).toEqual([r.loteId]);
    expect((await lotesRecentes(admin)).map((l) => l.id)).toEqual([r.loteId]);
    expect(await lotesRecentes(outro)).toEqual([]);
    await expect(desfazer(outro, `lote:${r.loteId}`)).rejects.toMatchObject({ codigo: "GS403" });

    // Um dos leads muda depois do lote: ele fica como está; o outro volta.
    const { mudarEstagio } = await repo();
    const mexido = (await detalheDeal(alvo[0]!, anna)).deal;
    await mudarEstagio(anna, mexido.id, mexido.atualizadoEm, "Lost", { motivo: "preco" });

    await expect(desfazer(anna, `lote:${r.loteId}`)).resolves.toEqual({ restaurados: 1, pulados: 1 });
    expect((await detalheDeal(alvo[1]!, anna)).deal.estagio).toBe("Prospecting");
    expect((await detalheDeal(alvo[0]!, anna)).deal.estagio).toBe("Lost");

    const depois = await lotesRecentes(anna);
    expect(depois[0]).toMatchObject({ id: r.loteId, desfeitoPor: anna.nome });
    expect(depois[0]!.desfeitoEm).not.toBeNull();
    await expect(desfazer(anna, `lote:${r.loteId}`)).rejects.toMatchObject({ codigo: "GS422" });
  });
});
