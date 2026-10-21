import { AlertOctagon, AlertTriangle, BellRing, ArrowRight, Shuffle } from "lucide-react"
import type { Alerta, Severidade } from "@/lib/api"
import { ESTILO_SEVERIDADE, usd } from "@/lib/format"

const ICONE: Record<Severidade, typeof AlertOctagon> = {
  critico: AlertOctagon,
  atencao: AlertTriangle,
  lembrete: BellRing,
}

// Card de alerta: ícone colorido, título em negrito, explicação curta e a ação
// sugerida destacada.
export function AlertaItem({ alerta, onAbrirDeal }: { alerta: Alerta; onAbrirDeal?: (id: string) => void }) {
  const Icone = ICONE[alerta.severidade]
  const estilo = ESTILO_SEVERIDADE[alerta.severidade]
  const clicavel = Boolean(alerta.opportunity_id && onAbrirDeal)

  return (
    <div
      onClick={clicavel ? () => onAbrirDeal!(alerta.opportunity_id!) : undefined}
      className={`flex items-start gap-3 rounded-xl border border-border/60 bg-card/70 p-3.5 shadow-sm transition-colors ${
        clicavel ? "cursor-pointer hover:border-primary/30 hover:bg-card" : ""
      }`}
    >
      <div className={`mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-lg ring-1 ${estilo.classe}`}>
        <Icone className="h-3.5 w-3.5" />
      </div>
      <div className="min-w-0 flex-1">
        <div className="flex flex-wrap items-center gap-x-2 gap-y-0.5">
          <p className="text-sm font-semibold leading-snug">{alerta.titulo}</p>
          {alerta.opportunity_id && (
            <span className="text-xs text-muted-foreground">
              {alerta.conta ?? "Conta não preenchida"} · {alerta.produto} · {alerta.agente}
            </span>
          )}
        </div>
        <p className="mt-0.5 text-sm leading-relaxed text-muted-foreground">{alerta.mensagem}</p>
        {alerta.rebaixado && (
          <p className="mt-1 text-[11px] text-muted-foreground/80">
            Rebaixado de crítico: limite de 3 críticos por vendedor — os de maior valor esperado ficaram como críticos.
          </p>
        )}
        {alerta.redistribuicao && alerta.redistribuicao.length > 0 && (
          <ul className="mt-2 space-y-1 rounded-lg bg-muted/50 p-2 text-xs">
            {alerta.redistribuicao.map((r) => (
              <li key={r.opportunity_id} className="flex items-center gap-1.5">
                <Shuffle className="h-3 w-3 shrink-0 text-primary" />
                <span>
                  {r.conta ?? "Sem conta"} · {r.produto} ({usd(r.valor_esperado)} esperado) →{" "}
                  <strong>{r.para}</strong> <span className="text-muted-foreground">(fecha {Math.round(r.afinidade_destino * 100)}% em {r.produto})</span>
                </span>
              </li>
            ))}
          </ul>
        )}
        <p className="mt-1.5 flex items-center gap-1 text-xs font-medium text-primary">
          <ArrowRight className="h-3 w-3" /> {alerta.acao_sugerida}
        </p>
      </div>
    </div>
  )
}
