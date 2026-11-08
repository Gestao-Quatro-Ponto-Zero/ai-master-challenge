import React from 'react';

interface Props {
  /** Prazo máximo (GET /meta thresholds.reviewDays). */
  reviewDays: number;
  selectedCount: number;
  confirming: boolean;
  onSnooze: () => void;
  onAskLost: () => void;
  onConfirmLost: () => void;
  onCancel: () => void;
}

/** Ação em lote da aba "A revisar": age só nos deals que o vendedor marcou. */
export default class BulkBar extends React.Component<Props> {
  render() {
    const { selectedCount: n, confirming, reviewDays } = this.props;

    if (n === 0) {
      return (
        <div className="bulkbar">
          <span className="bulkbar__text">
            Mais de {reviewDays} dias no funil, mais antigos que qualquer deal já fechado. Marque os deals da lista para agir em lote.
          </span>
        </div>
      );
    }

    if (confirming) {
      return (
        <div role="alert" className="bulkbar bulkbar--confirm">
          <span className="bulkbar__text bulkbar__text--strong">
            Encerrar {n} {n === 1 ? 'deal' : 'deals'} como {n === 1 ? 'perdido' : 'perdidos'}?
          </span>
          <button type="button" className="btn btn--danger" onClick={this.props.onConfirmLost}>
            Confirmar
          </button>
          <button type="button" className="btn" onClick={this.props.onCancel}>
            Cancelar
          </button>
        </div>
      );
    }

    return (
      <div className="bulkbar">
        <span className="bulkbar__text bulkbar__text--strong">
          {n} {n === 1 ? 'deal selecionado' : 'deals selecionados'}
        </span>
        <button type="button" className="btn btn--danger-outline" onClick={this.props.onAskLost}>
          Encerrar como perdidos
        </button>
        <button type="button" className="btn" onClick={this.props.onSnooze}>
          Adiar 30 dias
        </button>
      </div>
    );
  }
}
