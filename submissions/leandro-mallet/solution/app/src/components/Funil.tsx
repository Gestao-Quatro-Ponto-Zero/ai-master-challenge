"use client";
// Situação do funil hoje (O-30): barras verticais por estágio, em tons de dourado, com Perdido em cinza no fim.
// Cada barra tem o número em cima e o nome embaixo. Alterna entre quantidade e valor.
import { useState } from "react";
import { dinheiroCurto, inteiro, ROTULO_ESTAGIO } from "@/lib/calculos";
import type { BarraFunil } from "@/lib/painel";
import { Alternador, classeSuperficie } from "./ui/Superficie";

const COR: Record<BarraFunil["estagio"], string> = { Prospecting: "bg-funil-1", Engaging: "bg-funil-2", Won: "bg-funil-3", Lost: "bg-funil-perdido" };

export function Funil({ barras, className = "" }: { barras: BarraFunil[]; className?: string }) {
  const [modo, setModo] = useState<"quantidade" | "valor">("quantidade");
  const max = Math.max(1, ...barras.map((b) => b[modo]));
  const vazio = barras.every((b) => b.quantidade === 0);
  const ordenadas = [...barras.filter((b) => b.estagio !== "Lost"), ...barras.filter((b) => b.estagio === "Lost")];
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
          <div
            className="mt-auto grid grid-cols-4 items-end gap-3 pt-3 sm:gap-6"
            role="img"
            aria-label={`Funil por ${modo === "quantidade" ? "quantidade" : "valor"}: ${ordenadas
              .map((b) => `${ROTULO_ESTAGIO[b.estagio]} ${modo === "quantidade" ? inteiro(b.quantidade) : dinheiroCurto(b.valor)}`)
              .join(", ")}`}
          >
            {ordenadas.map((b) => (
              <div key={b.estagio} className={`flex min-w-0 flex-col ${b.estagio === "Lost" ? "border-l border-divisoria pl-3 sm:pl-6" : ""}`}>
                {/* O número fica logo acima da barra, que cresce de baixo para cima. */}
                <div className="flex h-44 items-end pt-7 lg:h-40">
                  <div className={`relative w-full rounded-t-controle ${COR[b.estagio]}`} style={{ height: `${Math.max(b[modo] ? 2 : 0, (b[modo] / max) * 100)}%` }}>
                    <span className="absolute inset-x-0 -top-6 text-center text-sm font-bold whitespace-nowrap tabular-nums">
                      {modo === "quantidade" ? inteiro(b.quantidade) : dinheiroCurto(b.valor)}
                    </span>
                  </div>
                </div>
                <span className="mt-2 truncate border-t border-borda pt-1 text-center text-xs font-semibold text-texto-2" title={ROTULO_ESTAGIO[b.estagio]}>
                  {ROTULO_ESTAGIO[b.estagio]}
                </span>
              </div>
            ))}
          </div>
          {modo === "valor" ? <p className="mt-3 text-xs text-texto-2">Abertos e perdidos pelo preço de tabela; ganhos pelo valor de fechamento.</p> : null}
        </>
      )}
    </section>
  );
}
