import React from 'react';
import type { Reason } from '../api/types';
import { reasonStyle } from '../lib/theme';

interface Props {
  reason: Reason;
}

export default class ReasonChip extends React.Component<Props> {
  render() {
    const { reason } = this.props;
    const style = reasonStyle(reason.direction);
    return (
      <span className="chip" style={{ background: style.bg, color: style.fg }} title={reason.long}>
        {style.sym} {reason.short}
      </span>
    );
  }
}
