import type { Metadata } from 'next'
import { DataTable } from '@/components/DataTable'
import { InfoTip } from '@/components/InfoTip'
import lab from '@/data/lab.json'
import stress from '@/data/stress.json'
import { EXPLAIN } from '@/lib/glossary'
import { num, pct } from '@/lib/labels'
import type { LabReport, StressReport } from '@/lib/types'
import styles from './como.module.css'

export const metadata: Metadata = { title: 'Como funciona' }

const L = lab as unknown as LabReport
const b = (stress as unknown as StressReport).baseline
const MODEL_PT: Record<string, string> = {
  majority: 'Sempre a fila mais comum (piso)',
  complement_nb: 'Naive Bayes complementar',
  logreg_word: 'Regressão logística, palavras (escolhido)',
  svm_word_calibrated: 'SVM linear calibrado, palavras',
  logreg_char: 'Regressão logística, pedaços de palavra',
}

const STEPS = [
  { t: 'O ticket entra', d: 'Por e-mail, chat, portal ou telefone transcrito. O texto vai para o roteador como chegou.' },
  { t: 'O roteador lê', d: `Escolhe uma de 8 filas e diz o quanto confia. Modelo simples, explicável e calibrado: acerta ${pct(b.accuracy, 1)} e roda em milissegundos.` },
  { t: 'As travas conferem', d: 'Vocabulário e sequência conhecidos, histórico parecido, fila privilegiada, conteúdo e trecho sensível, limiar de confiança. A primeira que dispara decide.' },
  { t: 'A rota é definida', d: `Automático (${pct(b.tiers.auto.share, 0)}), assistido com duas sugestões (${pct(b.tiers.assist.share, 0)}) ou triagem humana (${pct(b.tiers.human.share, 0)}).` },
  { t: 'O agente recebe um rascunho', d: 'Próxima fase: um LLM escreve a resposta a partir de tickets resolvidos parecidos. O agente edita e envia. Ele nunca envia sozinho.' },
  { t: 'A operação vigia', d: 'Override por fila, auditoria cega de 2% do automático, disjuntor de distribuição e recalibração semanal do limiar.' },
]

const NOT_AUTOMATE = [
  { what: 'Conceder direito de administrador', why: 'Risco de segurança. A IA escolhe a fila; conceder é humano, com dupla checagem.' },
  { what: 'Responder ou decidir assunto de RH', why: 'Dado pessoal e sensível (LGPD). A IA só roteia, e conteúdo com cara de RH nunca segue sozinho para outra fila.' },
  { what: 'Aprovar compra', why: 'Decisão financeira com alçada. A IA organiza o pedido; quem aprova tem nome.' },
  { what: 'Enviar resposta ao cliente', why: 'O rascunho poupa tempo; o envio continua com o agente, que responde pelo que foi dito.' },
  { what: 'Ticket fora do que o modelo conhece', why: 'Outro idioma, outro domínio ou fila nova: vai para humano até existir dado para treinar.' },
]

const SUSTAIN = [
  { m: 'Taxa de override por fila', d: 'Quanto o agente corrige o roteador. Sobe primeiro quando o modelo envelhece.', a: 'Acima de 10% numa fila por uma semana: revisar' },
  { m: 'Auditoria cega de 2% do automático', d: 'Uma pessoa refaz a triagem sem ver a sugestão. Mede a precisão real, sem o viés de quem concorda com a máquina.', a: 'Abaixo de 92%: subir o limiar' },
  { m: 'Disjuntor de distribuição (PSI)', d: 'Compara as últimas 200 previsões com o histórico. Mudança brusca pausa o automático.', a: 'Acima de 0,25: automático pausado' },
  { m: 'Recalibração do limiar', d: 'Com a amostra auditada da semana, o limiar volta para onde a precisão é 95%.', a: 'Semanal' },
  { m: 'Retreino', d: 'Com os tickets confirmados pelos agentes, que viram rótulo novo.', a: 'Mensal, ou na criação de uma fila' },
]

