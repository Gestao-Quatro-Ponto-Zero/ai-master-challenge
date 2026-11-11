"use client";
// Entrada (O-47): tela de login clássica, sem senha (decisão 16). Um cartão estreito e centralizado com
// "Selecione o Perfil" e "Selecione o Usuário" (listas suspensas) e o botão Login; ao lado, em telas largas,
// o bloco no azul do deck com o nome e o que é o G4 Sight. Com perfil na sessão, "Continuar como <nome>" embaixo.
// Teclado: Tab segue Perfil → Usuário → Login; escolher o usuário leva o foco ao Login, e Enter entra.
import { useMemo, useRef, useState, type FormEvent } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { pedir } from "@/lib/cliente";
import type { Papel, Usuario } from "@/lib/tipos";
import { classeBotao } from "./ui/Botao";
import { ErroFormulario, Rotulo } from "./ui/Campo";
import { Seletor, type Opcao } from "./ui/Seletor";

type UsuarioLista = Usuario & { abertos?: number };

const PERFIS: Opcao[] = [
  { valor: "vendedor", rotulo: "Vendedor" },
  { valor: "manager", rotulo: "Manager" },
  { valor: "admin", rotulo: "Admin" },
];

const porNome = (a: Usuario, b: Usuario) => a.nome.localeCompare(b.nome, "pt-BR");

/** Os nomes do perfil escolhido. Vendedores vêm agrupados pelo time (manager e região), em ordem alfabética. */
export function usuariosDoPerfil(usuarios: Usuario[], papel: Papel | null): Opcao[] {
  if (!papel) return [];
  const doPapel = usuarios.filter((u) => u.papel === papel);
  if (papel !== "vendedor") return [...doPapel].sort(porNome).map((u) => ({ valor: String(u.id), rotulo: papel === "manager" && u.regiao ? `${u.nome} · ${u.regiao}` : u.nome }));
  const managers = usuarios.filter((u) => u.papel === "manager").sort(porNome);
  const times = managers.map((m) => ({ titulo: `Time de ${m.nome}${m.regiao ? ` (${m.regiao})` : ""}`, chave: m.manager }));
  const semTime = doPapel.filter((v) => !managers.some((m) => m.manager === v.manager));
  return [
    ...times.flatMap((t) => doPapel.filter((v) => v.manager === t.chave).sort(porNome).map((v) => ({ valor: String(v.id), rotulo: v.nome, grupo: t.titulo }))),
    ...semTime.sort(porNome).map((v) => ({ valor: String(v.id), rotulo: v.nome, grupo: "Sem time" })),
  ];
}

export function EscolhaPerfil({ usuarios, destino, atual }: { usuarios: UsuarioLista[]; destino: string; atual: { nome: string; papel: Papel } | null }) {
  const [papel, setPapel] = useState<Papel | null>(null);
  const [usuarioId, setUsuarioId] = useState("");
  const [entrando, setEntrando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const login = useRef<HTMLButtonElement>(null);
  const router = useRouter();

  const opcoesUsuario = useMemo(() => usuariosDoPerfil(usuarios, papel), [usuarios, papel]);

  function escolherPerfil(valor: string) {
    const p = valor as Papel;
    setPapel(p);
    setErro(null);
    // Admin tem um usuário só: já vem escolhido.
    const lista = usuariosDoPerfil(usuarios, p);
    setUsuarioId(lista.length === 1 ? lista[0]!.valor : "");
  }

  function escolherUsuario(valor: string) {
    setUsuarioId(valor);
    setErro(null);
    // Depois do Seletor devolver o foco ao próprio botão, o foco vai para o Login.
    requestAnimationFrame(() => login.current?.focus());
  }

  async function entrar(e: FormEvent) {
    e.preventDefault();
    if (entrando) return;
    if (!papel) return setErro("Selecione o perfil para entrar.");
    if (!usuarioId) return setErro("Selecione o usuário para entrar.");
    setEntrando(true);
    setErro(null);
    const r = await pedir("/api/perfil", "POST", { usuarioId: Number(usuarioId) });
    if (!r.ok) {
      setErro(r.erro ?? "Não foi possível entrar. Tente de novo.");
      setEntrando(false);
      return;
    }
    router.push(destino);
    router.refresh();
  }

  return (
    <div className="mx-auto grid w-full max-w-4xl items-stretch py-2 sm:py-8 lg:grid-cols-[minmax(0,1fr)_400px]">
      {/* Destaque no azul do deck, só em telas largas: o nome e o que é */}
      <section className="fundo-escuro hidden rounded-l-cartao border border-escuro-1 px-10 py-8 text-claro-2 lg:flex lg:flex-col lg:justify-center">
        <p className="font-titulo text-3xl font-bold text-claro sm:text-4xl">
          G4 <span className="text-ouro">Sight</span>
        </p>
        <p className="mt-3 max-w-md text-base sm:text-lg">CRM do time comercial com a prioridade do dia dentro do pipeline.</p>
      </section>

      <form
        onSubmit={entrar}
        noValidate
        aria-labelledby="t-login"
        className="mx-auto grid w-full max-w-[400px] gap-5 rounded-cartao border border-borda bg-superficie p-6 shadow-cartao sm:p-8 lg:max-w-none lg:rounded-l-none lg:border-l-0"
      >
        <div>
          <h1 id="t-login" className="font-titulo text-2xl font-bold">
            G4 <span className="text-dourado">Sight</span>
          </h1>
          <p className="mt-1 text-sm text-texto-2">Login sem senha.</p>
        </div>

        <Rotulo texto="Selecione o Perfil">
          <Seletor rotulo="Selecione o Perfil" textoVazio="Selecione o Perfil" valor={papel ?? ""} opcoes={PERFIS} onMudar={escolherPerfil} desligado={entrando} className="w-full" />
        </Rotulo>

        <Rotulo texto="Selecione o Usuário">
          <Seletor
            rotulo="Selecione o Usuário"
            textoVazio={papel ? "Selecione o Usuário" : "Escolha o perfil primeiro"}
            valor={usuarioId}
            opcoes={opcoesUsuario}
            onMudar={escolherUsuario}
            desligado={!papel || entrando}
            className="w-full"
          />
        </Rotulo>

        <ErroFormulario texto={erro} />

        <button ref={login} type="submit" disabled={entrando} className={classeBotao("primario", "normal", "w-full")}>
          {entrando ? "Entrando…" : "Login"}
        </button>

        {atual ? (
          <p className="text-center text-sm text-texto-2">
            <Link href={destino} className="underline underline-offset-2 hover:text-texto">
              Continuar como {atual.nome}
            </Link>
          </p>
        ) : null}
      </form>
    </div>
  );
}
