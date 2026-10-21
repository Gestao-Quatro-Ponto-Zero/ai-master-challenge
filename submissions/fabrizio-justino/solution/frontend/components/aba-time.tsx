"use client"

import { useEffect, useState } from "react"
import { Loader2, Sparkles } from "lucide-react"
import { Card } from "@/components/ui/card"
import { BarraRitmo } from "@/components/barra-ritmo"
import { BotaoCopiar, SeloFonte, TextoRico } from "@/components/texto-ia"
import { ia, type Recorte, type TextoIA, type TimeResponse } from "@/lib/api"
import { pct, usd, xVezes } from "@/lib/format"

// 3 a 5 insights de win-loss do trimestre para o manager
function AnaliseTrimestre({ data, recorte }: { data: string; recorte: Recorte }) {
  const [r, setR] = useState<TextoIA | null>(null)
  const [erro, setErro] = useState("")
  useEffect(() => {
    let ativo = true
    ia.winloss(data, recorte).then((x) => ativo && setR(x)).catch((e) => ativo && setErro(e.message))
    return () => { ativo = false }
  }, [data, recorte.agente, recorte.manager]) // eslint-disable-line react-hooks/exhaustive-deps
  return (
    <Card className="gap-2 border-primary/25 p-4">
      <div className="flex items-center justify-between">
        <h3 className="flex items-center gap-1.5 font-semibold"><Sparkles className="h-4 w-4 text-primary" /> Análise do trimestre</h3>
        {r && <div className="flex items-center gap-1"><SeloFonte fonte={r.fonte} motivo={r.motivo} /><BotaoCopiar texto={r.texto} /></div>}
      </div>
      {erro ? <p className="text-sm text-destructive">{erro}</p>
        : r ? <TextoRico texto={r.texto} />
        : <p className="flex items-center gap-2 text-sm text-muted-foreground"><Loader2 className="h-4 w-4 animate-spin" /> Lendo ganhos e perdas...</p>}
    </Card>
  )
}

function Celula({ children, alerta }: { children: React.ReactNode; alerta?: boolean }) {
  return <td className={`px-3 py-2 tabular-nums ${alerta ? "font-semibold text-rose-600 dark:text-rose-300" : ""}`}>{children}</td>
}

// Visão do manager: ritmo, cobertura, velocidade, capacidade e qualidade de dado
export function AbaTime({ t, data, recorte }: { t: TimeResponse; data: string; recorte: Recorte }) {
  const pctTri = t.trimestre.pct_decorrido
  return (
    <div className="space-y-6">
      <AnaliseTrimestre data={data} recorte={recorte} />
      <div className="grid gap-3 md:grid-cols-3">
        {t.times.map((m) => (
          <Card key={m.manager} className="gap-2 p-4">
            <div className="flex items-baseline justify-between">
              <h3 className="font-semibold">{m.manager}</h3>
              <span className="text-xs text-muted-foreground">{m.regiao}</span>
            </div>
            <BarraRitmo pctMeta={m.pct_meta} pctTrimestre={pctTri} />
            <p className="text-xs text-muted-foreground">
              Cobertura {xVezes(m.cobertura)} · carga {xVezes(m.carga_rel)} da capacidade · {m.n_atacar} em "Atacar agora"
            </p>
          </Card>
        ))}
      </div>

      <div className="overflow-x-auto rounded-xl border border-border/60 bg-card/70">
        <table className="w-full text-sm">
          <thead className="border-b border-border/60 text-left text-[11px] uppercase tracking-widest text-muted-foreground">
            <tr>
              <th className="px-3 py-2.5">Vendedor</th>
              <th className="px-3 py-2.5">Ritmo do trimestre</th>
              <th className="px-3 py-2.5 text-right">Meta</th>
              <th className="px-3 py-2.5" title="Valor esperado até o fim do trimestre ÷ o que falta para a meta">Cobertura</th>
              <th className="px-3 py-2.5" title="Ciclo mediano dos ganhos vs mediana do time">Velocidade</th>
              <th className="px-3 py-2.5" title="Deals vivos em Engaging ÷ capacidade histórica (throughput × ciclo médio)">Carga</th>
              <th className="px-3 py-2.5" title="% dos deals abertos sem conta no CRM">Sem conta</th>
              <th className="px-3 py-2.5">Atacar</th>
            </tr>
          </thead>
          <tbody>
            {t.vendedores.map((v) => (
              <tr key={v.agente} className="border-b border-border/40 last:border-0">
                <td className="px-3 py-2">
                  <p className="font-medium">{v.agente}</p>
                  <p className="text-xs text-muted-foreground">{v.manager} · {v.regiao}</p>
                </td>
                <td className="px-3 py-2"><BarraRitmo pctMeta={v.pct_meta} pctTrimestre={pctTri} compacta /></td>
                <Celula>{v.meta ? usd(v.meta) : "—"}</Celula>
                <Celula alerta={v.cobertura !== null && v.cobertura < 1}>{xVezes(v.cobertura)}</Celula>
                <Celula>
                  {v.ciclo_vs_time === null ? "—" : `${v.ciclo_mediano}d (${v.ciclo_vs_time > 0 ? "+" : ""}${Math.round(v.ciclo_vs_time)}d)`}
                </Celula>
                <Celula alerta={v.carga_rel !== null && v.carga_rel >= t.fator_sobrecarga}>
                  {v.carga}/{Math.round(v.capacidade)} · {xVezes(v.carga_rel)}
                  {v.carga_total > v.carga && <span className="block text-[11px] font-normal text-muted-foreground">+{v.carga_total - v.carga} fora do ciclo</span>}
                </Celula>
                <Celula alerta={v.pct_sem_conta !== null && v.pct_sem_conta >= 0.75}>{v.pct_sem_conta === null ? "—" : pct(v.pct_sem_conta)}</Celula>
                <Celula>{v.n_atacar}</Celula>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="text-xs leading-relaxed text-muted-foreground">
        Cobertura = valor esperado até o fim do trimestre ÷ o que falta para a meta. Abaixo de 1× = mesmo fechando o que
        é provável, a meta não é batida; "—" = meta já batida.
        Carga conta só os deals dentro do ciclo; os fora do ciclo aparecem à parte e deveriam ser limpos.
      </p>
    </div>
  )
}