const REFS = [
  { r: 'Chow, C. K. (1970). On optimum recognition error and reject tradeoff. IEEE Transactions on Information Theory.', u: 'Automatizar só onde o modelo sabe que sabe: a ideia do gate.' },
  { r: 'Guo, C. et al. (2017). On Calibration of Modern Neural Networks. ICML.', u: 'Confiança de 90% tem que acertar 9 em 10; por isso medimos o erro de calibração.' },
  { r: 'Ovadia, Y. et al. (2019). Can You Trust Your Model’s Uncertainty? NeurIPS.', u: 'Calibração não sobrevive a dado diferente: por isso as travas de novidade.' },
  { r: 'Sculley, D. et al. (2015). Hidden Technical Debt in Machine Learning Systems. NeurIPS.', u: 'Comparar distribuição prevista com a esperada e ter limite de ação: o disjuntor.' },
  { r: 'Parasuraman, R. e Manzey, D. (2010). Complacency and Bias in Human Use of Automation. Human Factors.', u: 'Override baixo pode ser confiança demais: por isso a auditoria é cega.' },
  { r: 'Brynjolfsson, E., Li, D. e Raymond, L. (2025). Generative AI at Work. The Quarterly Journal of Economics.', u: 'IA no atendimento rendeu 15% a mais de casos por hora com 5 mil agentes. Ganho real, não mágico.' },
  { r: 'Price, B. e Jaffe, D. (2008). The Best Service Is No Service. Jossey-Bass.', u: 'Contato também é informação: a fila errada é sintoma a medir, não só a corrigir.' },
  { r: 'Anthropic (2024). Building effective agents.', u: 'Comece pelo fluxo mais simples que resolve; agente só quando precisar.' },
  { r: 'Lowd, D. e Meek, C. (2005). Good Word Attacks on Statistical Spam Filters. CEAS.', u: 'Colar palavras inocentes engana classificador de texto: por isso a leitura por trecho.' },
  { r: 'OWASP (2023). Machine Learning Security Top 10.', u: 'Manipulação de entrada (ML01) e envenenamento de dado (ML02) entraram no pentest e no retreino.' },
]

