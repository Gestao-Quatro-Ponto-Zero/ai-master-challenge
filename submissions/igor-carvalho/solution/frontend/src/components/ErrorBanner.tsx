import React from 'react';

interface Props {
  message: string;
  onRetry: () => void;
}

export default class ErrorBanner extends React.Component<Props> {
  render() {
    return (
      <div role="alert" className="errorbanner">
        <span className="errorbanner__text">{this.props.message}</span>
        <button type="button" className="btn btn--sm" onClick={this.props.onRetry}>
          Tentar de novo
        </button>
      </div>
    );
  }
}
