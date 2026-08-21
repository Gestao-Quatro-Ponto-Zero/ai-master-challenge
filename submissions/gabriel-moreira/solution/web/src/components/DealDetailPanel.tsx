import {
  useEffect,
  useRef,
  useState,
  type ReactNode,
  type KeyboardEvent as ReactKeyboardEvent,
} from "react";
import { api, ApiError } from "../api";
import { ESTADO_BADGE } from "../estadoColors";
import { formatIdade, formatPct, formatUsd } from "../format";
import type { DealDetail } from "../types";
import { ConfidenceBadge } from "./ConfidenceBadge";

/** Painel lateral de detalhe — sete seções em linguagem de negócio,
 * identificador refletido na URL, navegação anterior/próxima sobre a
 * fila corrente (mesmo atravessando página), fechamento com `Esc`,
 * retenção e devolução de foco (Requirement "Painel de detalhe da
 * oportunidade"). */
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
        className="relative w-full max-w-xl h-full bg-white shadow-xl overflow-y-auto p-6 flex flex-col gap-6 focus:outline-none"
      >
        <div className="flex items-center justify-between">
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

        {erro && (
          <p className="text-alert text-sm bg-alert/5 border border-alert rounded-xs px-3 py-2">
            Não foi possível carregar a oportunidade: {erro}
          </p>
        )}

        {!erro && !detail && <p className="text-muted text-sm">Carregando…</p>}

        {detail && <DetailContent detail={detail} />}
      </div>
    </div>
  );
}

function DetailContent({ detail: o }: { detail: DealDetail }) {
  return (
    <div className="flex flex-col gap-6">
      <section>
        <h2 className="text-lg font-bold text-navy">{o.product}</h2>
        <p className="text-xs text-muted font-mono">{o.opportunity_id}</p>
        <p className="text-sm text-muted">
          {o.account ?? "Sem conta vinculada"} · {o.sales_agent}
        </p>
        <div className="flex items-center gap-3 mt-2">
          <span
            className={
              "text-xs font-semibold px-2 py-0.5 rounded-full border " +
              ESTADO_BADGE[o.estado]
            }
          >
            {o.estado_label}
          </span>
          <span className="text-2xl font-bold text-navy">
            {o.score.toFixed(1)}
          </span>
          <span className="text-xs text-muted">SCORE</span>
        </div>
      </section>

      <section>
        <dl className="grid grid-cols-3 gap-3 text-sm mt-4 pt-4 border-t border-border">
          <Componente
            label="Probabilidade"
            valor={formatPct(o.p_hat)}
            explicacao="Chance de fechamento, calibrada pelo histórico do produto e pela janela de tempo."
          />
          <Componente
            label="Preço tabela"
            valor={formatUsd(o.preco_tabela)}
            explicacao="Preço de catálogo do produto."
          />
          <Componente
            label="Urgência"
            valor={formatPct(o.urgencia)}
            explicacao="Urgência de o negócio se resolver nos próximos 30 dias."
          />
        </dl>
      </section>

      <Section title="O que se sabe">
        <ConfidenceBadge
          confianca={o.confianca}
          completude={o.completude}
          suporte={o.suporte}
          razao={o.razao_confianca}
        />
        <p className="text-sm text-muted mt-2">{o.razao_confianca}</p>
      </Section>

      <Section title="Contexto de idade">
        <p className="text-sm text-navy">
          Estágio: {o.deal_stage} · Idade: {formatIdade(o.age_days)}
        </p>
        {o.sem_precedente && (
          <p className="text-sm text-alert mt-1">
            Fora de qualquer precedente histórico de fechamento — nenhum negócio
            ganho fechou nesta faixa de idade.
          </p>
        )}
      </Section>

      <Section title="Conta">
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
      </Section>

      <Section title="Time">
        <p className="text-sm text-navy">
          {o.sales_agent} · {o.manager ?? "—"} · {o.regional_office ?? "—"}
        </p>
      </Section>

      <Section title="Por que este score">
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
      </Section>
      <Section title="Plano de ação">
        <ol className="list-decimal list-inside text-sm text-navy flex flex-col gap-1.5">
          {o.plano_de_acao_passos.map((passo, i) => (
            <li key={i}>{passo}</li>
          ))}
        </ol>
      </Section>
    </div>
  );
}

function Section({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section>
      <h3 className="text-xs font-bold text-navy uppercase tracking-wide mb-2">
        {title}
      </h3>
      {children}
    </section>
  );
}

function Componente({
  label,
  valor,
  explicacao,
}: {
  label: string;
  valor: string;
  explicacao: string;
}) {
  return (
    <div>
      <dt className="text-xs text-muted">{label}</dt>
      <dd className="font-semibold text-navy">{valor}</dd>
      <dd className="text-xs text-muted mt-0.5">{explicacao}</dd>
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
