"use client";

import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScenarioBadge } from "@/components/prototype/scenario-badge";
import { cn } from "@/lib/utils";
import { SCENARIO_LABELS } from "@/lib/routing/taxonomy";
import { Loader2, Clock } from "lucide-react";

// ─── Types ───────────────────────────────────────────────────────────

export interface ClassificationData {
  category: string | null;
  subject: string | null;
  scenario: string | null;
  confidence: number | null;
  action: string | null;
  explanation?: string;
  kb_title?: string | null;
  rag_articles?: Array<{
    title: string;
    similarity: number;
  }> | null;
  auto_routed: boolean;
  escalated: boolean;
  escalation_details?: {
    operator_name?: string;
    operator_level?: string;
    tier?: number;
    sla_deadline?: string;
    escalation_channel?: string;
    original_channel?: string;
  } | null;
  turn_count: number;
  fallback?: boolean;
  gate_passed?: boolean;
  gate_reason?: string | null;
  density_score?: number | null;
  density_details?: {
    tokenCount: number;
    technicalTerms: string[];
    problemVerbs: string[];
    hasErrorCode: boolean;
  } | null;
  raw_confidence?: number | null;
  effective_confidence?: number | null;
  grouped_count?: number;
}

export interface ClassificationHistoryEntry {
  timestamp: string;
  turn: number;
  data: ClassificationData;
}

interface ClassificationPanelProps {
  classification: ClassificationData | null;
  isLoading: boolean;
  turnCount: number;
  /** When viewing a historical conversation, pass the full history */
  history?: ClassificationHistoryEntry[];
  /** Whether this is a live (new) conversation or loaded from queue */
  isHistorical?: boolean;
}

// ─── Confidence Badge ───────────────────────────────────────────────

function ConfidenceBadge({ confidence, label }: { confidence: number; label?: string }) {
  const pct = Math.round(confidence * 100);
  const colorClass =
    confidence >= 0.85
      ? "bg-green-100 text-green-800"
      : confidence >= 0.5
        ? "bg-yellow-100 text-yellow-800"
        : "bg-red-100 text-red-800";

  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-2 py-0.5 text-xs font-semibold",
        colorClass
      )}
    >
      {label ? `${label}: ` : ""}{pct}%
    </span>
  );
}

// ─── Density Score Bar ──────────────────────────────────────────────

function DensityBar({ score }: { score: number }) {
  const pct = Math.round(score * 100);
  const colorClass =
    score > 0.6
      ? "bg-green-500"
      : score >= 0.3
        ? "bg-yellow-500"
        : "bg-red-500";

  return (
    <div className="flex items-center gap-2">
      <div className="h-2 flex-1 rounded-full bg-muted">
        <div
          className={cn("h-2 rounded-full transition-all duration-500", colorClass)}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className={cn(
        "text-xs font-semibold",
        score > 0.6 ? "text-green-700" : score >= 0.3 ? "text-yellow-700" : "text-red-700"
      )}>
        {pct}%
      </span>
    </div>
  );
}

// ─── Animated Step ──────────────────────────────────────────────────

function AnimatedStep({
  show,
  delay,
  children,
  skipAnimation,
}: {
  show: boolean;
  delay: number;
  children: React.ReactNode;
  skipAnimation?: boolean;
}) {
  const [visible, setVisible] = useState(skipAnimation ?? false);

  useEffect(() => {
    if (skipAnimation) {
      setVisible(true);
      return;
    }
    if (show) {
      const timer = setTimeout(() => setVisible(true), delay);
      return () => clearTimeout(timer);
    } else {
      setVisible(false);
    }
  }, [show, delay, skipAnimation]);

  return (
    <div
      className={cn(
        "transform transition-all duration-300",
        visible
          ? "translate-x-0 opacity-100"
          : "-translate-x-4 opacity-0"
      )}
    >
      {children}
    </div>
  );
}

// ─── Timestamp Label ────────────────────────────────────────────────

function TimestampLabel({ timestamp }: { timestamp: string }) {
  return (
    <div className="flex items-center gap-1 text-[10px] text-muted-foreground mb-1">
      <Clock className="h-2.5 w-2.5" />
      {new Date(timestamp).toLocaleTimeString("pt-BR", {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      })}
    </div>
  );
}

