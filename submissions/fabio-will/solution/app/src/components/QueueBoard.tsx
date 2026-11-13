'use client'

import { useMemo, useRef, useState } from 'react'
import { EXPLAIN } from '@/lib/glossary'
import { QUEUE_PT, REASON_PT, TIER_HINT, TIER_PT, pct, queuePt } from '@/lib/labels'
import type { Tier } from '@/lib/router'
import { nextSort, sortBy, type SortDir, type SortState } from '@/lib/sort'
import type { QueueTicket } from '@/lib/types'
import { InfoTip } from './InfoTip'
import styles from './QueueBoard.module.css'
import { SortHeader } from './SortHeader'

type Filter = 'all' | Tier
type Outcome = 'confirmed' | 'changed' | 'escalated'

const FILTERS: Filter[] = ['all', 'auto', 'assist', 'human']

type SortKey = 'id' | 'queue' | 'conf' | 'tier'
const TIER_ORDER: Record<Tier, number> = { auto: 0, assist: 1, human: 2 }
const SORT_VALUE: Record<SortKey, (t: QueueTicket) => number | string> = {
  id: (t) => t.id,
  queue: (t) => queuePt(t.pred),
  conf: (t) => t.top[0]?.p ?? 0,
  tier: (t) => TIER_ORDER[t.tier],
}
const NATURAL: Record<SortKey, SortDir> = { id: 'asc', queue: 'asc', conf: 'desc', tier: 'asc' }
/** The phone layout hides the header row, so the same orders are offered in a select. */
const MOBILE_ORDERS: { value: string; label: string; sort: SortState<SortKey> | null }[] = [
  { value: 'fila', label: 'Ordem da fila', sort: null },
  { value: 'conf-desc', label: 'Maior confiança', sort: { key: 'conf', dir: 'desc' } },
  { value: 'conf-asc', label: 'Menor confiança', sort: { key: 'conf', dir: 'asc' } },
  { value: 'queue-asc', label: 'Fila sugerida, A a Z', sort: { key: 'queue', dir: 'asc' } },
  { value: 'tier-asc', label: 'Rota: automático primeiro', sort: { key: 'tier', dir: 'asc' } },
  { value: 'tier-desc', label: 'Rota: humano primeiro', sort: { key: 'tier', dir: 'desc' } },
]

