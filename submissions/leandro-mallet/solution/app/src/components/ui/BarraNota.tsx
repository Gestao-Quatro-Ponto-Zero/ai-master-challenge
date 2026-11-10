// Barra da nota: um componente só, fina, com a cor pela faixa (alta, média, baixa) e o número em Manrope 600
// com algarismos tabulares. Igual no Painel, no Pipeline, nos Leads e no deal. A nota vai de 0 a 120 (com o bônus).
import type { FaixaNota } from "@/lib/tipos";

const COR_FAIXA: Record<FaixaNota, string> = { alta: "bg-nota-alta", media: "bg-nota-media", baixa: "bg-nota-baixa" };
const ROTULO_FAIXA: Record<FaixaNota, string> = { alta: "alta", media: "média", baixa: "baixa" };

export function BarraNota({ score, faixa, grande }: { score: number | null; faixa: FaixaNota | null; grande?: boolean }) {
  const trilho = `flex-1 overflow-hidden rounded-selo bg-trilho ${grande ? "h-2" : "h-1.5"}`;
  if (score === null || faixa === null) {
    return (
      <div className="flex items-center gap-2">
        <div className={trilho} role="img" aria-label="Sem nota ainda" />
        <span className="text-xs whitespace-nowrap text-texto-2">Sem nota ainda</span>
      </div>
    );
  }
  return (
    <div className="flex items-center gap-2">
      <div className={trilho} role="img" aria-label={`Nota ${score}, faixa ${ROTULO_FAIXA[faixa]}`}>
        <div className={`h-full rounded-selo ${COR_FAIXA[faixa]}`} style={{ width: `${Math.min(100, (score / 120) * 100)}%` }} />
      </div>
      <span className={`min-w-[2ch] text-right font-texto font-semibold tabular-nums ${grande ? "text-2xl" : "text-sm"}`} aria-hidden>
        {score}
      </span>
    </div>
  );
}
