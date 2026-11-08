import React from 'react';
import type { Factor } from '../api/types';
import { reasonStyle } from '../lib/theme';

interface Props {
  factors: Factor[];
  disclaimer: string;
}

const MAX_ROWS = 6;

/** Explicação do índice, fator por fator: o que foi observado, com o que se compara e quanto pesa. Os dados vêm da API. */
export default class FactorTable extends React.Component<Props> {
  render() {
    const { factors, disclaimer } = this.props;
    if (factors.length === 0) return null;
    const rows = factors.slice(0, MAX_ROWS);
    const max = Math.max(...rows.map((f) => f.impact), 0.0001);
    return (
      <div className="factors">
        <table className="factors__table">
          <caption className="sr-only">Fatores que explicam a prioridade</caption>
          <thead>
            <tr>
              <th scope="col">Fator</th>
              <th scope="col">Observado</th>
              <th scope="col">Referência</th>
              <th scope="col">Peso</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((f) => {
              const style = reasonStyle(f.direction === 'positive' ? 'pos' : 'neg');
              return (
                <tr key={f.code + f.factor}>
                  <th scope="row">{f.factor}</th>
                  <td className="num">{f.observed ?? '–'}</td>
                  <td className="factors__ref">{f.reference ?? '–'}</td>
                  <td>
                    <span className="factors__weight" title={f.direction === 'positive' ? 'Pesa a favor da prioridade' : 'Pesa contra a prioridade'}>
                      <span className="factors__bar" aria-hidden="true">
                        <span style={{ width: `${Math.max(6, Math.round((f.impact / max) * 100))}%`, background: style.fg }} />
                      </span>
                      <span style={{ color: style.fg }}>{f.direction === 'positive' ? 'a favor' : 'contra'}</span>
                    </span>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        <p className="detail__fine">{disclaimer} O peso é relativo entre os fatores: não é uma porcentagem de chance.</p>
      </div>
    );
  }
}