export function QueueBoard({ tickets }: { tickets: QueueTicket[] }) {
  const [filter, setFilter] = useState<Filter>('all')
  const [selectedId, setSelectedId] = useState<string>(tickets[0]?.id ?? '')
  const [outcomes, setOutcomes] = useState<Record<string, Outcome>>({})
  const [sort, setSort] = useState<SortState<SortKey> | null>(null)
  const sheetRef = useRef<HTMLDialogElement>(null)

  const counts = useMemo(() => {
    const c: Record<Filter, number> = { all: tickets.length, auto: 0, assist: 0, human: 0 }
    for (const t of tickets) c[t.tier]++
    return c
  }, [tickets])

  const filtered = filter === 'all' ? tickets : tickets.filter((t) => t.tier === filter)
  const visible = useMemo(() => (sort ? sortBy(filtered, SORT_VALUE[sort.key], sort.dir) : filtered), [filtered, sort])
  const sortDir = (key: SortKey) => (sort?.key === key ? sort.dir : undefined)
  const toggleSort = (key: SortKey) => setSort((s) => nextSort(s, key, NATURAL[key]))
  const mobileValue = MOBILE_ORDERS.find((o) => o.sort?.key === sort?.key && o.sort?.dir === sort?.dir)?.value ?? 'fila'
  const selected = tickets.find((t) => t.id === selectedId) ?? visible[0]
  const decided = Object.values(outcomes)
  const overrides = decided.filter((o) => o !== 'confirmed').length

  const decide = (id: string, outcome: Outcome) => setOutcomes((prev) => ({ ...prev, [id]: outcome }))

  /** Desktop shows the sticky panel; up to 1024 px the detail opens as a bottom sheet next to the thumb. */
  const open = (id: string) => {
    setSelectedId(id)
    const sheet = sheetRef.current
    if (sheet && !sheet.open && window.matchMedia('(max-width: 1024px)').matches) sheet.showModal()
  }

  return (
    <div className={styles.board}>
      <div className={styles.listCol}>
        <div className={styles.controls}>
          <div className={styles.toolbar} role="group" aria-label="Filtrar por rota">
            {FILTERS.map((f) => (
              <button key={f} type="button" aria-pressed={filter === f} className={styles.filter} onClick={() => setFilter(f)}>
                {f === 'all' ? 'Todos' : TIER_PT[f]} <span className={styles.count}>{counts[f]}</span>
              </button>
            ))}
          </div>
          <label className={styles.mobileSort}>
            <span>Ordenar</span>
            <select className="select" value={mobileValue} onChange={(e) => setSort(MOBILE_ORDERS.find((o) => o.value === e.target.value)?.sort ?? null)}>
              {MOBILE_ORDERS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </label>
        </div>

        <div className="table-wrap">
          <table className={styles.table}>
            <caption className="skip">Fila de tickets com a decisão do roteador</caption>
            <thead>
              <tr>
                <SortHeader label="Ticket" dir={sortDir('id')} onSort={() => toggleSort('id')} info={EXPLAIN.ticketId} />
                <SortHeader label="Fila sugerida" dir={sortDir('queue')} onSort={() => toggleSort('queue')} info={EXPLAIN.suggestedQueue} />
                <SortHeader label="Confiança" numeric dir={sortDir('conf')} onSort={() => toggleSort('conf')} info={EXPLAIN.confidence} />
                <SortHeader label="Rota" dir={sortDir('tier')} onSort={() => toggleSort('tier')} info={EXPLAIN.route} />
              </tr>
            </thead>
            <tbody>
              {visible.map((t) => (
                <tr key={t.id} className={t.id === selected?.id ? styles.active : undefined} onClick={() => open(t.id)}>
                  <td>
                    <button
                      type="button"
                      className={styles.rowButton}
                      onClick={(e) => {
                        e.stopPropagation()
                        open(t.id)
                      }}
                    >
                      <span className={styles.id}>{t.id}</span>
                      <span className={styles.excerpt}>{t.text}</span>
                    </button>
                  </td>
                  <td>{queuePt(t.pred)}</td>
                  <td className="num">
                    <div className={styles.conf}>
                      <span>{pct(t.top[0]?.p ?? 0, 0)}</span>
                      <div className="meter" aria-hidden="true">
                        <span style={{ width: `${Math.round((t.top[0]?.p ?? 0) * 100)}%` }} />
                      </div>
                    </div>
                  </td>
                  <td>
                    <span className={`chip ${t.tier}`}>{TIER_PT[t.tier]}</span>
                    {outcomes[t.id] && (
                      <span className={styles.done}>
                        {outcomes[t.id] === 'confirmed' ? 'confirmado' : outcomes[t.id] === 'changed' ? 'fila trocada' : 'escalado'}
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <p className={styles.session} aria-live="polite">
          Nesta sessão: {decided.length} decisões, {overrides} correções humanas
          {decided.length > 0 && <> (taxa de override {pct(overrides / decided.length, 0)})</>}. Em produção, esse número por fila é o primeiro alarme de que o
          modelo envelheceu.
        </p>
      </div>

      {selected && (
        <aside className={styles.panel} aria-label={`Detalhe do ticket ${selected.id}`}>
          <TicketDetail key={selected.id} ticket={selected} outcome={outcomes[selected.id]} onDecide={decide} idPrefix="panel" />
        </aside>
      )}

      <dialog
        ref={sheetRef}
        className={styles.sheet}
        aria-label={selected ? `Detalhe do ticket ${selected.id}` : 'Detalhe do ticket'}
        onClick={(e) => e.target === e.currentTarget && e.currentTarget.close()}
      >
        <div className={styles.sheetHead}>
          <span className={styles.grabber} aria-hidden="true" />
          <button type="button" className="btn ghost" onClick={() => sheetRef.current?.close()}>
            Fechar
          </button>
        </div>
        {selected && (
          <div className={styles.sheetBody}>
            <TicketDetail
              key={selected.id}
              ticket={selected}
              outcome={outcomes[selected.id]}
              onDecide={(id, o) => {
                decide(id, o)
                sheetRef.current?.close()
              }}
              idPrefix="sheet"
            />
          </div>
        )}
      </dialog>
    </div>
  )
}

interface DetailProps {
  ticket: QueueTicket
  outcome: Outcome | undefined
  onDecide: (id: string, outcome: Outcome) => void
  /** Keeps form ids unique: the detail renders in the desktop panel and in the mobile sheet. */
  idPrefix: string
}

function TicketDetail({ ticket, outcome, onDecide, idPrefix }: DetailProps) {
  const [newQueue, setNewQueue] = useState<string>('')
  const choose = () => {
    onDecide(ticket.id, 'changed')
    setNewQueue('')
  }
  return (
    <>
      <div className={styles.panelHead}>
        <span className={styles.id}>{ticket.id}</span>
        <span className={`chip ${ticket.tier}`}>{TIER_PT[ticket.tier]}</span>
      </div>
      <p className={styles.reason}>{REASON_PT[ticket.reason]}</p>
      <p className={styles.hint}>{TIER_HINT[ticket.tier]}</p>

      <section className={styles.block}>
        <h3>
          Texto do ticket
          <InfoTip label="texto do ticket" text={EXPLAIN.ticketText} />
        </h3>
        <p className={styles.ticketText}>{ticket.text}</p>
      </section>

      <section className={styles.block}>
        <h3>
          Filas mais prováveis
          <InfoTip label="filas mais prováveis" text={EXPLAIN.topQueues} />
        </h3>
        <ul className={styles.probs}>
          {ticket.top.map((q) => (
            <li key={q.queue}>
              <span>{queuePt(q.queue)}</span>
              <div className="meter" aria-hidden="true">
                <span style={{ width: `${Math.round(q.p * 100)}%` }} />
              </div>
              <span className="mono">{pct(q.p, 0)}</span>
            </li>
          ))}
        </ul>
      </section>

      {ticket.why.length > 0 && (
        <section className={styles.block}>
          <h3>
            Por que essa fila
            <InfoTip label="por que essa fila" text={EXPLAIN.why} />
          </h3>
          <p className={styles.note}>Palavras do ticket que mais puxaram a decisão.</p>
          <div className={styles.terms}>
            {ticket.why.map((w) => (
              <span key={w.term} className="tag">
                {w.term}
              </span>
            ))}
          </div>
        </section>
      )}

      <section className={styles.block}>
        <h3>
          Parecidos no histórico
          <InfoTip label="parecidos no histórico" text={EXPLAIN.similar} />
        </h3>
        <ul className={styles.similar}>
          {ticket.similar.map((s, i) => (
            <li key={i}>
              <span className="tag">{queuePt(s.queue)}</span>
              <span className={styles.simText}>{s.text}</span>
            </li>
          ))}
        </ul>
      </section>

      <section className={styles.block}>
        <h3>
          Decisão do agente
          <InfoTip label="decisão do agente" text={EXPLAIN.agentDecision} />
        </h3>
        {outcome ? (
          <p className={styles.note}>Registrado. Próximo ticket na lista.</p>
        ) : (
          <div className={styles.actions}>
            <button type="button" className="btn primary" onClick={() => onDecide(ticket.id, 'confirmed')}>
              Confirmar {queuePt(ticket.pred)}
            </button>
            <div className={styles.change}>
              <label htmlFor={`${idPrefix}-trocar-fila`} className="skip">
                Trocar para outra fila
              </label>
              <select className="select" id={`${idPrefix}-trocar-fila`} value={newQueue} onChange={(e) => setNewQueue(e.target.value)}>
                <option value="">Trocar fila…</option>
                {Object.keys(QUEUE_PT)
                  .filter((q) => q !== ticket.pred)
                  .map((q) => (
                    <option key={q} value={q}>
                      {queuePt(q)}
                    </option>
                  ))}
              </select>
              <button type="button" className="btn ghost" disabled={!newQueue} onClick={() => choose()}>
                Aplicar
              </button>
            </div>
            <button type="button" className="btn danger" onClick={() => onDecide(ticket.id, 'escalated')}>
              Escalar para supervisor
            </button>
          </div>
        )}
        <p className={styles.truth}>
          Rótulo real no dataset: <strong>{queuePt(ticket.label)}</strong>{' '}
          {ticket.label === ticket.pred ? '(o roteador acertou)' : '(o roteador errou: é aqui que a revisão humana paga a conta)'}
        </p>
      </section>
    </>
  )
}
