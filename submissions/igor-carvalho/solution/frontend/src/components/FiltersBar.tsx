import React from 'react';
import type { PriorityLevel, SortKey } from '../api/types';
import { SORT_OPTIONS } from '../lib/constants';

interface Props {
  search: string;
  product: string;
  level: PriorityLevel;
  /** Ordenação em vigor (a escolhida ou o padrão da aba, que vem de GET /meta). */
  sort: SortKey;
  /** Produtos de GET /filters. */
  products: string[];
  /** Opções de prioridade já montadas a partir de GET /meta (priority_levels). */
  levelOptions: { value: PriorityLevel; label: string }[];
  /** "A revisar" não tem índice, então o filtro de prioridade fica desligado. */
  levelDisabled: boolean;
  canClear: boolean;
  onSearch: (value: string) => void;
  onProduct: (value: string) => void;
  onLevel: (value: PriorityLevel) => void;
  onSort: (value: SortKey) => void;
  onClear: () => void;
}

export default class FiltersBar extends React.Component<Props> {
  render() {
    const p = this.props;
    return (
      <div className="filters">
        <div className="field field--grow">
          <label htmlFor="q">Buscar</label>
          <input
            id="q"
            type="search"
            placeholder="ID, produto ou conta"
            value={p.search}
            onChange={(e) => p.onSearch(e.target.value)}
          />
        </div>
        <div className="field">
          <label htmlFor="prod">Produto</label>
          <select id="prod" value={p.product} onChange={(e) => p.onProduct(e.target.value)}>
            <option value="all">Todos os produtos</option>
            {p.products.map((name) => (
              <option key={name} value={name}>
                {name}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label htmlFor="level">Prioridade</label>
          <select
            id="level"
            value={p.level}
            disabled={p.levelDisabled}
            onChange={(e) => p.onLevel(e.target.value as PriorityLevel)}
          >
            {p.levelOptions.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </div>
        <div className="field">
          <label htmlFor="sort">Ordenar por</label>
          <select id="sort" value={p.sort} onChange={(e) => p.onSort(e.target.value as SortKey)}>
            {SORT_OPTIONS.map((o) => (
              <option key={o.value} value={o.value}>
                {o.label}
              </option>
            ))}
          </select>
        </div>
        <span className="lockchip">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
            <rect x="5" y="11" width="14" height="9" rx="2" />
            <path d="M8 11V8a4 4 0 0 1 8 0v3" />
          </svg>
          Só os seus deals
        </span>
        {p.canClear && (
          <button type="button" className="btn btn--ghost" onClick={p.onClear}>
            Limpar filtros
          </button>
        )}
      </div>
    );
  }
}
