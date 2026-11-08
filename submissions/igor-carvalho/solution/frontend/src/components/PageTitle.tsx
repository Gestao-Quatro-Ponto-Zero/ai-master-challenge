import React from 'react';
import { formatFullDate } from '../lib/format';

interface Props {
  title: string;
  subtitle: string;
  /** Linha de apoio (ex.: regra de ordenação) com o link "Como é calculado". */
  hint?: string;
  referenceDate: string | null;
  sampleData: boolean;
  onHowItWorks: () => void;
}

export default class PageTitle extends React.Component<Props> {
  render() {
    const { title, subtitle, hint, referenceDate, sampleData, onHowItWorks } = this.props;
    return (
      <section className="pagetitle">
        <div>
          <h1 className="pagetitle__title">{title}</h1>
          <p className="pagetitle__sub">{subtitle}</p>
          {hint && (
            <p className="pagetitle__hint">
              {hint}{' '}
              <button type="button" className="linkbtn" onClick={onHowItWorks}>
                Como a prioridade é calculada
              </button>
            </p>
          )}
        </div>
        {referenceDate && (
          <span
            className="refbadge"
            title={sampleData ? 'Conta e último contato são exemplos.' : undefined}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
              <rect x="3" y="5" width="18" height="16" rx="2" />
              <path d="M3 10h18M8 3v4M16 3v4" />
            </svg>
            Pipeline em <strong>{formatFullDate(referenceDate)}</strong>
            {sampleData && <span className="refbadge__sample"> · dados de exemplo</span>}
          </span>
        )}
      </section>
    );
  }
}
