import React from 'react';
import type { ListTab, TabKey } from '../api/types';

export interface TabItem {
  key: TabKey;
  label: string;
  /** null enquanto o resumo não chegou. */
  count: number | null;
}

interface Props {
  tabs: TabItem[];
  active: ListTab;
  onPick: (key: TabKey) => void;
}

export default class BandTabs extends React.Component<Props> {
  render() {
    const { tabs, active, onPick } = this.props;
    return (
      <div role="tablist" aria-label="Faixas de prioridade" className="bandtabs">
        {tabs.map((tab) => {
          const on = active === tab.key;
          return (
            <button
              key={tab.key}
              type="button"
              role="tab"
              aria-selected={on}
              className={'bandtab' + (on ? ' is-active' : '')}
              onClick={() => onPick(tab.key)}
            >
              {tab.label}
              <span className="bandtab__count">{tab.count === null ? '–' : tab.count}</span>
            </button>
          );
        })}
      </div>
    );
  }
}
