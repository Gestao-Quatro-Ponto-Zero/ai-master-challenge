import type { Metadata } from 'next'
import { BusinessCase } from '@/components/BusinessCase'
import { InfoTip } from '@/components/InfoTip'
import audit from '@/data/audit.json'
import stress from '@/data/stress.json'
import { DEFAULT_INPUTS, FULL_TIME_HOURS, savedMinutes } from '@/lib/business'
import { d1Pt, num, pct } from '@/lib/labels'
import type { StressReport } from '@/lib/types'

export const metadata: Metadata = { title: 'Diagnóstico' }

const d1 = audit.dataset1
const d2 = audit.dataset2
const b = (stress as unknown as StressReport).baseline
const pValues = Object.values(d1.csat.drivers).map((v) => v.kruskal_p)

const stall = d1.director_questions.where_flow_stalls
const mood = d1.director_questions.what_moves_csat
const slowest = stall.worst[0]!
const saddest = mood.worst[0]!
const stallP = Object.values(stall.by_dimension).map((v) => v.kruskal_p)
const combo = (w: { channel: string; priority: string; type: string }) => `${d1Pt(w.channel)} · ${d1Pt(w.priority)} · ${d1Pt(w.type)}`
const hoursSaved = savedMinutes(DEFAULT_INPUTS, { auto: b.tiers.auto.share, assist: b.tiers.assist.share, autoPrecision: b.tiers.auto.precision ?? 0 }) / 60

const ANSWERS = [
  {
    q: 'Onde o fluxo trava?',
    how: 'Teste de permutação: os tempos são embaralhados entre os tickets 2.000 vezes e a pior das 80 combinações é comparada com a real. Se o acaso cria algo tão lento com frequência, não há gargalo provado.',
    n: pct(stall.permutation_p, 0),
    t: 'Nenhuma combinação trava além do acaso',
    d: `A mais lenta, ${combo(slowest)}, leva ${num(slowest.value, 1)} h contra ${num(stall.overall, 1)} h no geral. Embaralhando os tempos ${num(2000)} vezes, o acaso cria uma combinação tão lenta quanto essa em ${pct(stall.permutation_p, 0)} das vezes. Canal, prioridade e tipo, um a um: p entre ${num(Math.min(...stallP), 2)} e ${num(Math.max(...stallP), 2)}.`,
  },
  {
    q: 'O que impacta satisfação?',
    how: 'Correlação de Spearman entre o tempo, em módulo, e a nota, mais o mesmo teste de permutação na pior combinação. Perto de zero quer dizer nenhuma relação.',
    n: num(d1.csat.spearman_abs_delta_hours[0] ?? 0, 3),
    t: 'Nada que esteja na base',
    d: `É a correlação entre tempo e nota. A pior combinação, ${combo(saddest)}, tem nota ${num(saddest.value, 2)} contra ${num(mood.overall, 2)}, e o acaso faz igual em ${pct(mood.permutation_p, 0)} dos embaralhamentos.`,
  },
  {
    q: 'Quanto estamos desperdiçando?',
    how: 'Horas de triagem poupadas por mês com as premissas do painel abaixo, já descontando o retrabalho dos erros do automático e a auditoria por amostra.',
    n: `${num(hoursSaved)} h`,
    t: 'por mês em triagem, o desperdício que dá para provar',
    d: `${num(hoursSaved / FULL_TIME_HOURS, 1)} pessoa ou R$ ${num(hoursSaved * DEFAULT_INPUTS.hourCost)} por mês, com as premissas do painel abaixo. Tempo de fila não vira hora sem o carimbo de abertura, que a base não tem.`,
  },
]

