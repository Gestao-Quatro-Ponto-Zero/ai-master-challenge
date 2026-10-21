"use client"

import { useState } from "react"
import { AlertaItem } from "@/components/alerta-item"
import { Button } from "@/components/ui/button"
import type { AlertasResponse, Severidade } from "@/lib/api"
import { ESTILO_SEVERIDADE } from "@/lib/format"

const LOTE = 30

// Fila de alertas de deals, do mais grave pro mais leve, com filtro por severidade
export function FilaAlertas({ dados, onAbrirDeal }: { dados: AlertasResponse; onAbrirDeal: (id: string) => void }) {
  const [severidade, setSeveridade] = useState<Severidade | undefined>()
  const [mostrar, setMostrar] = useState(LOTE)
  const porDeal = dados.alertas.filter((a) => a.opportunity_id && (!severidade || a.severidade === severidade))

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap gap-2">
        {(Object.keys(ESTILO_SEVERIDADE) as Severidade[]).map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => { setSeveridade(severidade === s ? undefined : s); setMostrar(LOTE) }}
            className={`rounded-full px-3 py-1 text-xs font-semibold ring-1 transition-smooth ${ESTILO_SEVERIDADE[s].classe} ${
              severidade && severidade !== s ? "opacity-40" : ""
            }`}
          >
            {ESTILO_SEVERIDADE[s].rotulo} · {dados.alertas.filter((a) => a.opportunity_id && a.severidade === s).length}
          </button>
        ))}
      </div>
      <div className="space-y-2">
        {porDeal.slice(0, mostrar).map((a) => (
          <AlertaItem key={`${a.opportunity_id}-${a.tipo}`} alerta={a} onAbrirDeal={onAbrirDeal} />
        ))}
      </div>
      {porDeal.length > mostrar && (
        <Button variant="outline" size="sm" onClick={() => setMostrar(mostrar + LOTE)}>
          Mostrar mais ({porDeal.length - mostrar} restantes)
        </Button>
      )}
    </div>
  )
}
