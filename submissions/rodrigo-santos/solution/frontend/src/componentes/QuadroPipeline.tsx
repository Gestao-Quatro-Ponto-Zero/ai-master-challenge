/**
 * Quadro em colunas (uma por etapa), com os deals ordenados por prioridade.
 * Cada coluna mostra poucos cartões por vez para não sobrecarregar a tela.
 */

import { useEffect, useMemo, useState } from "react";

import type { DealResumo, Etapa } from "../tipos";
import { formatarMoeda, formatarNumero, NOMES_ETAPA } from "../utils/formatadores";
import CartaoDeal from "./CartaoDeal";

const ETAPAS: Etapa[] = ["Prospecting", "Engaging"];
const CARTOES_POR_PAGINA = 20;

interface Props {
  deals: DealResumo[];
  aoSelecionar: (id: string) => void;
}

export default function QuadroPipeline({ deals, aoSelecionar }: Props) {
  // Memorizado para que a coluna só "volte ao início" quando os dados mudarem de fato.
  const dealsPorEtapa = useMemo(
    () => Object.fromEntries(ETAPAS.map((etapa) => [etapa, deals.filter((d) => d.etapa === etapa)])),
    [deals],
  );

  return (
    <div className="quadro">
      {ETAPAS.map((etapa) => (
        <ColunaEtapa key={etapa} etapa={etapa} deals={dealsPorEtapa[etapa]} aoSelecionar={aoSelecionar} />
      ))}
    </div>
  );
}

interface PropsColuna extends Props {
  etapa: Etapa;
}

function ColunaEtapa({ etapa, deals, aoSelecionar }: PropsColuna) {
  const [visiveis, setVisiveis] = useState(CARTOES_POR_PAGINA);

  // Quando os filtros mudam, volta a mostrar só a primeira página.
  useEffect(() => setVisiveis(CARTOES_POR_PAGINA), [deals]);

  const valorEsperado = deals.reduce((soma, d) => soma + d.valor_esperado, 0);

  return (
    <section className="coluna">
      <header className="coluna-cabecalho">
        <h2>{NOMES_ETAPA[etapa]}</h2>
        <span>
          {formatarNumero(deals.length)} negócios · {formatarMoeda(valorEsperado)} esperados
        </span>
      </header>

      <div className="coluna-cartoes">
        {deals.slice(0, visiveis).map((deal) => (
          <CartaoDeal key={deal.id} deal={deal} aoSelecionar={aoSelecionar} />
        ))}
      </div>

      {visiveis < deals.length && (
        <button className="botao-mais" onClick={() => setVisiveis(visiveis + CARTOES_POR_PAGINA)}>
          Mostrar mais ({deals.length - visiveis} restantes)
        </button>
      )}
    </section>
  );
}