const FINDINGS = [
  { n: num(d1.records), t: 'tickets, não 30 mil', d: `O CSV tem ${num(d1.raw_csv_lines)} linhas porque o texto quebra linha. O enunciado contou linhas.` },
  { n: `${num(d1.timestamps.span_hours, 0)} h`, t: 'é tudo o que os carimbos cobrem', d: `Primeira resposta e resolução cabem num intervalo de 27 horas, para compras de ${d1.timestamps.purchase_date_range[0]?.slice(0, 4)} a ${d1.timestamps.purchase_date_range[1]?.slice(0, 4)}.` },
  { n: pct(d1.timestamps.resolution_before_first_response_pct / 100), t: 'resolvem antes da primeira resposta', d: `${num(d1.timestamps.resolution_before_first_response)} dos ${num(d1.resolution_time_present)} tickets fechados. E não existe carimbo de abertura.` },
  { n: `p = ${num(d1.csat.uniformity_p, 2)}`, t: 'a nota de satisfação é sorteada', d: `Cerca de 550 tickets em cada nota de 1 a 5. Prioridade, canal, tipo, produto e gênero não mexem na nota (p entre ${num(Math.min(...pValues), 2)} e ${num(Math.max(...pValues), 2)}).` },
  { n: pct(d1.text.resolution_word_overlap_with_description_mean_pct / 100), t: 'das palavras da resolução aparecem no ticket', d: 'O texto de resolução é frase aleatória. Não serve para treinar resposta sugerida.' },
  { n: pct(d1.text.placeholder_product_purchased_pct / 100, 0), t: 'das descrições com {product_purchased}', d: 'O marcador do gerador de dados nunca foi preenchido.' },
]

const REGISTER = [
  { field: 'Carimbo de abertura do ticket', answers: 'Tempo até a primeira resposta e tempo total, por canal e prioridade' },
  { field: 'Fila inicial, fila final e cada troca de fila', answers: 'Quanto custa a triagem errada hoje: é a linha de base do roteador' },
  { field: 'Momento da primeira atribuição a um agente', answers: 'Tempo de triagem, o desperdício que a automação ataca' },
  { field: 'Nota de satisfação ligada ao ticket, ao agente e ao canal', answers: 'O que move a satisfação de verdade' },
  { field: 'Reabertura e motivo', answers: 'Resolução que não resolveu' },
  { field: 'Custo hora por nível de atendimento', answers: 'Transforma horas em reais sem premissa' },
]

