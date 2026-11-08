import React from 'react';
import { SNOOZE_OPTIONS } from '../lib/constants';
import { daysText } from '../lib/format';

interface Props {
  onPick: (days: number) => void;
  /** Contexto para leitores de tela, ex.: nome do produto. */
  subject?: string;
}

interface State {
  open: boolean;
}

/** Botão "Adiar" que deixa o vendedor escolher por quanto tempo (1, 7 ou 30 dias). */
export default class SnoozeMenu extends React.Component<Props, State> {
  state: State = { open: false };

  private pick = (days: number) => {
    this.setState({ open: false });
    this.props.onPick(days);
  };

  render() {
    const { open } = this.state;
    const subject = this.props.subject ? ` ${this.props.subject}` : '';
    return (
      <div className="snooze">
        <button
          type="button"
          className="btn"
          aria-haspopup="menu"
          aria-expanded={open}
          aria-label={`Adiar${subject}`}
          onClick={() => this.setState({ open: !open })}
        >
          Adiar ▾
        </button>
        {open && (
          <div role="menu" className="snooze__menu">
            {SNOOZE_OPTIONS.map((days) => (
              <button key={days} type="button" role="menuitem" className="snooze__item" onClick={() => this.pick(days)}>
                Adiar {daysText(days)}
              </button>
            ))}
          </div>
        )}
      </div>
    );
  }
}
