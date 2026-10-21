"use client"

import { useEffect, useState } from "react"
import { Loader2, Sunrise } from "lucide-react"
import { Card } from "@/components/ui/card"
import { BotaoCopiar, SeloFonte, TextoRico } from "@/components/texto-ia"
import { ia, type Recorte, type TextoIA } from "@/lib/api"

// Briefing de segunda: do vendedor filtrado, do manager filtrado ou da RevOps (sem filtro)
export function CardBriefing({ data, recorte }: { data: string; recorte: Recorte }) {
  const [r, setR] = useState<TextoIA | null>(null)
  const [carregando, setCarregando] = useState(true)
  const [erro, setErro] = useState("")
  const nome = recorte.agente ?? recorte.manager ?? "visão de todos os times"

  useEffect(() => {
    let ativo = true
    setCarregando(true)
    setErro("")
    ia.briefing(data, recorte)
      .then((x) => ativo && setR(x))
      .catch((e) => ativo && setErro(e.message))
      .finally(() => ativo && setCarregando(false))
    return () => { ativo = false }
  }, [data, recorte.agente, recorte.manager]) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <Card className="glass-card gap-2 border-primary/25 p-4">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 className="flex items-center gap-2 text-sm font-bold uppercase tracking-widest text-primary/80">
          <Sunrise className="h-4 w-4" /> Briefing de segunda · {nome}
        </h2>
        <div className="flex items-center gap-1">
          {r && <SeloFonte fonte={r.fonte} motivo={r.motivo} />}
          {r && <BotaoCopiar texto={r.texto} />}
        </div>
      </div>
      {carregando ? (
        <p className="flex items-center gap-2 text-sm text-muted-foreground"><Loader2 className="h-4 w-4 animate-spin" /> Montando o briefing...</p>
      ) : erro ? (
        <p className="text-sm text-destructive">{erro}</p>
      ) : r ? (
        <TextoRico texto={r.texto} />
      ) : null}
    </Card>
  )
}
