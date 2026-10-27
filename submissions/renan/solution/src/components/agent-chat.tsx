"use client";

import { ArrowRight, Bot, CircleX, KeyRound, LoaderCircle, Radar, Send, Sparkles, TriangleAlert, Info, Flag } from "lucide-react";
import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { KEY_HEADER, loadSettings, MODELS, type AgentSettings } from "@/lib/agent/config";
import type { Insight } from "@/lib/agent/insights";
import { pct, usd, usdCompact } from "@/lib/format";
import { RichText } from "./rich-text";

interface DealRow {
  id: string;
  produto: string;
  vendedor: string;
  momento: string;
  parado: boolean;
  dias: number | null;
  chance: number | null;
  valorEsperado: number;
  precoTabela: number;
  proximaAcao: string;
}

interface AgentAnswer {
  resposta: string;
  destaques: { rotulo: string; valor: string }[];
  grafico?: { titulo: string; unidade: "usd" | "deals" | "pct" | "dias"; barras: { rotulo: string; valor: number }[] };
  deals: DealRow[];
  acoes: string[];
  proximasPerguntas: string[];
  ferramentas: string[];
}

type Turn = { role: "usuario"; text: string } | { role: "agente"; answer: AgentAnswer } | { role: "erro"; text: string };

/** Texto da resposta devolvido como histórico nas perguntas seguintes. */
const asHistory = (a: AgentAnswer) =>
  [a.resposta, a.deals.length > 0 && `Deals citados: ${a.deals.map((d) => d.id).join(", ")}`, a.acoes.length > 0 && `Ações: ${a.acoes.join("; ")}`]
    .filter(Boolean)
    .join("\n");

const SEVERITY = {
  alta: { icon: TriangleAlert, chip: "bg-stalled-soft text-stalled", label: "Urgente" },
  media: { icon: Flag, chip: "bg-moment-soft text-moment", label: "Oportunidade" },
  info: { icon: Info, chip: "bg-hover text-secondary", label: "Atenção" },
} as const;

