import React from 'react';

interface Props {
  /** Conteúdo do deal selecionado; null mostra a dica de seleção. */
  children: React.ReactNode | null;
}

export default class DetailPanel extends React.Component<Props> {
  render() {
    const { children } = this.props;
    return (
      <aside aria-label="Detalhe do deal selecionado" className="detailpanel">
        {children ?? <div className="detailpanel__empty">Selecione um deal para ver o porquê do score.</div>}
      </aside>
    );
  }
}
