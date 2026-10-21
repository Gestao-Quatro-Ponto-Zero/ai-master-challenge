"use client"

import { useState } from "react"
import { AlertOctagon, AlertTriangle, BellRing } from "lucide-react"
import { Button } from "@/components/ui/button"
import type { Deal } from "@/lib/api"
import { ESTILO_ACAO, corScore, pct, usd } from "@/lib/format"

const POR_PAGINA = 25

function IconesAlerta({ deal }: { deal: Deal }) {
  const tem = (s: string) => deal.alertas.some((a) => a.severidade === s)
  return (
    <span className="flex items-center gap-1">
      {tem("critico") && <AlertOctagon className="h-4 w-4 text-rose-500" aria-label="Alerta crítico" />}
      {tem("atencao") && <AlertTriangle className="h-4 w-4 text-amber-500" aria-label="Atenção" />}
      {tem("lembrete") && <BellRing className="h-4 w-4 text-sky-500" aria-label="Lembrete" />}
    </span>
  )
}

export function TabelaDeals({ deals, onAbrir }: { deals: Deal[]; onAbrir: (d: Deal) => void }) {
  const [pagina, setPagina] = useState(0)
  const total = Math.ceil(deals.length / POR_PAGINA)
  const visiveis = deals.slice(pagina * POR_PAGINA, (pagina + 1) * POR_PAGINA)

  if (!deals.length) {
    return <p className="py-10 text-center text-sm text-muted-foreground">Nenhum deal aberto neste recorte.</p>
  }

  return (
    <div className="space-y-3">
      <div className="overflow-x-auto rounded-xl border border-border/60 bg-card/70">
        <table className="w-full text-sm">
          <thead className="border-b border-border/60 text-left text-[11px] uppercase tracking-widest text-muted-foreground">
            <tr>
              <th className="px-3 py-2.5">Score</th>
              <th className="px-3 py-2.5">Ação</th>
              <th className="px-3 py-2.5">Conta / Produto</th>
              <th className="hidden px-3 py-2.5 md:table-cell">Vendedor</th>
              <th className="px-3 py-2.5">Stage</th>
              <th className="px-3 py-2.5 text-right" title="Probabilidade calibrada de ganhar até o fim do horizonte">Chance</th>
              <th className="px-3 py-2.5 text-right" title="Chance × preço × desconto histórico">Valor esperado</th>
              <th className="hidden px-3 py-2.5 lg:table-cell">Principal motivo</th>
              <th className="px-3 py-2.5"></th>
            </tr>
          </thead>
          <tbody>
            {visiveis.map((d) => (
              <tr
                key={d.opportunity_id}
                onClick={() => onAbrir(d)}
                className="cursor-pointer border-b border-border/40 last:border-0 hover:bg-primary/5"
              >
                <td className="px-3 py-2.5">
                  <span className={`inline-flex h-8 w-10 items-center justify-center rounded-md font-bold tabular-nums ${corScore(d.acao)}`}>
                    {d.score}
                  </span>
                </td>
                <td className="px-3 py-2.5">
                  <span className={`whitespace-nowrap rounded-md px-2 py-0.5 text-xs font-semibold ring-1 ${ESTILO_ACAO[d.acao].badge}`}>
                    {d.acao}
                  </span>
                </td>
                <td className="px-3 py-2.5">
                  <p className="font-medium">{d.conta ?? <span className="italic text-muted-foreground">Conta não preenchida</span>}</p>
                  <p className="text-xs text-muted-foreground">{d.produto}</p>
                </td>
                <td className="hidden px-3 py-2.5 md:table-cell">{d.agente}</td>
                <td className="px-3 py-2.5 whitespace-nowrap">
                  {d.stage}
                  {d.idade_dias !== null && <span className="text-xs text-muted-foreground"> · {d.idade_dias}d</span>}
                </td>
                <td className="px-3 py-2.5 text-right tabular-nums">{pct(d.probabilidade)}</td>
                <td className="px-3 py-2.5 text-right tabular-nums">
                  {usd(d.valor_esperado)}
                  <span className="block text-[11px] text-muted-foreground">de {usd(d.valor_liquido)}</span>
                </td>
                <td className="hidden max-w-[320px] px-3 py-2.5 text-xs text-muted-foreground lg:table-cell">
                  <span className="line-clamp-2">{d.motivos[0]?.texto}</span>
                </td>
                <td className="px-3 py-2.5"><IconesAlerta deal={d} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {total > 1 && (
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>{deals.length} deals · página {pagina + 1} de {total}</span>
          <div className="flex gap-2">
            <Button variant="outline" size="sm" disabled={pagina === 0} onClick={() => setPagina(pagina - 1)}>Anterior</Button>
            <Button variant="outline" size="sm" disabled={pagina >= total - 1} onClick={() => setPagina(pagina + 1)}>Próxima</Button>
          </div>
        </div>
      )}
    </div>
  )
}
