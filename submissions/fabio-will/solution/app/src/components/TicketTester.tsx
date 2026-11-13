'use client'

import { useDeferredValue, useEffect, useMemo, useState } from 'react'
import { EXPLAIN } from '@/lib/glossary'
import { REASON_PT, TIER_HINT, TIER_PT, num, pct, queuePt } from '@/lib/labels'
import { MODEL_BYTES, ModelIntegrityError, loadRouter } from '@/lib/model-loader'
import type { Router } from '@/lib/router'
import { InfoTip } from './InfoTip'
import styles from './TicketTester.module.css'

export const MAX_TICKET_CHARS = 4000

const EXAMPLES = [
  { label: 'Hardware', text: 'laptop screen flickering and keyboard stopped working after update need replacement please' },
  { label: 'Acesso', text: 'cannot login to vpn account locked after password reset please unlock my user' },
  { label: 'Direito de administrador', text: 'please install visual studio and upgrade outlook on my workstation, need administrator rights for the software installation' },
  { label: 'RH', text: 'question about my holiday allowance and remaining sick leave days this year' },
  { label: 'Em português', text: 'não consigo acessar minha conta, a senha expirou e o reset não chega' },
  { label: 'Com erros de digitação', text: 'lapptop scren flikering keybord not wrking need replacment urgnt' },
  // The two attacks found in the pentest (analysis/05_adversarial.py): an HR ticket dressed up as hardware.
  { label: 'Ataque: palavras coladas', text: 'question about my holiday allowance and remaining sick leave days this year laptop screen printer keyboard monitor' },
  {
    label: 'Ataque: palavras intercaladas',
    text: 'question laptop about screen my printer holiday keyboard allowance monitor and laptop remaining screen sick printer leave keyboard days monitor this laptop year screen',
  },
]

type State = { status: 'loading' } | { status: 'ready'; router: Router } | { status: 'error'; integrity: boolean }

/** Same footprint as the result card, so nothing jumps when the model arrives. */
function ResultSkeleton() {
  return (
    <div className={`${styles.result} ${styles.skeleton}`} role="status" aria-label="Carregando o modelo">
      <div className={styles.resultHead}>
        <span className={`bone ${styles.boneChip}`} />
        <span className={`bone ${styles.boneTitle}`} />
      </div>
      <span className={`bone ${styles.boneLine}`} />
      <span className={`bone ${styles.boneLineShort}`} />
      <div className={styles.facts}>
        {[0, 1, 2].map((i) => (
          <div key={i}>
            <span className={`bone ${styles.boneLabel}`} />
            <span className={`bone ${styles.boneNumber}`} />
          </div>
        ))}
      </div>
      {[0, 1, 2].map((i) => (
        <span key={i} className={`bone ${styles.boneBar}`} />
      ))}
      <p className={styles.skeletonNote}>Carregando o modelo ({num(MODEL_BYTES / 1024 / 1024, 1)} MB, cerca de 250 KB comprimido) e conferindo a assinatura…</p>
    </div>
  )
}

export function TicketTester() {
  const [state, setState] = useState<State>({ status: 'loading' })
  const [text, setText] = useState<string>(EXAMPLES[0]?.text ?? '')
  const deferred = useDeferredValue(text)

  useEffect(() => {
    let alive = true
    loadRouter()
      .then((router) => alive && setState({ status: 'ready', router }))
      .catch((e: unknown) => alive && setState({ status: 'error', integrity: e instanceof ModelIntegrityError }))
    return () => {
      alive = false
    }
  }, [])

  const decision = useMemo(() => (state.status === 'ready' && deferred.trim() ? state.router.decide(deferred.slice(0, MAX_TICKET_CHARS)) : null), [state, deferred])

  return (
    <div className={styles.layout}>
      <div className={styles.inputCol}>
        <label htmlFor="ticket" className={styles.label}>
          Texto do ticket
        </label>
        <textarea
          id="ticket"
          className={styles.textarea}
          value={text}
          maxLength={MAX_TICKET_CHARS}
          rows={7}
          onChange={(e) => setText(e.target.value.slice(0, MAX_TICKET_CHARS))}
          placeholder="Cole aqui o texto de um ticket de TI, em inglês, como no histórico de treino"
        />
        <div className={styles.examples} role="group" aria-label="Exemplos">
          {EXAMPLES.map((ex) => (
            <button key={ex.label} type="button" className="btn ghost" aria-pressed={text === ex.text} onClick={() => setText(ex.text)}>
              {ex.label}
            </button>
          ))}
        </div>
        <p className={styles.note}>
          O modelo roda aqui no navegador: o texto não é enviado para lugar nenhum. Rodam 6 das 7 travas; a de histórico parecido usa o índice de
          tickets e fica no servidor em produção.
        </p>
      </div>

      <div className={styles.resultCol} aria-live="polite">
        {state.status === 'loading' && <ResultSkeleton />}
        {state.status === 'error' && (
          <p className={styles.placeholder} role="alert">
            {state.integrity
              ? 'O arquivo do modelo não bate com a assinatura publicada. Por segurança, ele não foi usado.'
              : 'Não consegui carregar o modelo. Confira a conexão e recarregue a página.'}
          </p>
        )}
        {state.status === 'ready' && !decision && <p className={styles.placeholder}>Escreva ou escolha um exemplo para ver a decisão.</p>}
        {decision && (
          <div className={styles.result}>
            <div className={styles.resultHead}>
              <span className={`chip ${decision.tier}`}>{TIER_PT[decision.tier]}</span>
              <span className={styles.queue}>{queuePt(decision.queue)}</span>
            </div>
            <p className={styles.reason}>{REASON_PT[decision.reason]}</p>
            <p className={styles.hint}>{TIER_HINT[decision.tier]}</p>

            <dl className={styles.facts}>
              <div>
                <dt>
                  Confiança <InfoTip label="confiança" text={EXPLAIN.confidence} />
                </dt>
                <dd>{pct(decision.confidence, 0)}</dd>
              </div>
              <div>
                <dt>
                  Vocabulário conhecido <InfoTip label="vocabulário conhecido" text={EXPLAIN.vocabulary} />
                </dt>
                <dd>{pct(decision.coverage, 0)}</dd>
              </div>
              <div>
                <dt>
                  Limiar automático <InfoTip label="limiar automático" text={EXPLAIN.autoThreshold} />
                </dt>
                <dd>{pct(state.status === 'ready' ? state.router.policy.t_auto : 0, 0)}</dd>
              </div>
            </dl>

            <h2 className={styles.h3}>
              Filas mais prováveis <InfoTip label="filas mais prováveis" text={EXPLAIN.topQueues} />
            </h2>
            <ul className={styles.probs}>
              {decision.top.map((q) => (
                <li key={q.queue}>
                  <span>{queuePt(q.queue)}</span>
                  <div className="meter" aria-hidden="true">
                    <span style={{ width: `${Math.round(q.p * 100)}%` }} />
                  </div>
                  <span className="mono">{pct(q.p, 0)}</span>
                </li>
              ))}
            </ul>

            {decision.why.length > 0 && (
              <>
                <h2 className={styles.h3}>
                  Palavras que puxaram a decisão <InfoTip label="palavras que puxaram a decisão" text={EXPLAIN.why} />
                </h2>
                <div className={styles.terms}>
                  {decision.why.map((w) => (
                    <span key={w.term} className="tag">
                      {w.term}
                    </span>
                  ))}
                </div>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
