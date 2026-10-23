import { preencher, type ItemFila, type TextosDaNutricao } from '@lead-scorer/dominio/priorizacao';
import { link } from '../app/rotas';
import { formatarData } from '../ui/formato';

/**
 * Um negócio na lista, em 3 linhas e nada mais: o score ("Score 87", a qualidade do negócio, ou
 * "Score —"), a ação em uma linha e "{produto} · US$ {preço} em jogo" pequeno (o valor, fora do
 * score), com o "ver por quê" que abre o detalhe (o porquê do score, a posição na lista, a chance e
 * os fatores ficam lá). Em Nutrição, a ação é o botão de encaminhar ou, depois, "Encaminhado em
 * {data}." com "Contestar".
 */
export function ItemDaFila({
  item,
  rotuloBotaoNutricao,
  rotuloPorque,
  textosNutricao,
  aoEncaminhar,
}: {
  item: ItemFila;
  /** O rótulo do botão de Nutrição, dos textos da política. */
  rotuloBotaoNutricao: string;
  /** "ver por quê", dos textos da política. */
  rotuloPorque: string;
  /** "Encaminhado em {data}." e "Contestar", dos textos da política. */
  textosNutricao: TextosDaNutricao;
  /** Ausente = só leitura (sem botão). */
  aoEncaminhar?: (item: ItemFila) => void;
}) {
  const { deal, indicador, proximaAcao, decisao } = item;
  const encaminhado = decisao?.acao === 'encaminhar_para_nutricao' && decisao.aceita;
  return (
    <li
      className="item item--cartao ls-hover-outline"
      data-testid="fila-item"
      data-deal-id={deal.id}
    >
      <p className="item__score" data-testid="fila-item-indicador">
        {indicador.numero}
      </p>
      {item.bloco === 'nutricao' && encaminhado ? (
        <p className="item__acao" data-testid="fila-item-acao">
          {preencher(textosNutricao.encaminhado, { data: formatarData(decisao.em) })}{' '}
          {aoEncaminhar ? (
            <a href={link.deal(deal.id)} data-testid="fila-item-contestar">
              {textosNutricao.contestar}
            </a>
          ) : null}
        </p>
      ) : item.bloco === 'nutricao' && aoEncaminhar ? (
        <button
          type="button"
          className="botao botao--ghost ls-t-colors item__botao"
          data-testid="fila-item-acao"
          onClick={() => aoEncaminhar(item)}
        >
          {rotuloBotaoNutricao}
        </button>
      ) : (
        <p className="item__acao" data-testid="fila-item-acao">
          {item.bloco === 'nutricao' ? rotuloBotaoNutricao : proximaAcao.texto}
        </p>
      )}
      <p className="item__meta" data-testid="fila-item-produto">
        {indicador.emJogo} ·{' '}
        <a href={link.deal(deal.id)} data-testid="fila-item-porque">
          {rotuloPorque}
        </a>
      </p>
    </li>
  );
}
