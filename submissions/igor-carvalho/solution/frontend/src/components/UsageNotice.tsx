import React from 'react';

interface Props {
  onHowItWorks: () => void;
}

export default class UsageNotice extends React.Component<Props> {
  render() {
    return (
      <section aria-label="Aviso" className="notice">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true" className="notice__icon">
          <circle cx="12" cy="12" r="9" />
          <path d="M12 11v5M12 8h.01" />
        </svg>
        <p className="notice__text">
          A ordem da lista pesa sobretudo <strong>valor do produto, tempo no funil e limpeza do pipeline</strong>. A chance
          de ganhar é só um apoio fraco, vinda de padrões do histórico: use junto com seu julgamento.{' '}
          <button type="button" className="linkbtn" onClick={this.props.onHowItWorks}>
            Como a prioridade é calculada
          </button>
        </p>
      </section>
    );
  }
}
