import { ArrowRight, FileText } from "lucide-react"

import type { AppSummary } from "@/components/painel/diagnostic-data"
import { content, isAiError, isHumanJudgment } from "@/components/metodo/content"
import { DocDialog } from "@/components/metodo/doc-dialog"
import { Headline } from "@/components/shared/headline"
import { fmt } from "@/lib/format"
import { getMetric } from "@/lib/queries/analysis"
import { getOpsSummary } from "@/lib/queries/ops"
import { computeRoi, defaultInputs, type PremiseSource } from "@/lib/roi"

/** Preços oficiais da OpenAI consultados em 09/11/2026 (docs/n8n-flows.md), em US$ por 1M de tokens. */
const PRICE = { miniIn: 0.75, miniOut: 4.5, embedding: 0.02 }
/** Tokens do embedding do DS2 inteiro (scripts/embed_ds2.py, context/STATE.md). */
const EMBED_TOKENS = 2_190_000

interface Usage {
  n: number
  usage: { prompt_tokens: number; completion_tokens: number }
}
const llmCost = (u: Usage["usage"]) => (u.prompt_tokens * PRICE.miniIn + u.completion_tokens * PRICE.miniOut) / 1e6

const evidenceLink = "inline-flex w-fit cursor-pointer items-center gap-1.5 text-xs text-text-3 underline underline-offset-4 hover:text-text-1"

/** Evidência de cada bloco: rota interna, pop-up com o documento ou só o nome do arquivo (o repositório é privado). */
type Evidence = { label: string; href?: string; doc?: { eyebrow: string; title: string; html: string } }

function Block({ n, title, evidence, children }: { n: number; title: string; evidence: Evidence; children: React.ReactNode }) {
  return (
    <article className="flex flex-col gap-2 rounded-xl border border-border bg-surface p-5 shadow-soft">
      <p className="font-mono text-[10px] uppercase tracking-[0.14em] text-text-3">{String(n).padStart(2, "0")}</p>
      <h3 className="font-serif text-lg leading-snug text-text-1">{title}</h3>
      <div className="flex-1 text-sm leading-relaxed text-text-2">{children}</div>
      {evidence.href ? (
        <a href={evidence.href} className={evidenceLink}>
          {evidence.label} <ArrowRight className="size-3" aria-hidden />
        </a>
      ) : evidence.doc ? (
        <DocDialog {...evidence.doc} className={evidenceLink}>
          {evidence.label} <FileText className="size-3" aria-hidden />
        </DocDialog>
      ) : (
        <p className="font-mono text-[11px] text-text-3">Evidência: {evidence.label}</p>
      )}
    </article>
  )
}

