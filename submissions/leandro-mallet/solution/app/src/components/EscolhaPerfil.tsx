"use client";
// Entrada (O-37): fundo branco, bloco de destaque no azul do deck com o nome e o que é o G4 Sight, e a escolha do
// papel em 3 cartões grandes. Vendedor e manager escolhem o nome (sem senha, decisão 16); admin entra direto.
// Com perfil na sessão, oferece "Continuar como <nome>" além da escolha.
import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { pedir } from "@/lib/cliente";
import { plural } from "@/lib/calculos";
import type { Papel, Usuario } from "@/lib/tipos";
import { ErroFormulario } from "./ui/Campo";
import { Icone, type NomeIcone } from "./ui/Icones";

type UsuarioLista = Usuario & { abertos?: number };

const PAPEIS: { papel: Papel; titulo: string; texto: string; icone: NomeIcone }[] = [
  { papel: "vendedor", titulo: "Vendedor", texto: "Vejo o meu dia e o meu pipeline.", icone: "conversa" },
  { papel: "manager", titulo: "Manager", texto: "Acompanho o pipeline do meu time.", icone: "pessoas" },
  { papel: "admin", titulo: "Admin", texto: "Vejo todos os times.", icone: "trofeu" },
];

const ROTULO_PAPEL: Record<Papel, string> = { vendedor: "vendas", manager: "manager", admin: "admin" };

export function EscolhaPerfil({ usuarios, destino, atual }: { usuarios: UsuarioLista[]; destino: string; atual: { nome: string; papel: Papel } | null }) {
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
    <div className="mx-auto grid max-w-5xl gap-8 py-2 sm:py-6">
      {/* Destaque no azul do deck: o nome e o que é */}
      <section className="fundo-escuro rounded-cartao border border-escuro-1 px-6 py-8 text-claro-2 sm:px-10 sm:py-12 [&_*:focus-visible]:outline-ouro">
        <p className="font-titulo text-3xl font-bold text-claro sm:text-4xl">
          G4 <span className="text-ouro">Sight</span>
        </p>
        <p className="mt-3 max-w-2xl text-base sm:text-lg">CRM do time comercial com a prioridade do dia dentro do pipeline.</p>
        {atual ? (
          <div className="mt-6 flex flex-wrap items-center gap-3 border-t border-fio-ouro pt-5">
            <Link
              href={destino}
              className="inline-flex h-10 items-center gap-2 rounded-selo bg-ouro px-5 text-sm font-semibold text-escuro-2 hover:bg-dourado-claro"
            >
              Continuar como {atual.nome}
              <Icone nome="seta-cima" className="h-4 w-4 rotate-90" />
            </Link>
            <span className="text-sm text-claro-3">ou escolha outro perfil abaixo.</span>
          </div>
        ) : null}
      </section>

      <section aria-labelledby="t-quem">
        <h1 id="t-quem" className="text-2xl font-bold sm:text-3xl">
          Quem é você?
        </h1>
        <p className="mt-2 text-texto-2">Escolha o seu perfil para ver o que importa hoje. Não precisa de senha.</p>
        {atual ? <p className="mt-1 text-sm text-texto-2">Agora: {atual.nome}, {ROTULO_PAPEL[atual.papel]}.</p> : null}
        {erro ? (
          <div className="mt-4">
            <ErroFormulario texto={erro} />
          </div>
        ) : null}

        <div className="mt-6 grid gap-3 sm:grid-cols-3">
          {PAPEIS.map((p) => {
            const ativo = papel === p.papel;
            return (
              <button
                key={p.papel}
                type="button"
                onClick={() => escolherPapel(p.papel)}
                aria-pressed={ativo}
                disabled={entrando !== null}
                className={`group flex min-h-36 flex-col items-start gap-3 rounded-cartao border p-5 text-left transition-colors disabled:opacity-60 ${
                  ativo ? "border-marinho bg-marinho text-branco" : "border-borda bg-superficie hover:border-marinho hover:bg-superficie-2"
                }`}
              >
                <span className={`inline-flex h-10 w-10 items-center justify-center rounded-controle ${ativo ? "bg-ouro text-escuro-2" : "bg-marinho text-branco"}`} aria-hidden>
                  <Icone nome={p.icone} className="h-5 w-5" />
                </span>
                <span>
                  <span className="block font-titulo text-xl font-bold">{p.titulo}</span>
                  <span className={`mt-1 block text-sm ${ativo ? "text-dourado-claro" : "text-texto-2"}`}>{p.texto}</span>
                </span>
              </button>
            );
          })}
        </div>
      </section>

      {papel === "manager" ? (
        <section className="motion-safe:animate-entrar" aria-label="Managers">
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
        <section className="motion-safe:animate-entrar" aria-label="Vendedores">
          <h2 className="text-lg font-bold">Escolha o seu nome</h2>
          <div className="mt-3 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {managers.map((m) => (
              <div key={m.id}>
                <h3 className="mb-2 text-sm font-semibold text-texto-2">
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
      type="button"
      onClick={onClick}
      disabled={desligado}
      className="flex min-h-10 w-full items-center justify-between gap-3 rounded-controle border border-borda bg-superficie px-3 py-2 text-left hover:border-marinho hover:bg-superficie-2 disabled:opacity-60"
    >
      <span className="font-semibold">{carregando ? "Entrando…" : nome}</span>
      <span className="text-xs text-texto-2">{detalhe}</span>
    </button>
  );
}
