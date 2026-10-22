/** Números principais do recorte filtrado, no topo da tela. */

import type { Resumo } from "../tipos";
import { formatarMoedaCompacta, formatarNumero } from "../utils/formatadores";

interface Props {
  resumo: Resumo | null;
}

export default function CartoesResumo({ resumo }: Props) {
  // Enquanto carrega, mostra "–" para manter o layout estável.
  const numero = (valor: number | undefined) => (resumo ? formatarNumero(valor ?? 0) : "–");

  return (
    <section className="cartoes-resumo">
      <div className="cartao-resumo">
        <span className="rotulo">Negócios abertos</span>
        <strong>{numero(resumo?.total_abertos)}</strong>
      </div>
      <div className="cartao-resumo destaque-alta">
        <span className="rotulo">Prioridade alta</span>
        <strong>{numero(resumo?.qtd_prioridade_alta)}</strong>
        <span className="dica">Foque nestes primeiro</span>
      </div>
      <div className="cartao-resumo">
        <span className="rotulo">Em negociação ativa</span>
        <strong>{numero(resumo?.qtd_ativos)}</strong>
        <span className="dica">Dentro do prazo em que os negócios se resolvem</span>
      </div>
      <div className="cartao-resumo destaque-parado">
        <span className="rotulo">Parados</span>
        <strong>{numero(resumo?.qtd_parados)}</strong>
        <span className="dica">Fora do padrão: atualize ou encerre</span>
      </div>
      <div className="cartao-resumo">
        <span className="rotulo">Valor esperado</span>
        <strong>{resumo ? formatarMoedaCompacta(resumo.valor_esperado_total) : "–"}</strong>
        <span className="dica">Valor × chance, sem contar os parados</span>
      </div>
    </section>
  );
}
