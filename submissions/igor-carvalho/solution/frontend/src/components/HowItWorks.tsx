import React from 'react';
import type { Meta } from '../api/types';

interface Props {
  /** Regras vindas de GET /meta: nada aqui é fixo no código. */
  meta: Pick<Meta, 'thresholds' | 'priorityLevels' | 'lowConfidenceBelowClosedDeals' | 'horizonDays'>;
}

export default class HowItWorks extends React.Component<Props> {
  render() {
    const { thresholds: t, priorityLevels, lowConfidenceBelowClosedDeals, horizonDays } = this.props.meta;
    const horizon = horizonDays !== null ? `nos próximos ${horizonDays} dias` : 'no próximo período';
    const highest = priorityLevels[0];
    return (
      <div className="howto">
        <h2 className="howto__title">Como a prioridade é calculada</h2>
        <p>
          O modelo estima a <strong>chance de cada deal ser ganho {horizon}</strong>. Multiplicada pelo preço, vira o{' '}
          <strong>valor esperado</strong>: a receita que se espera do deal {horizon}.
        </p>
        <p>
          O <strong>índice de 0 a 100</strong> é a posição do deal nessa lista: o percentil do valor esperado entre os
          deals abertos que não estão em "A revisar". Quanto maior, mais vale trabalhar o deal agora.
        </p>
        <p>
          O <strong>foco da semana</strong> reúne os deals de prioridade {priorityLevels[0].label} e {priorityLevels[1].label}.{' '}
          <strong>Seu dia</strong> mostra os melhores deles, pelo índice, para você começar hoje.
        </p>
        <h3>O que pesa</h3>
        <ul>
          <li>Valor do produto (ticket).</li>
          <li>Tempo no funil, comparado ao prazo típico de quem fecha.</li>
          <li>Histórico do vendedor com o produto e desempenho recente.</li>
          <li>Quantidade de deals abertos ao mesmo tempo.</li>
        </ul>
        <h3>Como ler o índice</h3>
        <ul>
          <li>O índice é uma posição, não uma probabilidade: 87/100 não quer dizer 87% de chance. Preço, valor esperado e chance de fechar aparecem à parte.</li>
          <li>{priorityLevels.map((l) => `${l.label}: ${l.minScore} a ${l.maxScore}`).join('. ')}.</li>
          <li>
            Prazos dos deals já fechados: metade fecha em até {t.typicalP50} dias, a maioria em até {t.staleDays} dias e quase
            todos em até {t.reviewDays} dias.
          </li>
          <li>
            Acima de {t.staleDays} dias o deal vai para "Decidir agora": o índice só ordena a fila e não chega a{' '}
            {highest.label}.
          </li>
          <li>
            Acima de {t.reviewDays} dias vai para "A revisar" e fica sem índice: encerrar ou reativar é mais útil que
            prever.
          </li>
          <li>Deals em Prospecção ainda não têm data de engajamento e ficam sem índice.</li>
        </ul>
        <h3>O que tomar com cuidado</h3>
        <ul>
          <li>Os motivos mostrados são padrões do histórico, não causas.</li>
          <li>A chance de ganhar é um apoio fraco. Use junto com o seu julgamento.</li>
          <li>A confiança da previsão fica baixa quando o vendedor tem menos de {lowConfidenceBelowClosedDeals} deals fechados.</li>
          <li>A completude dos dados é outra coisa: mostra se falta algum campo do deal e se isso afeta o cálculo.</li>
        </ul>
      </div>
    );
  }
}
