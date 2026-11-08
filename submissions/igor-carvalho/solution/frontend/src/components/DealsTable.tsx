import React from 'react';
import type { Deal, SortKey } from '../api/types';
import DealRow from './DealRow';

interface Props {
  items: Deal[];
  selectedId: string | null;
  accent: string;
  /** GET /meta thresholds.reviewDays (escala da barra de tempo). */
  reviewDays: number;
  sort: SortKey;
  onSort: (key: SortKey) => void;
  onSelect: (id: string) => void;
  /** Quando definido, a tabela mostra caixas de seleção (aba "A revisar"). */
  checked?: Record<string, boolean>;
  onToggle: (id: string) => void;
  onTogglePage: (all: boolean) => void;
  loading: boolean;
  hasLoaded: boolean;
  canClear: boolean;
  onClear: () => void;
}

export default class DealsTable extends React.Component<Props> {
  private sortHeader(key: SortKey, label: string) {
    const active = this.props.sort === key;
    return (
      <button
        type="button"
        className={'table__sort' + (active ? ' is-active' : '')}
        aria-pressed={active}
        title={`Ordenar por ${label.toLowerCase()}`}
        onClick={() => this.props.onSort(key)}
      >
        {label}
        {active ? ' ↓' : ''}
      </button>
    );
  }

  render() {
    const { items, selectedId, accent, reviewDays, checked, loading, hasLoaded, canClear } = this.props;
    const selectable = checked !== undefined;
    const allChecked = selectable && items.length > 0 && items.every((d) => checked[d.id]);

    return (
      <div className="table">
        <div className={'table__head' + (selectable ? ' has-check' : '')}>
          {selectable && (
            <label className="dealrow__check">
              <input
                type="checkbox"
                checked={allChecked}
                disabled={items.length === 0}
                onChange={() => this.props.onTogglePage(!allChecked)}
                aria-label="Selecionar todos desta página"
              />
            </label>
          )}
          <div className="table__cols">
            {this.sortHeader('score', 'Prioridade')}
            <span>Deal e conta</span>
            {this.sortHeader('age_days', 'Tempo no funil')}
            {this.sortHeader('expected_value', 'Valor')}
            <span>Próxima ação</span>
          </div>
        </div>

        <div className={selectable ? 'table__body has-check' : 'table__body'} aria-busy={loading}>
          {items.map((deal) => (
            <DealRow
              key={deal.id}
              deal={deal}
              accent={accent}
              reviewDays={reviewDays}
              selected={deal.id === selectedId}
              checked={selectable ? !!checked[deal.id] : undefined}
              onSelect={this.props.onSelect}
              onToggle={this.props.onToggle}
            />
          ))}
        </div>

        {!hasLoaded && items.length === 0 && (
          <div role="status" className="state">
            Carregando deals…
          </div>
        )}
        {hasLoaded && items.length === 0 && (
          <div className="state">
            <div className="state__title">Nenhum deal encontrado</div>
            <div className="state__text">Tente limpar a busca ou escolher outro produto.</div>
            {canClear && (
              <button type="button" className="btn" onClick={this.props.onClear}>
                Limpar filtros
              </button>
            )}
          </div>
        )}
      </div>
    );
  }
}
