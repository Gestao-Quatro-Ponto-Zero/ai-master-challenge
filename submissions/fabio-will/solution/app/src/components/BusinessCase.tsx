'use client'

import { useState } from 'react'
import { DEFAULT_INPUTS as DEFAULTS, FULL_TIME_HOURS, savedMinutes, type Inputs, type Shares } from '@/lib/business'
import { num, pct } from '@/lib/labels'
import { InfoTip } from './InfoTip'
import styles from './BusinessCase.module.css'

const FIELDS: { key: keyof Inputs; label: string; min: number; max: number; step: number; fmt: (v: number) => string; unit?: string }[] = [
  { key: 'volume', label: 'Tickets por mês', min: 500, max: 20000, step: 500, fmt: (v) => num(v), unit: 'tickets' },
  { key: 'triageMin', label: 'Minutos de triagem manual por ticket', min: 1, max: 10, step: 0.5, fmt: (v) => num(v, 1), unit: 'minutos' },
  { key: 'assistSavedMin', label: 'Minutos poupados no assistido', min: 0, max: 5, step: 0.5, fmt: (v) => num(v, 1), unit: 'minutos' },
  { key: 'reworkMin', label: 'Minutos de retrabalho por erro automático', min: 0, max: 60, step: 5, fmt: (v) => num(v), unit: 'minutos' },
  { key: 'hourCost', label: 'Custo da hora do agente (R$, com encargos)', min: 20, max: 150, step: 5, fmt: (v) => `R$ ${num(v)}` },
]

export function BusinessCase({ shares }: { shares: Shares }) {
  const [inputs, setInputs] = useState<Inputs>(DEFAULTS)
  const minutes = savedMinutes(inputs, shares)
  const hours = minutes / 60
  const money = hours * inputs.hourCost

  const grid = [0.5, 1, 2].map((v) => [1, 3, 5].map((m) => savedMinutes({ ...inputs, volume: inputs.volume * v, triageMin: m }, shares) / 60))

  return (
    <div className={styles.layout}>
      <form className={styles.form} onSubmit={(e) => e.preventDefault()} aria-label="Premissas do business case">
        {FIELDS.map((f) => (
          <div key={f.key} className={styles.field}>
            <div className={styles.fieldHead}>
              <label htmlFor={`bc-${f.key}`}>{f.label}</label>
              <output htmlFor={`bc-${f.key}`}>{f.fmt(inputs[f.key])}</output>
            </div>
            <input
              id={`bc-${f.key}`}
              type="range"
              min={f.min}
              max={f.max}
              step={f.step}
              value={inputs[f.key]}
              aria-valuetext={`${f.fmt(inputs[f.key])} ${f.unit ?? ''}`.trim()}
              onChange={(e) => setInputs((p) => ({ ...p, [f.key]: Number(e.target.value) }))}
            />
          </div>
        ))}
        <button type="button" className="btn ghost" onClick={() => setInputs(DEFAULTS)}>
          Voltar às premissas iniciais
        </button>
      </form>

      <div className={styles.output}>
        <div className={styles.headline}>
          <div>
            <b>{num(hours)}</b>
            <span>
              horas de triagem por mês <InfoTip label="horas por mês" text="Minutos poupados por mês divididos por 60, já sem o retrabalho dos erros e sem a auditoria de 2%." />
            </span>
          </div>
          <div>
            <b>{num(hours / FULL_TIME_HOURS, 1)}</b>
            <span>
              pessoas em tempo integral (160 h) <InfoTip label="pessoas em tempo integral" text="Horas por mês divididas por 160, a jornada de uma pessoa. É capacidade que volta para atender, não corte de vaga." />
            </span>
          </div>
          <div>
            <b>R$ {num(money)}</b>
            <span>
              por mês, ou R$ {num(money * 12)} por ano <InfoTip label="custo por mês" text="Horas por mês vezes o custo da hora do agente com encargos, que é premissa e você ajusta no controle." />
            </span>
          </div>
        </div>

        <div className={styles.formula}>
          <p>
            <strong>Como a conta é feita.</strong> Tickets × ({pct(shares.auto, 1)} automático × minutos de triagem + {pct(shares.assist, 1)} assistido
            × minutos poupados) − retrabalho dos {pct(1 - shares.autoPrecision, 1)} de erro do automático − auditoria de {pct(inputs.auditShare, 0)} do
            automático.
          </p>
          <p className="muted small">
            As parcelas e a taxa de erro foram medidas no teste. Volume, minutos e custo são premissas: o Dataset 1 não tem o carimbo de abertura, então
            não dá para medir o tempo de triagem de hoje. O volume inicial vem do enunciado (cerca de 30 mil tickets por ano).
          </p>
        </div>

        <div className="table-wrap">
          <table>
            <caption className="skip">Sensibilidade: horas por mês</caption>
            <thead>
              <tr>
                <th scope="col">Volume ↓ · triagem →</th>
                <th scope="col" className="num">1 min</th>
                <th scope="col" className="num">3 min</th>
                <th scope="col" className="num">5 min</th>
              </tr>
            </thead>
            <tbody>
              {grid.map((row, r) => (
                <tr key={r}>
                  <th scope="row">{num(inputs.volume * [0.5, 1, 2][r]!)} tickets</th>
                  {row.map((h, c) => (
                    <td key={c} className="num">
                      {num(h)} h
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
