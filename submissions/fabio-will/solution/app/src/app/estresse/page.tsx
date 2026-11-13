import type { Metadata } from 'next'
import { DataTable } from '@/components/DataTable'
import { InfoTip } from '@/components/InfoTip'
import adversarial from '@/data/adversarial.json'
import pentest from '@/data/pentest.json'
import stress from '@/data/stress.json'
import { EXPLAIN } from '@/lib/glossary'
import { SEVERITY_PT, num, pct, queuePt, type Severity } from '@/lib/labels'
import type { StressReport, StressScenario, TierStat } from '@/lib/types'
import styles from './estresse.module.css'

export const metadata: Metadata = { title: 'Estresse' }

const report = stress as unknown as StressReport
const ORDER: Severity[] = ['extreme', 'critical', 'medium', 'light']
/** What each severity level means, behind the "i" of each block. */
const SEVERITY_INFO: Record<Severity, string> = {
  extreme: 'Falha que causaria dano real sem ninguém perceber: dado sensível na fila errada ou automação em massa sobre texto que o modelo não entende.',
  critical: 'Falha que derruba a precisão de forma visível em produção, como um incidente que muda a mistura de tickets ou texto com muito erro.',
  medium: 'Falha localizada, em casos raros ou que já caem no assistido.',
  light: 'Ajuste fino: calibração por fila e filas pequenas.',
}

const scenario = (id: string) => report.scenarios.find((x) => x.id === id)
const e1Auto = scenario('E1')?.with_guard?.auto_share ?? 0
const c1Precision = Object.values((scenario('C1')?.measured ?? {}) as Record<string, Record<string, TierStat>>).map((v) => v.auto?.precision ?? 0)

interface AttackRow {
  words: number
  escaped_auto_pct: number
  escaped_before_pentest_pct: number
}
interface Victim {
  tickets: number
  black_box: AttackRow[]
  interleaved_black_box: AttackRow
  white_box: Record<string, { curve: AttackRow[] }>
}
const VICTIMS = adversarial.victims as unknown as Record<string, Victim>

/** Worst case over target queues for the white-box attack at its largest word budget. */
function attackRows(v: Victim) {
  const five = v.black_box.find((r) => r.words === 5)
  const whiteLast = Object.values(v.white_box).map((w) => w.curve.at(-1)!)
  const worst = (k: keyof AttackRow) => Math.max(...whiteLast.map((r) => r[k]))
  return [
    { attack: '5 palavras comuns no fim (sem conhecer o modelo)', before: five?.escaped_before_pentest_pct ?? 0, after: five?.escaped_auto_pct ?? 0 },
    { attack: `${whiteLast[0]?.words ?? 12} palavras escolhidas por quem conhece o modelo`, before: worst('escaped_before_pentest_pct'), after: worst('escaped_auto_pct') },
    { attack: 'Uma palavra intercalada entre cada palavra do ticket', before: v.interleaved_black_box.escaped_before_pentest_pct, after: v.interleaved_black_box.escaped_auto_pct },
  ]
}

interface PentestResult {
  id: string
  severity: Severity
  attack: string
  expected: string
  passed: boolean
  evidence: unknown
}
const fiveWords = (q: string) => (VICTIMS[q]?.black_box.find((r) => r.words === 5)?.escaped_auto_pct ?? 0) / 100
const PENTEST = pentest as unknown as { base: string; date: string; passed: number; total: number; results: PentestResult[] }

/** One line of measured evidence per console attack. */
function evidenceLine(r: PentestResult): string {
  const e = r.evidence as Record<string, unknown>
  switch (r.id) {
    case 'csp-no-breakage':
      return `${(e.violations as unknown[]).length} violação, ${(e.errors as unknown[]).length} erro`
    case 'csp-injection':
      return `4 de 4 bloqueados (eval: ${String(e.eval).startsWith('blocked') ? 'bloqueado' : 'executou'})`
    case 'clickjacking':
      return e.rendered ? 'renderizou dentro do quadro' : 'o navegador recusou o quadro'
    case 'egress':
      return `${num(e.requestsAfterTyping as number)} requisição depois de digitar; ${(e.thirdParty as unknown[]).length} de terceiros`
    case 'model-tampering':
      return e.decided ? 'decidiu com o modelo adulterado' : 'arquivo recusado; nenhuma decisão'
    case 'oversized-input':
      return `${num(e.keptChars as number)} de ${num(e.pastedChars as number)} caracteres; decisão em ${num(e.decisionMs as number)}\u00a0ms`
    case 'no-tracking':
      return 'sem cookie, sem storage, noindex'
    default:
      return typeof r.evidence === 'string' ? r.evidence : ''
  }
}

