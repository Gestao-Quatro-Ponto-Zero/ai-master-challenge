"use client"

import type { CrossSellResponse } from "@/lib/api"
import { dataBr, usd } from "@/lib/format"

// Contas que já compraram uma série e nunca compraram outra — "próximo produto"
export function AbaCrossSell({ cs }: { cs: CrossSellResponse }) {
  if (!cs.sugestoes.length) {
    return <p className="py-10 text-center text-sm text-muted-foreground">Nenhuma oportunidade de cross-sell neste recorte.</p>
  }
  const series = new Set(cs.sugestoes.map((s) => s.serie_sugerida))
  return (
    <div className="space-y-3">
      {series.size === 1 && (
        <p className="rounded-lg bg-muted/60 p-3 text-xs leading-relaxed text-muted-foreground">
          Todas as contas deste recorte já compraram as outras séries — a única expansão possível é a série{" "}
          {[...series][0]}. Priorizado por quanto a conta já comprou com a gente.
        </p>
      )}
      <div className="overflow-x-auto rounded-xl border border-border/60 bg-card/70">
        <table className="w-full text-sm">
          <thead className="border-b border-border/60 text-left text-[11px] uppercase tracking-widest text-muted-foreground">
            <tr>
              <th className="px-3 py-2.5">Conta</th>
              <th className="px-3 py-2.5">Já compra</th>
              <th className="px-3 py-2.5">Oferecer</th>
              <th className="px-3 py-2.5 text-right">Histórico</th>
              <th className="hidden px-3 py-2.5 md:table-cell">Quem tem o relacionamento</th>
            </tr>
          </thead>
          <tbody>
            {cs.sugestoes.map((s) => (
              <tr key={s.conta + s.serie_sugerida} className="border-b border-border/40 last:border-0">
                <td className="px-3 py-2">
                  <p className="font-medium">{s.conta}</p>
                  <p className="text-xs capitalize text-muted-foreground">{s.setor}</p>
                </td>
                <td className="px-3 py-2">{s.series_compradas.join(", ")}</td>
                <td className="px-3 py-2 font-semibold text-primary">{s.produto_sugerido} <span className="font-normal text-muted-foreground">({s.serie_sugerida})</span></td>
                <td className="px-3 py-2 text-right tabular-nums">
                  {usd(s.valor_historico)}
                  <span className="block text-[11px] text-muted-foreground">{s.n_compras} compras · última {dataBr(s.ultima_compra)}</span>
                </td>
                <td className="hidden px-3 py-2 md:table-cell">{s.agente}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}
