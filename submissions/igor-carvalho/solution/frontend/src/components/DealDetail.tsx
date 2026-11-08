import React from 'react';
import type { Deal, DealExplanation, DisagreeReason, FeedbackEntry, FeedbackKind, Thresholds } from '../api/types';
import { CONFIDENCE_LABELS } from '../lib/constants';
import { money, percent } from '../lib/format';
import { isProspecting, stageLabel } from '../lib/labels';
import { bandStyle, priorityStyle } from '../lib/theme';
import FactorTable from './FactorTable';
import FeedbackSection from './FeedbackSection';
import FunnelTimeline from './FunnelTimeline';
import QuickActions from './QuickActions';
import ReasonChip from './ReasonChip';

export interface DetailHandlers {
  onAct: () => void;
  onLost: () => void;
  onSnooze: (days: number) => void;
  onDisagree: (reason: DisagreeReason | null) => void;
  onIgnore: () => void;
}

interface Props extends DetailHandlers {
  deal: Deal;
  accent: string;
  showProbability: boolean;
  lastFeedback?: FeedbackKind;
  history: FeedbackEntry[];
  thresholds: Thresholds;
  /** Horizonte do modelo em dias (GET /meta); null em versões antigas da API. */
  horizonDays: number | null;
  /** A chance em % só é confiável quando a calibração provou valor (GET /meta). */
  calibrationUseful: boolean | null;
  /** Fatores do índice (GET /deals/{id}); undefined enquanto carrega ou se falhar. */
  explanation?: DealExplanation;
}

/** Tudo o que o vendedor precisa saber de um deal: o que fazer, por quê, e as ações. */
export default class DealDetail extends React.Component<Props> {
  render() {
    const { deal, accent, showProbability, lastFeedback, history } = this.props;
    const band = bandStyle(deal.band, accent);
    const prio = priorityStyle(deal.priorityLevel, accent);
    const prospecting = isProspecting(deal.stage);
    const horizon = this.props.horizonDays !== null ? `nos próximos ${this.props.horizonDays} dias` : 'no próximo período';

    return (
      <div className="detail">
        <div className="detail__head">
          {deal.score !== null ? (
            <span className="detail__prio">
              <span className="bars" aria-hidden="true">
                <span style={{ height: 11, background: prio.bar1 }} />
                <span style={{ height: 19, background: prio.bar2 }} />
                <span style={{ height: 28, background: prio.bar3 }} />
              </span>
              <span className="detail__priolabel" style={{ color: prio.fg }}>
                Prioridade {prio.label}
              </span>
              <span className="detail__prioscore">Índice {deal.score}/100</span>
            </span>
          ) : (
            <span className="detail__prio detail__prio--none">Sem prioridade</span>
          )}
          <div className="detail__title">
            <h2>{deal.product}</h2>
            <div className="detail__tags">
              <span className="pill" style={{ background: band.bg, color: band.fg }}>
                {band.label}
              </span>
              <span className="detail__id">
                {deal.id} · {stageLabel(deal.stage)}
              </span>
            </div>
          </div>
        </div>

        <div className="detail__action" style={{ background: band.bg, color: band.fg }}>
          {deal.suggestedAction}
        </div>

        <dl className="facts">
          <dt>Conta</dt>
          <dd style={{ color: deal.account ? '#0F1B2D' : '#8A4B00' }}>{deal.account ?? 'Sem conta informada'}</dd>
        </dl>

        <div className="indicators" aria-label="Indicadores do deal">
          <div className="indicator">
            <div className="indicator__label">Índice de prioridade</div>
            <div className="indicator__value num">{deal.score !== null ? `${deal.score}/100` : 'Sem índice'}</div>
            <div className="indicator__note">Posição entre os seus deals abertos. Não é uma probabilidade.</div>
          </div>
          <div className="indicator">
            <div className="indicator__label">Preço do deal</div>
            <div className="indicator__value num">{money(deal.price)}</div>
            <div className="indicator__note">O que o cliente paga se fechar.</div>
          </div>
          <div className="indicator">
            <div className="indicator__label">Valor esperado</div>
            <div className="indicator__value num">{money(deal.expectedValue)}</div>
            <div className="indicator__note">Receita esperada {horizon}: preço × chance de fechar.</div>
          </div>
          {deal.probability !== null && showProbability && (
            <div className="indicator">
              <div className="indicator__label">Chance de fechar</div>
              <div className="indicator__value num">{percent(deal.probability)}</div>
              <div className="indicator__note">Chance de ganhar {horizon}.</div>
            </div>
          )}
        </div>
        {deal.probability !== null && showProbability && this.props.calibrationUseful === false && (
          <p className="detail__fine">
            A chance ainda não é calibrada: serve para comparar deals, não como promessa de fechamento.
          </p>
        )}

        {(deal.reasons.length > 0 || (this.props.explanation?.factors.length ?? 0) > 0) && (
          <div>
            <h3 className="detail__h3">Por que esta prioridade?</h3>
            {this.props.explanation && this.props.explanation.factors.length > 0 ? (
              <FactorTable factors={this.props.explanation.factors} disclaimer={this.props.explanation.disclaimer} />
            ) : (
              <>
                <div className="detail__reasons">
                  {deal.reasons.slice(0, 5).map((reason) => (
                    <ReasonChip key={reason.short} reason={reason} />
                  ))}
                </div>
                <p className="detail__fine">Padrões do histórico de deals fechados. Não são causas.</p>
              </>
            )}
          </div>
        )}

        {!prospecting && deal.ageDays !== null && <FunnelTimeline ageDays={deal.ageDays} thresholds={this.props.thresholds} />}

        <div className="metrics">
          <div className="metric">
            <div className="metric__label">Confiança da previsão</div>
            <div className="metric__value">{CONFIDENCE_LABELS[deal.confidence]}</div>
            {deal.confidenceReason && <div className="metric__note">Porque {deal.confidenceReason}.</div>}
          </div>
          {deal.dataQuality && (
            <div className="metric">
              <div className="metric__label">Completude dos dados</div>
              <div className="metric__value" style={{ color: deal.dataQuality.status === 'complete' ? undefined : '#8A4B00' }}>
                {deal.dataQuality.status === 'complete' ? 'Completa' : 'Incompleta'}
              </div>
              <div className="metric__note">{deal.dataQuality.summary}</div>
            </div>
          )}
        </div>

        <QuickActions
          product={deal.product}
          onAct={this.props.onAct}
          onSnooze={this.props.onSnooze}
          onLost={this.props.onLost}
        />

        <FeedbackSection
          lastKind={lastFeedback}
          history={history}
          onDisagree={this.props.onDisagree}
          onIgnore={this.props.onIgnore}
        />
      </div>
    );
  }
}
