import React from 'react';
import type { Funnel } from '../api/types';
import { money } from '../lib/format';
import { heatStyle } from '../lib/theme';

type Metric = 'count' | 'value';

interface Props {
  funnel: Funnel;
  /** Produto filtrado na lista ('all' = nenhum). */
  product: string;
  onPick: (product: string) => void;
}

interface State {
  metric: Metric;
}

/**
 * Heatmap do funil: produto (linhas) x tempo no funil (colunas). Mostra onde estão os deals e onde eles envelhecem.
 * Os números e as faixas de dias vêm da API (GET /summary, funnel); aqui só se desenha.
 */
export default class FunnelHeatmap extends React.Component<Props, State> {
  state: State = { metric: 'count' };

  private onMetric = (metric: Metric) => this.setState({ metric });

  private amount(cell: { count: number; expectedValue: number }): number {
    return this.state.metric === 'count' ? cell.count : cell.expectedValue;
  }

  render() {
    const { funnel, product } = this.props;
    const { metric } = this.state;
    if (funnel.rows.length === 0 || funnel.columns.length === 0) return null;

    const max = Math.max(0, ...funnel.rows.flatMap((r) => r.cells.map((c) => this.amount(c))));
    const cols = funnel.columns.length;
    const text = (n: number) => (metric === 'count' ? String(n) : money(n));
    const unit = metric === 'count' ? 'deals' : 'de valor esperado';

    return (
      <section className="heat" aria-label="Funil por produto e tempo">
        <div className="heat__head">
          <div>
            <h2 className="heat__title">Funil: onde estão seus deals</h2>
            <p className="heat__sub">
              Produto por tempo no funil. Quanto mais escuro, mais {metric === 'count' ? 'deals' : 'valor esperado'}. Clique para filtrar a lista.
            </p>
          </div>
          <div className="heat__metric" role="group" aria-label="O que mostrar">
            <button type="button" className={metric === 'count' ? 'is-on' : ''} aria-pressed={metric === 'count'} onClick={() => this.onMetric('count')}>
              Deals
            </button>
            <button type="button" className={metric === 'value' ? 'is-on' : ''} aria-pressed={metric === 'value'} onClick={() => this.onMetric('value')}>
              Valor esperado
            </button>
          </div>
        </div>

        <div className="heat__grid" role="table" style={{ gridTemplateColumns: `minmax(120px, 1.4fr) repeat(${cols}, minmax(64px, 1fr))` }}>
          <div className="heat__corner" role="columnheader">
            Produto
          </div>
          {funnel.columns.map((c) => (
            <div key={c.key} className="heat__col" role="columnheader">
              {c.label}
            </div>
          ))}
          {funnel.rows.map((row) => (
            <React.Fragment key={row.product}>
              <div className={'heat__row' + (row.product === product ? ' is-picked' : '')} role="rowheader">
                {row.product}
                <span className="heat__rowtotal">{row.count} deals</span>
              </div>
              {row.cells.map((cell, i) => {
                const n = this.amount(cell);
                const style = heatStyle(i, max > 0 ? n / max : 0);
                return (
                  <button
                    key={funnel.columns[i].key}
                    type="button"
                    role="cell"
                    className="heat__cell"
                    data-testid={`heat-${row.product}-${funnel.columns[i].key}`}
                    style={{ background: style.bg, color: style.fg }}
                    aria-label={`${row.product}, ${funnel.columns[i].label}: ${cell.count} deals, ${money(cell.expectedValue)} de valor esperado`}
                    title={`${cell.count} deals · ${money(cell.expectedValue)} esperado`}
                    onClick={() => this.props.onPick(row.product)}
                  >
                    {n === 0 ? '·' : text(n)}
                  </button>
                );
              })}
            </React.Fragment>
          ))}
        </div>
        <p className="heat__note">
          Mostrando {unit}. Valor esperado não conta deals a revisar. Deals em prospecção ficam de fora (ainda sem data).
        </p>
      </section>
    );
  }
}
