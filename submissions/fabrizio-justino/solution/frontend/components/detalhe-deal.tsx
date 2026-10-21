"use client"

import { useEffect, useState } from "react"
import { Loader2, MessageSquareText, PenLine } from "lucide-react"
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet"
import { Separator } from "@/components/ui/separator"
import { Button } from "@/components/ui/button"
import { AlertaItem } from "@/components/alerta-item"
import { BotaoCopiar, SeloFonte, TextoRico } from "@/components/texto-ia"
import { ia, type Deal, type Motivo, type RascunhoIA, type TextoIA, type TipoRascunho } from "@/lib/api"
import { ESTILO_ACAO, NOME_PILAR, corScore, dataBr, faixa, pct, usd } from "@/lib/format"

const COR_TOM: Record<Motivo["tom"], string> = {
  positivo: "bg-emerald-500",
  neutro: "bg-sky-500",
  negativo: "bg-rose-500",
}

// Rascunhos que fazem sentido para cada ação
const RASCUNHOS: Record<string, { tipo: TipoRascunho; rotulo: string }[]> = {
  "Atacar agora": [{ tipo: "followup", rotulo: "E-mail de follow-up" }],
  Nutrir: [{ tipo: "followup", rotulo: "E-mail de follow-up" }],
  "Primeiro contato": [],
  Requalificar: [{ tipo: "requalificacao", rotulo: "E-mail de requalificação" }, { tipo: "encerramento", rotulo: "Nota de encerramento" }],
  Encerrar: [{ tipo: "encerramento", rotulo: "Nota de encerramento" }],
  "Baixa prioridade": [{ tipo: "followup", rotulo: "E-mail de follow-up" }],
}

// Um pilar do score: barra de pontos + a frase que explica de onde vieram
function PilarScore({ motivo }: { motivo: Motivo }) {
  const frac = motivo.maximo ? motivo.pontos / motivo.maximo : 0
  return (
    <div className="space-y-1.5">
      <div className="flex items-baseline justify-between text-sm">
        <span className="font-semibold">{NOME_PILAR[motivo.pilar]}</span>
        <span className="tabular-nums text-muted-foreground">
          <span className="font-semibold text-foreground">+{Math.round(motivo.pontos)}</span> / {motivo.maximo}
        </span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-muted">
        <div className={`h-full rounded-full ${COR_TOM[motivo.tom]}`} style={{ width: `${Math.max(frac * 100, 2)}%` }} />
      </div>
      <p className="text-sm leading-relaxed text-muted-foreground">{motivo.texto}</p>
    </div>
  )
}

function Explicacao({ data, deal }: { data: string; deal: Deal }) {
  const [r, setR] = useState<TextoIA | null>(null)
  const [erro, setErro] = useState("")
  useEffect(() => {
    let ativo = true
    setR(null)
    setErro("")
    ia.deal(data, deal.opportunity_id).then((x) => ativo && setR(x)).catch((e) => ativo && setErro(e.message))
    return () => { ativo = false }
  }, [data, deal.opportunity_id])

  return (
    <section className="space-y-2 rounded-lg border border-primary/20 bg-primary/5 p-3">
      <div className="flex items-center justify-between">
        <h3 className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-widest text-primary/80">
          <MessageSquareText className="h-3.5 w-3.5" /> Em uma frase
        </h3>
        {r && <SeloFonte fonte={r.fonte} motivo={r.motivo} />}
      </div>
      {erro ? <p className="text-sm text-destructive">{erro}</p>
        : r ? <TextoRico texto={r.texto} />
        : <p className="flex items-center gap-2 text-sm text-muted-foreground"><Loader2 className="h-4 w-4 animate-spin" /> Escrevendo...</p>}
    </section>
  )
}

