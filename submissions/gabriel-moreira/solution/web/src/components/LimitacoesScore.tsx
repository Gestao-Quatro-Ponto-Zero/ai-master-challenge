import type { ComponenteScore, LimitacaoScore } from "../types";

/** Nome de exibição de cada componente afetado — o mesmo rótulo que o
 * painel usa no número em si, para que a ficha de limitação e o número
 * que ela ressalva se reconheçam. */
export const COMPONENTE_LABEL: Record<ComponenteScore, string> = {
  score: "Score",
  p_hat: "Probabilidade",
  valor: "Valor",
  urgencia: "Urgência",
  confianca: "Confiança",
};

export function limitacoesDe(
  limitacoes: LimitacaoScore[],
  componente: ComponenteScore
): LimitacaoScore[] {
  return limitacoes.filter((limitacao) => limitacao.componentes.includes(componente));
}

/** Marcador colado ao número afetado — só o rótulo curto, porque a
 * explicação inteira vive uma vez só, na ficha abaixo. Serve de âncora
 * visual: quem estranha o número encontra a ressalva no mesmo lugar em
 * que estranhou, não numa aba separada. */
export function MarcadorLimitacao({
  limitacoes,
  componente,
}: {
  limitacoes: LimitacaoScore[];
  componente: ComponenteScore;
}) {
  const aplicaveis = limitacoesDe(limitacoes, componente);
  if (aplicaveis.length === 0) return null;

  return (
    <span className="flex flex-wrap gap-1 mt-1.5">
      {aplicaveis.map((limitacao) => (
        <span
          key={limitacao.id}
          className="inline-flex items-center gap-1 text-[10px] font-semibold text-navy bg-gold/15 border border-gold/50 rounded-full px-1.5 py-0.5 leading-tight"
        >
          <span aria-hidden="true">!</span>
          {limitacao.rotulo_curto}
        </span>
      ))}
    </span>
  );
}

/** Ficha de cada limitação que incide sobre este score: o que é, em que
 * números pega, e o que muda neles. A lista vem da API já filtrada para
 * esta oportunidade — uma oportunidade completa, jovem e com conta traz
 * só a primeira, que define o que o SCORE é. */
export function LimitacoesScore({ limitacoes }: { limitacoes: LimitacaoScore[] }) {
  return (
    <ul className="flex flex-col gap-3">
      {limitacoes.map((limitacao) => (
        <li
          key={limitacao.id}
          className="border-l-2 border-gold pl-3 flex flex-col gap-1"
        >
          <div className="flex flex-wrap items-baseline gap-x-2 gap-y-1">
            <span className="text-sm font-bold text-navy leading-snug">
              {limitacao.titulo}
            </span>
            <span className="flex flex-wrap gap-1">
              {limitacao.componentes.map((componente) => (
                <span
                  key={componente}
                  className="text-[10px] uppercase tracking-wide text-muted border border-border rounded-full px-1.5 py-0.5 whitespace-nowrap"
                >
                  {COMPONENTE_LABEL[componente]}
                </span>
              ))}
            </span>
          </div>
          <p className="text-sm text-muted leading-relaxed">{limitacao.impacto}</p>
        </li>
      ))}
    </ul>
  );
}
