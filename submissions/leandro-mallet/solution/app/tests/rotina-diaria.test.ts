// O-41 — relógio que anda e rotina diária do score (cron da Vercel), com o banco simulado.
import { beforeEach, describe, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";
import { dataNegocioEm, ehDomingo } from "@/lib/relogio";
import type { MotorScore, Sql } from "@/server/motor/contrato";
import type { Conexao } from "@/server/motor/rotina";

describe("relógio do CRM (decisão 48)", () => {
  it("10/11/2026 = 31/12/2017; 17/11/2026 = 07/01/2018, domingo; anda 1 dia por dia real", () => {
    expect(dataNegocioEm("2026-11-10")).toBe("2017-12-31");
    expect(dataNegocioEm("2026-11-11")).toBe("2018-01-01");
    expect(dataNegocioEm("2026-11-17")).toBe("2018-01-07");
    expect(ehDomingo("2018-01-07")).toBe(true);
    expect(ehDomingo("2018-01-08")).toBe(false);
    expect(dataNegocioEm("2027-11-10")).toBe("2018-12-31");
  });
});

// Banco simulado: responde às consultas da rotina e guarda o que foi gravado; commit só se a função não lançar.
function bancoFalso(opts: { data: string; dow: number; jaRodou?: boolean; trava?: boolean }) {
  const eventos: { tipo: string; detalhe: Record<string, unknown> }[] = [];
  const consultas: string[] = [];
  const conexao: Conexao = {
    async transacao(fn) {
      const pendentes: typeof eventos = [];
      const sql: Sql = async (texto, p = []) => {
        consultas.push(texto);
        if (texto.includes("pg_try_advisory_xact_lock")) return [{ ok: opts.trava ?? true }] as never;
        if (texto.includes("system_data_negocio()::text")) return [{ data: opts.data, dia_real: "2026-11-17", dow: opts.dow }] as never;
        if (texto.includes("system_rotina_ja_rodou")) return [{ rodou: !!opts.jaRodou }] as never;
        if (texto.includes("system_registrar_evento")) pendentes.push({ tipo: String(p[0]), detalhe: JSON.parse(String(p[1])) });
        return [] as never;
      };
      const r = await fn(sql);
      eventos.push(...pendentes); // commit
      return r;
    },
  };
  return { conexao, eventos, consultas };
}

const motorFalso = (falhar = false) => {
  const chamadas: string[] = [];
  const motor: MotorScore = {
    semanal: async (ctx) => {
      chamadas.push(`semanal ${ctx.dataNegocio}`);
      return { redistribuidos: 3 };
    },
    diario: async (ctx) => {
      chamadas.push(`diario ${ctx.dataNegocio} ${ctx.correlationId.length}`);
      if (falhar) throw new Error("falhou no meio");
      return { deals: 2089 };
    },
  };
  return { motor, chamadas };
};

describe("rotina diária", () => {
  it("dia comum: roda só o diário, com o papel de carga e o contexto 'sistema', e registra ok", async () => {
    const { rodarRotina } = await import("@/server/motor/rotina");
    const b = bancoFalso({ data: "2018-01-08", dow: 1 });
    const m = motorFalso();
    const r = await rodarRotina(b.conexao, m.motor, "cron");
    expect(r).toMatchObject({ status: "ok", dataNegocio: "2018-01-08", domingo: false, diario: { deals: 2089 }, semanal: null });
    expect(m.chamadas).toEqual(["diario 2018-01-08 36"]);
    expect(b.consultas[0]).toBe("set local role system_carga");
    expect(b.consultas[1]).toContain("system_iniciar_contexto_sistema");
    expect(b.eventos).toEqual([{ tipo: "rotina_diaria", detalhe: expect.objectContaining({ dia_negocio: "2018-01-08", status: "ok", origem: "cron" }) }]);
    expect(b.consultas.join(" ")).not.toMatch(/\bdelete\b/i);
  });

  it("domingo: roda o semanal antes do diário", async () => {
    const { rodarRotina } = await import("@/server/motor/rotina");
    const m = motorFalso();
    const r = await rodarRotina(bancoFalso({ data: "2018-01-07", dow: 0 }).conexao, m.motor, "cron");
    expect(r).toMatchObject({ status: "ok", domingo: true, semanal: { redistribuidos: 3 } });
    expect(m.chamadas.map((c) => c.split(" ")[0])).toEqual(["semanal", "diario"]);
  });

  it("idempotente: dia que já rodou não roda de novo", async () => {
    const { rodarRotina } = await import("@/server/motor/rotina");
    const b = bancoFalso({ data: "2018-01-08", dow: 1, jaRodou: true });
    const m = motorFalso();
    expect(await rodarRotina(b.conexao, m.motor, "manual")).toMatchObject({ status: "ja_rodou" });
    expect(m.chamadas).toEqual([]);
    expect(b.eventos).toEqual([]);
  });

  it("forçada (O-45): roda mesmo com o dia marcado e registra 'rotina_forcada'; o cron nunca força", async () => {
    const { rodarRotina } = await import("@/server/motor/rotina");
    const b = bancoFalso({ data: "2017-12-31", dow: 0, jaRodou: true });
    const m = motorFalso();
    const r = await rodarRotina(b.conexao, m.motor, "manual", { forcar: true });
    expect(r).toMatchObject({ status: "ok", dataNegocio: "2017-12-31", domingo: true });
    expect(m.chamadas.map((c) => c.split(" ")[0])).toEqual(["semanal", "diario"]);
    expect(b.eventos).toEqual([{ tipo: "rotina_forcada", detalhe: expect.objectContaining({ dia_negocio: "2017-12-31", origem: "manual" }) }]);
    expect(b.consultas.join(" ")).not.toMatch(/delete/i);
    // o cron ignora o pedido de forçar
    const c = bancoFalso({ data: "2017-12-31", dow: 0, jaRodou: true });
    const m2 = motorFalso();
    expect(await rodarRotina(c.conexao, m2.motor, "cron", { forcar: true })).toMatchObject({ status: "ja_rodou" });
    expect(m2.chamadas).toEqual([]);
  });

  it("outra rotina rodando: sai sem fazer nada", async () => {
    const { rodarRotina } = await import("@/server/motor/rotina");
    const m = motorFalso();
    expect(await rodarRotina(bancoFalso({ data: "2018-01-08", dow: 1, trava: false }).conexao, m.motor, "cron")).toMatchObject({ status: "ocupada" });
    expect(m.chamadas).toEqual([]);
  });

  it("erro: desfaz a transação e registra a falha à parte", async () => {
    const { rodarRotina } = await import("@/server/motor/rotina");
    const b = bancoFalso({ data: "2018-01-08", dow: 1 });
    const r = await rodarRotina(b.conexao, motorFalso(true).motor, "cron");
    expect(r).toMatchObject({ status: "falha", dataNegocio: "2018-01-08", erro: "falhou no meio" });
    // o "ok" da transação que falhou não foi gravado; só o registro da falha
    expect(b.eventos).toEqual([{ tipo: "rotina_diaria_falha", detalhe: { dia_negocio: "2018-01-08", origem: "cron", erro: "falhou no meio" } }]);
  });

  it("sem o motor do score instalado: registra 'sem_motor' e o dia não conta como rodado", async () => {
    const { rodarRotina } = await import("@/server/motor/rotina");
    const b = bancoFalso({ data: "2018-01-08", dow: 1 });
    expect(await rodarRotina(b.conexao, null, "cron")).toMatchObject({ status: "sem_motor" });
    expect(b.eventos[0]).toMatchObject({ tipo: "rotina_diaria", detalhe: { status: "sem_motor" } });
  });
});

describe("rotas da rotina", () => {
  const rodar = vi.hoisted(() => vi.fn<(origem: string, opcoes?: { forcar?: boolean }) => Promise<unknown>>(async () => ({ status: "ok", dataNegocio: "2018-01-08", domingo: false })));
  vi.mock("@/server/motor/responder", async () => {
    const { NextResponse } = await import("next/server");
    const { rotinaAutorizada } = await import("@/server/motor/autorizacao");
    return {
      responderRotina: async (req: NextRequest, origem: string, opcoes?: { forcar?: boolean }) => {
        if (!rotinaAutorizada(req.headers.get("authorization"))) return NextResponse.json({ erro: "Não autorizado." }, { status: 401 });
        return NextResponse.json(await rodar(origem, opcoes), { status: 200 });
      },
    };
  });

  beforeEach(() => {
    rodar.mockClear();
    process.env.CRON_SECRET = "segredo-de-teste-123";
  });

  const pedido = (metodo: "GET" | "POST", url: string, auth?: string) =>
    new NextRequest(`http://localhost${url}`, { method: metodo, headers: auth ? { authorization: auth } : {} });

  it("sem o segredo, segredo errado ou sem CRON_SECRET configurado: 401 e nada roda", async () => {
    const { GET } = await import("@/app/api/rotina/diaria/route");
    const { POST } = await import("@/app/api/rotina/rodar-agora/route");
    expect((await GET(pedido("GET", "/api/rotina/diaria"))).status).toBe(401);
    expect((await GET(pedido("GET", "/api/rotina/diaria", "Bearer errado"))).status).toBe(401);
    expect((await POST(pedido("POST", "/api/rotina/rodar-agora", "segredo-de-teste-123"))).status).toBe(401);
    delete process.env.CRON_SECRET;
    expect((await GET(pedido("GET", "/api/rotina/diaria", "Bearer "))).status).toBe(401);
    expect(rodar).not.toHaveBeenCalled();
  });

  it("com o segredo, o cron (GET) e o manual (POST) rodam", async () => {
    const { GET } = await import("@/app/api/rotina/diaria/route");
    const { POST } = await import("@/app/api/rotina/rodar-agora/route");
    expect((await GET(pedido("GET", "/api/rotina/diaria", "Bearer segredo-de-teste-123"))).status).toBe(200);
    expect((await POST(pedido("POST", "/api/rotina/rodar-agora", "Bearer segredo-de-teste-123"))).status).toBe(200);
    expect(rodar.mock.calls.map((c) => c[0])).toEqual(["cron", "manual"]);
  });

  it("POST ?forcar=1 pede a rodada forçada; sem o parâmetro, não; o GET do cron nunca", async () => {
    const { GET } = await import("@/app/api/rotina/diaria/route");
    const { POST } = await import("@/app/api/rotina/rodar-agora/route");
    await POST(pedido("POST", "/api/rotina/rodar-agora?forcar=1", "Bearer segredo-de-teste-123"));
    await POST(pedido("POST", "/api/rotina/rodar-agora", "Bearer segredo-de-teste-123"));
    await GET(pedido("GET", "/api/rotina/diaria?forcar=1", "Bearer segredo-de-teste-123"));
    expect(rodar.mock.calls.map((c) => [c[0], c[1]?.forcar ?? false])).toEqual([["manual", true], ["manual", false], ["cron", false]]);
    expect((await POST(pedido("POST", "/api/rotina/rodar-agora?forcar=1"))).status).toBe(401);
  });
});

describe("cron configurado", () => {
  it("vercel.json chama /api/rotina/diaria às 06:00 UTC (03:00 de Brasília)", async () => {
    const { readFileSync } = await import("node:fs");
    const cfg = JSON.parse(readFileSync("vercel.json", "utf8")) as { crons: { path: string; schedule: string }[] };
    expect(cfg.crons).toEqual([{ path: "/api/rotina/diaria", schedule: "0 6 * * *" }]);
  });
});
