"use client";
// Quadro do Pipeline: duas colunas (Prospecção e Em negociação), cartões e mudança de estágio por arraste
// ou pelo seletor do cartão. Ganho e Perdido são áreas de soltar que aparecem durante o arraste.
import { useState } from "react";
import Link from "next/link";
import { usePathname, useSearchParams } from "next/navigation";
import { dataBR, dinheiro, dinheiroCurto, plural, ROTULO_ESTAGIO } from "@/lib/calculos";
import type { DealVisao, Estagio, Papel } from "@/lib/tipos";
import { SeletorEstagio, transicoesDe, useMudarEstagio } from "./Estagio";
import { BarraNota, IconeDeal } from "./Nota";

export interface Coluna {
  estagio: "Prospecting" | "Engaging";
  total: number;
  valor: number;
  cartoes: DealVisao[];
}

export function Quadro({ colunas, papel, somenteLeitura, mostrarVendedor }: { colunas: Coluna[]; papel: Papel; somenteLeitura: boolean; mostrarVendedor: boolean }) {
  const mudar = useMudarEstagio();
  const params = useSearchParams();
  const caminho = usePathname();
  const [arrastando, setArrastando] = useState<DealVisao | null>(null);
  const [sobre, setSobre] = useState<Estagio | null>(null);
  const [aba, setAba] = useState<Coluna["estagio"]>("Engaging");

  const linkDeal = (id: string) => {
    const p = new URLSearchParams(params.toString());
    p.set("deal", id);
    return `${caminho}?${p}`;
  };
  const maisCartoes = (estagio: string, mostrados: number) => {
    const p = new URLSearchParams(params.toString());
    p.set("n", String(mostrados + 50));
    p.delete("deal");
    return `${caminho}?${p}#col-${estagio}`;
  };
  const aceita = (para: Estagio) => !!arrastando && transicoesDe(arrastando.estagio, papel).includes(para);

  function soltar(para: Estagio) {
    const d = arrastando;
    setArrastando(null);
    setSobre(null);
    if (d && transicoesDe(d.estagio, papel).includes(para)) void mudar(d, para);
  }

  const alvo = (para: Estagio) => ({
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
      <div className="mb-3 flex gap-1 rounded-controle bg-trilho p-1 md:hidden" role="tablist" aria-label="Estágio">
        {colunas.map((c) => (
          <button
            key={c.estagio}
            role="tab"
            aria-selected={aba === c.estagio}
            onClick={() => setAba(c.estagio)}
            className={`flex-1 rounded-controle px-3 py-2 text-sm font-semibold ${aba === c.estagio ? "bg-marinho text-branco" : "text-texto"}`}
          >
            {ROTULO_ESTAGIO[c.estagio]} ({c.total})
          </button>
        ))}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        {colunas.map((c) => (
          <section
            key={c.estagio}
            id={`col-${c.estagio}`}
            aria-labelledby={`t-${c.estagio}`}
            {...alvo(c.estagio)}
            className={`rounded-cartao border p-3 ${aba === c.estagio ? "" : "hidden md:block"} ${
              sobre === c.estagio ? "border-marinho bg-dourado-claro" : aceita(c.estagio) ? "border-dourado bg-marfim" : "border-linha bg-marfim"
            }`}
          >
            <header className="mb-3 flex flex-wrap items-baseline justify-between gap-2 border-b-2 border-marinho pb-2">
              <h2 id={`t-${c.estagio}`} className="text-lg font-bold">
                {ROTULO_ESTAGIO[c.estagio]}
              </h2>
              <p className="text-sm text-texto-2">
                {plural(c.total, "deal", "deals")} · {dinheiroCurto(c.valor)}
              </p>
            </header>
            {c.cartoes.length === 0 ? (
              <p className="px-2 py-6 text-center text-sm text-texto-2">Nenhum deal nesta coluna.</p>
            ) : (
              <ul className="grid gap-2">
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
              <Link href={maisCartoes(c.estagio, c.cartoes.length)} scroll={false} className="mt-3 block rounded-controle border border-linha-forte px-3 py-2 text-center text-sm font-semibold">
                Mostrar mais ({c.total - c.cartoes.length} restantes)
              </Link>
            ) : null}
          </section>
        ))}
      </div>

      {arrastando ? (
        <div className="fixed inset-x-0 bottom-0 z-20 grid grid-cols-2 gap-3 bg-veu p-4" aria-label="Encerrar o deal">
          {(["Won", "Lost"] as const).map((e) =>
            aceita(e) ? (
              <div
                key={e}
                {...alvo(e)}
                className={`rounded-cartao border-2 border-dashed px-4 py-6 text-center font-titulo text-lg font-bold ${
                  sobre === e ? "border-marinho bg-dourado text-marinho" : "border-dourado bg-fundo text-marinho"
                }`}
              >
                Soltar aqui: {ROTULO_ESTAGIO[e]}
              </div>
            ) : (
              <div key={e} className="rounded-cartao border-2 border-dashed border-linha bg-fundo px-4 py-6 text-center text-sm text-texto-2">
                {ROTULO_ESTAGIO[e]}: primeiro passe por Em negociação
              </div>
            ),
          )}
        </div>
      ) : null}
    </div>
  );
}

function Cartao({ d, href, papel, somenteLeitura, mostrarVendedor, onArrastar }: { d: DealVisao; href: string; papel: Papel; somenteLeitura: boolean; mostrarVendedor: boolean; onArrastar: (ativo: boolean) => void }) {
  return (
    <article
      draggable={!somenteLeitura}
      onDragStart={(e) => {
        e.dataTransfer.effectAllowed = "move";
        e.dataTransfer.setData("text/plain", d.id);
        onArrastar(true);
      }}
      onDragEnd={() => onArrastar(false)}
      className={`rounded-cartao border border-linha-forte bg-fundo p-3 shadow-cartao ${somenteLeitura ? "" : "cursor-grab active:cursor-grabbing"}`}
    >
      <div className="flex items-start gap-2">
        <div className="min-w-0 flex-1">
          <Link href={href} scroll={false} className="block font-semibold break-words hover:underline">
            {d.nome}
          </Link>
          <p className="text-sm text-texto-2">{d.contato ? `${d.contato.nome}${d.contato.cargo ? `, ${d.contato.cargo}` : ""}` : "Sem contato cadastrado"}</p>
        </div>
        <IconeDeal icone={d.icone} dias={d.diasDesdeAbertura} />
      </div>
      <div className="mt-2">
        <BarraNota score={d.score} faixa={d.faixaNota} />
      </div>
      <p className="mt-2 text-sm text-texto-2">
        {d.dataAbertura ? `Aberto em ${dataBR(d.dataAbertura)}${d.diasDesdeAbertura !== null ? ` · ${d.diasDesdeAbertura} dias` : ""}` : "Não iniciado"}
      </p>
      <div className="mt-2 flex flex-wrap items-center justify-between gap-2">
        <span className="text-sm">
          <strong>{dinheiro(d.valorEsperado)}</strong> <span className="text-xs text-texto-2">{d.valorPeloPrecoDeTabela ? "preço de tabela" : "esperado"}</span>
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
