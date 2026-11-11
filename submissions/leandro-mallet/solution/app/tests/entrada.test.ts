// O-37 — tela de entrada: cookie de sessão, raiz sempre na entrada (com "Continuar como") e ?voltar= mantido.
import { beforeEach, describe, expect, it, vi } from "vitest";
import { NextRequest } from "next/server";
import type { Usuario } from "@/lib/tipos";

const ANNA = { id: 3, nome: "Anna Snelling", papel: "vendedor", vendedor: "Anna Snelling" } as Usuario;
const estado = vi.hoisted(() => ({ cookie: undefined as string | undefined }));

vi.mock("next/headers", () => ({ cookies: async () => ({ get: () => (estado.cookie ? { value: estado.cookie } : undefined) }) }));
vi.mock("@/server/repositorio", async () => {
  const { ErroCRM } = await import("@/server/banco");
  return {
    ErroCRM,
    usuarioPorId: async (id: number) => (id === 3 ? ANNA : undefined),
    listarUsuarios: async () => [ANNA],
    contagemPorVendedor: async () => new Map([["Anna Snelling", 54]]),
  };
});

beforeEach(() => {
  estado.cookie = undefined;
  vi.spyOn(console, "log").mockImplementation(() => undefined);
});

describe("cookie do perfil", () => {
  it("é de sessão do navegador: sem Max-Age nem Expires, httpOnly", async () => {
    const { POST } = await import("@/app/api/perfil/route");
    const r = await POST(
      new NextRequest("http://localhost/api/perfil", {
        method: "POST",
        headers: { "content-type": "application/json", "x-forwarded-for": "10.9.0.1" },
        body: JSON.stringify({ usuarioId: 3 }),
      }),
    );
    expect(r.status).toBe(200);
    const c = r.headers.get("set-cookie") ?? "";
    expect(c).toMatch(/^g4_perfil=3/);
    expect(c).toMatch(/HttpOnly/i);
    expect(c).not.toMatch(/Max-Age/i);
    expect(c).not.toMatch(/Expires/i);
  });
});

describe("raiz e retorno", () => {
  it("a raiz sempre mostra a entrada; com perfil na sessão, oferece continuar como a pessoa", async () => {
    estado.cookie = "3";
    const { default: Pagina } = await import("@/app/page");
    const el = (await Pagina({ searchParams: Promise.resolve({}) })) as { props: { atual: unknown; destino: string } };
    expect(el.props.atual).toEqual({ nome: "Anna Snelling", papel: "vendedor" });
    expect(el.props.destino).toBe("/painel");
  });

  it("sem perfil, a entrada aparece sem o continuar", async () => {
    const { default: Pagina } = await import("@/app/page");
    const el = (await Pagina({ searchParams: Promise.resolve({}) })) as { props: { atual: unknown } };
    expect(el.props.atual).toBeNull();
  });

  it("?voltar= continua: rota interna sem perfil manda para a entrada e a entrada volta para lá", async () => {
    const { exigirUsuario } = await import("@/server/sessao");
    await expect(exigirUsuario("/pipeline?f=x")).rejects.toMatchObject({ digest: expect.stringContaining("/?voltar=%2Fpipeline%3Ff%3Dx") });
    const { default: Pagina } = await import("@/app/page");
    const ok = (await Pagina({ searchParams: Promise.resolve({ voltar: "/pipeline" }) })) as { props: { destino: string } };
    expect(ok.props.destino).toBe("/pipeline");
    const fora = (await Pagina({ searchParams: Promise.resolve({ voltar: "https://exemplo.com" }) })) as { props: { destino: string } };
    expect(fora.props.destino).toBe("/painel");
  });
});

describe("login (O-47): listas de perfil e usuário", () => {
  const U = [
    { id: 1, papel: "admin", nome: "Admin" },
    { id: 10, papel: "manager", nome: "Rocco Neubert", manager: "Rocco Neubert", regiao: "East" },
    { id: 11, papel: "manager", nome: "Dustin Brinkmann", manager: "Dustin Brinkmann", regiao: "Central" },
    { id: 20, papel: "vendedor", nome: "Zane Levy", manager: "Rocco Neubert", vendedor: "Zane Levy" },
    { id: 21, papel: "vendedor", nome: "Anna Snelling", manager: "Dustin Brinkmann", vendedor: "Anna Snelling" },
    { id: 22, papel: "vendedor", nome: "Boris Faz", manager: "Rocco Neubert", vendedor: "Boris Faz" },
  ] as Usuario[];

  it("sem perfil, a lista de usuários fica vazia", async () => {
    const { usuariosDoPerfil } = await import("@/components/EscolhaPerfil");
    expect(usuariosDoPerfil(U, null)).toEqual([]);
  });

  it("vendedores agrupados por time (times e nomes em ordem alfabética)", async () => {
    const { usuariosDoPerfil } = await import("@/components/EscolhaPerfil");
    expect(usuariosDoPerfil(U, "vendedor")).toEqual([
      { valor: "21", rotulo: "Anna Snelling", grupo: "Time de Dustin Brinkmann (Central)" },
      { valor: "22", rotulo: "Boris Faz", grupo: "Time de Rocco Neubert (East)" },
      { valor: "20", rotulo: "Zane Levy", grupo: "Time de Rocco Neubert (East)" },
    ]);
  });

  it("managers com a região; admin mostra o usuário admin", async () => {
    const { usuariosDoPerfil } = await import("@/components/EscolhaPerfil");
    expect(usuariosDoPerfil(U, "manager").map((o) => o.rotulo)).toEqual(["Dustin Brinkmann · Central", "Rocco Neubert · East"]);
    expect(usuariosDoPerfil(U, "admin")).toEqual([{ valor: "1", rotulo: "Admin" }]);
  });
});
