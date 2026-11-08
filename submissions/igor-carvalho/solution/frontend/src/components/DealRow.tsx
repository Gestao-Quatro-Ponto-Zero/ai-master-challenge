import React from 'react';
import type { Deal } from '../api/types';
import { money, percent } from '../lib/format';
import { isProspecting, stageLabel } from '../lib/labels';
import { bandStyle, priorityStyle } from '../lib/theme';
import ReasonChip from './ReasonChip';

interface Props {
  deal: Deal;
  accent: string;
  /** Prazo máximo (GET /meta thresholds.reviewDays): só escala a barrinha de tempo. */
  reviewDays: number;
  selected: boolean;
  /** undefined = a linha não tem caixa de seleção. */
  checked?: boolean;
  onSelect: (id: string) => void;
  onToggle?: (id: string) => void;
}

export default class DealRow extends React.PureComponent<Props> {
  render() {
    const { deal, accent, reviewDays, selected, checked, onSelect, onToggle } = this.props;
    const noScoreHint = `Deals acima de ${reviewDays} dias e deals em Prospecção ficam sem índice: o histórico não sustenta uma previsão.`;
    const band = bandStyle(deal.band, accent);
    const prio = priorityStyle(deal.priorityLevel, accent);
    const prospecting = isProspecting(deal.stage);
    const age = deal.ageDays;
    // A faixa vem da API; aqui ela só escolhe a cor e a frase.
    const barColor = deal.band === 'review' ? '#C0504D' : deal.band === 'stale_risk' ? '#D9902F' : '#8FA3B5';
    let ageNote = 'Dentro do prazo típico';
    if (prospecting || age === null) ageNote = 'Ainda não engajado';
    else if (deal.band === 'review') ageNote = 'Acima do máximo já visto';
    else if (deal.band === 'stale_risk') ageNote = 'Passou do prazo típico';

    const aria =
      `Deal ${deal.id}, ${deal.product}, faixa ${band.label}` +
      (deal.score !== null ? `, prioridade ${prio.label.toLowerCase()}` : ', sem prioridade') +
      `, valor esperado ${money(deal.expectedValue)}`;

    return (
      <div className="dealrow-wrap">
        {checked !== undefined && (
          <label className="dealrow__check">
            <input
              type="checkbox"
              checked={checked}
              onChange={() => onToggle?.(deal.id)}
              aria-label={`Selecionar deal ${deal.id}`}
            />
          </label>
        )}
        <button
          type="button"
          className={'dealrow' + (selected ? ' is-selected' : '')}
          aria-pressed={selected}
          aria-label={aria}
          style={{ borderLeftColor: selected ? band.edge : 'transparent' }}
          onClick={() => onSelect(deal.id)}
        >
          <span className="dealrow__prio">
            {deal.score !== null ? (
              <span className="prio">
                <span className="prio__score" style={{ color: prio.fg }}>
                  {deal.score}
                </span>
                <span className="prio__label" style={{ color: prio.fg }}>
                  {prio.label}
                </span>
              </span>
            ) : (
              <span className="prio__none" title={noScoreHint}>
                Sem prioridade
              </span>
            )}
          </span>

          <span className="dealrow__deal">
            <span className="dealrow__product">{deal.product}</span>
            <span className="dealrow__meta">
              <span className="pill" style={{ background: band.bg, color: band.fg }}>
                {band.label}
              </span>
              <span className="dealrow__id">
                {deal.id} · {stageLabel(deal.stage)}
              </span>
            </span>
            <span className="dealrow__account" style={{ color: deal.account ? '#0F1B2D' : '#8A4B00' }}>
              {deal.account ?? 'Sem conta informada'}
            </span>
          </span>

          <span className="dealrow__time">
            <span className="dealrow__age">{age === null ? 'Sem data' : `${age} dias`}</span>
            {age !== null && (
              <span className="meter">
                <span
                  className="meter__fill"
                  style={{ width: `${Math.round((Math.min(age, reviewDays) / reviewDays) * 100)}%`, background: barColor }}
                />
              </span>
            )}
            <span className="dealrow__note">{ageNote}</span>
          </span>

          <span className="dealrow__value">
            <span className="dealrow__price">{money(deal.price)}</span>
            <span className="dealrow__note">Esperado {money(deal.expectedValue)}</span>
            {deal.probability !== null && (
              <span className="dealrow__note" title="Chance de fechar estimada pelo modelo. Serve para comparar deals.">
                Chance {percent(deal.probability)}
              </span>
            )}
          </span>

          <span className="dealrow__next">
            <span className="dealrow__nexttext">{deal.suggestedAction}</span>
            {deal.reasons.slice(0, 2).map((reason) => (
              <ReasonChip key={reason.short} reason={reason} />
            ))}
            {deal.confidence === 'low' && (
              <span className="lowconf" title={deal.confidenceReason ? `Confiança baixa: ${deal.confidenceReason}` : undefined}>
                Confiança baixa
              </span>
            )}
          </span>
        </button>
      </div>
    );
  }
}
