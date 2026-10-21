"use client"

import { useState, type ReactNode } from "react"
import { Check, Copy, Sparkles, FileText } from "lucide-react"
import { Button } from "@/components/ui/button"

// Selo "IA" × "texto automático": o vendedor sempre sabe de onde veio o texto
export function SeloFonte({ fonte, motivo }: { fonte: "ia" | "template"; motivo?: string }) {
  return fonte === "ia" ? (
    <span className="inline-flex items-center gap-1 rounded-full bg-primary/10 px-2 py-0.5 text-[11px] font-medium text-primary ring-1 ring-primary/20">
      <Sparkles className="h-3 w-3" /> gerado por IA
    </span>
  ) : (
    <span title={motivo} className="inline-flex items-center gap-1 rounded-full bg-muted px-2 py-0.5 text-[11px] text-muted-foreground ring-1 ring-border">
      <FileText className="h-3 w-3" /> texto automático
    </span>
  )
}

// **negrito** dentro de uma linha — parser simples, sem dependência de markdown
function Rico({ texto }: { texto: string }) {
  return (
    <>
      {texto.split(/(\*\*[^*]+\*\*)/).map((p, i) =>
        p.startsWith("**") && p.endsWith("**") ? <strong key={i} className="font-semibold text-foreground">{p.slice(2, -2)}</strong> : <span key={i}>{p}</span>,
      )}
    </>
  )
}

export function TextoRico({ texto }: { texto: string }) {
  const nos: ReactNode[] = []
  let lista: string[] = []
  const fechaLista = (k: number) => {
    if (lista.length) {
      nos.push(
        <ul key={`l${k}`} className="my-1.5 ml-4 list-disc space-y-1">
          {lista.map((l, i) => <li key={i}><Rico texto={l} /></li>)}
        </ul>,
      )
      lista = []
    }
  }
  texto.split("\n").forEach((bruta, i) => {
    const linha = bruta.trim()
    if (!linha) return fechaLista(i)
    if (linha.startsWith("- ") || linha.startsWith("• ")) return void lista.push(linha.slice(2))
    fechaLista(i)
    nos.push(<p key={i} className="my-1.5"><Rico texto={linha} /></p>)
  })
  fechaLista(-1)
  return <div className="text-sm leading-relaxed text-foreground/90">{nos}</div>
}

export function BotaoCopiar({ texto }: { texto: string }) {
  const [copiado, setCopiado] = useState(false)
  return (
    <Button
      variant="ghost"
      size="sm"
      className="h-7 px-2 text-xs"
      onClick={async () => {
        await navigator.clipboard.writeText(texto).catch(() => {})
        setCopiado(true)
        setTimeout(() => setCopiado(false), 1500)
      }}
    >
      {copiado ? <><Check className="mr-1 h-3 w-3" /> Copiado</> : <><Copy className="mr-1 h-3 w-3" /> Copiar</>}
    </Button>
  )
}
