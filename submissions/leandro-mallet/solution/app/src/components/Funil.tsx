"use client";
// Situação do funil hoje: uma barra por estágio, com Perdido à parte. Alterna entre quantidade e valor.
import { useState } from "react";
import { dinheiroCurto, inteiro, ROTULO_ESTAGIO } from "@/lib/calculos";
import type { BarraFunil } from "@/lib/painel";

const COR: Record<BarraFunil["estagio"], string> = { Prospecting: "bg-marinho", Engaging: "bg-marinho", Won: "bg-dourado-medio", Lost: "bg-cinza" };

export function Funil({ barras }: { barras: BarraFunil[] }) {
  const [modo, setModo] = useState<"quantidade" | "valor">("quantidade");
  const max = Math.max(1, ...barras.map((b) => b[modo]));
  const vazio = barras.every((b) => b.quantidade === 0);
  const linha = (b: BarraFunil) => (
    <div key={b.estagio} className="grid grid-cols-[7.5rem_1fr_auto] items-center gap-3 text-sm">
      <span className="font-semibold">{ROTULO_ESTAGIO[b.estagio]}</span>
      <div className="h-6 overflow-hidden rounded-controle bg-trilho">
        <div className={`h-full rounded-controle ${COR[b.estagio]}`} style={{ width: `${Math.max(b[modo] ? 1 : 0, (b[modo] / max) * 100)}%` }} />
      </div>
      <span className="min-w-16 text-right font-semibold">{modo === "quantidade" ? inteiro(b.quantidade) : dinheiroCurto(b.valor)}</span>
    </div>
  );
  return (
    <section aria-labelledby="t-funil" className="rounded-cartao border border-linha bg-fundo p-4 shadow-cartao">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 id="t-funil" className="text-lg font-bold">
          Situação do funil hoje
        </h2>
        <div className="flex gap-1 rounded-controle bg-trilho p-1 text-sm" role="group" aria-label="Medida do funil">
          {(["quantidade", "valor"] as const).map((m) => (
            <button key={m} onClick={() => setModo(m)} aria-pressed={modo === m} className={`rounded-controle px-3 py-1 font-semibold ${modo === m ? "bg-marinho text-branco" : ""}`}>
              {m === "quantidade" ? "Quantidade" : "Valor"}
            </button>
          ))}
        </div>
      </div>
      {vazio ? (
        <p className="mt-4 text-sm text-texto-2">Sem deals ainda neste perfil.</p>
      ) : (
        <div className="mt-4 grid gap-2">
          {barras.filter((b) => b.estagio !== "Lost").map(linha)}
          <div className="mt-2 border-t border-linha pt-3">{barras.filter((b) => b.estagio === "Lost").map(linha)}</div>
          {modo === "valor" ? (
            <p className="text-xs text-texto-2">Abertos e perdidos pelo preço de tabela; ganhos pelo valor de fechamento.</p>
          ) : null}
        </div>
      )}
    </section>
  );
}
