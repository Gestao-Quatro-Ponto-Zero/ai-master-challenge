import React from 'react';
import type { DisagreeReason, FeedbackEntry, FeedbackKind } from '../api/types';
import { DISAGREE_REASONS, FEEDBACK_LABELS, FEEDBACK_MESSAGES } from '../lib/constants';
import { formatShortDateTime } from '../lib/format';

interface Props {
  /** Último feedback enviado nesta sessão (mostra a confirmação). */
  lastKind?: FeedbackKind;
  history: FeedbackEntry[];
  onDisagree: (reason: DisagreeReason | null) => void;
  onIgnore: () => void;
}

interface State {
  askingReason: boolean;
}

export default class FeedbackSection extends React.Component<Props, State> {
  state: State = { askingReason: false };

  private sendReason(reason: DisagreeReason | null) {
    this.setState({ askingReason: false });
    this.props.onDisagree(reason);
  }

  render() {
    const { lastKind, history, onIgnore } = this.props;
    const { askingReason } = this.state;
    const reasonLabel = (reason: DisagreeReason | null) =>
      DISAGREE_REASONS.find((r) => r.value === reason)?.label ?? null;

    return (
      <div>
        <h3 className="detail__h3">Esta prioridade faz sentido?</h3>
        <div className="actions">
          <button
            type="button"
            className={'btn' + (lastKind === 'disagree' ? ' btn--chosen' : '')}
            aria-expanded={askingReason}
            onClick={() => this.setState({ askingReason: !askingReason })}
          >
            Discordo da prioridade
          </button>
          <button type="button" className={'btn' + (lastKind === 'ignore' ? ' btn--chosen' : '')} onClick={onIgnore}>
            Ignorar
          </button>
        </div>

        {askingReason && (
          <div role="group" aria-label="Por que você discorda?" className="reasons-ask">
            <p className="reasons-ask__title">Por que você discorda? (opcional)</p>
            <div className="actions">
              {DISAGREE_REASONS.map((r) => (
                <button key={r.value} type="button" className="btn btn--sm" onClick={() => this.sendReason(r.value)}>
                  {r.label}
                </button>
              ))}
              <button type="button" className="btn btn--sm btn--ghost" onClick={() => this.sendReason(null)}>
                Enviar sem motivo
              </button>
            </div>
          </div>
        )}

        <div aria-live="polite" className="feedback__msg">
          {lastKind ? FEEDBACK_MESSAGES[lastKind] : ''}
        </div>

        {history.length > 0 && (
          <ul aria-label="Histórico de feedback" className="history">
            {history.slice(0, 3).map((entry) => (
              <li key={entry.createdAt + entry.kind}>
                {FEEDBACK_LABELS[entry.kind]}
                {entry.reason ? ` · ${reasonLabel(entry.reason)}` : ''}
                <span className="history__when"> — {formatShortDateTime(entry.createdAt)}</span>
              </li>
            ))}
          </ul>
        )}
      </div>
    );
  }
}
