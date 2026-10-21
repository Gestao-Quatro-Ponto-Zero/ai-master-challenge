"use client"

import { useMemo } from "react"
import { X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import type { FiltrosResponse, Recorte } from "@/lib/api"

// Radix Select não aceita value="" — "todos" é o sentinela de "sem filtro"
const TODOS = "todos"

interface Props {
  opcoes: FiltrosResponse
  recorte: Recorte
  onChange: (r: Recorte) => void
}

function Campo({ rotulo, valor, itens, onChange }: {
  rotulo: string
  valor?: string
  itens: { value: string; label: string }[]
  onChange: (v?: string) => void
}) {
  return (
    <label className="flex min-w-[160px] flex-1 flex-col gap-1">
      <span className="text-[11px] font-semibold uppercase tracking-widest text-muted-foreground/80">{rotulo}</span>
      <Select value={valor ?? TODOS} onValueChange={(v) => onChange(v === TODOS ? undefined : v)}>
        <SelectTrigger className="w-full bg-card">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={TODOS}>Todos</SelectItem>
          {itens.map((i) => (
            <SelectItem key={i.value} value={i.value}>{i.label}</SelectItem>
          ))}
        </SelectContent>
      </Select>
    </label>
  )
}

export function Filtros({ opcoes, recorte, onChange }: Props) {
  // Filtros em cascata: região restringe managers, manager restringe vendedores
  const agentesVisiveis = useMemo(
    () => opcoes.agentes.filter((a) =>
      (!recorte.regiao || a.regiao === recorte.regiao) && (!recorte.manager || a.manager === recorte.manager)),
    [opcoes, recorte.regiao, recorte.manager],
  )
  const managersVisiveis = useMemo(
    () => [...new Set(opcoes.agentes.filter((a) => !recorte.regiao || a.regiao === recorte.regiao).map((a) => a.manager))].sort(),
    [opcoes, recorte.regiao],
  )
  const temFiltro = Object.values(recorte).some(Boolean)

  return (
    <div className="flex flex-wrap items-end gap-3">
      <Campo
        rotulo="Região"
        valor={recorte.regiao}
        itens={opcoes.regioes.map((r) => ({ value: r, label: r }))}
        onChange={(regiao) => onChange({ ...recorte, regiao, manager: undefined, agente: undefined })}
      />
      <Campo
        rotulo="Manager"
        valor={recorte.manager}
        itens={managersVisiveis.map((m) => ({ value: m, label: m }))}
        onChange={(manager) => onChange({ ...recorte, manager, agente: undefined })}
      />
      <Campo
        rotulo="Vendedor"
        valor={recorte.agente}
        itens={agentesVisiveis.map((a) => ({
          value: a.nome,
          label: a.deals_abertos ? `${a.nome} (${a.deals_abertos})` : `${a.nome} — sem deals abertos`,
        }))}
        onChange={(agente) => onChange({ ...recorte, agente })}
      />
      <Campo
        rotulo="Stage"
        valor={recorte.stage}
        itens={[{ value: "Engaging", label: "Engaging" }, { value: "Prospecting", label: "Prospecting" }]}
        onChange={(stage) => onChange({ ...recorte, stage })}
      />
      {temFiltro && (
        <Button variant="ghost" size="sm" onClick={() => onChange({})} className="text-muted-foreground">
          <X className="mr-1 h-4 w-4" /> Limpar
        </Button>
      )}
    </div>
  )
}