export default function DiagnosisPage() {
  return (
    <>
      <section className="hero">
        <div className="wrap">
          <p className="eyebrow">Para o Diretor de Operações</p>
          <h1>
            Onde o tempo vai, e o que os dados <span className="accent">não contam.</span>
          </h1>
          <p className="lede">
            Antes de calcular gargalo, auditei os dados. A base operacional não sustenta diagnóstico de tempo nem de satisfação: qualquer gráfico de
            &ldquo;canal mais lento&rdquo; feito com ela é ruído com cara de insight. O que dá para provar está na base de texto real, e é por ela que a
            automação começa.
          </p>
        </div>
      </section>

      <section className="section">
        <div className="wrap">
          <div className="section-head on-light">
            <p className="eyebrow">As três perguntas do Diretor</p>
            <h2>
              Resposta curta, com o <span className="accent">número que sustenta</span>
              <InfoTip
                label="as três perguntas"
                text="As perguntas do enunciado, respondidas sobre os 2.769 tickets fechados do Dataset 1, com teste estatístico para separar padrão de acaso."
              />
            </h2>
            <p>
              Calculei o que o enunciado pede, por canal, prioridade e tipo, e testei se a diferença é maior que o acaso. Um painel de &ldquo;combinação
              mais lenta&rdquo; sempre acha uma; a pergunta é se ela existe.
            </p>
          </div>
          <div className="grid-3">
            {ANSWERS.map((a) => (
              <article key={a.q} className="card">
                <p className="eyebrow">
                  {a.q} <InfoTip label={a.q.toLowerCase()} text={a.how} />
                </p>
                <span className="big-number">{a.n}</span>
                <h3>{a.t}</h3>
                <p className="muted small">{a.d}</p>
              </article>
            ))}
          </div>
          <div className="table-wrap gap-top">
            <table>
              <caption className="table-caption">
                As cinco combinações mais lentas, que um painel ingênuo chamaria de gargalo. Base: {num(stall.tickets)} tickets fechados em{' '}
                {num(stall.cells)} combinações; horas entre primeira resposta e resolução, em módulo, a leitura mais favorável à base.
              </caption>
              <thead>
                <tr>
                  <th scope="col">Canal · prioridade · tipo</th>
                  <th scope="col" className="num">
                    Mediana
                  </th>
                  <th scope="col" className="num">
                    Tickets
                  </th>
                </tr>
              </thead>
              <tbody>
                {stall.worst.map((w) => (
                  <tr key={combo(w)}>
                    <td>{combo(w)}</td>
                    <td className="num">{num(w.value, 1)}&nbsp;h</td>
                    <td className="num">{num(w.n)}</td>
                  </tr>
                ))}
                <tr>
                  <td>
                    <strong>Todas as combinações</strong>
                  </td>
                  <td className="num">
                    <strong>{num(stall.overall, 1)}&nbsp;h</strong>
                  </td>
                  <td className="num">
                    <strong>{num(stall.tickets)}</strong>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="wrap">
          <div className="section-head on-light">
            <p className="eyebrow">Auditoria do Dataset 1</p>
            <h2>
              Seis sinais de que a base operacional é <span className="accent">sintética</span>
              <InfoTip
                label="auditoria do Dataset 1"
                text="Medidos pelo script de auditoria antes de qualquer análise. Juntos, mostram que tempo e satisfação foram gerados ao acaso e não sustentam diagnóstico."
              />
            </h2>
            <p>Todos reproduzíveis pelo script de auditoria. Nenhum deles depende de opinião.</p>
          </div>
          <div className="grid-3">
            {FINDINGS.map((f) => (
              <article key={f.t} className="card">
                <span className="big-number">{f.n}</span>
                <h3>{f.t}</h3>
                <p className="muted small">{f.d}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section className="section">
        <div className="wrap">
          <div className="section-head on-light">
            <p className="eyebrow">Onde está o desperdício recuperável</p>
            <h2>
              Triagem é o tempo que <span className="accent">ninguém mede</span> e todo mundo paga
              <InfoTip
                label="business case"
                text="A conta é uma função: as parcelas de automático e assistido e a taxa de erro vêm do teste; volume, minutos e custo são premissas que você ajusta nos controles."
              />
            </h2>
            <p>
              Cada ticket precisa de alguém que leia, entenda e mande para a fila certa. Na base real, {num(d2.records)} tickets se dividem em 8 filas, e o
              roteador acerta a fila em {pct(b.accuracy, 1)} dos casos. Com as travas, {pct(b.tiers.auto.share, 0)} seguem sem triagem humana, com{' '}
              {pct(b.tiers.auto.precision ?? 0, 0)} de precisão. Mexa nas premissas: a conta se ajusta.
            </p>
          </div>
          <BusinessCase shares={{ auto: b.tiers.auto.share, assist: b.tiers.assist.share, autoPrecision: b.tiers.auto.precision ?? 0 }} />
        </div>
      </section>

      <section className="section">
        <div className="wrap">
          <div className="section-head on-light">
            <p className="eyebrow">A partir de segunda-feira</p>
            <h2>
              O que registrar para a próxima conta <span className="accent">não precisar de premissa</span>
              <InfoTip
                label="campos a registrar"
                text="Campos que a operação ainda não grava. Com quatro semanas deles, tempo e satisfação passam a ser medidos, e o business case deixa de depender de premissa."
              />
            </h2>
            <p>Seis campos. Em quatro semanas de registro, o diagnóstico de tempo e de satisfação passa a ser medido, não estimado.</p>
          </div>
          <div className="table-wrap">
            <table>
              <thead>
                <tr>
                  <th scope="col">Registrar</th>
                  <th scope="col">Para responder</th>
                </tr>
              </thead>
              <tbody>
                {REGISTER.map((r) => (
                  <tr key={r.field}>
                    <td>
                      <strong>{r.field}</strong>
                    </td>
                    <td>{r.answers}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>
    </>
  )
}
