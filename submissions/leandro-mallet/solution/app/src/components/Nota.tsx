import { fraseIcone, ROTULO_ICONE } from "@/lib/calculos";
import type { FaixaNota, Icone } from "@/lib/tipos";

const COR_FAIXA: Record<FaixaNota, string> = { alta: "bg-nota-alta", media: "bg-nota-media", baixa: "bg-nota-baixa" };
const ROTULO_FAIXA: Record<FaixaNota, string> = { alta: "alta", media: "média", baixa: "baixa" };

/** Barra da nota: preenchida até a nota, com a cor da faixa. A nota vai de 0 a 120 (com o bonus). */
export function BarraNota({ score, faixa, grande }: { score: number | null; faixa: FaixaNota | null; grande?: boolean }) {
  if (score === null || faixa === null) {
    return (
      <div className="flex items-center gap-2">
        <div className={`flex-1 rounded-selo bg-trilho ${grande ? "h-3" : "h-2"}`} role="img" aria-label="Sem nota ainda" />
        <span className="text-xs whitespace-nowrap text-texto-2">Sem nota ainda</span>
      </div>
    );
  }
  return (
    <div className="flex items-center gap-2">
      <div
        className={`flex-1 overflow-hidden rounded-selo bg-trilho ${grande ? "h-3" : "h-2"}`}
        role="img"
        aria-label={`Nota ${score}, faixa ${ROTULO_FAIXA[faixa]}`}
      >
        <div className={`h-full rounded-selo ${COR_FAIXA[faixa]}`} style={{ width: `${Math.min(100, (score / 120) * 100)}%` }} />
      </div>
      <span className={`font-titulo font-bold ${grande ? "text-nota" : "text-base"}`}>{score}</span>
    </div>
  );
}

// Chama, triângulo de alerta e floco.
const DESENHO: Record<Icone, string> = {
  super_hot:
    "M12 2c1 4 5 5.5 5 10.5A5 5 0 0 1 12 18a5 5 0 0 1-5-5.5C7 10 9 9 9.5 6.5 11 7.5 11.5 5 12 2Zm0 9c-1.2 1.2-2 2-2 3.2A2 2 0 0 0 12 16a2 2 0 0 0 2-1.8c0-1.2-.8-2-2-3.2Z",
  em_risco: "M12 3 2 20h20L12 3Zm-1 6h2v6h-2V9Zm0 8h2v2h-2v-2Z",
  esfriou:
    "M11 2h2v4.6l3.3-1.9 1 1.7L14 8.3l4 2.3-1 1.7-4-2.3V14l4-2.3 1 1.7-4 2.3 3.3 1.9-1 1.7L13 17.4V22h-2v-4.6l-3.3 1.9-1-1.7L10 15.7l-4-2.3 1-1.7 4 2.3V10l-4 2.3-1-1.7 4-2.3-3.3-1.9 1-1.7L11 6.6V2Z",
};
const ESTILO: Record<Icone, string> = {
  super_hot: "bg-dourado text-marinho",
  em_risco: "border border-bronze bg-aviso-fundo text-bronze-escuro",
  esfriou: "bg-trilho text-cinza",
};

/** Ícone na ponta do cartão: super hot, em risco de esfriar ou esfriou (critérios na ESPEC 2.4). */
export function IconeDeal({ icone, dias, comRotulo }: { icone: Icone | null; dias: number | null; comRotulo?: boolean }) {
  if (!icone) return null;
  const frase = fraseIcone(icone, dias);
  return (
    <span title={frase} className={`inline-flex shrink-0 items-center gap-1 rounded-selo px-2 py-1 text-xs font-semibold ${ESTILO[icone]}`}>
      <svg viewBox="0 0 24 24" className="h-4 w-4" fill="currentColor" aria-hidden>
        <path d={DESENHO[icone]} />
      </svg>
      {comRotulo ? <span>{ROTULO_ICONE[icone]}</span> : <span className="sr-only">{`${ROTULO_ICONE[icone]}. ${frase}`}</span>}
    </span>
  );
}
