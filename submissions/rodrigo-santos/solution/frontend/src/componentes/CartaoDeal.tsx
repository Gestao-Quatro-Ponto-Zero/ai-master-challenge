/** Cartão de um deal no quadro do pipeline. Clicar abre o detalhe. */

import type { DealResumo } from "../tipos";
import { formatarDias, formatarMoeda, tituloDeal } from "../utils/formatadores";
import SeloPrioridade from "./SeloPrioridade";

interface Props {
  deal: DealResumo;
  aoSelecionar: (id: string) => void;
}

export default function CartaoDeal({ deal, aoSelecionar }: Props) {
  return (
    <button className="cartao-deal" onClick={() => aoSelecionar(deal.id)}>
      <div className="linha-topo">
        <SeloPrioridade prioridade={deal.prioridade} />
        <span className="score" title="Pontuação de 0 a 100">
          {deal.score}
        </span>
      </div>
      <strong className="conta">{tituloDeal(deal)}</strong>
      <span className="produto">
        {deal.produto} · {formatarMoeda(deal.valor)}
      </span>
      {/* O que mais explica a nota: ponto forte se for prioridade alta, ponto fraco nos demais. */}
      <span className={`motivo-cartao ${deal.prioridade === "Alta" ? "motivo-positivo" : "motivo-negativo"}`}>
        {deal.prioridade === "Alta" ? "▲" : "▼"} {deal.motivo_principal}
      </span>
      <div className="linha-rodape">
        <span>{deal.vendedor}</span>
        <span className={deal.parado ? "alerta-parado" : ""}>
          {deal.parado && "⚠ "}
          {formatarDias(deal.dias_aberto)}
        </span>
      </div>
    </button>
  );
}