export default function HowPage() {
  const models = Object.entries(L.models)
  return (
    <>
      <section className="hero">
        <div className="wrap">
          <p className="eyebrow">Como funciona</p>
          <h1>
            A IA escolhe a fila. <span className="accent">Quem decide é gente.</span>
          </h1>
          <p className="lede">
            Um fluxo simples, que dá para explicar numa reunião e auditar numa planilha. A IA faz a parte repetitiva e diz quando não sabe; as decisões
            com risco ficam com quem responde por elas.
          </p>
        </div>
      </section>

      <section className="section">
        <div className="wrap">
          <div className="section-head on-light">
            <p className="eyebrow">O fluxo</p>
            <h2>
              Do ticket à fila em <span className="accent">seis passos</span>
              <InfoTip label="o fluxo" text="O caminho de um ticket, do recebimento à vigilância depois do lançamento. A IA atua nos passos 2 a 5; pessoas decidem onde há risco." />
            </h2>
          </div>
          <ol className={styles.steps}>
            {STEPS.map((s, i) => (
              <li key={s.t} className={styles.step}>
                <span className={styles.stepN} aria-hidden="true">{i + 1}</span>
                <div>
                  <h3>{s.t}</h3>
                  <p className="muted">{s.d}</p>
                </div>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section className="section">
        <div className="wrap">
          <div className="section-head on-light">
            <p className="eyebrow">Onde a automação para</p>
            <h2>
              O que <span className="accent">não</span> automatizar, e por quê
              <InfoTip label="o que não automatizar" text="Decisões que ficam com pessoas por risco, lei ou responsabilidade, mesmo quando o modelo acertaria a fila." />
            </h2>
            <p>Automatizar 100% é sinal de alerta, não de ambição. Estes cinco pontos ficam com pessoas, por desenho.</p>
          </div>
          <div className="table-wrap">
            <table>
              <thead><tr><th scope="col">Não automatizar</th><th scope="col">Por quê</th></tr></thead>
              <tbody>
                {NOT_AUTOMATE.map((n) => (
                  <tr key={n.what}><td><strong>{n.what}</strong></td><td>{n.why}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="wrap">
          <div className="section-head on-light">
            <p className="eyebrow">Laboratório</p>
            <h2>
              Cinco modelos, um critério: <span className="accent">confiança que significa algo</span>
              <InfoTip label="laboratório" text="Todos treinados e medidos na mesma divisão de dados. As colunas ordenam com um clique; a linha destacada é o modelo escolhido." />
            </h2>
            <p>
              Mesma divisão para todos: {num(L.split.train)} tickets para treinar, {num(L.split.val)} para escolher os limiares e {num(L.split.test)} só para
              medir. O SVM acerta um pouco mais, mas a confiança dele é pior calibrada, e o gate depende dela. A regressão logística ainda roda no
              navegador e explica cada decisão por palavra.
            </p>
          </div>
          <DataTable
            highlightClassName={styles.chosen}
            columns={[
              { key: 'model', label: 'Modelo' },
              { key: 'accuracy', label: 'Acerto', format: 'pct1', natural: 'desc', info: EXPLAIN.accuracy },
              { key: 'f1', label: 'F1 macro', format: 'num3', natural: 'desc', info: EXPLAIN.macroF1 },
              { key: 'ece', label: 'Erro de calibração', format: 'num3', natural: 'asc', info: EXPLAIN.ece },
              { key: 'fit', label: 'Treino', format: 'sec1', natural: 'asc', info: EXPLAIN.fitTime },
              { key: 'infer', label: 'ms por mil tickets', format: 'num0', natural: 'asc', info: EXPLAIN.inferTime },
            ]}
            rows={models.map(([k, m]) => ({
              id: k,
              highlight: k === 'logreg_word',
              cells: { model: MODEL_PT[k] ?? k, accuracy: m.accuracy, f1: m.macro_f1, ece: m.ece, fit: m.fit_seconds, infer: m.infer_ms_per_1k },
            }))}
          />
        </div>
      </section>

      <section className="section">
        <div className="wrap grid-2">
          <div className="card">
            <p className="eyebrow">Próxima fase</p>
            <h2>
              Rascunho de resposta com <span className="accent">fonte</span>
              <InfoTip label="próxima fase" text="Desenho do rascunho com LLM. Não roda no protótipo porque o texto de resolução do Dataset 1 é aleatório: treinar com ele ensinaria ruído." />
            </h2>
            <p className="muted">
              Para cada ticket, buscar os resolvidos mais parecidos (os mesmos que o painel já mostra) e pedir a um LLM um rascunho que cite essas fontes.
              O agente edita e envia.
            </p>
            <ul className="clean">
              <li>O LLM não tem ferramenta: não abre chamado, não concede acesso, não envia nada.</li>
              <li>Texto do cliente entra como dado, nunca como instrução. Suíte de injeção de prompt definida antes do primeiro uso.</li>
              <li>A métrica é a taxa de edição do rascunho, não a de envio.</li>
            </ul>
            <p className="small muted">
              Por que não está rodando aqui: o texto de resolução do Dataset 1 é aleatório, então não existe base de respostas boas para recuperar. Treinar
              rascunho com ele ensinaria a escrever ruído.
            </p>
          </div>
          <div className="card">
            <p className="eyebrow">Sustentação</p>
            <h2>
              O que a operação <span className="accent">vigia</span> depois do lançamento
              <InfoTip label="sustentação" text="Métricas com limite de ação definido antes do lançamento. Cada uma diz o que fazer quando passa do limite, sem depender de opinião." />
            </h2>
            <div className={styles.sustain}>
              {SUSTAIN.map((s) => (
                <div key={s.m}>
                  <h3>{s.m}</h3>
                  <p className="muted small">{s.d}</p>
                  <p className="small"><strong>Ação:</strong> {s.a}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="section">
        <div className="wrap">
          <div className="section-head on-light">
            <p className="eyebrow">Em que isso se apoia</p>
            <h2>
              Referências que <span className="accent">mudaram o desenho</span>
              <InfoTip label="referências" text="Cada leitura vem com a decisão que ela mudou no desenho. A lista completa, com links conferidos, está em docs/boas-praticas-e-referencias.md." />
            </h2>
          </div>
          <ul className={styles.refs}>
            {REFS.map((r) => (
              <li key={r.r}>
                <p className={styles.ref}>{r.r}</p>
                <p className="muted small">{r.u}</p>
              </li>
            ))}
          </ul>
        </div>
      </section>
    </>
  )
}
