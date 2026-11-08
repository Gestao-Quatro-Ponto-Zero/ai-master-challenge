import React from 'react';
import type { ListTab } from '../api/types';

export interface KpiItem {
  key: ListTab;
  label: string;
  value: string;
  note: string;
  valueColor: string;
  selected: boolean;
}

interface Props {
  item: KpiItem;
  onPick: (key: ListTab) => void;
}

export default class KpiCard extends React.Component<Props> {
  render() {
    const { item, onPick } = this.props;
    return (
      <button
        type="button"
        className={'kpi' + (item.selected ? ' is-selected' : '')}
        aria-pressed={item.selected}
        onClick={() => onPick(item.key)}
      >
        <span className="kpi__label">{item.label}</span>
        <span className="kpi__value" style={{ color: item.valueColor }}>
          {item.value}
        </span>
        <span className="kpi__note">{item.note}</span>
        <span className="kpi__cta">Ver na lista →</span>
      </button>
    );
  }
}
