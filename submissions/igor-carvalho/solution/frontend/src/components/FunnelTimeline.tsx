import React from 'react';
import type { Thresholds } from '../api/types';
import { heatTint } from '../lib/theme';

interface Props {
  ageDays: number;
  thresholds: Thresholds;
}

/** Posição do deal comparada ao prazo típico de quem fecha. Os prazos vêm de GET /meta (thresholds). */
export default class FunnelTimeline extends React.Component<Props> {
  render() {
    const { ageDays, thresholds: t } = this.props;
    // Só escala do desenho: um pouco além do prazo máximo, para o marcador caber.
    const scale = Math.ceil(t.reviewDays * 1.1);
    const pct = (days: number) => Math.round((days / scale) * 1000) / 10;
    const markerLeft = pct(Math.min(ageDays, scale));
    return (
      <div className="timeline">
        <h3 className="detail__h3">
          Tempo no funil: <span className="num">{ageDays} dias</span>
        </h3>
        <div className="timeline__bar">
          <div style={{ width: `${pct(t.typicalP50)}%`, background: heatTint(0) }} />
          <div style={{ width: `${pct(t.staleDays) - pct(t.typicalP50)}%`, background: heatTint(1) }} />
          <div style={{ width: `${pct(t.reviewDays) - pct(t.staleDays)}%`, background: heatTint(2) }} />
          <div style={{ width: `${100 - pct(t.reviewDays)}%`, background: heatTint(3) }} />
        </div>
        <div className="timeline__markerrow">
          <div className="timeline__marker" data-testid="timeline-marker" style={{ left: `${markerLeft}%` }} />
        </div>
        <div className="timeline__labels">
          <span style={{ left: 0 }}>0</span>
          <span style={{ left: `${pct(t.typicalP50)}%` }}>
            {t.typicalP50} d · metade fecha
          </span>
          <span style={{ left: `${pct(t.staleDays)}%`, top: 16, transform: 'translateX(-50%)' }}>
            {t.staleDays} d · prazo típico
          </span>
          <span style={{ right: 0 }}>{t.reviewDays} d · máx.</span>
        </div>
      </div>
    );
  }
}
