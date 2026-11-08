import React from 'react';
import SnoozeMenu from './SnoozeMenu';

interface Props {
  product: string;
  onAct: () => void;
  onSnooze: (days: number) => void;
  onLost: () => void;
}

export default class QuickActions extends React.Component<Props> {
  render() {
    const { product, onAct, onSnooze, onLost } = this.props;
    return (
      <div>
        <h3 className="detail__h3">Ações rápidas</h3>
        <div className="actions">
          <button type="button" className="btn btn--primary" onClick={onAct}>
            Registrar atividade
          </button>
          <SnoozeMenu onPick={onSnooze} subject={product} />
          <button type="button" className="btn btn--danger-text" onClick={onLost}>
            Marcar como perdido
          </button>
        </div>
      </div>
    );
  }
}
