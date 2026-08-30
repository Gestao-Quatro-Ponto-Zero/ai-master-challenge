import {
  useEffect,
  useRef,
  useState,
  type ReactNode,
  type KeyboardEvent as ReactKeyboardEvent,
} from "react";
import { api, ApiError } from "../api";
import { ESTADO_BADGE, SOBRECARGA_BADGE_CLASSES } from "../estadoColors";
import { formatIdade, formatPct, formatUsd } from "../format";
import type { ComponenteScore, DealDetail, LimitacaoScore } from "../types";
import { ConfidenceBadge } from "./ConfidenceBadge";
import { FitCell, FitRessalva } from "./FitDisplay";
import { LimitacoesScore, MarcadorLimitacao, limitacoesDe } from "./LimitacoesScore";

/** Painel lateral de detalhe — sete blocos de negócio agrupados em cartões
 * visualmente distintos (mesmo padrão `bg-white border border-border
 * rounded-sm` usado no restante do app), identificador refletido na URL,
 * navegação anterior/próxima sobre a fila corrente (mesmo atravessando
 * página), fechamento com `Esc`, retenção e devolução de foco (Requirement
 * "Painel de detalhe da oportunidade"). */
export function DealDetailPanel({
  opportunityId,
  asOf,
  onClose,
  onNotFound,
  onPrev,
  onNext,
  prevDisabled,
  nextDisabled,
}: {
  opportunityId: string;
  asOf?: string;
  onClose: () => void;
  onNotFound: () => void;
  onPrev: () => void;
  onNext: () => void;
  prevDisabled: boolean;
  nextDisabled: boolean;
}) {
  const [detail, setDetail] = useState<DealDetail | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const previouslyFocused = useRef<HTMLElement | null>(null);

  useEffect(() => {
    setDetail(null);
    setErro(null);
    api
      .getDealDetail(opportunityId, asOf)
      .then(setDetail)
      .catch((err: unknown) => {
        const message =
          err instanceof ApiError ? err.message : "falha ao carregar detalhe";
        setErro(message);
        if (err instanceof ApiError && err.status === 404) onNotFound();
      });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [opportunityId, asOf]);

  useEffect(() => {
    previouslyFocused.current = document.activeElement as HTMLElement | null;
    panelRef.current?.focus();
    return () => {
      previouslyFocused.current?.focus?.();
    };
  }, []);

  useEffect(() => {
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
  }, [onClose]);

  function trapFocus(e: ReactKeyboardEvent) {
    if (e.key !== "Tab" || !panelRef.current) return;
    // :not(:disabled) — um botão desabilitado (ex.: "Anterior" no primeiro
    // item) não recebe foco via .focus(), o que travaria o ciclo do trap
    // silenciosamente se ele fosse tratado como extremo do ciclo.
    const focusable = panelRef.current.querySelectorAll<HTMLElement>(
      'button:not(:disabled), [href], input:not(:disabled), select:not(:disabled), textarea:not(:disabled), [tabindex]:not([tabindex="-1"])',
    );
    if (focusable.length === 0) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (e.shiftKey && document.activeElement === first) {
      e.preventDefault();
      last.focus();
    } else if (!e.shiftKey && document.activeElement === last) {
      e.preventDefault();
      first.focus();
    }
  }

  return (
    <div className="fixed inset-0 z-40 flex justify-end">
      <button
        type="button"
        aria-label="Fechar painel de detalhe"
        onClick={onClose}
        className="absolute inset-0 bg-navy/40 border-0 cursor-default p-0"
      />
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-label="Detalhe da oportunidade"
        tabIndex={-1}
        onKeyDown={trapFocus}
        className="relative w-full max-w-xl h-full bg-bg shadow-xl overflow-y-auto flex flex-col focus:outline-none"
      >
        <div className="sticky top-0 z-10 flex items-center justify-between bg-white border-b border-border px-6 py-3">
          <div className="flex gap-2">
            <button
              type="button"
              onClick={onPrev}
              disabled={prevDisabled}
              className="text-sm text-navy border border-border rounded-xs px-2 py-1 disabled:opacity-40"
            >
              ← Anterior
            </button>
            <button
              type="button"
              onClick={onNext}
              disabled={nextDisabled}
              className="text-sm text-navy border border-border rounded-xs px-2 py-1 disabled:opacity-40"
            >
              Próxima →
            </button>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Fechar painel"
            className="text-navy text-2xl leading-none px-2 bg-transparent border-0"
          >
            ×
          </button>
        </div>

        <div className="flex-1 px-6 py-5 flex flex-col gap-4">
          {erro && (
            <p className="text-alert text-sm bg-alert/5 border border-alert rounded-xs px-3 py-2">
              Não foi possível carregar a oportunidade: {erro}
            </p>
          )}

          {!erro && !detail && <p className="text-muted text-sm">Carregando…</p>}

          {detail && <DetailContent detail={detail} />}
        </div>
      </div>
    </div>
  );
}

function DetailContent({ detail: o }: { detail: DealDetail }) {
  return (
    <div className="flex flex-col gap-4">
      <section>
        <h2 className="text-xl font-bold text-navy">{o.product}</h2>
        <p className="text-sm text-muted mt-0.5">
          {o.account ?? "Sem conta vinculada"} · {o.sales_agent}
        </p>
        <span className="inline-block font-mono text-[11px] text-muted bg-white border border-border rounded-xs px-1.5 py-0.5 mt-1.5">
          {o.opportunity_id}
        </span>
      </section>

      <div className="rounded-sm border border-navy/15 bg-navy/5 p-4 flex items-center justify-between gap-4">
        <div>
          <div className="text-[11px] font-bold text-gold uppercase tracking-wide">
            Score
          </div>
          <div className="text-4xl font-extrabold text-navy leading-none mt-1">
            {o.score.toFixed(1)}
          </div>
          {/* Colado ao número, não numa página de metodologia: "SCORE 98"
              lido sem esta linha vira "98% de chance de fechar". */}
          <p className="text-[11px] text-muted mt-1.5 max-w-[16rem] leading-snug">
            Percentil de valor em risco contra os negócios já ganhos — não é
            a chance de este fechar.
          </p>
        </div>
        <div className="flex flex-col items-end gap-2">
          <span
            className={
              "text-xs font-semibold px-2 py-0.5 rounded-full border " +
              ESTADO_BADGE[o.estado]
            }
          >
            {o.estado_label}
          </span>
          {o.sobrecarregado && (
            <span
              className={
                "text-xs font-semibold px-2 py-0.5 rounded-full border " +
                SOBRECARGA_BADGE_CLASSES
              }
            >
              Vendedor sobrecarregado
            </span>
          )}
        </div>
      </div>

      <section>
        <h3 className="text-[11px] font-bold text-navy uppercase tracking-wide mb-2">
          Componentes do score
        </h3>
        <dl className="grid grid-cols-3 gap-3">
          <Componente
            label="Probabilidade"
            valor={formatPct(o.p_hat)}
            explicacao="Chance de fechamento, calibrada pelo histórico do produto e pela janela de tempo."
            limitacoes={o.limitacoes}
            componente="p_hat"
          />
          <Componente
            label="Preço tabela"
            valor={formatUsd(o.preco_tabela)}
            explicacao="Preço de catálogo do produto."
            limitacoes={o.limitacoes}
            componente="valor"
          />
          <Componente
            label="Urgência"
            valor={formatPct(o.urgencia)}
            explicacao="Urgência de o negócio se resolver nos próximos 30 dias."
            limitacoes={o.limitacoes}
            componente="urgencia"
          />
        </dl>
      </section>

      <Card title="O que limita este score">
        <LimitacoesScore limitacoes={o.limitacoes} />
      </Card>

      <Card title="Confiança & contexto">
        <div>
          <ConfidenceBadge
            confianca={o.confianca}
            completude={o.completude}
            suporte={o.suporte}
            razao={o.razao_confianca}
          />
          <p className="text-sm text-muted mt-2">{o.razao_confianca}</p>

          {/* As duas metades lado a lado, com a que governa o mínimo
              marcada: completude baixa pede cadastro, suporte baixo é
              ausência de precedente — as duas ações são opostas, e o
              número sozinho não distingue qual é o caso. */}
          <dl className="grid grid-cols-2 gap-3 mt-3">
            <MetadeConfianca
              label="Completude do cadastro"
              valor={o.completude}
              governa={o.completude < o.suporte}
              descricao="Quanto dos cinco campos de cadastro existe."
            />
            <MetadeConfianca
              label="Suporte histórico"
              valor={o.suporte}
              governa={o.suporte < o.completude}
              descricao="Quantos negócios fechados respaldam esta idade e este produto."
            />
          </dl>
          <p className="text-[11px] text-muted mt-2">
            CONFIANÇA é o menor dos dois — {o.confianca.toFixed(0)} — e mede a
            veracidade do dado, nunca a chance de fechar.
          </p>
          <MarcadorLimitacao limitacoes={o.limitacoes} componente="confianca" />
        </div>

        <div className="border-t border-border pt-3">
          <p className="text-[11px] font-semibold text-muted uppercase tracking-wide mb-1.5">
            Idade do negócio
          </p>
          <p className="text-sm text-navy">
            Estágio: {o.deal_stage} · Idade: {formatIdade(o.age_days)}
          </p>
          {o.sem_precedente && (
            <p className="text-xs text-alert bg-alert/5 border border-alert rounded-xs px-3 py-2 mt-2">
              Fora de qualquer precedente histórico de fechamento — nenhum
              negócio ganho fechou nesta faixa de idade.
            </p>
          )}
        </div>
      </Card>

      <Card title="Conta & time">
        {o.conta.vinculada ? (
          <dl className="grid grid-cols-2 gap-3 text-sm text-navy">
            <Campo label="Setor" valor={o.conta.sector ?? "—"} />
            <Campo label="Porte" valor={o.conta.porte ?? "—"} />
            <Campo
              label="Receita anual"
              valor={
                o.conta.revenue !== null ? formatUsd(o.conta.revenue) : "—"
              }
            />
            <Campo
              label="Funcionários"
              valor={
                o.conta.employees !== null
                  ? o.conta.employees.toLocaleString("pt-BR")
                  : "—"
              }
            />
            <Campo
              label="Ano de fundação"
              valor={o.conta.year_established?.toString() ?? "—"}
            />
            <Campo label="Localização" valor={o.conta.office_location ?? "—"} />
          </dl>
        ) : (
          <p className="text-sm text-muted">Sem conta vinculada</p>
        )}

        <div className="border-t border-border pt-3">
          <p className="text-[11px] font-semibold text-muted uppercase tracking-wide mb-1.5">
            Time responsável
          </p>
          <dl className="grid grid-cols-3 gap-3">
            <Campo label="Vendedor" valor={o.sales_agent} />
            <Campo label="Gerente" valor={o.manager ?? "—"} />
            <Campo label="Escritório" valor={o.regional_office ?? "—"} />
          </dl>
        </div>
      </Card>

      <Card title="Fit histórico do vendedor">
        <dl className="grid grid-cols-2 gap-3">
          <FitCell label="Produto" fit={o.fit_produto} />
          <FitCell label="Setor" fit={o.fit_setor} />
        </dl>
        <FitRessalva texto={o.ressalva_fit} />
      </Card>

      <Card title="Por que este score">
        <ul className="flex flex-col gap-2 text-sm text-navy">
          {o.score_fatores.map((fator, i) => (
            <li key={i} className="flex gap-2">
              <span className="text-gold" aria-hidden="true">
                •
              </span>
              <span>{fator}</span>
            </li>
          ))}
        </ul>
      </Card>

      <Card title="Plano de ação">
        <ol className="flex flex-col gap-2.5">
          {o.plano_de_acao_passos.map((passo, i) => (
            <li key={i} className="flex gap-3 text-sm text-navy">
              <span className="shrink-0 flex items-center justify-center w-5 h-5 rounded-full bg-gold text-white text-[11px] font-bold">
                {i + 1}
              </span>
              <span className="pt-0.5">{passo}</span>
            </li>
          ))}
        </ol>
      </Card>
    </div>
  );
}

function Card({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded-sm border border-border bg-white p-4 flex flex-col gap-3">
      <h3 className="text-[11px] font-bold text-navy uppercase tracking-wide">
        {title}
      </h3>
      {children}
    </section>
  );
}

/** Um componente do score. Quando alguma limitação incide sobre ele, o
 * cartão ganha a borda de destaque e o marcador curto — a ressalva fica no
 * mesmo lugar em que o leitor estranha o número, e a explicação inteira
 * aparece uma vez só, na ficha "O que limita este score". */
function Componente({
  label,
  valor,
  explicacao,
  limitacoes,
  componente,
}: {
  label: string;
  valor: string;
  explicacao: string;
  limitacoes: LimitacaoScore[];
  componente: ComponenteScore;
}) {
  const limitado = limitacoesDe(limitacoes, componente).length > 0;

  return (
    <div
      className={
        "rounded-sm border p-3 " +
        (limitado ? "border-gold bg-gold/5" : "border-border bg-white")
      }
    >
      <dt className="text-[11px] uppercase tracking-wide text-muted mb-1">
        {label}
      </dt>
      <dd className="text-lg font-bold text-navy">{valor}</dd>
      <dd className="text-xs text-muted mt-1 leading-snug">{explicacao}</dd>
      <dd>
        <MarcadorLimitacao limitacoes={limitacoes} componente={componente} />
      </dd>
    </div>
  );
}

function MetadeConfianca({
  label,
  valor,
  governa,
  descricao,
}: {
  label: string;
  valor: number;
  governa: boolean;
  descricao: string;
}) {
  return (
    <div
      className={
        "rounded-xs border p-2.5 " +
        (governa ? "border-navy bg-navy/5" : "border-border bg-white")
      }
    >
      <dt className="text-[11px] uppercase tracking-wide text-muted flex items-center gap-1.5">
        {label}
        {governa && (
          <span className="text-[9px] font-bold text-white bg-navy rounded-full px-1.5 py-0.5 leading-none">
            GOVERNA
          </span>
        )}
      </dt>
      <dd className="text-lg font-bold text-navy leading-none mt-1">
        {valor.toFixed(0)}
      </dd>
      <dd className="text-[11px] text-muted mt-1 leading-snug">{descricao}</dd>
    </div>
  );
}

function Campo({ label, valor }: { label: string; valor: string }) {
  return (
    <div>
      <dt className="text-xs text-muted">{label}</dt>
      <dd className="font-medium">{valor}</dd>
    </div>
  );
}
