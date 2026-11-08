import React from 'react';
import type { Deal } from '../api/types';
import { money, percent } from '../lib/format';
import { priorityStyle } from '../lib/theme';
import SnoozeMenu from './SnoozeMenu';

interface Props {
  deal: Deal;
  done: boolean;
  accent: string;
  onOpen: (id: string) => void;
  onToggleDone: (id: string) => void;
  onSnooze: (deal: Deal, days: number) => void;
}

export default class TodayDealCard extends React.Component<Props> {
  render() {
    const { deal, done, accent, onOpen, onToggleDone, onSnooze } = this.props;
    const prio = priorityStyle(deal.priorityLevel, accent);
    const topReason = deal.reasons[0];

    return (
      <div className={'todaycard' + (done ? ' is-done' : '')} style={{ borderLeftColor: done ? '#B8C0CC' : accent }}>
        <span className="todaycard__prio" title="Índice de prioridade de 0 a 100">
          <span className="todaycard__score" style={{ color: prio.fg }}>
            {deal.score}
          </span>
          <span className="todaycard__label" style={{ color: prio.fg }}>
            Prioridade {prio.label}
          </span>
        </span>

        <button type="button" className="todaycard__body" onClick={() => onOpen(deal.id)}>
          <span className="todaycard__next" style={{ textDecoration: done ? 'line-through' : 'none' }}>
            {deal.suggestedAction}
          </span>
          <span className="todaycard__line">
            {deal.product} ·{' '}
            <strong style={{ color: deal.account ? '#0F1B2D' : '#8A4B00' }}>{deal.account ?? 'Sem conta informada'}</strong>
          </span>
          <span className="todaycard__why">
            {topReason ? `${topReason.short} · ` : ''}
            {deal.ageDays} dias no funil
          </span>
          <span className="todaycard__money" style={{ color: '#3B4656' }}>
            Esperado {money(deal.expectedValue)}
            {deal.probability !== null && <> · Chance {percent(deal.probability)}</>} · Preço {money(deal.price)}
          </span>
          <span className="todaycard__more">Ver detalhes →</span>
        </button>

        <div className="todaycard__actions">
          <button
            type="button"
            className={'btn btn--toggle' + (done ? ' is-on' : '')}
            aria-pressed={done}
            onClick={() => onToggleDone(deal.id)}
          >
            {done ? '✓ Feito' : 'Marcar feito'}
          </button>
          <SnoozeMenu onPick={(days) => onSnooze(deal, days)} subject={deal.product} />
        </div>
      </div>
    );
  }
}
