"use client"

import { Card } from "@/components/ui/card"
import type { BenchmarksResponse, Pilar } from "@/lib/api"
import { NOME_PILAR, dataBr, pct } from "@/lib/format"

// Previsto (estimador bruto) × real × calibrado, por faixa — o argumento de que a régua funciona
function GraficoCalibracao({ cal }: { cal: BenchmarksResponse["calibracao"] }) {
  const pontos = cal.curva.filter((p) => p.n >= 100)
  const maxY = Math.max(...pontos.map((p) => Math.max(p.real, p.previsto)), 0.01)
  return (
    <div>
      <div className="flex h-48 items-end gap-1">
        {pontos.map((p) => (
          <div key={p.de} className="group relative flex h-full flex-1 items-end justify-center gap-0.5">
            <div className="w-1/2 rounded-t bg-muted-foreground/30" style={{ height: `${(p.previsto / maxY) * 100}%` }} />
            <div className="w-1/2 rounded-t bg-primary" style={{ height: `${(p.real / maxY) * 100}%` }} />
            <div className="pointer-events-none absolute bottom-full z-10 mb-1 hidden w-44 rounded-md border bg-popover p-2 text-[11px] shadow-md group-hover:block">
              Chance bruta {pct(p.de)}–{pct(p.ate)}: previsto {pct(p.previsto)}, real {pct(p.real)}, usado {pct(p.calibrado)} · {p.n.toLocaleString("pt-BR")} deals
            </div>
          </div>
        ))}
      </div>
      <div className="mt-1 flex justify-between text-[11px] text-muted-foreground">
        <span>chance bruta baixa</span><span>chance bruta alta</span>
      </div>
      <div className="mt-2 flex gap-4 text-xs text-muted-foreground">
        <span className="flex items-center gap-1"><span className="h-2.5 w-2.5 rounded-sm bg-muted-foreground/30" /> previsto pelo estimador</span>
        <span className="flex items-center gap-1"><span className="h-2.5 w-2.5 rounded-sm bg-primary" /> aconteceu de verdade</span>
      </div>
    </div>
  )
}

export function ComoFunciona({ bm }: { bm: BenchmarksResponse }) {
  const cal = bm.calibracao
  const explicacao: Record<Pilar, string> = {
    chance: "Probabilidade de o deal ser GANHO até o fim do trimestre, dada a idade dele. Vem do que aconteceu com deals " +
      "da mesma idade, no mesmo ponto do trimestre, e é recalibrada pelo backtest abaixo. Deals que passaram do " +
      `maior ciclo já fechado (${bm.ciclo_max_dias} dias) ficam com chance zero; Prospecting fica "n/d" (sem data de engajamento).`,
    valor: "Preço do produto em escala logarítmica: o catálogo vai de US$ 55 a US$ 26.768, então um deal grande pesa mais sem engolir a chance.",
    dados: "Cliente já engajado vale mais que Prospecting; conta preenchida soma pontos (sem conta, o forecast é menos confiável).",
  }

  return (
    <div className="space-y-4">
      <div className="grid gap-4 md:grid-cols-3">
        {(Object.keys(bm.pesos) as Pilar[]).map((p) => (
          <Card key={p} className="gap-2 p-4">
            <div className="flex items-baseline justify-between">
              <h3 className="font-semibold">{NOME_PILAR[p]}</h3>
              <span className="text-sm font-bold text-primary">até {bm.pesos[p]} pts</span>
            </div>
            <p className="text-sm leading-relaxed text-muted-foreground">{explicacao[p]}</p>
          </Card>
        ))}
      </div>

      <Card className="gap-3 p-4">
        <h3 className="font-semibold">A régua funciona? Backtest de {cal.n_datas} segundas-feiras</h3>
        {!cal.calibrada ? (
          <p className="rounded-lg bg-amber-500/10 p-3 text-sm text-amber-800 dark:text-amber-200">
            Em {dataBr(cal.data_corte)} ainda não havia histórico suficiente com desfecho conhecido para calibrar
            ({cal.n_observacoes.toLocaleString("pt-BR")} observações). A chance mostrada é a estimativa bruta, que tende a
            ser otimista nas faixas altas.
          </p>
        ) : (
          <>
            <p className="text-sm leading-relaxed text-muted-foreground">
              Reconstruímos o pipeline de cada segunda entre {dataBr(cal.data_inicio!)} e {dataBr(cal.data_fim!)}, calculamos a
              chance com o que se sabia naquele dia e conferimos o que aconteceu ({cal.n_observacoes.toLocaleString("pt-BR")} observações).
              Quanto maior a chance prevista, mais o deal ganhou — até um teto de ~{pct(Math.max(...cal.curva.map((c) => c.calibrado)))},
              que é o máximo usado. AUC {cal.auc.toFixed(2).replace(".", ",")} entre deals dentro do ciclo e{" "}
              {cal.auc_com_teto.toFixed(2).replace(".", ",")} no pipeline inteiro (0,50 = cara ou coroa).
            </p>
            <p className="text-xs leading-relaxed text-muted-foreground">
              Sem olhar o futuro: a calibração usada em {dataBr(cal.data_corte)} só conta deals cujo desfecho já era conhecido
              nesta data. "Atacar agora" = top {Math.round((1 - bm.limites_acao.percentil_atacar) * 100)}% dos deals vivos
              (score ≥ {bm.limites_acao.atacar} nesta data); "Nutrir" = score ≥ {bm.limites_acao.nutrir}.
            </p>
            <GraficoCalibracao cal={cal} />
          </>
        )}
      </Card>

      <div className="grid gap-4 md:grid-cols-2">
        <Card className="gap-2 p-4">
          <h3 className="font-semibold">A regra dos {bm.ciclo_max_dias} dias</h3>
          <p className="text-sm leading-relaxed text-muted-foreground">
            No backtest, {cal.zumbis_observados.toLocaleString("pt-BR")} vezes um deal estava aberto além do maior ciclo já
            fechado. Quantos ganharam depois: <strong className="text-foreground">{cal.zumbis_que_ganharam}</strong>.
            Por isso eles têm chance zero e vão para Encerrar ou Requalificar — que significa perguntar ao cliente e, se o
            projeto continuar, encerrar este deal e abrir uma oportunidade nova, com o relógio zerado.
          </p>
        </Card>
        <Card className="gap-2 p-4">
          <h3 className="font-semibold">Fim de trimestre importa</h3>
          <p className="text-sm leading-relaxed text-muted-foreground">
            Deals fechados no último mês do trimestre ganharam {pct(bm.win_fim_trimestre)} das vezes, contra{" "}
            {pct(bm.win_fora_trimestre)} nos outros meses. É por isso que o modo emergência liga no último mês.
          </p>
        </Card>
        <Card className="gap-2 p-4 md:col-span-2">
          <h3 className="font-semibold">O que testamos e NÃO entrou no score</h3>
          <p className="text-sm leading-relaxed text-muted-foreground">
            Taxa histórica do vendedor, da conta e do produto, histórico da conta (já comprou / perdeu recentemente) e
            afinidade do vendedor com produto e setor: no backtest, nenhum separa ganho de perda (AUC entre 0,49 e 0,52).
            Setor, região, manager e porte da conta têm taxas de ganho parecidas em todas as faixas (61%–66%). Colocar
            isso no score só adicionaria ruído com cara de precisão. A afinidade do vendedor ainda é usada para sugerir
            para quem redistribuir deals.
          </p>
        </Card>
      </div>
    </div>
  )
}
