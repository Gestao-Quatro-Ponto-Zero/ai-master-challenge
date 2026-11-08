import React from 'react';
import { PAGE_SIZE_OPTIONS } from '../lib/constants';

interface Props {
  page: number;
  pageCount: number;
  pageSize: number;
  onPage: (page: number) => void;
  onPageSize: (size: number) => void;
}

export default class Pagination extends React.Component<Props> {
  render() {
    const { page, pageCount, pageSize, onPage, onPageSize } = this.props;
    const pages = Array.from({ length: pageCount }, (_, i) => i + 1);
    return (
      <nav aria-label="Paginação" className="pager">
        <div className="pager__size">
          <label htmlFor="psize">Por página</label>
          <select id="psize" value={pageSize} onChange={(e) => onPageSize(parseInt(e.target.value, 10))}>
            {PAGE_SIZE_OPTIONS.map((n) => (
              <option key={n} value={n}>
                {n}
              </option>
            ))}
          </select>
        </div>
        <div className="pager__pages">
          <button type="button" className="btn btn--sm" disabled={page <= 1} onClick={() => onPage(page - 1)}>
            ← Anterior
          </button>
          {pages.map((n) => (
            <button
              key={n}
              type="button"
              className={'btn btn--sm pager__num' + (n === page ? ' is-current' : '')}
              aria-current={n === page ? 'page' : undefined}
              aria-label={`Página ${n}`}
              onClick={() => onPage(n)}
            >
              {n}
            </button>
          ))}
          <button type="button" className="btn btn--sm" disabled={page >= pageCount} onClick={() => onPage(page + 1)}>
            Próxima →
          </button>
        </div>
      </nav>
    );
  }
}
