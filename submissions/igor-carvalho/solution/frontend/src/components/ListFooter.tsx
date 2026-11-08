import React from 'react';

interface Props {
  text: string;
  sampleData: boolean;
  /** Só existe no mock: volta os dados de exemplo ao início. */
  onReset?: () => void;
}

export default class ListFooter extends React.Component<Props> {
  render() {
    const { text, sampleData, onReset } = this.props;
    return (
      <div className="listfooter">
        <span>{text}</span>
        {sampleData && (
          <span>
            Conta e último contato são exemplos.
            {onReset && (
              <>
                {' '}
                <button type="button" className="linkbtn" onClick={onReset}>
                  Restaurar dados de exemplo
                </button>
              </>
            )}
          </span>
        )}
      </div>
    );
  }
}
