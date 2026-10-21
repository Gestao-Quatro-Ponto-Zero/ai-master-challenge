"use client"

import { useState } from "react"
import { Siren, CheckCircle2, CalendarClock, Loader2, Sparkles } from "lucide-react"
import { Card } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { BarraRitmo } from "@/components/barra-ritmo"
import { BotaoCopiar, SeloFonte, TextoRico } from "@/components/texto-ia"
import { ia, type EmergenciaResponse, type Recorte, type TextoIA } from "@/lib/api"
import { dataBr, pct, usd } from "@/lib/format"

// Plano de ataque por vendedor escrito pela IA a partir da lista de resgate
function PlanoResgate({ data, recorte }: { data: string; recorte: Recorte }) {
  const [r, setR] = useState<TextoIA | null>(null)
  const [carregando, setCarregando] = useState(false)
  const [erro, setErro] = useState("")
  if (!r) {
    return (
      <div className="space-y-1">
        <Button size="sm" disabled={carregando} onClick={() => {
          setCarregando(true)
          ia.planoResgate(data, recorte).then(setR).catch((e) => setErro(e.message)).finally(() => setCarregando(false))
        }} className="bg-rose-600 text-white hover:bg-rose-700">
          {carregando ? <Loader2 className="mr-1 h-4 w-4 animate-spin" /> : <Sparkles className="mr-1 h-4 w-4" />} Montar plano de resgate por vendedor
        </Button>
        {erro && <p className="text-sm text-destructive">{erro}</p>}
      </div>
    )
  }
  return (
    <div className="space-y-1 rounded-lg border border-rose-500/30 bg-card p-3">
      <div className="flex items-center justify-between">
        <h3 className="text-xs font-bold uppercase tracking-widest text-rose-700/80 dark:text-rose-300/80">Plano de resgate</h3>
        <div className="flex items-center gap-1"><SeloFonte fonte={r.fonte} motivo={r.motivo} /><BotaoCopiar texto={r.texto} /></div>
      </div>
      <TextoRico texto={r.texto} />
    </div>
  )
}

function Numero({ rotulo, valor, destaque }: { rotulo: string; valor: string; destaque?: boolean }) {
  return (
    <div>
      <p className="text-[11px] uppercase tracking-widest text-muted-foreground">{rotulo}</p>
      <p className={`text-lg font-bold tabular-nums ${destaque ? "text-rose-600 dark:text-rose-300" : ""}`}>{valor}</p>
    </div>
  )
}

// Meta × projeção do recorte. Em emergência (último mês do trimestre + meta em risco)
// vira o painel principal da tela, com a lista de resgate.
export function PainelEmergencia({ e, data, recorte, onAbrirDeal }: {
  e: EmergenciaResponse; data: string; recorte: Recorte; onAbrirDeal: (id: string) => void
}) {
  if (e.meta === null) return null
  const tri = e.trimestre

  if (!e.ativa) {
    return (
      <Card className="flex flex-col gap-3 border-border/60 bg-card/70 p-4 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-2 text-sm">
          {e.em_risco
            ? <CalendarClock className="h-4 w-4 text-amber-500" />
            : <CheckCircle2 className="h-4 w-4 text-emerald-500" />}
          <span>
            Trimestre até {dataBr(tri.fim)}: {usd(e.fechado)} fechados de {usd(e.meta)} de meta.
            {e.em_risco ? ` Projeção abaixo da meta (${usd(e.projecao)}).` : " Projeção bate a meta."}
            {!e.na_janela && ` Modo emergência liga nos últimos ${e.janela_dias} dias.`}
          </span>
        </div>
        <div className="md:w-72"><BarraRitmo pctMeta={e.pct_meta} pctTrimestre={tri.pct_decorrido} /></div>
      </Card>
    )
  }

  const r = e.resgate
  return (
    <Card className="gap-4 border-2 border-rose-500/50 bg-rose-500/5 p-5">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-rose-500/15 ring-1 ring-rose-500/30">
            <Siren className="h-5 w-5 text-rose-600 dark:text-rose-300" />
          </div>
          <div>
            <h2 className="font-bold">Modo emergência — meta em risco</h2>
            <p className="text-sm text-muted-foreground">
              Faltam {tri.dias_restantes} dias para {dataBr(tri.fim)}. Meta = média trimestral fechada
              {e.meta_fator !== 1 ? ` × ${e.meta_fator}` : ""}.
            </p>
          </div>
        </div>
        <div className="w-full md:w-80"><BarraRitmo pctMeta={e.pct_meta} pctTrimestre={tri.pct_decorrido} /></div>
      </div>

      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        <Numero rotulo="Meta" valor={usd(e.meta)} />
        <Numero rotulo="Fechado" valor={usd(e.fechado)} />
        <Numero rotulo="Projeção" valor={usd(e.projecao)} />
        <Numero rotulo="Falta fechar" valor={usd(e.falta)} destaque />
      </div>

      <PlanoResgate key={data + JSON.stringify(recorte)} data={data} recorte={recorte} />

      <div>
        <h3 className="mb-2 text-xs font-bold uppercase tracking-widest text-rose-700/80 dark:text-rose-300/80">
          Lista de resgate — {r.n} deals somam {usd(r.valor)}
          {!r.cobre_a_meta && " (não cobre tudo: nem fechando todo o pipeline viável a meta é batida)"}
        </h3>
        <div className="overflow-x-auto rounded-lg border border-border/60 bg-card">
          <table className="w-full text-sm">
            <thead className="text-left text-[11px] uppercase tracking-widest text-muted-foreground">
              <tr>
                <th className="px-3 py-2">#</th><th className="px-3 py-2">Conta / Produto</th>
                <th className="hidden px-3 py-2 md:table-cell">Vendedor</th>
                <th className="px-3 py-2 text-right">Chance no tri</th><th className="px-3 py-2 text-right">Se fechar</th>
              </tr>
            </thead>
            <tbody>
              {r.deals.map((d, i) => (
                <tr key={d.opportunity_id} onClick={() => onAbrirDeal(d.opportunity_id)} className="cursor-pointer border-t border-border/40 hover:bg-primary/5">
                  <td className="px-3 py-2 tabular-nums text-muted-foreground">{i + 1}</td>
                  <td className="px-3 py-2">
                    <p className="font-medium">{d.conta ?? <span className="italic text-muted-foreground">Conta não preenchida</span>}</p>
                    <p className="text-xs text-muted-foreground">{d.produto} · {d.idade_dias}d em Engaging</p>
                  </td>
                  <td className="hidden px-3 py-2 md:table-cell">{d.agente}</td>
                  <td className="px-3 py-2 text-right tabular-nums">{pct(d.prob_trimestre)}</td>
                  <td className="px-3 py-2 text-right font-semibold tabular-nums">{usd(d.valor_liquido)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {r.n > r.deals.length && (
          <p className="mt-1 text-xs text-muted-foreground">
            Mostrando os {r.deals.length} primeiros de {r.n}. Filtre por vendedor para ver a lista de resgate de cada um.
          </p>
        )}
      </div>
    </Card>
  )
}
