// Ritmo do trimestre: % da meta atingida (barra) contra % do trimestre decorrido
// (marcador). Barra antes do marcador = atrás do ritmo. Pressão sem precisar de alerta.
export function BarraRitmo({ pctMeta, pctTrimestre, compacta = false }: { pctMeta: number | null; pctTrimestre: number; compacta?: boolean }) {
  if (pctMeta === null || pctMeta === undefined) return <span className="text-xs text-muted-foreground">sem meta</span>
  const atras = pctMeta < pctTrimestre
  return (
    <div className={compacta ? "w-32" : "w-full"}>
      <div className="relative h-2.5 overflow-hidden rounded-full bg-muted">
        <div
          className={`h-full rounded-full ${atras ? "bg-rose-500" : "bg-emerald-500"}`}
          style={{ width: `${Math.min(pctMeta, 1) * 100}%` }}
        />
        <div className="absolute inset-y-0 w-0.5 bg-foreground/70" style={{ left: `${Math.min(pctTrimestre, 1) * 100}%` }} />
      </div>
      <p className="mt-0.5 text-[11px] tabular-nums text-muted-foreground">
        {Math.round(pctMeta * 100)}% da meta · {Math.round(pctTrimestre * 100)}% do trimestre
      </p>
    </div>
  )
}
