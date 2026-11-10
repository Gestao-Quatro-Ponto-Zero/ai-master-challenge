import { getNavCounts } from "@/lib/queries/ops"

/** Pendentes da fila + não lidas da caixa (PRD §3.1, B3). Renderizado dentro de <Suspense>. */
export async function ConsoleBadge() {
  const { fila, caixa } = await getNavCounts().catch(() => ({ fila: 0, caixa: 0 }))
  const total = fila + caixa
  if (!total) return null
  return (
    <span
      className="inline-flex min-w-5 items-center justify-center rounded-full bg-text-1 px-1.5 text-[10px] font-semibold leading-5 text-bg"
      aria-label={`${fila} na fila, ${caixa} não lidas na caixa`}
    >
      {total}
    </span>
  )
}