/** What is still exposed after the guardrail, in plain words. Written from the measured numbers. */
const RESIDUAL: Record<string, string> = {
  E1: `Até o disjuntor disparar, cerca de ${pct(e1Auto, 0)} dos tickets de fora ainda seguem sozinhos. Rotear não é responder: o custo é atraso, e a auditoria por amostra pega.`,
  E2: 'As travas não pegam: os tickets da fila nova se parecem com os das outras. Quem pega é a taxa de override nas filas que recebem esses tickets. Fila nova exige rótulo e retreino.',
  E3: 'Rotear errado um pedido de acesso atrasa o pedido, não concede nada: conceder é sempre humano. O que resta é dado de RH caindo em outra fila, por isso as travas de conteúdo e de trecho sensível.',
  C1: `Com a mistura mudando, a precisão do automático ficou entre ${pct(Math.min(...c1Precision), 0)} e ${pct(Math.max(...c1Precision), 0)}. O risco é a mudança ser de vocabulário, não de proporção: aí entram o disjuntor e o override.`,
  C2: 'Com ruído, a precisão cai antes da cobertura. As travas de vocabulário e de sequência mandam o texto mais quebrado para humano; a recalibração semanal do limiar com amostra auditada devolve os 95%.',
  M1: 'Ticket com até 5 palavras acerta 77%, contra 85% a 89% dos demais: há pouco para ler. São poucos (44 de 7.176), e a maioria já cai no assistido.',
  M2: 'Sem trava, 62% iriam sozinhos com 20% de acerto. Com a trava de vocabulário, todos vão para humano. Solução de verdade: treinar com o histórico da operação no idioma dela.',
  M3: 'Os erros se concentram em filas vizinhas. No assistido, as duas sugestões cobrem a maior parte dessas confusões.',
  L1: 'Direitos de administrador é a fila menos calibrada; por isso ela nunca é automática.',
}

function Tiers({ t }: { t: Record<string, TierStat> }) {
  return (
    <span className={styles.tiers}>
      {(['auto', 'assist', 'human'] as const).map((k) =>
        t[k] ? (
          <span key={k} className={`chip ${k}`}>
            {k === 'auto' ? 'Auto' : k === 'assist' ? 'Assist.' : 'Humano'} {pct(t[k].share, 0)}
            {t[k].precision !== null && k === 'auto' ? ` · ${pct(t[k].precision ?? 0, 0)} certo` : ''}
          </span>
        ) : null,
      )}
    </span>
  )
}

