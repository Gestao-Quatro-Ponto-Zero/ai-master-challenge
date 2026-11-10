import { fmt } from "@/lib/format"
import { cn } from "@/lib/utils"

const SHORT: Record<string, string> = {
  Access: "Access",
  "Administrative rights": "Admin rights",
  "HR Support": "HR",
  Hardware: "Hardware",
  "Internal Project": "Int. project",
  Miscellaneous: "Misc.",
  Purchase: "Purchase",
  Storage: "Storage",
}

/**
 * Matriz de confusão compacta (linhas = categoria real, colunas = prevista), sombreada pela fração da
 * linha numa escala de um tom só. O número de cada célula aparece no tooltip nativo e no rótulo acessível.
 */
export function ConfusionMatrix({ labels, matrix }: { labels: string[]; matrix: number[][] }) {
  const rowTotals = matrix.map((r) => r.reduce((a, b) => a + b, 0))
  return (
    <div className="overflow-x-auto">
      <table className="w-full min-w-[560px] table-fixed border-separate border-spacing-0.5 text-xs">
        <caption className="sr-only">Matriz de confusão do RAG no holdout: linhas com a categoria real e colunas com a categoria prevista</caption>
        <thead>
          <tr>
            <th scope="col" className="p-1 text-left font-mono text-[10px] font-normal uppercase tracking-wider text-text-3">
              Real ↓ · Prevista →
            </th>
            {labels.map((l) => (
              <th key={l} scope="col" className="p-1 text-center font-medium text-text-2">
                {SHORT[l] ?? l}
              </th>
            ))}
            <th scope="col" className="p-1 text-right font-medium text-text-2">
              Acerto
            </th>
          </tr>
        </thead>
        <tbody>
          {matrix.map((row, i) => (
            <tr key={labels[i]}>
              <th scope="row" className="p-1 text-left font-medium whitespace-nowrap text-text-2">
                {SHORT[labels[i]] ?? labels[i]}
              </th>
              {row.map((n, j) => {
                const share = rowTotals[i] ? n / rowTotals[i] : 0
                const diag = i === j
                return (
                  <td
                    key={j}
                    title={`Real ${labels[i]} → prevista ${labels[j]}: ${fmt.int(n)} tickets (${fmt.pct(share)})`}
                    aria-label={`Real ${labels[i]}, prevista ${labels[j]}: ${fmt.int(n)} tickets`}
                    className={cn("h-8 rounded-[4px] text-center tabular-nums", share >= 0.5 ? "text-bg" : "text-text-2")}
                    style={{ backgroundColor: `color-mix(in oklab, var(--text-1) ${Math.round(Math.max(share, 0.02) * 100)}%, var(--surface-2))` }}
                  >
                    {diag || share >= 0.05 ? fmt.pct(share, 0) : ""}
                  </td>
                )
              })}
              <td className="p-1 text-right font-semibold tabular-nums text-text-1">{fmt.pct(rowTotals[i] ? row[i] / rowTotals[i] : 0, 0)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