function Rascunhos({ data, deal }: { data: string; deal: Deal }) {
  const [r, setR] = useState<RascunhoIA | null>(null)
  const [carregando, setCarregando] = useState<TipoRascunho | null>(null)
  const [erro, setErro] = useState("")

  const gerar = (tipo: TipoRascunho) => {
    setCarregando(tipo)
    setErro("")
    ia.rascunho(data, deal.opportunity_id, tipo).then(setR).catch((e) => setErro(e.message)).finally(() => setCarregando(null))
  }

  return (
    <section className="space-y-2">
      <h3 className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-widest text-primary/80">
        <PenLine className="h-3.5 w-3.5" /> Rascunhos
      </h3>
      <div className="flex flex-wrap gap-2">
        {(RASCUNHOS[deal.acao] ?? []).map((x) => (
          <Button key={x.tipo} variant="outline" size="sm" disabled={carregando !== null} onClick={() => gerar(x.tipo)}>
            {carregando === x.tipo && <Loader2 className="mr-1 h-3 w-3 animate-spin" />} {x.rotulo}
          </Button>
        ))}
      </div>
      {erro && <p className="text-sm text-destructive">{erro}</p>}
      {r && (
        <div className="space-y-1 rounded-lg border border-border/60 bg-muted/40 p-3">
          <div className="flex items-center justify-between gap-2">
            <p className="text-sm"><span className="text-muted-foreground">Assunto:</span> <strong>{r.assunto}</strong></p>
            <div className="flex items-center gap-1"><SeloFonte fonte={r.fonte} /><BotaoCopiar texto={`${r.assunto}\n\n${r.corpo}`} /></div>
          </div>
          <p className="whitespace-pre-wrap text-sm leading-relaxed">{r.corpo}</p>
        </div>
      )}
    </section>
  )
}

export function DetalheDeal({ deal, data, onFechar }: { deal: Deal | null; data: string; onFechar: () => void }) {
  return (
    <Sheet open={deal !== null} onOpenChange={(aberto) => !aberto && onFechar()}>
      <SheetContent className="w-full overflow-y-auto sm:max-w-lg">
        {deal && (
          <>
            <SheetHeader>
              <div className="flex items-center gap-3">
                <span className={`flex h-14 w-14 shrink-0 items-center justify-center rounded-xl text-2xl font-bold tabular-nums ${corScore(deal.acao)}`}>
                  {deal.score}
                </span>
                <div className="min-w-0">
                  <SheetTitle className="truncate">{deal.conta ?? "Conta não preenchida"}</SheetTitle>
                  <SheetDescription>
                    {deal.produto} · {usd(deal.valor)} · {deal.opportunity_id}
                  </SheetDescription>
                  <span className={`mt-1 inline-block rounded-md px-2 py-0.5 text-xs font-semibold ring-1 ${ESTILO_ACAO[deal.acao].badge}`}>
                    {deal.acao}
                  </span>
                </div>
              </div>
            </SheetHeader>

            <div className="space-y-5 px-4 pb-6">
              <Explicacao data={data} deal={deal} />

              <dl className="grid grid-cols-2 gap-x-4 gap-y-2 rounded-lg bg-muted/50 p-3 text-sm">
                <dt className="text-muted-foreground">Vendedor</dt><dd>{deal.agente}</dd>
                <dt className="text-muted-foreground">Manager / Região</dt><dd>{deal.manager} · {deal.regiao}</dd>
                <dt className="text-muted-foreground">Stage</dt><dd>{deal.stage}</dd>
                <dt className="text-muted-foreground">Chance no prazo</dt>
                <dd>
                  {pct(deal.probabilidade)}
                  {faixa(deal.prob_min, deal.prob_max) && (
                    <span className="text-muted-foreground" title="Intervalo de 95% (Wilson) pelo tamanho da amostra de deals dessa idade">
                      {" "}({faixa(deal.prob_min, deal.prob_max)})
                    </span>
                  )}
                  {deal.probabilidade === null && <span className="block text-[11px] text-muted-foreground">sem data de engajamento</span>}
                </dd>
                <dt className="text-muted-foreground">Valor esperado</dt>
                <dd>{usd(deal.valor_esperado)} <span className="text-muted-foreground">de {usd(deal.valor_liquido)}</span></dd>
                <dt className="text-muted-foreground">Engajado em</dt>
                <dd>{deal.engage_date ? `${dataBr(deal.engage_date)} (${deal.idade_dias} dias)` : "—"}</dd>
                {deal.setor && (<><dt className="text-muted-foreground">Setor</dt><dd className="capitalize">{deal.setor}</dd></>)}
              </dl>

              {deal.alertas.length > 0 && (
                <section className="space-y-2">
                  <h3 className="text-xs font-bold uppercase tracking-widest text-primary/80">O que fazer</h3>
                  {deal.alertas.map((a) => <AlertaItem key={a.tipo} alerta={a} />)}
                </section>
              )}

              <Rascunhos data={data} deal={deal} />

              <Separator />

              <section className="space-y-4">
                <h3 className="text-xs font-bold uppercase tracking-widest text-primary/80">Por que score {deal.score}?</h3>
                {deal.motivos.map((m) => <PilarScore key={m.pilar} motivo={m} />)}
              </section>
            </div>
          </>
        )}
      </SheetContent>
    </Sheet>
  )
}