/** Como foi feito › Condução (PRD §4.7.1): uma tela, blocos curtos, cada um com o fato e a evidência. */
export async function ConducaoView() {
  const [ops, zs, ragLlm, premises, summary] = await Promise.all([
    getOpsSummary(),
    getMetric<Usage>("zero_shot_eval"),
    getMetric<Usage>("rag_llm_eval"),
    getMetric<PremiseSource>("cost_premises"),
    getMetric<AppSummary>("app_summary"),
  ])
  const { adrs, judgment, sessions } = content
  const accepted = adrs.filter((a) => a.statusKind === "aceita").length
  const byDaniel = adrs.filter((a) => a.originKind === "daniel").length
  const danielIa = adrs.filter((a) => a.originKind === "daniel_ia").length
  const iaDaniel = adrs.filter((a) => a.originKind === "ia_daniel" || a.originKind === "ia").length
  const errors = judgment.filter(isAiError).length
  const human = judgment.filter(isHumanJudgment).length

  const embedCost = (EMBED_TOKENS * PRICE.embedding) / 1e6
  const evalCost = llmCost(zs.usage) + llmCost(ragLlm.usage)
  const total = embedCost + evalCost + ops.custo_usd_total
  const roi = computeRoi(defaultInputs(premises, summary.roi_inputs))

  return (
    <div className="flex flex-col gap-6">
      <Headline>
        Dois turnos noturnos, {adrs.length} decisões registradas e {fmt.usd(total, 2)} de OpenAI no projeto inteiro
      </Headline>
      <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        <Block n={1} title="Estrutura do projeto no Claude Code" evidence={{ label: "AGENTS.md" }}>
          <ul className="list-disc space-y-1 pl-4">
            <li>Memória no repositório: AGENTS.md como fonte única, CLAUDE.md só importa, context/STATE.md para o handoff. O Codex lê o mesmo conteúdo.</li>
            <li>Protocolo de sessão: ler o STATE, registrar ADR e process log, commitar com co-autoria da IA.</li>
            <li>MCPs isolados (supabase-g4, vercel-g4, n8n-g4), git-add.sh que respeita o .gitignore e sessões paralelas por frente.</li>
          </ul>
        </Block>
        <Block n={2} title="Plano e timebox" evidence={{ label: "context/STATE.md" }}>
          Dois turnos noturnos, 09/11 e 10/11/2026, com entregas por turno: dados, diagnóstico e classificador no 1º; fluxos n8n, app, vídeo e PR no 2º.
          {sessions.length ? ` Sessões registradas: ${sessions.map((s) => `${s.name.replace("Sessão ", "#")} ${s.duration ?? ""}`.trim()).join(", ")}.` : null}
        </Block>
        <Block n={3} title="Decisões registradas" evidence={{ label: "Como foi feito › Decisões", href: "/como-foi-feito/decisoes" }}>
          {adrs.length} ADRs, {accepted} aceitas pelo Daniel. {byDaniel} vieram só dele, {danielIa} partiram de uma ideia dele com desenho da IA e {iaDaniel} foram propostas pela IA e validadas ou ajustadas por
          ele. O judgment log tem {judgment.length} registros: {human} julgamentos do Daniel e {errors} erros da IA corrigidos.
        </Block>
        <Block n={4} title="Riscos tratados" evidence={{ label: "judgment log #2, #30, #33 e PRD §8", doc: { eyebrow: `Judgment log · ${judgment.length} registros`, title: "Judgment log: IA e julgamento humano", html: content.judgmentHtml } }}>
          <ul className="list-disc space-y-1 pl-4">
            <li>Dado sintético: diagnóstico com teste de significância antes de cada conclusão (ADR-0003).</li>
            <li>Credenciais de outros projetos auto-atribuídas pelo n8n: trocadas pelas do case antes de qualquer execução.</li>
            <li>Custo da OpenAI com teto no projeto, e app público com limites de uso por IP e monitoramento que só alerta.</li>
          </ul>
        </Block>
        <Block n={5} title="Custo do projeto" evidence={{ label: "preços oficiais em docs/n8n-flows.md" }}>
          <dl className="grid grid-cols-[1fr_auto] gap-x-4 gap-y-1 tabular-nums">
            <dt>Embeddings do DS2 (2,19 M tokens)</dt>
            <dd className="text-right text-text-1">{fmt.usd(embedCost, 2)}</dd>
            <dt>Avaliações com LLM ({fmt.int(zs.n + ragLlm.n)} chamadas)</dt>
            <dd className="text-right text-text-1">{fmt.usd(evalCost, 2)}</dd>
            <dt>Triagens no sistema ({fmt.int(ops.triagens)})</dt>
            <dd className="text-right text-text-1">{fmt.usd(ops.custo_usd_total, 2)}</dd>
            <dt className="font-semibold text-text-1">Total</dt>
            <dd className="text-right font-semibold text-text-1">{fmt.usd(total, 2)}</dd>
          </dl>
        </Block>
        <Block n={6} title="Capacidade da operação" evidence={{ label: "Painel › ROI", href: "/painel/roi" }}>
          Com os padrões do ROI, a Resposta automática devolve {fmt.int(roi.hoursSaved)} horas de atendente por ano, o equivalente a {fmt.dec(roi.ftesFreed, 2)} atendente em tempo integral (1.976 h/ano), em{" "}
          {fmt.pct(roi.automatedShare)} do volume.
        </Block>
      </div>
    </div>
  )
}
