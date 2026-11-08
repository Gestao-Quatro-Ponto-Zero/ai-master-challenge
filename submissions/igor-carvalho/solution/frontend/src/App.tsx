import React from 'react';
import type { DealsApi } from './api/DealsApi';
import SellerPage from './pages/SellerPage';
import { DEFAULT_ACCENT, accentSoft } from './lib/theme';

interface Props {
  api: DealsApi;
  /** Cor de destaque (hex de 6 dígitos). */
  accent?: string;
  showProbability?: boolean;
}

/** Raiz da aplicação: define o tema e monta a tela do vendedor. */
export default class App extends React.Component<Props> {
  render() {
    const accent = this.props.accent ?? DEFAULT_ACCENT;
    const style = { '--accent': accent, '--accent-soft': accentSoft(accent) } as React.CSSProperties;
    return (
      <div className="app" style={style}>
        <SellerPage api={this.props.api} accent={accent} showProbability={this.props.showProbability} />
      </div>
    );
  }
}
