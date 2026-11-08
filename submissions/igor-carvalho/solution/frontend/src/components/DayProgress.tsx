import React from 'react';
import { CAP_OPTIONS } from '../lib/constants';

interface Props {
  doneCount: number;
  total: number;
  cap: number;
  onCap: (cap: number) => void;
}

export default class DayProgress extends React.Component<Props> {
  render() {
    const { doneCount, total, cap, onCap } = this.props;
    const pct = total ? Math.round((doneCount / total) * 100) : 0;
    return (
      <section aria-label="Progresso do dia" className="dayprogress">
        <div className="dayprogress__main">
          <div className="dayprogress__label">Hoje</div>
          <div className="dayprogress__count">
            {doneCount} de {total} feitos
          </div>
          <div className="meter meter--lg" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100} aria-label="Progresso do dia">
            <div className="meter__fill" style={{ width: `${pct}%`, background: 'var(--accent)' }} />
          </div>
        </div>
        <div className="field">
          <label htmlFor="cap">Quantos deals você cuida hoje?</label>
          <select id="cap" value={cap} onChange={(e) => onCap(parseInt(e.target.value, 10))}>
            {CAP_OPTIONS.map((n) => (
              <option key={n} value={n}>
                {n} deals
              </option>
            ))}
          </select>
        </div>
      </section>
    );
  }
}
