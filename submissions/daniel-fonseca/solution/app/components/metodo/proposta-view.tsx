import type { AppSummary } from "@/components/painel/diagnostic-data"
import { ConfusionMatrix } from "@/components/metodo/confusion-matrix"
import { repoHref } from "@/components/metodo/content"
import { FlowDiagram, type FlowNode } from "@/components/metodo/flow-diagram"
import { Section } from "@/components/metodo/section"
import { PathBadge } from "@/components/shared/path-badge"
import { fmt } from "@/lib/format"
import { PATHS } from "@/lib/paths"
import { getMetric, getSensitiveExamples } from "@/lib/queries/analysis"
import type { PathKey } from "@/lib/types"

interface RagPolicy {
  accuracy: number
  tiers: Record<"1_automatico" | "2_revisao_humana" | "3_so_humano", { share: number; precision: number }> & {
    sensitive_escapes: { to_level_1: number; to_level_2: number; total_sensitive: number }
  }
}
interface ClassifierEval {
  n_train: number
  n_test: number
  results: { method: string; accuracy: number }[]
}
interface Confusion {
  labels: string[]
  matrix: number[][]
  accuracy: number
}
interface Blocklist {
  lists: { estreita: { terms: string[]; false_positive_rate_l1: number; escapes_caught: number } }
}