export function AgentChat({ agent, insights }: { agent?: string; insights: Insight[] }) {
  const [settings, setSettings] = useState<AgentSettings | null>(null);
  const [turns, setTurns] = useState<Turn[]>([]);
  const [draft, setDraft] = useState("");
  const [busy, setBusy] = useState(false);
  const conversationRef = useRef<HTMLDivElement>(null);
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // A configuração (chave inclusa) só existe no navegador.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setSettings(loadSettings());
  }, []);

  useEffect(() => {
    if (turns.length > 0) endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [turns, busy]);

  const hasKey = Boolean(settings?.apiKey);

  async function ask(question: string) {
    const text = question.trim();
    if (!text || busy || !settings?.apiKey) return;
    const history = [...turns, { role: "usuario", text } as Turn];
    setTurns(history);
    setDraft("");
    setBusy(true);
    conversationRef.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    try {
      const mensagens = history
        .filter((t): t is Exclude<Turn, { role: "erro" }> => t.role !== "erro")
        .slice(-10)
        .map((t) => (t.role === "usuario" ? { papel: "vendedor", texto: t.text } : { papel: "agente", texto: asHistory(t.answer) }));
      const response = await fetch("/api/agente", {
        method: "POST",
        headers: { "content-type": "application/json", [KEY_HEADER]: settings.apiKey },
        body: JSON.stringify({ mensagens, vendedor: agent, modelo: settings.model, esforco: settings.effort }),
      });
      const data = (await response.json()) as AgentAnswer & { erro?: string };
      setTurns((t) => [...t, data.erro ? { role: "erro", text: data.erro } : { role: "agente", answer: data }]);
    } catch {
      setTurns((t) => [...t, { role: "erro", text: "Não foi possível falar com o agente. Verifique a conexão." }]);
    } finally {
      setBusy(false);
    }
  }

  const who = agent ?? "o time";
  const ofWho = agent ? `de ${agent}` : "do time";

  return (
    <div className="space-y-8">
      <section aria-labelledby="radar" className="space-y-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <h2 id="radar" className="flex items-center gap-2 text-[20px] font-semibold tracking-[-0.02em]">
            <Radar className="size-5 text-moment" aria-hidden /> Radar {ofWho}
          </h2>
          <p className="text-[13px] text-secondary">Calculado dos dados a cada acesso, sem IA. Clique para o agente aprofundar.</p>
        </div>
        {insights.length === 0 ? (
          <p className="card p-6 text-secondary">Nenhum alerta para este recorte.</p>
        ) : (
          <ul className="grid gap-4 md:grid-cols-2 2xl:grid-cols-3">
            {insights.map((insight) => {
              const sev = SEVERITY[insight.severity];
              const Icon = sev.icon;
              return (
                <li key={insight.id} className="card flex flex-col p-5">
                  <div className="flex items-start justify-between gap-3">
                    <span className={`inline-flex items-center gap-1.5 rounded-full px-2.5 py-1 text-[12px] font-semibold ${sev.chip}`}>
                      <Icon className="size-3.5" aria-hidden /> {sev.label}
                    </span>
                    <span className="text-[22px] leading-none font-bold tracking-[-0.03em] tabular-nums">{insight.metric}</span>
                  </div>
                  <p className="mt-3 text-[16px] leading-snug font-semibold">{insight.title}</p>
                  <p className="mt-1 text-[13px] text-secondary">{insight.detail}</p>
                  <div className="mt-auto flex flex-wrap gap-2 pt-4">
                    {hasKey && (
                      <button
                        type="button"
                        onClick={() => ask(insight.question)}
                        disabled={busy}
                        className="inline-flex h-9 cursor-pointer items-center gap-1.5 rounded-full bg-primary px-4 text-[13px] font-semibold text-surface hover:opacity-90 disabled:opacity-50"
                      >
                        <Sparkles className="size-3.5" aria-hidden /> Analisar
                      </button>
                    )}
                    <Link href={insight.href} className="inline-flex h-9 items-center gap-1 rounded-full border border-line px-4 text-[13px] font-semibold hover:bg-hover">
                      Ver deals <ArrowRight className="size-3.5" aria-hidden />
                    </Link>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </section>

      {settings !== null && !hasKey && (
        <div className="card flex flex-wrap items-center justify-between gap-6 p-6">
          <div className="flex items-start gap-4">
            <span className="grid size-12 shrink-0 place-items-center rounded-full bg-hover text-secondary">
              <KeyRound className="size-6" aria-hidden />
            </span>
            <div>
              <h2 className="text-[18px] font-semibold">Conecte sua chave para conversar com os dados</h2>
              <p className="mt-1 max-w-[62ch] text-[14px] text-secondary">
                O Radar funciona sem IA. Para fazer perguntas e aprofundar alertas, cadastre a sua chave da API do Claude; ela fica só no seu navegador.
              </p>
            </div>
          </div>
          <Link href="/configuracoes" className="inline-flex h-11 items-center rounded-full bg-primary px-6 text-[15px] font-semibold text-surface hover:opacity-90">
            Abrir Configurações
          </Link>
        </div>
      )}

      {hasKey && settings && (
        <section ref={conversationRef} aria-label="Conversa com os dados" className="card scroll-mt-24">
          <div className="space-y-6 p-6" aria-live="polite">
            {turns.length === 0 && (
              <div className="flex flex-wrap items-center gap-4">
                <span className="grid size-12 place-items-center rounded-2xl bg-moment-soft text-moment">
                  <Bot className="size-6" aria-hidden />
                </span>
                <div className="min-w-0 flex-1">
                  <p className="text-[17px] font-semibold">Pergunte aos dados {ofWho}</p>
                  <p className="text-[14px] text-secondary">Respostas com números do pipeline, gráficos e os deals envolvidos. Só dados da Régua.</p>
                </div>
                <button
                  type="button"
                  onClick={() => ask(`Gere o briefing de hoje para ${who}: o que exige ação e em que ordem.`)}
                  disabled={busy}
                  className="inline-flex h-11 cursor-pointer items-center gap-2 rounded-full bg-moment px-5 text-[15px] font-semibold text-surface hover:opacity-90 disabled:opacity-50"
                >
                  <Sparkles className="size-4" aria-hidden /> Gerar briefing do dia
                </button>
              </div>
            )}

            {turns.map((turn, i) =>
              turn.role === "usuario" ? (
                <div key={i} className="flex justify-end">
                  <p className="max-w-[80%] rounded-2xl rounded-br-md bg-primary px-4 py-3 text-[15px] text-surface">{turn.text}</p>
                </div>
              ) : turn.role === "erro" ? (
                <p key={i} className="flex items-start gap-2 rounded-xl bg-stalled-soft p-4 text-[14px] text-stalled">
                  <CircleX className="mt-0.5 size-4 shrink-0" aria-hidden />
                  <span>
                    {turn.text}{" "}
                    <Link href="/configuracoes" className="underline underline-offset-4">
                      Configurações
                    </Link>
                  </span>
                </p>
              ) : (
                <Answer key={i} answer={turn.answer} onAsk={ask} disabled={busy} />
              ),
            )}

            {busy && (
              <p className="flex items-center gap-2 text-[14px] text-secondary">
                <LoaderCircle className="size-4 animate-spin" aria-hidden /> Analisando o pipeline…
              </p>
            )}
            <div ref={endRef} />
          </div>

          <form
            onSubmit={(e) => {
              e.preventDefault();
              ask(draft);
            }}
            className="flex items-end gap-2 border-t border-line p-4"
          >
            <label htmlFor="pergunta" className="sr-only">
              Pergunta sobre os dados
            </label>
            <textarea
              id="pergunta"
              value={draft}
              onChange={(e) => setDraft(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === "Enter" && !e.shiftKey) {
                  e.preventDefault();
                  ask(draft);
                }
              }}
              rows={1}
              maxLength={4000}
              placeholder="Ex.: quanto valor esperado o time tem em GTX Pro na reta final?"
              className="max-h-40 min-h-11 flex-1 resize-y rounded-2xl border border-line bg-surface px-4 py-2.5 text-[15px] placeholder:text-secondary focus:border-moment focus:outline-none"
            />
            <button
              type="submit"
              disabled={busy || !draft.trim()}
              aria-label="Enviar pergunta"
              className="grid size-11 shrink-0 cursor-pointer place-items-center rounded-full bg-primary text-surface hover:opacity-90 disabled:opacity-40"
            >
              <Send className="size-4" aria-hidden />
            </button>
          </form>
          <p className="border-t border-line px-6 py-3 text-[12px] text-secondary">
            {MODELS.find((m) => m.id === settings.model)?.label} · esforço{" "}
            {settings.effort === "low" ? "baixo" : settings.effort === "high" ? "alto" : "médio"} · consumo na sua chave.{" "}
            <Link href="/configuracoes" className="underline underline-offset-4">
              Alterar
            </Link>
          </p>
        </section>
      )}
    </div>
  );
}

const formatValue = (value: number, unit: NonNullable<AgentAnswer["grafico"]>["unidade"]) =>
  unit === "usd" ? usdCompact(value) : unit === "pct" ? `${value.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%` : unit === "dias" ? `${value} d` : value.toLocaleString("pt-BR");

function Answer({ answer, onAsk, disabled }: { answer: AgentAnswer; onAsk: (q: string) => void; disabled: boolean }) {
  const max = Math.max(1, ...(answer.grafico?.barras.map((b) => b.valor) ?? [1]));
  return (
    <article className="space-y-4 rounded-2xl border border-line bg-ground/50 p-5">
      <RichText text={answer.resposta} />

      {answer.destaques.length > 0 && (
        <dl className="grid grid-cols-2 gap-3 lg:grid-cols-4">
          {answer.destaques.map((d) => (
            <div key={d.rotulo} className="rounded-xl bg-surface p-3">
              <dt className="field">{d.rotulo}</dt>
              <dd className="mt-1 text-[20px] leading-none font-bold tracking-[-0.02em] tabular-nums">{d.valor}</dd>
            </div>
          ))}
        </dl>
      )}

      {answer.grafico && answer.grafico.barras.length > 0 && (
        <figure className="rounded-xl bg-surface p-4">
          <figcaption className="text-[14px] font-semibold">{answer.grafico.titulo}</figcaption>
          <ul className="mt-3 space-y-2">
            {answer.grafico.barras.map((b) => (
              <li key={b.rotulo} className="grid grid-cols-[minmax(0,9rem)_1fr_auto] items-center gap-3 text-[13px]">
                <span className="truncate" title={b.rotulo}>
                  {b.rotulo}
                </span>
                <span className="h-2.5 overflow-hidden rounded-full bg-track">
                  <span className="block h-full rounded-full bg-moment" style={{ width: `${(Math.max(0, b.valor) / max) * 100}%` }} />
                </span>
                <span className="font-mono tabular-nums">{formatValue(b.valor, answer.grafico!.unidade)}</span>
              </li>
            ))}
          </ul>
        </figure>
      )}

      {answer.deals.length > 0 && (
        <div className="overflow-x-auto rounded-xl bg-surface">
          <table className="w-full text-left text-[13px]">
            <thead>
              <tr className="border-b border-line">
                {["Deal", "Vendedor", "Momento", "Chance", "Valor esperado", "Próxima ação"].map((h) => (
                  <th key={h} scope="col" className="field px-3 py-2 font-medium">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-line">
              {answer.deals.map((d) => (
                <tr key={d.id}>
                  <td className="px-3 py-2">
                    <Link href={`/deal/${d.id}`} className="font-semibold hover:underline">
                      {d.produto}
                    </Link>
                    <span className="deal-id block text-[11px] text-secondary">{d.id}</span>
                  </td>
                  <td className="px-3 py-2">{d.vendedor}</td>
                  <td className={`px-3 py-2 whitespace-nowrap ${d.parado ? "text-stalled" : "text-moment"}`}>
                    {d.momento}
                    {d.dias !== null && <span className="ml-1 font-mono text-[11px]">{d.dias}d</span>}
                  </td>
                  <td className="px-3 py-2 tabular-nums">{d.chance === null ? "—" : pct(d.chance)}</td>
                  <td className="px-3 py-2 whitespace-nowrap tabular-nums">{d.parado ? `${usd(d.precoTabela)} parado` : usd(d.valorEsperado)}</td>
                  <td className="min-w-[14rem] px-3 py-2 text-secondary">{d.proximaAcao}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {answer.acoes.length > 0 && (
        <div>
          <p className="field">O que fazer</p>
          <ul className="mt-2 space-y-1.5 text-[14px]">
            {answer.acoes.map((a) => (
              <li key={a} className="flex items-start gap-2">
                <ArrowRight className="mt-0.5 size-4 shrink-0 text-moment" aria-hidden />
                {a}
              </li>
            ))}
          </ul>
        </div>
      )}

      {answer.proximasPerguntas.length > 0 && (
        <div className="flex flex-wrap gap-2 border-t border-line pt-4">
          {answer.proximasPerguntas.map((q) => (
            <button
              key={q}
              type="button"
              onClick={() => onAsk(q)}
              disabled={disabled}
              className="cursor-pointer rounded-full border border-line bg-surface px-3.5 py-1.5 text-left text-[13px] hover:border-moment hover:text-moment disabled:opacity-50"
            >
              {q}
            </button>
          ))}
        </div>
      )}

      {answer.ferramentas.length > 0 && <p className="field">Fontes consultadas: {answer.ferramentas.join(" · ")}</p>}
    </article>
  );
}
