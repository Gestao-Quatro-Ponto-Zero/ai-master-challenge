"use client";
// Situação do funil hoje (O-30): barras verticais por estágio, em tons de dourado, com Perdido em cinza no fim.
// Cada barra tem o número em cima e o nome embaixo. Alterna entre quantidade e valor.
import { useState } from "react";
import { dinheiroCurto, inteiro } from "@/lib/calculos";
import { ROTULO_ETAPA, type Etapa } from "@/lib/etapas";
import type { BarraFunil } from "@/lib/painel";
import { Alternador, classeSuperficie } from "./ui/Superficie";

const COR: Record<Etapa, string> = { novo: "bg-funil-1", atendimento: "bg-funil-2", negociacao: "bg-funil-3", fechado: "bg-funil-4", perdido: "bg-funil-perdido" };

export function Funil({ barras, className = "" }: { barras: BarraFunil[]; className?: string }) {
  const [modo, setModo] = useState<"quantidade" | "valor">("quantidade");
  const max = Math.max(1, ...barras.map((b) => b[modo]));
  const vazio = barras.every((b) => b.quantidade === 0);
  const ordenadas = [...barras.filter((b) => b.etapa !== "perdido"), ...barras.filter((b) => b.etapa === "perdido")];
  const rotulo = `Funil por ${modo === "quantidade" ? "quantidade" : "valor"}: ${ordenadas
    .map((b) => `${ROTULO_ETAPA[b.etapa]} ${modo === "quantidade" ? inteiro(b.quantidade) : dinheiroCurto(b.valor)}`)
    .join(", ")}`;
  return (
    <section aria-labelledby="t-funil" className={`${classeSuperficie} flex flex-col p-4 ${className}`}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 id="t-funil" className="text-lg font-bold">
          Situação do funil hoje
        </h2>
        <Alternador
          rotulo="Medida do funil"
          valor={modo}
          onMudar={setModo}
          opcoes={[
            { valor: "quantidade", rotulo: "Quantidade" },
            { valor: "valor", rotulo: "Valor" },
          ]}
        />
      </div>
      {vazio ? (
        <p className="mt-4 text-sm text-texto-2">Sem deals ainda neste perfil.</p>
      ) : (
        <>
          <p className="mt-2 flex items-center justify-between border-b border-divisoria pb-1.5 text-xs text-texto-2" aria-hidden>
            <span>Início do funil</span>
            <span>Fim do funil</span>
          </p>
          {/* Celular (< 640 px): barras horizontais, com o nome inteiro à esquerda e o número à direita. */}
          <ul className="mt-3 grid gap-2 sm:hidden" role="img" aria-label={rotulo}>
            {ordenadas.map((b) => (
              <li key={b.etapa} className={`grid grid-cols-[6.5rem_1fr_auto] items-center gap-2 text-sm ${b.etapa === "perdido" ? "mt-1 border-t border-divisoria pt-3" : ""}`}>
                <span className="font-semibold">{ROTULO_ETAPA[b.etapa]}</span>
                <span className="h-4 overflow-hidden rounded-controle bg-superficie-2">
                  <span className={`block h-full rounded-controle ${COR[b.etapa]}`} style={{ width: `${Math.max(b[modo] ? 2 : 0, (b[modo] / max) * 100)}%` }} />
                </span>
                <span className="min-w-12 text-right font-bold whitespace-nowrap tabular-nums">{modo === "quantidade" ? inteiro(b.quantidade) : dinheiroCurto(b.valor)}</span>
              </li>
            ))}
          </ul>
          <div
            className="mt-auto hidden grid-cols-5 items-end gap-2 pt-3 sm:grid sm:gap-4"
            role="img"
            aria-label={rotulo}
          >
            {ordenadas.map((b) => (
              <div key={b.etapa} className={`flex min-w-0 flex-col ${b.etapa === "perdido" ? "border-l border-divisoria pl-2 sm:pl-4" : ""}`}>
                {/* O número fica logo acima da barra, que cresce de baixo para cima. */}
                <div className="flex h-44 items-end pt-7 lg:h-40">
                  <div className={`relative w-full rounded-t-controle ${COR[b.etapa]}`} style={{ height: `${Math.max(b[modo] ? 2 : 0, (b[modo] / max) * 100)}%` }}>
                    <span className="absolute inset-x-0 -top-6 text-center text-sm font-bold whitespace-nowrap tabular-nums">
                      {modo === "quantidade" ? inteiro(b.quantidade) : dinheiroCurto(b.valor)}
                    </span>
                  </div>
                </div>
                <span className="mt-2 line-clamp-2 border-t border-borda pt-1 text-center text-xs leading-tight font-semibold text-texto-2" title={ROTULO_ETAPA[b.etapa]}>
                  {ROTULO_ETAPA[b.etapa]}
                </span>
              </div>
            ))}
          </div>
          {modo === "valor" ? <p className="mt-3 text-xs text-texto-2">Abertos pelo valor esperado; perdidos pelo preço de tabela; fechados pelo valor de fechamento.</p> : null}
        </>
      )}
    </section>
  );
}
