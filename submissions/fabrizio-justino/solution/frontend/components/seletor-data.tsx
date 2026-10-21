"use client"

import { CalendarClock, Siren } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import type { DatasResponse } from "@/lib/api"
import { dataBr } from "@/lib/format"

// Segunda-feira a 27 dias do fim do Q4/2017 — atalho pra ver o modo emergência
const DATA_PRESSAO = "2017-12-04"

function rotulo(d: DatasResponse["datas"][number]) {
  const base = dataBr(d.data)
  if (d.final) return `${base} · último dia do dataset`
  return `${base} · ${d.dias_para_fim_trimestre} dias p/ fechar o trimestre`
}

// O dataset termina em 31/12/2017. Escolher outra data reconstrói o pipeline como ele
// estava naquela segunda-feira (backend: dados.snapshot) — sem ver o futuro.
export function SeletorData({ datas, valor, onChange }: { datas: DatasResponse; valor: string; onChange: (d: string) => void }) {
  const temPressao = datas.datas.some((d) => d.data === DATA_PRESSAO)
  return (
    <div className="flex flex-wrap items-end gap-2">
      <label className="flex min-w-[260px] flex-col gap-1">
        <span className="flex items-center gap-1 text-[11px] font-semibold uppercase tracking-widest text-muted-foreground/80">
          <CalendarClock className="h-3 w-3" /> Ver o pipeline em
        </span>
        <Select value={valor} onValueChange={onChange}>
          <SelectTrigger className="w-full bg-card"><SelectValue /></SelectTrigger>
          <SelectContent className="max-h-80">
            {datas.datas.map((d) => <SelectItem key={d.data} value={d.data}>{rotulo(d)}</SelectItem>)}
          </SelectContent>
        </Select>
      </label>
      {temPressao && valor !== DATA_PRESSAO && (
        <Button variant="outline" size="sm" onClick={() => onChange(DATA_PRESSAO)} className="border-rose-500/40 text-rose-600 dark:text-rose-300">
          <Siren className="mr-1 h-4 w-4" /> Simular pressão de fim de trimestre
        </Button>
      )}
    </div>
  )
}
