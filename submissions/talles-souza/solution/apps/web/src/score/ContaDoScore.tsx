import type { LinhaDoScore } from '@lead-scorer/dominio/priorizacao';

/**
 * A conta da nota, fator a fator: primeiro os que estão no score ("+7 · Idade: 45 dias (41 a 50
 * dias)"), depois os que valem 0 e o porquê ("Setor: 0 · não muda a chance no histórico"). As
 * frases vêm prontas do domínio.
 */
export function ContaDoScore({ parcelas, testid }: { parcelas: LinhaDoScore[]; testid: string }) {
  return (
    <ul className="conta" data-testid={testid}>
      {parcelas.map((p) => (
        <li
          key={p.fator}
          className={p.noScore ? 'conta__linha' : 'conta__linha conta__linha--fora'}
          data-fator={p.fator}
        >
          {p.texto}
        </li>
      ))}
    </ul>
  );
}
