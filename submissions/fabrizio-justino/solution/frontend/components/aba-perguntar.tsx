"use client"

import { useState } from "react"
import { Loader2, Send, Wrench } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { SeloFonte, TextoRico } from "@/components/texto-ia"
import { ia, type MensagemChat, type TextoIA } from "@/lib/api"

const SUGESTOES = [
  "Quais deals fecham o gap da meta do Melvin Marxen?",
  "Quem do time Central está mais atrás do ritmo?",
  "Quantos deals estão fora do ciclo e quanto valem?",
  "O que a Anna Snelling deve atacar esta semana?",
]

const NOME_FERRAMENTA: Record<string, string> = {
  consultar_pipeline: "pipeline", consultar_deal: "deal", consultar_emergencia: "emergência",
  consultar_time: "time", consultar_alertas: "alertas", consultar_winloss: "win-loss", consultar_cross_sell: "cross-sell",
}

interface Turno extends MensagemChat {
  meta?: TextoIA
}

// "Pergunte ao pipeline": a IA consulta as mesmas consultas da tela (tool calling)
export function AbaPerguntar({ data, onAbrirDeal }: { data: string; onAbrirDeal: (id: string) => void }) {
  const [turnos, setTurnos] = useState<Turno[]>([])
  const [texto, setTexto] = useState("")
  const [carregando, setCarregando] = useState(false)

  const enviar = async (pergunta: string) => {
    if (!pergunta.trim() || carregando) return
    const historico = turnos.map(({ role, content }) => ({ role, content }))
    setTurnos((t) => [...t, { role: "user", content: pergunta }])
    setTexto("")
    setCarregando(true)
    try {
      const r = await ia.perguntar(data, pergunta, historico)
      setTurnos((t) => [...t, { role: "assistant", content: r.texto, meta: r }])
    } catch (e) {
      setTurnos((t) => [...t, { role: "assistant", content: e instanceof Error ? e.message : "Erro ao perguntar." }])
    } finally {
      setCarregando(false)
    }
  }

  return (
    <div className="space-y-4">
      {turnos.length === 0 && (
        <div className="space-y-2">
          <p className="text-sm text-muted-foreground">
            Pergunte em português sobre o pipeline desta data. A IA busca os números nas mesmas consultas da tela e não
            calcula nada por conta própria.
          </p>
          <div className="flex flex-wrap gap-2">
            {SUGESTOES.map((s) => (
              <button key={s} type="button" onClick={() => enviar(s)}
                className="rounded-full border border-primary/30 bg-card px-3 py-1 text-xs text-primary hover:bg-primary/5">
                {s}
              </button>
            ))}
          </div>
        </div>
      )}

      <div className="space-y-3">
        {turnos.map((t, i) => (
          <div key={i} className={t.role === "user" ? "flex justify-end" : ""}>
            {t.role === "user" ? (
              <p className="max-w-[80%] rounded-2xl rounded-br-sm bg-primary px-4 py-2 text-sm text-primary-foreground">{t.content}</p>
            ) : (
              <div className="max-w-[90%] rounded-2xl rounded-bl-sm border border-border/60 bg-card/80 px-4 py-3">
                <TextoRico texto={t.content} />
                {t.meta && (
                  <div className="mt-2 flex flex-wrap items-center gap-2 text-[11px] text-muted-foreground">
                    <SeloFonte fonte={t.meta.fonte} motivo={t.meta.motivo} />
                    {!!t.meta.ferramentas?.length && (
                      <span className="flex items-center gap-1">
                        <Wrench className="h-3 w-3" /> consultou: {[...new Set(t.meta.ferramentas)].map((f) => NOME_FERRAMENTA[f] ?? f).join(", ")}
                      </span>
                    )}
                    {t.meta.deals_citados?.map((id) => (
                      <button key={id} type="button" onClick={() => onAbrirDeal(id)} className="font-mono text-primary underline">
                        {id}
                      </button>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
        {carregando && (
          <p className="flex items-center gap-2 text-sm text-muted-foreground"><Loader2 className="h-4 w-4 animate-spin" /> Consultando o pipeline...</p>
        )}
      </div>

      <form onSubmit={(e) => { e.preventDefault(); enviar(texto) }} className="flex gap-2">
        <Input value={texto} onChange={(e) => setTexto(e.target.value)} placeholder="Ex.: quais deals do time West fecham este mês?"
          maxLength={1000} className="bg-card" />
        <Button type="submit" disabled={carregando || !texto.trim()}><Send className="h-4 w-4" /></Button>
      </form>
    </div>
  )
}
