import React from 'react';
import type { Deal } from '../api/types';
import DayProgress from './DayProgress';
import TodayDealCard from './TodayDealCard';

interface Props {
  /** null enquanto carrega. */
  deals: Deal[] | null;
  cap: number;
  done: Record<string, boolean>;
  accent: string;
  onCap: (cap: number) => void;
  onOpen: (id: string) => void;
  onToggleDone: (id: string) => void;
  onSnooze: (deal: Deal, days: number) => void;
}

export default class TodayView extends React.Component<Props> {
  render() {
    const { deals, cap, done, accent } = this.props;
    const list = deals ?? [];
    const doneCount = list.filter((d) => done[d.id]).length;

    return (
      <>
        <DayProgress doneCount={doneCount} total={list.length} cap={cap} onCap={this.props.onCap} />

        {deals === null && (
          <div role="status" className="state">
            Carregando seus deals…
          </div>
        )}

        <section aria-label="Deals de hoje" className="todaylist">
          {list.map((deal) => (
            <TodayDealCard
              key={deal.id}
              deal={deal}
              done={!!done[deal.id]}
              accent={accent}
              onOpen={this.props.onOpen}
              onToggleDone={this.props.onToggleDone}
              onSnooze={this.props.onSnooze}
            />
          ))}
        </section>

        {deals !== null && list.length === 0 && <div className="state state--card">Nada pendente para hoje.</div>}

        <p className="todaynote">Os outros deals ficam para outro dia.</p>
      </>
    );
  }
}
