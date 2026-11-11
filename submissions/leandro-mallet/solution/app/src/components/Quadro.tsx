"use client";
// Quadro do Pipeline (O-31): cinco colunas, uma por etapa (Novo lead, Atendimento, Em negociação, Fechado,
// Perdido). Mudança de etapa por arraste ou pelo controle do cartão. Soltar em Atendimento abre o registro
// do contato; em Fechado, o valor; em Perdido, o motivo.
import { useState } from "react";
import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { dataBR, dinheiro, dinheiroCurto, plural } from "@/lib/calculos";
import { ROTULO_ETAPA, type Etapa } from "@/lib/etapas";
import type { DealVisao, Papel } from "@/lib/tipos";
import { SeletorEstagio, transicoesDe, useMudarEstagio } from "./Estagio";
import { BarraNota, IconeDeal } from "./Nota";
import { classeBotao } from "./ui/Botao";
import { classeCartao } from "./ui/Superficie";

export interface Coluna {
  etapa: Etapa;
  total: number;
  valor: number;
  cartoes: DealVisao[];
}

export function Quadro({ colunas, papel, somenteLeitura, mostrarVendedor }: { colunas: Coluna[]; papel: Papel; somenteLeitura: boolean; mostrarVendedor: boolean }) {
  const mudar = useMudarEstagio();
  const params = useSearchParams();
  const caminho = usePathname();
  const [arrastando, setArrastando] = useState<DealVisao | null>(null);
  const [sobre, setSobre] = useState<Etapa | null>(null);
  const [aba, setAba] = useState<Etapa>("negociacao");

  const linkDeal = (id: string) => {
    const p = new URLSearchParams(params.toString());
    p.set("deal", id);
    return `${caminho}?${p}`;
  };
  const maisCartoes = (etapa: string, mostrados: number) => {
    const p = new URLSearchParams(params.toString());
    p.set("n", String(mostrados + 50));
    p.delete("deal");
    return `${caminho}?${p}#col-${etapa}`;
  };
  const aceita = (para: Etapa) => !!arrastando && transicoesDe(arrastando, papel).includes(para);

  function soltar(para: Etapa) {
    const d = arrastando;
    setArrastando(null);
    setSobre(null);
    if (d && transicoesDe(d, papel).includes(para)) void mudar(d, para);
  }

  const alvo = (para: Etapa) => ({
    onDragOver: (e: React.DragEvent) => {
      if (!aceita(para)) return;
      e.preventDefault();
      setSobre(para);
    },
    onDragLeave: () => setSobre((s) => (s === para ? null : s)),
    onDrop: (e: React.DragEvent) => {
      e.preventDefault();
      soltar(para);
    },
  });

  return (
    <div>
      {/* Celular: uma coluna por vez, escolhida nestas abas (rolam para o lado se não couberem). */}
      <div role="tablist" aria-label="Etapa" className="mb-3 flex gap-1 overflow-x-auto rounded-controle border border-borda bg-superficie-2 p-1 md:hidden">
        {colunas.map((c) => (
          <button
            key={c.etapa}
            type="button"
            role="tab"
            aria-selected={aba === c.etapa}
            onClick={() => setAba(c.etapa)}
            className={`h-8 shrink-0 rounded-controle px-3 text-sm font-semibold whitespace-nowrap ${aba === c.etapa ? "bg-superficie text-marinho shadow-menu" : "text-texto-2"}`}
          >
            {ROTULO_ETAPA[c.etapa]} <span className="font-normal">({c.total})</span>
          </button>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-3 md:grid-cols-2 xl:grid-cols-5">
        {colunas.map((c) => (
          <section
            key={c.etapa}
            id={`col-${c.etapa}`}
            aria-labelledby={`t-${c.etapa}`}
            {...alvo(c.etapa)}
            className={`min-w-0 rounded-cartao border p-2.5 ${aba === c.etapa ? "" : "hidden md:block"} ${
              sobre === c.etapa ? "border-marinho bg-tom-destaque" : aceita(c.etapa) ? "border-marinho border-dashed bg-superficie-2" : "border-borda bg-superficie-2"
            }`}
          >
            <header className="mb-2.5 border-b border-borda pb-2">
              <h2 id={`t-${c.etapa}`} className="text-base font-bold">
                {ROTULO_ETAPA[c.etapa]}
              </h2>
              <p className="text-xs text-texto-2">
                {plural(c.total, "deal", "deals")} · {dinheiroCurto(c.valor)}
              </p>
            </header>
            {c.cartoes.length === 0 ? (
              <p className="px-2 py-6 text-center text-sm text-texto-2">
                {c.etapa === "atendimento" ? "Nenhum lead em atendimento. Registre o contato de um novo lead para trazê-lo para cá." : "Nenhum deal nesta coluna."}
              </p>
            ) : (
              <ul className="grid grid-cols-1 gap-2">
                {c.cartoes.map((d) => (
                  <li key={d.id}>
                    <Cartao
                      d={d}
                      href={linkDeal(d.id)}
                      papel={papel}
                      somenteLeitura={somenteLeitura}
                      mostrarVendedor={mostrarVendedor}
                      onArrastar={(a) => {
                        setArrastando(a ? d : null);
                        if (!a) setSobre(null);
                      }}
                    />
                  </li>
                ))}
              </ul>
            )}
            {c.total > c.cartoes.length ? (
              <Link href={maisCartoes(c.etapa, c.cartoes.length)} scroll={false} className={classeBotao("secundario", "compacto", "mt-2.5 w-full")}>
                Mostrar mais ({c.total - c.cartoes.length} restantes)
              </Link>
            ) : null}
          </section>
        ))}
      </div>
    </div>
  );
}

function Cartao({ d, href, papel, somenteLeitura, mostrarVendedor, onArrastar }: { d: DealVisao; href: string; papel: Papel; somenteLeitura: boolean; mostrarVendedor: boolean; onArrastar: (ativo: boolean) => void }) {
  const aberto = d.estagio === "Prospecting" || d.estagio === "Engaging";
  return (
    <article
      draggable={!somenteLeitura}
      onDragStart={(e) => {
        e.dataTransfer.effectAllowed = "move";
        e.dataTransfer.setData("text/plain", d.id);
        onArrastar(true);
      }}
      onDragEnd={() => onArrastar(false)}
      className={`${classeCartao} p-3 ${somenteLeitura ? "" : "cursor-grab active:cursor-grabbing"}`}
    >
      <div className="flex items-start gap-2">
        <div className="min-w-0 flex-1">
          <Link href={href} scroll={false} title={d.nome} className="block truncate font-semibold hover:underline">
            {d.nome}
          </Link>
          <p className="truncate text-sm text-texto-2">{d.contato ? `${d.contato.nome}${d.contato.cargo ? `, ${d.contato.cargo}` : ""}` : "Sem contato cadastrado"}</p>
        </div>
      </div>
      {d.icone ? (
        <div className="mt-1.5">
          <IconeDeal icone={d.icone} dias={d.diasDesdeAbertura} />
        </div>
      ) : null}
      {aberto ? (
        <div className="mt-2">
          <BarraNota score={d.score} faixa={d.faixaNota} />
        </div>
      ) : null}
      <p className="mt-2 truncate text-sm text-texto-2">
        {aberto
          ? d.dataAbertura
            ? `Aberto em ${dataBR(d.dataAbertura)}${d.diasDesdeAbertura !== null ? ` · ${d.diasDesdeAbertura} dias` : ""}`
            : "Não iniciado"
          : d.closeDate
            ? `Encerrado em ${dataBR(d.closeDate)}`
            : "Encerrado"}
      </p>
      <div className="mt-2 flex flex-wrap items-center justify-between gap-2">
        <span className="text-sm whitespace-nowrap">
          <strong>{dinheiro(aberto ? d.valorEsperado : d.estagio === "Won" ? d.closeValue : d.preco)}</strong>{" "}
          <span className="text-xs text-texto-2">{aberto ? (d.valorPeloPrecoDeTabela ? "preço de tabela" : "esperado") : d.estagio === "Won" ? "fechamento" : "preço de tabela"}</span>
        </span>
        <SeletorEstagio deal={d} papel={papel} desligado={somenteLeitura} />
      </div>
      {mostrarVendedor || d.tags.length || d.qtdComentarios ? (
        <p className="mt-2 flex flex-wrap items-center gap-2 text-xs text-texto-2">
          {mostrarVendedor ? <span>{d.vendedor}</span> : null}
          {d.qtdComentarios ? <span>{plural(d.qtdComentarios, "comentário", "comentários")}</span> : null}
        </p>
      ) : null}
    </article>
  );
}