export async function PropostaView() {
  const [rag, clf, zs, ragLlm, conf, db, block, summary, examples] = await Promise.all([
    getMetric<RagPolicy>("rag_only_policy"),
    getMetric<ClassifierEval>("classifier_eval"),
    getMetric<{ n: number; zero_shot: { accuracy: number; precision_at_conf_0_9: number } }>("zero_shot_eval"),
    getMetric<{ n: number; rag_llm_accuracy: number }>("rag_llm_eval"),
    getMetric<Confusion>("rag_confusion"),
    getMetric<{ latency_ms: { p50: number } }>("db_rag_validation"),
    getMetric<Blocklist>("blocklist_eval"),
    getMetric<AppSummary>("app_summary"),
    getSensitiveExamples(),
  ])
  const tfidf = clf.results.find((r) => r.method === "tfidf_lr")?.accuracy ?? 0
  const t = rag.tiers
  const esc = t.sensitive_escapes
  const terms = block.lists.estreita.terms

  const nodes: FlowNode[] = [
    { id: "ticket", title: "Ticket chega", subtitle: "webhook do n8n", detail: "O ticket entra pelo webhook do fluxo de triagem no n8n, protegido por um segredo no cabeçalho. No Console, ele vem do holdout do DS2 ou de um texto livre em inglês." },
    { id: "embedding", title: "Embedding", subtitle: "OpenAI · 512 dim.", detail: "O texto vira um vetor de 512 dimensões com o text-embedding-3-small, ao custo de cerca de US$ 0,000002 por ticket." },
    {
      id: "busca",
      title: "50 casos parecidos",
      subtitle: "pgvector · Supabase",
      detail: `A função classify_ticket busca os 50 tickets mais parecidos entre os ${fmt.int(clf.n_train)} de treino do DS2, com índice HNSW. A busca leva ${fmt.ms(db.latency_ms.p50)} na mediana.`,
    },
    {
      id: "voto",
      title: "Voto ponderado",
      subtitle: "peso similaridade¹⁶",
      detail: `Cada vizinho vota na própria categoria com peso igual à similaridade elevada a 16, o que dá mais força aos casos quase idênticos. A confiança é a fração dos votos da categoria vencedora. Acurácia de ${fmt.pct(rag.accuracy)} em ${fmt.int(clf.n_test)} tickets do holdout.`,
    },
    {
      id: "regra",
      title: "Regra de decisão",
      subtitle: "3 caminhos",
      detail: "Somente humano quando a categoria prevista é sensível, quando 30% ou mais dos votos caem em categoria sensível, quando a confiança fica abaixo de 0,5 ou quando o texto tem um termo da lista de bloqueio. Resposta automática quando a confiança chega a 0,9 e existe solução validada da categoria. O restante segue para Revisão humana.",
    },
    { id: "auto", kind: "auto", title: PATHS.auto.label, subtitle: "adapta solução validada", detail: "O gpt-5.4-mini adapta ao ticket a solução validada mais parecida e mantém só os passos dela, sem prazo, promessa ou exceção nova. Se a solução não serve ao caso, o ticket segue para a Revisão humana." },
    { id: "review", kind: "review", title: PATHS.review.label, subtitle: "rascunho na fila", detail: "O LLM redige um rascunho e uma lista de pontos de checagem. Um agente aprova, edita ou rejeita no Console › Fila, e pode corrigir a categoria." },
    { id: "human", kind: "human", title: PATHS.human.label, subtitle: "resumo + alerta", detail: "A IA classifica e resume o ticket em pt-BR para o agente. O atendimento fica com uma pessoa, e o alerta chega à Caixa (no ambiente real, pelo nó Slack do n8n)." },
    { id: "base", kind: "base", title: "Soluções validadas", subtitle: "playbook + aprendidas", detail: "A base reúne o playbook inicial revisado pelo Daniel e cada resposta aprovada na Revisão humana. Uma aprovação passa a atender tickets parecidos pela Resposta automática." },
  ]

  const paths: { key: PathKey; tier: { share: number; precision: number }; rule: string }[] = [
    { key: "auto", tier: t["1_automatico"], rule: "Confiança ≥ 0,9, categoria não sensível, menos de 30% dos votos em categoria sensível e solução validada disponível." },
    { key: "review", tier: t["2_revisao_humana"], rule: "Confiança entre 0,5 e 0,9, ou sem solução validada que sirva ao caso." },
    { key: "human", tier: t["3_so_humano"], rule: "Categoria sensível prevista, 30% ou mais dos votos em categoria sensível, confiança < 0,5 ou termo da lista de bloqueio." },
  ]

  const methods = [
    { name: "TF-IDF + regressão logística", acc: tfidf, n: clf.n_test, note: "melhor acerto, sem casos para mostrar" },
    { name: "RAG por similaridade (escolhido)", acc: rag.accuracy, n: clf.n_test, note: "casos parecidos + base que aprende", chosen: true },
    { name: "RAG + LLM", acc: ragLlm.rag_llm_accuracy, n: ragLlm.n, note: "mesmo acerto do voto, com custo de LLM" },
    { name: "LLM zero-shot", acc: zs.zero_shot.accuracy, n: zs.n, note: `com confiança declarada ≥ 0,9, acerta ${fmt.pct(zs.zero_shot.precision_at_conf_0_9, 0)}` },
  ]

  const off: { n: number; real: string; pred: string }[] = []
  conf.matrix.forEach((row, i) => row.forEach((n, j) => i !== j && off.push({ n, real: conf.labels[i], pred: conf.labels[j] })))
  off.sort((a, b) => b.n - a.n)
  const top = off[0]

  const rule = summary.roi_inputs.ds1_eligible_rule.replace(/^fora:\s*/, "").replace(/\s*\(sempre humano\)/, "")

  return (
    <div className="flex flex-col gap-8">
      <Section eyebrow="Fluxo da automação" title="Cada ticket passa por 5 etapas até chegar a um dos 3 caminhos" lead="Passe o mouse, foque ou toque numa etapa para ver a regra.">
        <FlowDiagram nodes={nodes} />
      </Section>

      <Section eyebrow="Os 3 caminhos" title="A IA responde sozinha quando o voto é forte e existe solução validada" lead={`Proporções e acerto da categoria medidos no holdout de ${fmt.int(clf.n_test)} tickets do DS2.`}>
        <div className="grid gap-4 md:grid-cols-3">
          {paths.map((p) => (
            <div key={p.key} className="flex flex-col gap-3 rounded-xl border border-border bg-surface p-5 shadow-soft">
              <PathBadge path={p.key} className="w-fit" />
              <p className="text-sm leading-relaxed text-text-2">{p.rule}</p>
              <dl className="mt-auto grid grid-cols-2 gap-3 border-t border-border pt-3">
                <div>
                  <dt className="text-xs text-text-3">Dos tickets</dt>
                  <dd className="text-xl font-semibold tabular-nums text-text-1">{fmt.pct(p.tier.share)}</dd>
                </div>
                <div>
                  <dt className="text-xs text-text-3">Categoria certa</dt>
                  <dd className="text-xl font-semibold tabular-nums text-text-1">{fmt.pct(p.tier.precision)}</dd>
                </div>
              </dl>
            </div>
          ))}
        </div>
        <p className="text-sm leading-relaxed text-text-2">
          Dos {fmt.int(esc.total_sensitive)} tickets sensíveis do holdout, {fmt.int(esc.to_level_1)} ({fmt.pct(esc.to_level_1 / esc.total_sensitive)}) chegariam à Resposta automática pela regra de votos, a maioria
          com rótulo duvidoso na leitura. A lista de bloqueio ({terms.length} termos de RH e jurídico, como {terms.slice(0, 4).join(", ")}) pega {fmt.int(block.lists.estreita.escapes_caught)} deles e rebaixa{" "}
          {fmt.pct(block.lists.estreita.false_positive_rate_l1)} dos casos automáticos.
        </p>
      </Section>

      <Section eyebrow="O que não automatizar" title="RH, permissões administrativas, reembolso, cancelamento e prioridade crítica ficam com pessoas">
        <div className="grid gap-4 lg:grid-cols-[minmax(0,2fr)_minmax(0,1fr)]">
          <div className="flex flex-col gap-3">
            <p className="text-sm leading-relaxed text-text-2">
              Tickets reais do holdout que o RAG classifica certo e com confiança alta. Mesmo assim, seguem para Somente humano: tratam de pessoas, dados de RH ou acesso privilegiado.
            </p>
            <ul className="flex flex-col gap-3">
              {examples.map((e) => (
                <li key={e.ds2_id} className="rounded-lg border border-border bg-surface p-4">
                  <div className="mb-2 flex flex-wrap items-center gap-2">
                    <PathBadge path="human" size="sm" />
                    <span className="font-mono text-xs text-text-3">
                      DS2 #{e.ds2_id} · {e.note}
                    </span>
                  </div>
                  <p className="font-mono text-sm leading-relaxed text-text-1">“{e.document}”</p>
                </li>
              ))}
            </ul>
          </div>
          <div className="flex flex-col gap-3 self-start rounded-xl border border-border bg-surface-2/60 p-5">
            <p className="font-mono text-xs uppercase tracking-[0.14em] text-text-3">No DS1</p>
            <p className="text-sm leading-relaxed text-text-2">
              {rule.charAt(0).toUpperCase() + rule.slice(1)} vão sempre para atendimento humano. Envolvem dinheiro, contrato ou um cliente com impacto crítico, e são {fmt.pct(1 - summary.roi_inputs.ds1_eligible_share)} dos tickets.
            </p>
            <p className="text-sm leading-relaxed text-text-2">
              Por isso a economia do ROI parte dos {fmt.pct(summary.roi_inputs.ds1_eligible_share)} elegíveis.
            </p>
          </div>
        </div>
      </Section>

      <Section
        eyebrow="Comparação de métodos"
        title={`O RAG acerta ${fmt.pct(rag.accuracy)} e mostra ao agente os casos que sustentam cada decisão`}
        lead={`O Daniel escolheu o RAG como classificador único (ADR-0010), aceitando ${fmt.dec((tfidf - rag.accuracy) * 100, 1)} pontos a menos que o TF-IDF: ele entrega os casos parecidos, aprende com a Revisão humana e fica simples de manter no n8n. O LLM entra só para redigir.`}
      >
        <ul className="flex flex-col gap-2.5">
          {methods.map((m) => (
            <li key={m.name} className="grid grid-cols-[minmax(0,1fr)_56px] items-center gap-x-3 gap-y-1 sm:grid-cols-[240px_minmax(0,1fr)_56px]">
              <span className={m.chosen ? "text-sm font-semibold text-text-1" : "text-sm text-text-2"}>{m.name}</span>
              <span className="order-3 col-span-2 flex items-center gap-3 sm:order-none sm:col-span-1">
                <span className="relative h-3 flex-1 rounded-r-[4px] bg-surface-2">
                  <span className={m.chosen ? "absolute inset-y-0 left-0 rounded-r-[4px] bg-text-1" : "absolute inset-y-0 left-0 rounded-r-[4px] bg-text-3/60"} style={{ width: `${m.acc * 100}%` }} />
                </span>
              </span>
              <span className="text-right text-sm font-semibold tabular-nums text-text-1">{fmt.pct(m.acc)}</span>
              <span className="order-4 col-span-2 text-xs text-text-3 sm:col-span-3 sm:-mt-1 sm:pl-[252px]">
                {m.note} · {fmt.int(m.n)} tickets
              </span>
            </li>
          ))}
        </ul>
      </Section>

      <Section
        eyebrow="Matriz de confusão do RAG"
        title={`A maior confusão é ${top.real} prevista como ${top.pred}: ${fmt.int(top.n)} tickets`}
        lead={`Cada linha soma 100% da categoria real. Acurácia total de ${fmt.pct(conf.accuracy)} em ${fmt.int(clf.n_test)} tickets.`}
      >
        <ConfusionMatrix labels={conf.labels} matrix={conf.matrix} />
      </Section>

      <p className="text-xs leading-relaxed text-text-3">
        Evidência: <a className="underline underline-offset-2 hover:text-text-1" href={repoHref("docs/decisions/0010-classificador-de-producao.md")} target="_blank" rel="noreferrer">ADR-0010</a>,{" "}
        <a className="underline underline-offset-2 hover:text-text-1" href={repoHref("docs/n8n-flows.md")} target="_blank" rel="noreferrer">fluxos do n8n</a> e scripts{" "}
        <span className="font-mono">03</span> a <span className="font-mono">12</span> em <span className="font-mono">solution/analysis/</span>.
      </p>
    </div>
  )
}