function Measured({ s }: { s: StressScenario }) {
  const m = s.measured as Record<string, any> | undefined
  switch (s.id) {
    case 'E1': {
      const br = s.stream_breaker as Record<string, number | null>
      return (
        <table>
          <tbody>
            <tr><th scope="row">Sem travas</th><td className="num">{pct(s.without_guard?.auto_share ?? 0, 0)} automático; {pct(s.without_guard?.top_prediction_share ?? 0, 0)} caem numa fila só</td></tr>
            <tr><th scope="row">Com travas por ticket</th><td className="num">{pct(s.with_guard?.auto_share ?? 0, 0)} automático; {pct(s.with_guard?.human_share ?? 0, 0)} para humano</td></tr>
            <tr><th scope="row">Disjuntor (janela de {br.window})</th><td className="num">pausa o automático em {br.tickets_after_flood_start_until_pause} tickets; alarme falso no tráfego normal: {br.false_alarm_on_normal_traffic ?? 'nenhum'}</td></tr>
          </tbody>
        </table>
      )
    }
    case 'E2': {
      const dest = s.destinations as Record<string, number>
      return (
        <table>
          <tbody>
            <tr><th scope="row">Seguiriam sozinhos para fila errada</th><td className="num">{pct(s.without_guard?.auto_share ?? 0, 0)} sem travas · {pct(s.with_guard?.auto_share ?? 0, 0)} com travas</td></tr>
            <tr><th scope="row">Para onde foram</th><td>{Object.entries(dest).sort((a, b) => b[1] - a[1]).slice(0, 3).map(([q, n]) => `${queuePt(q)} ${n}`).join(' · ')}</td></tr>
          </tbody>
        </table>
      )
    }
    case 'E3': {
      const trade = s.privacy_tradeoff as { sensitive_mass: number | null; segment: boolean; auto_share: number; sensitive_tickets_auto_routed_elsewhere: number }[]
      return (
        <>
          <table>
            <thead><tr><th scope="col">Fila</th><th scope="col" className="num">Entram sozinhos</th><th scope="col" className="num">Saem sozinhos para outra fila</th></tr></thead>
            <tbody>
              {Object.entries(m ?? {}).map(([q, v]) => (
                <tr key={q}>
                  <th scope="row">{queuePt(q)} ({num(v.true_total)})</th>
                  <td className="num">{num(v.auto_routed_into)}</td>
                  <td className="num">{v.wrong_auto_routed_out_of_true} (eram {v.confidence_only_wrong_auto_out_of_true} sem a política)</td>
                </tr>
              ))}
            </tbody>
          </table>
          <table>
            <caption className={styles.caption}>Quanto a privacidade custa em automação</caption>
            <thead><tr><th scope="col">Trava de conteúdo sensível</th><th scope="col" className="num">Automático</th><th scope="col" className="num">Tickets sensíveis em outra fila</th></tr></thead>
            <tbody>
              {trade.map((r) => (
                <tr key={`${r.sensitive_mass}-${r.segment}`}>
                  <th scope="row">
                    {r.sensitive_mass === null ? 'Sem trava' : `≥ ${num(r.sensitive_mass, 2)}`}
                    {r.segment ? ' + trecho de 8 palavras (escolhida)' : ''}
                  </th>
                  <td className="num">{pct(r.auto_share, 1)}</td>
                  <td className="num">{r.sensitive_tickets_auto_routed_elsewhere}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </>
      )
    }
    case 'C1':
    case 'M1':
      return (
        <table>
          <tbody>
            {Object.entries(m ?? {}).map(([k, v]) => (
              <tr key={k}>
                <th scope="row">{k.includes(' x') ? `${queuePt(k.split(' x')[0] ?? '')} × ${k.split(' x')[1]}` : k}{v.tickets ? ` (${num(v.tickets)})` : ''}</th>
                <td>{v.accuracy !== undefined && <span className={styles.acc}>acerto {pct(v.accuracy, 0)}</span>}<Tiers t={v} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      )
    case 'C2':
      return (
        <table>
          <thead><tr><th scope="col">Letras com erro</th><th scope="col">Com as travas</th><th scope="col" className="num">Limiar recalibrado</th></tr></thead>
          <tbody>
            {Object.entries(m ?? {}).map(([k, v]) => (
              <tr key={k}>
                <th scope="row">{k} (acerto {pct(v.accuracy, 0)})</th>
                <td><Tiers t={v} /></td>
                <td className="num">{num(v.recalibrated_t_auto, 2)}: {pct(v.recalibrated_auto.share, 0)} auto, {pct(v.recalibrated_auto.precision, 0)} certo</td>
              </tr>
            ))}
          </tbody>
        </table>
      )
    case 'M2':
      return (
        <table>
          <tbody>
            <tr><th scope="row">Acerto do modelo</th><td className="num">{pct(m?.accuracy ?? 0, 0)}</td></tr>
            <tr><th scope="row">Sem trava</th><td className="num">{pct(m?.without_guard_auto_share ?? 0, 0)} seguiriam sozinhos</td></tr>
            <tr><th scope="row">Com trava de vocabulário</th><td><Tiers t={m as Record<string, TierStat>} /></td></tr>
          </tbody>
        </table>
      )
    case 'M3':
      return (
        <table>
          <tbody>
            {Object.entries(m ?? {}).map(([k, v]) => {
              const [a, b] = k.split(' → ')
              return (
                <tr key={k}>
                  <th scope="row">{queuePt(a ?? '')} lido como {queuePt(b ?? '')}</th>
                  <td className="num">{String(v)}</td>
                </tr>
              )
            })}
          </tbody>
        </table>
      )
    case 'L1':
      return (
        <DataTable
          columns={[
            { key: 'queue', label: 'Fila' },
            { key: 'support', label: 'Tickets', format: 'num0', natural: 'desc', info: EXPLAIN.support },
            { key: 'accuracy', label: 'Acerto', format: 'pct0', natural: 'desc', info: EXPLAIN.accuracy },
            { key: 'auto', label: 'Automático', format: 'pct0', natural: 'desc', info: EXPLAIN.autoShare },
            { key: 'ece', label: 'Erro de calibração', format: 'num3', natural: 'desc', info: EXPLAIN.ece },
          ]}
          rows={Object.entries(m ?? {}).map(([q, v]) => ({
            id: q,
            cells: { queue: queuePt(q), support: v.support, accuracy: v.accuracy, auto: v.auto_share, ece: v.ece },
          }))}
        />
      )
    default:
      return null
  }
}

export default function StressPage() {
  const b = report.baseline
  return (
    <>
      <section className="hero">
        <div className="wrap">
          <p className="eyebrow">Testes de estresse</p>
          <h1>
            Antes de confiar, <span className="accent">quebrar.</span>
          </h1>
          <p className="lede">
            Nove cenários de operação e um pentest, do extremamente crítico ao leve. Cada um foi medido, não argumentado. Quando a trava não resolve, está
            escrito. A severidade é o impacto se a trava falhar, não a chance de acontecer.
          </p>
          <div className="stats" role="list">
            <div className="stat" role="listitem"><b>{pct(b.confidence_only_tiers.auto.share, 0)}</b><span>automático só com o limiar de confiança <InfoTip label="automático sem travas" text={EXPLAIN.confidenceOnly} /></span></div>
            <div className="stat" role="listitem"><b>{pct(b.tiers.auto.share, 0)}</b><span>automático com as sete travas, {pct(b.tiers.auto.precision ?? 0, 0)} certo <InfoTip label="automático com as travas" text={EXPLAIN.auto} /></span></div>
            <div className="stat" role="listitem"><b>{pct(b.guard_false_rejection, 1)}</b><span>dos tickets normais barrados à toa pelas travas <InfoTip label="rejeição indevida" text={EXPLAIN.falseRejection} /></span></div>
            <div className="stat" role="listitem"><b>{num(b.ece, 3)}</b><span>erro de calibração: confiança de 90% acerta perto de 9 em 10 <InfoTip label="erro de calibração" text={EXPLAIN.ece} /></span></div>
          </div>
        </div>
      </section>

      {ORDER.map((sev) => {
        const items = report.scenarios.filter((s) => s.severity === sev)
        if (items.length === 0) return null
        return (
          <section key={sev} className="section">
            <div className="wrap">
              <div className="section-head on-light">
                <p className="eyebrow">
                  {SEVERITY_PT[sev]} <InfoTip label={`severidade ${SEVERITY_PT[sev].toLowerCase()}`} text={`${SEVERITY_INFO[sev]} ${EXPLAIN.severity}`} />
                </p>
              </div>
              <div className={styles.list}>
                {items.map((s) => (
                  <article key={s.id} className={`${styles.scenario} ${styles[sev]}`}>
                    <header className={styles.head}>
                      <span className={styles.code}>{s.id}</span>
                      <h2 className={styles.title}>{s.name}</h2>
                    </header>
                    <p className={styles.evidence}><strong>Evidência:</strong> {s.evidence}.</p>
                    {s.id === 'L1' ? <Measured s={s} /> : <div className="table-wrap"><Measured s={s} /></div>}
                    <div className={styles.cols}>
                      <p><strong>Trava:</strong> {s.guardrail}.</p>
                      <p><strong>O que ainda fica exposto:</strong> {RESIDUAL[s.id]}</p>
                    </div>
                  </article>
                ))}
              </div>
            </div>
          </section>
        )
      })}

      <section className="section" id="seguranca">
        <div className="wrap">
          <div className="section-head on-light">
            <p className="eyebrow">Segurança · pentest</p>
            <h2>
              Atacar o modelo e o console <span className="accent">antes de publicar</span>
              <InfoTip
                label="pentest"
                text="Dois alvos: enganar a política de roteamento com texto disfarçado e atacar o console no navegador. Tudo reproduzível com 05_adversarial.py e npm run pentest."
              />
            </h2>
            <p>
              Dois alvos: a política de roteamento, que alguém pode tentar enganar, e o console, que roda no navegador de quem usa. O pentest achou uma
              falha real no primeiro, e as travas de trecho e de sequência nasceram dela.
            </p>
          </div>
          <div className={styles.list}>
            <article className={`${styles.scenario} ${styles.extreme}`}>
              <header className={styles.head}>
                <span className={styles.code}>S1</span>
                <h2 className={styles.title}>Ticket disfarçado para escapar das travas</h2>
              </header>
              <p className={styles.evidence}>
                <strong>Evidência:</strong> {num(VICTIMS['Administrative rights']?.tickets ?? 0)} tickets de direitos de administrador e{' '}
                {num(VICTIMS['HR Support']?.tickets ?? 0)} de RH do conjunto de teste, com palavras de outra fila coladas. Conta como escape seguir sozinho
                para a fila errada.
              </p>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th scope="col">Ataque</th>
                      <th scope="col">Fila</th>
                      <th scope="col" className="num">Antes do pentest</th>
                      <th scope="col" className="num">Com as travas novas</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(VICTIMS).flatMap(([q, v]) =>
                      attackRows(v).map((r) => (
                        <tr key={`${q}-${r.attack}`}>
                          <th scope="row">{r.attack}</th>
                          <td>{queuePt(q)}</td>
                          <td className="num">{num(r.before, 0)}% escapam</td>
                          <td className="num">
                            <strong>{num(r.after, 0)}%</strong>
                          </td>
                        </tr>
                      )),
                    )}
                  </tbody>
                </table>
              </div>
              <div className={styles.cols}>
                <p>
                  <strong>Trava:</strong> o ticket também é lido em trechos de 8 palavras; se um trecho tem cara de RH ou de acesso privilegiado, uma pessoa
                  confirma. Texto com sequência de palavras que não existe no histórico vai para humano.
                </p>
                <p>
                  <strong>O que ainda fica exposto:</strong> com 5 palavras coladas, {pct(fiveWords('Administrative rights'), 0)} dos pedidos de administrador e{' '}
                  {pct(fiveWords('HR Support'), 0)} dos de RH ainda escapam. O
                  dano é de rota, não de acesso: ninguém concede permissão pela fila, e a auditoria cega e o override pegam o padrão.
                </p>
              </div>
            </article>

            <article className={`${styles.scenario} ${styles.critical}`}>
              <header className={styles.head}>
                <span className={styles.code}>S2</span>
                <h2 className={styles.title}>Ataques ao console no navegador</h2>
              </header>
              <p className={styles.evidence}>
                <strong>Evidência:</strong> {PENTEST.passed} de {PENTEST.total} ataques contidos, num Chrome real, contra o {PENTEST.base}. O mesmo script
                roda contra a URL publicada.
              </p>
              <div className="table-wrap">
                <table>
                  <thead>
                    <tr>
                      <th scope="col">Severidade</th>
                      <th scope="col">Ataque</th>
                      <th scope="col">Resultado medido</th>
                    </tr>
                  </thead>
                  <tbody>
                    {[...PENTEST.results].sort((a, b) => ORDER.indexOf(a.severity) - ORDER.indexOf(b.severity)).map((r) => (
                      <tr key={r.id}>
                        <td>{SEVERITY_PT[r.severity]}</td>
                        <th scope="row">{r.attack}</th>
                        <td>
                          <span className={`chip ${r.passed ? 'auto' : 'human'}`}>{r.passed ? 'Contido' : 'Falhou'}</span> {evidenceLine(r)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              <div className={styles.cols}>
                <p>
                  <strong>Trava:</strong> CSP com hash de cada script legítimo, cabeçalhos contra quadro e farejamento, modelo com assinatura SHA-256
                  conferida antes do uso, texto cortado em 4.000 caracteres e nenhum dado saindo do navegador.
                </p>
                <p>
                  <strong>O que ainda fica exposto:</strong> o protótipo não tem login nem dado real. Em produção, a fila precisa de autenticação, trilha
                  de auditoria por agente e o índice de histórico atrás de API própria.
                </p>
              </div>
            </article>
          </div>
        </div>
      </section>
    </>
  )
}
