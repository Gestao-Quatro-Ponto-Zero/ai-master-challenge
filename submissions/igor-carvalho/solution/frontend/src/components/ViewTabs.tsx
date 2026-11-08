import React from 'react';
import type { View } from '../lib/urlState';

interface Props {
  view: View;
  /** Total de deals abertos; null enquanto carrega. */
  allCount: number | null;
  onChange: (view: View) => void;
}

export default class ViewTabs extends React.Component<Props> {
  render() {
    const { view, allCount, onChange } = this.props;
    const tabs: { key: View; label: string }[] = [
      { key: 'today', label: 'Meu dia' },
      { key: 'all', label: `Todo o pipeline${allCount === null ? '' : ` (${allCount})`}` },
    ];
    return (
      <div role="tablist" aria-label="Visões" className="viewtabs">
        {tabs.map((tab) => (
          <button
            key={tab.key}
            type="button"
            role="tab"
            aria-selected={view === tab.key}
            className={'viewtabs__tab' + (view === tab.key ? ' is-active' : '')}
            onClick={() => onChange(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </div>
    );
  }
}
