"use client";
// "Quem é você?": vendedor, manager ou admin; vendedor e manager escolhem o nome (sem senha).
import { useState } from "react";
import { useRouter } from "next/navigation";
import { pedir } from "@/lib/cliente";
import { plural } from "@/lib/calculos";
import type { Papel, Usuario } from "@/lib/tipos";

type UsuarioLista = Usuario & { abertos?: number };

const PAPEIS: { papel: Papel; titulo: string; texto: string }[] = [
  { papel: "vendedor", titulo: "Vendedor", texto: "Vejo o meu dia e o meu pipeline." },
  { papel: "manager", titulo: "Manager", texto: "Acompanho o pipeline do meu time." },
  { papel: "admin", titulo: "Admin", texto: "Vejo todos os times." },
];

export function EscolhaPerfil({ usuarios, destino }: { usuarios: UsuarioLista[]; destino: string }) {
  const [papel, setPapel] = useState<Papel | null>(null);
  const [entrando, setEntrando] = useState<number | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const router = useRouter();

  async function entrar(u: Usuario) {
    setEntrando(u.id);
    setErro(null);
    const r = await pedir("/api/perfil", "POST", { usuarioId: u.id });
    if (!r.ok) {
      setErro(r.erro ?? "Não foi possível entrar. Tente de novo.");
      setEntrando(null);
      return;
    }
    router.push(destino);
    router.refresh();
  }

  function escolherPapel(p: Papel) {
    if (p === "admin") {
      const admin = usuarios.find((u) => u.papel === "admin");
      if (admin) void entrar(admin);
      return;
    }
    setPapel(p);
  }

  const managers = usuarios.filter((u) => u.papel === "manager");
  const vendedores = usuarios.filter((u) => u.papel === "vendedor");

  return (
    <div className="mx-auto max-w-4xl py-6">
      <h1 className="text-3xl font-bold">Quem é você?</h1>
      <p className="mt-2 text-texto-2">Escolha o seu perfil para ver o que importa hoje. Não precisa de senha.</p>
      {erro ? (
        <p role="alert" className="mt-4 rounded-controle border border-erro bg-erro-fundo px-3 py-2 text-sm text-erro">
          {erro}
        </p>
      ) : null}

      <div className="mt-6 grid gap-3 sm:grid-cols-3">
        {PAPEIS.map((p) => (
          <button
            key={p.papel}
            onClick={() => escolherPapel(p.papel)}
            aria-pressed={papel === p.papel}
            disabled={entrando !== null}
            className={`rounded-cartao border px-5 py-4 text-left shadow-cartao ${
              papel === p.papel ? "border-marinho bg-marinho text-branco" : "border-linha-forte bg-marfim hover:border-marinho"
            }`}
          >
            <span className="block font-titulo text-xl font-bold">{p.titulo}</span>
            <span className={`mt-1 block text-sm ${papel === p.papel ? "text-dourado-claro" : "text-texto-2"}`}>{p.texto}</span>
          </button>
        ))}
      </div>

      {papel === "manager" ? (
        <section className="mt-8 animate-entrar" aria-label="Managers">
          <h2 className="text-lg font-bold">Escolha o seu nome</h2>
          <ul className="mt-3 grid gap-2 sm:grid-cols-2">
            {managers.map((m) => (
              <li key={m.id}>
                <BotaoNome
                  nome={m.nome}
                  detalhe={`${m.regiao} · ${plural(vendedores.filter((v) => v.manager === m.manager).length, "vendedor", "vendedores")}`}
                  carregando={entrando === m.id}
                  desligado={entrando !== null}
                  onClick={() => entrar(m)}
                />
              </li>
            ))}
          </ul>
        </section>
      ) : null}

      {papel === "vendedor" ? (
        <section className="mt-8 animate-entrar" aria-label="Vendedores">
          <h2 className="text-lg font-bold">Escolha o seu nome</h2>
          <div className="mt-3 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {managers.map((m) => (
              <div key={m.id}>
                <h3 className="mb-2 font-texto text-sm font-semibold text-texto-2">
                  Time de {m.nome} ({m.regiao})
                </h3>
                <ul className="grid gap-2">
                  {vendedores
                    .filter((v) => v.manager === m.manager)
                    .map((v) => (
                      <li key={v.id}>
                        <BotaoNome
                          nome={v.nome}
                          detalhe={plural(v.abertos ?? 0, "deal aberto", "deals abertos")}
                          carregando={entrando === v.id}
                          desligado={entrando !== null}
                          onClick={() => entrar(v)}
                        />
                      </li>
                    ))}
                </ul>
              </div>
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}

function BotaoNome({ nome, detalhe, carregando, desligado, onClick }: { nome: string; detalhe: string; carregando: boolean; desligado: boolean; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      disabled={desligado}
      className="flex w-full items-center justify-between gap-3 rounded-controle border border-linha bg-fundo px-3 py-2 text-left hover:border-marinho disabled:opacity-60"
    >
      <span className="font-semibold">{carregando ? "Entrando…" : nome}</span>
      <span className="text-xs text-texto-2">{detalhe}</span>
    </button>
  );
}
