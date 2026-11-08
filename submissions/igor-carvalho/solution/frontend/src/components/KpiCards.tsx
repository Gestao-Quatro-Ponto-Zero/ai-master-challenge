import React from 'react';
import type { ListTab } from '../api/types';
import KpiCard, { type KpiItem } from './KpiCard';

interface Props {
  items: KpiItem[];
  onPick: (key: ListTab) => void;
}

export default class KpiCards extends React.Component<Props> {
  render() {
    return (
      <section aria-label="Resumo do pipeline" className="kpis">
        {this.props.items.map((item) => (
          <KpiCard key={item.key} item={item} onPick={this.props.onPick} />
        ))}
      </section>
    );
  }
}
