import React from 'react';

interface Props {
  message: string;
  onUndo: () => void;
  onClose: () => void;
}

/** Aviso fixo no rodapé da tela, para o vendedor ver o resultado da ação onde estiver na página. */
export default class Toast extends React.Component<Props> {
  render() {
    const { message, onUndo, onClose } = this.props;
    return (
      <div role="status" className="toast">
        <span className="toast__text">{message}</span>
        <button type="button" className="btn btn--sm" onClick={onUndo}>
          Desfazer
        </button>
        <button type="button" className="toast__close" aria-label="Fechar aviso" onClick={onClose}>
          ×
        </button>
      </div>
    );
  }
}