// ─── Classification Steps (reusable for both live and historical) ───

function ClassificationSteps({
  classification,
  skipAnimation,
  timestamp,
}: {
  classification: ClassificationData;
  skipAnimation: boolean;
  timestamp?: string;
}) {
  const hasClassification = true;
  const gateBlocked = classification.gate_passed === false;
  const gatePassed = classification.gate_passed !== false;
  const hasFullClassification = gatePassed && classification.category !== null;
  const scenarioInfo = classification.scenario
    ? SCENARIO_LABELS[classification.scenario]
    : null;

  return (
    <div className="space-y-3">
      {/* Timestamp for historical entries */}
      {timestamp && <TimestampLabel timestamp={timestamp} />}

      {/* Step 0: Message grouping indicator */}
      {classification.grouped_count && classification.grouped_count > 1 && (
        <AnimatedStep show={true} delay={0} skipAnimation={skipAnimation}>
          <div className="rounded-lg border border-indigo-200 bg-indigo-50/50 p-3">
            <p className="text-xs font-medium text-indigo-600">Agrupamento</p>
            <p className="mt-1 text-sm text-indigo-800">
              {classification.grouped_count} mensagens agrupadas em texto combinado
            </p>
          </div>
        </AnimatedStep>
      )}

      {/* Step 1: Pre-classification gate */}
      <AnimatedStep show={hasClassification} delay={classification.grouped_count && classification.grouped_count > 1 ? 200 : 0} skipAnimation={skipAnimation}>
        <div className={cn(
          "rounded-lg border p-3",
          gateBlocked
            ? "border-amber-200 bg-amber-50/50"
            : "bg-muted/30"
        )}>
          <p className="text-xs font-medium text-muted-foreground">
            Pre-classificacao
          </p>
          <div className="mt-1">
            {gateBlocked ? (
              <p className="text-sm font-medium text-amber-800">
                {classification.gate_reason === "greeting" && "Saudacao detectada"}
                {classification.gate_reason === "farewell" && "Despedida detectada"}
                {classification.gate_reason === "gratitude" && "Agradecimento detectado"}
                {classification.gate_reason === "too_short" && "Mensagem sem informacao tecnica suficiente"}
                {classification.gate_reason === "gibberish" && "Mensagem nao reconhecida"}
              </p>
            ) : (
              <p className="text-sm font-medium text-green-700">
                Mensagem contem informacao classificavel
              </p>
            )}
          </div>
        </div>
      </AnimatedStep>

      {/* Step 2: Information density (only if gate passed) */}
      {gatePassed && classification.density_score != null && (
        <AnimatedStep show={gatePassed} delay={200} skipAnimation={skipAnimation}>
          <div className="rounded-lg border bg-muted/30 p-3">
            <p className="text-xs font-medium text-muted-foreground">
              Densidade da Informacao
            </p>
            <div className="mt-2">
              <DensityBar score={classification.density_score} />
            </div>
            {classification.density_details && (
              <p className="mt-1.5 text-[11px] text-muted-foreground">
                {classification.density_details.tokenCount} tokens
                {classification.density_details.technicalTerms.length > 0 &&
                  ` | ${classification.density_details.technicalTerms.length} termos tecnicos`}
                {classification.density_details.problemVerbs.length > 0 &&
                  ` | ${classification.density_details.problemVerbs.length} verbos-problema`}
                {classification.density_details.hasErrorCode && " | codigo de erro"}
              </p>
            )}
          </div>
        </AnimatedStep>
      )}

      {/* Step 3: Classification (only if gate passed and classification ran) */}
      {hasFullClassification && (
        <AnimatedStep show={hasFullClassification} delay={400} skipAnimation={skipAnimation}>
          <div className="rounded-lg border bg-muted/30 p-3">
            <p className="text-xs font-medium text-muted-foreground">
              Classificacao — Categoria D2
            </p>
            <div className="mt-1 flex items-center gap-2">
              <span className="text-sm font-semibold">
                {classification.category}
              </span>
            </div>
            {classification.raw_confidence != null && classification.effective_confidence != null && (
              <div className="mt-2 flex flex-wrap gap-1.5">
                <ConfidenceBadge
                  confidence={classification.raw_confidence}
                  label="Bruta"
                />
                <ConfidenceBadge
                  confidence={classification.effective_confidence}
                  label="Efetiva"
                />
              </div>
            )}
            {classification.raw_confidence == null && classification.confidence != null && (
              <div className="mt-2">
                <ConfidenceBadge confidence={classification.confidence} />
              </div>
            )}
          </div>
        </AnimatedStep>
      )}

      {/* Step 4: Subject (sub-classification) */}
      {hasFullClassification && classification.subject && (
        <AnimatedStep show={hasFullClassification} delay={600} skipAnimation={skipAnimation}>
          <div className="rounded-lg border bg-muted/30 p-3">
            <p className="text-xs font-medium text-muted-foreground">
              Sub-classificacao D1
            </p>
            <p className="mt-1 text-sm font-semibold">
              {classification.subject}
            </p>
          </div>
        </AnimatedStep>
      )}

      {/* Step 5: Scenario */}
      {hasFullClassification && classification.scenario && (
        <AnimatedStep show={hasFullClassification} delay={800} skipAnimation={skipAnimation}>
          <div className="rounded-lg border bg-muted/30 p-3">
            <p className="text-xs font-medium text-muted-foreground">
              Cenario
            </p>
            <div className="mt-1">
              <ScenarioBadge scenario={classification.scenario} />
            </div>
          </div>
        </AnimatedStep>
      )}

      {/* Step 6: Recommended Action */}
      {hasFullClassification && (
        <AnimatedStep show={hasFullClassification} delay={1000} skipAnimation={skipAnimation}>
          <div className="rounded-lg border bg-muted/30 p-3">
            <p className="text-xs font-medium text-muted-foreground">
              Acao Recomendada
            </p>
            <p className="mt-1 text-sm">
              {scenarioInfo?.action || classification.action}
            </p>
          </div>
        </AnimatedStep>
      )}

      {/* Step 7: RAG — KB Semantic Search */}
      {hasFullClassification && classification.rag_articles && classification.rag_articles.length > 0 && (
        <AnimatedStep show={hasFullClassification} delay={1200} skipAnimation={skipAnimation}>
          <div className="rounded-lg border border-blue-200 bg-blue-50/50 p-3">
            <p className="text-xs font-medium text-blue-600">
              Busca na Base de Conhecimento (RAG)
            </p>
            <p className="mt-1 text-[10px] text-blue-500">
              Embedding gerado (1536 dims)
            </p>
            <div className="mt-2 space-y-1.5">
              {classification.rag_articles.map((article, idx) => {
                const pct = Math.round(article.similarity * 100);
                const colorClass =
                  pct >= 80
                    ? "text-green-700 bg-green-100"
                    : pct >= 60
                      ? "text-yellow-700 bg-yellow-100"
                      : "text-red-700 bg-red-100";
                return (
                  <div key={idx} className="flex items-start gap-2 text-xs">
                    <span
                      className={cn(
                        "inline-flex shrink-0 items-center rounded px-1.5 py-0.5 font-semibold",
                        colorClass
                      )}
                    >
                      {pct}%
                    </span>
                    <span className="text-blue-900 leading-tight">
                      {article.title}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>
        </AnimatedStep>
      )}

      {/* Escalation indicator */}
      {classification.escalated && (
        <AnimatedStep show={hasClassification} delay={1400} skipAnimation={skipAnimation}>
          <div className="rounded-lg border border-orange-200 bg-orange-50/50 p-3">
            <p className="text-xs font-medium text-orange-600">
              Escalonado para Operador
            </p>
            {classification.escalation_details ? (
              <div className="mt-2 space-y-1.5 text-sm text-orange-800">
                {classification.escalation_details.operator_name && (
                  <p>
                    <span className="font-medium">Operador:</span>{" "}
                    {classification.escalation_details.operator_name}
                    {classification.escalation_details.operator_level && (
                      <span className="ml-1 text-xs text-orange-600">
                        ({classification.escalation_details.operator_level})
                      </span>
                    )}
                  </p>
                )}
                {classification.escalation_details.tier != null && (
                  <p>
                    <span className="font-medium">Tier:</span>{" "}
                    {classification.escalation_details.tier}
                  </p>
                )}
                {classification.escalation_details.sla_deadline && (
                  <p>
                    <span className="font-medium">SLA:</span>{" "}
                    {new Date(classification.escalation_details.sla_deadline).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}
                  </p>
                )}
                {classification.escalation_details.escalation_channel &&
                  classification.escalation_details.original_channel &&
                  classification.escalation_details.escalation_channel !== classification.escalation_details.original_channel && (
                  <p className="rounded bg-orange-100 px-2 py-1 text-xs font-medium">
                    Canal redirecionado: {classification.escalation_details.original_channel} &rarr; {classification.escalation_details.escalation_channel}
                  </p>
                )}
              </div>
            ) : (
              <p className="mt-1 text-sm text-orange-800">
                Conversa encaminhada para operador especialista.
              </p>
            )}
          </div>
        </AnimatedStep>
      )}

      {/* Auto-route status */}
      {hasFullClassification && (
        <AnimatedStep show={hasFullClassification} delay={classification.rag_articles?.length ? 1400 : 1200} skipAnimation={skipAnimation}>
          <div className="mt-2 flex items-center gap-2">
            <div
              className={cn(
                "h-2 w-2 rounded-full",
                classification.auto_routed ? "bg-green-500" : "bg-yellow-500"
              )}
            />
            <span className="text-xs text-muted-foreground">
              {classification.auto_routed
                ? "Roteamento automatico aplicado"
                : "Aguardando mais informacoes..."}
            </span>
          </div>
        </AnimatedStep>
      )}
    </div>
  );
}

// ─── Main Component ─────────────────────────────────────────────────

export function ClassificationPanel({
  classification,
  isLoading,
  turnCount,
  history,
  isHistorical,
}: ClassificationPanelProps) {
  const hasClassification = classification !== null;
  const showTimeline = isHistorical && history && history.length > 0;

  return (
    <Card className="h-full">
      <CardHeader className="border-b">
        <div className="flex items-center justify-between">
          <CardTitle>Pipeline de Classificacao</CardTitle>
          <span className="text-xs text-muted-foreground">
            Turno: {turnCount}
          </span>
        </div>
        {showTimeline && (
          <p className="text-[10px] text-muted-foreground mt-1">
            Historico de {history.length} classificacao{history.length > 1 ? "oes" : ""}
          </p>
        )}
      </CardHeader>
      <CardContent className="space-y-4 pt-4">
        {/* Loading state */}
        {isLoading && !isHistorical && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>Analisando mensagem...</span>
          </div>
        )}

        {/* No classification yet */}
        {!isLoading && !hasClassification && !showTimeline && (
          <p className="text-sm text-muted-foreground">
            Envie uma mensagem para iniciar a classificacao.
          </p>
        )}

        {/* Historical timeline view */}
        {showTimeline && (
          <div className="space-y-6">
            {history.map((entry, idx) => (
              <div key={idx} className="relative">
                {/* Timeline connector */}
                {idx < history.length - 1 && (
                  <div className="absolute left-3 top-6 bottom-0 w-px bg-border" />
                )}
                {/* Turn label */}
                <div className="flex items-center gap-2 mb-2">
                  <div className="flex h-6 w-6 items-center justify-center rounded-full bg-primary/10 text-[10px] font-semibold text-primary">
                    {entry.turn}
                  </div>
                  <span className="text-[10px] text-muted-foreground">
                    Turno {entry.turn}
                  </span>
                </div>
                <div className="ml-8">
                  <ClassificationSteps
                    classification={entry.data}
                    skipAnimation={true}
                    timestamp={entry.timestamp}
                  />
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Live classification view (current / non-historical) */}
        {!showTimeline && hasClassification && classification && (
          <ClassificationSteps
            classification={classification}
            skipAnimation={false}
          />
        )}
      </CardContent>
    </Card>
  );
}
