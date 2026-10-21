"use client"

import { Card } from "@/components/ui/card"
import type { Acao, PipelineResponse } from "@/lib/api"
import { ESTILO_ACAO, ORDEM_ACOES, usd } from "@/lib/format"

interface Props {
  resumo: PipelineResponse["resumo"]
  acaoAtiva?: string
  onSelecionar: (acao?: Acao) => void
}

// Um card por ação recomendada — clicar filtra a lista de deals por ela
export function ResumoAcoes({ resumo, acaoAtiva, onSelecionar }: Props) {
  return (
    <div className="grid grid-cols-2 gap-3 md:grid-cols-3 xl:grid-cols-6">
      {ORDEM_ACOES.map((acao) => {
        const r = resumo.por_acao[acao] ?? { n: 0, valor: 0, valor_esperado: 0 }
        const ativo = acaoAtiva === acao
        return (
          <button key={acao} type="button" onClick={() => onSelecionar(ativo ? undefined : acao)} className="text-left">
            <Card
              className={`h-full gap-1 border-2 p-4 transition-smooth hover:shadow-md ${ESTILO_ACAO[acao].card} ${
                ativo ? "ring-2 ring-primary" : acaoAtiva ? "opacity-60" : ""
              }`}
            >
              <span className={`w-fit rounded-md px-2 py-0.5 text-xs font-semibold ring-1 ${ESTILO_ACAO[acao].badge}`}>{acao}</span>
              <span className="mt-1 text-2xl font-bold tabular-nums">{r.n}</span>
              <span className="text-xs text-muted-foreground tabular-nums">
                {acao === "Requalificar" || acao === "Encerrar" || acao === "Primeiro contato"
                  ? `${usd(r.valor)} de tabela` : `${usd(r.valor_esperado)} esperado`}
              </span>
              <span className="mt-1 text-[11px] leading-snug text-muted-foreground/80">{ESTILO_ACAO[acao].descricao}</span>
            </Card>
          </button>
        )
      })}
    </div>
  )
}
