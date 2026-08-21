import { Tooltip } from "./Tooltip";

/** Cor por faixa de CONFIANÇA — só estética (não é uma escala categórica
 * como a antiga A-D). */
function corPorValor(valor: number): string {
  if (valor >= 75) return "bg-navy text-white";
  if (valor >= 50) return "bg-navy/70 text-white";
  if (valor >= 25) return "bg-gray-300 text-navy";
  return "bg-alert/80 text-white";
}

/** CONFIANÇA numérica (0-100) com as duas metades que a compõem —
 * completude e suporte — e qual delas governa o mínimo, porque as duas
 * situações pedem ações opostas: completude baixa é "falta cadastro",
 * suporte baixo é "sem precedente histórico" (Requirement "Exibição
 * numérica de CONFIANÇA com as duas metades"). Tooltip próprio da
 * aplicação (não o `title` nativo), aberto no hover e no foco, dispensável
 * com `Esc` — texto sempre vindo da API, nunca reescrito no cliente. */
export function ConfidenceBadge({
  confianca,
  completude,
  suporte,
  razao,
}: {
  confianca: number;
  completude: number;
  suporte: number;
  razao: string;
}) {
  const metadeGovernante = completude <= suporte ? "completude" : "suporte";

  return (
    <Tooltip
      content={
        <>
          <p className="font-semibold mb-1">
            CONFIANÇA mede a veracidade do dado — não a chance de fechar.
          </p>
          <p className="mb-1">
            Completude {completude.toFixed(0)} · Suporte {suporte.toFixed(0)} — governada por{" "}
            {metadeGovernante === "completude" ? "completude do cadastro" : "suporte histórico"}.
          </p>
          <p>{razao}</p>
        </>
      }
    >
      <button
        type="button"
        className="inline-flex items-center gap-1.5 text-xs font-medium text-navy bg-transparent border-0 p-0 cursor-help"
      >
        <span
          className={
            "inline-flex items-center justify-center min-w-6 h-6 px-1 rounded-full text-xs font-bold shrink-0 " +
            corPorValor(confianca)
          }
        >
          {confianca.toFixed(0)}
        </span>
        <span className="text-muted">
          {metadeGovernante === "completude" ? "cadastro" : "histórico"}
        </span>
      </button>
    </Tooltip>
  );
}
