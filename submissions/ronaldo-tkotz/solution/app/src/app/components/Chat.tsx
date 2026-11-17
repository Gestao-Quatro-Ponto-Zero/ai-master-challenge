"use client";

import { useCallback, useEffect, useMemo, useReducer, useRef, useState, type ReactNode } from "react";
import { Sql } from "./Sql";
import { composeDrillQuestion } from "./charts/drill";
import { ArtifactFrame } from "./artifacts/ArtifactFrame";
import { MarcarToggle } from "./telas/Marcados";
import { EnviarParaTela } from "./telas/EnviarParaTela";
import { chartSpecFromRows, markdownRowsToTablePayload, sortMarkdownBody } from "./artifacts/helpers";
import type { ChartSpec } from "@/engine/tools";
import type { ArtifactTransform, PartKind, StoredChart } from "@/engine/parts";

interface Step {
  index: number;
  tool: string;
  sql?: string;
  rowCount?: number;
  columns?: string[];
  rows?: Record<string, unknown>[];
  chart?: ChartSpec;
  isError: boolean;
}
interface UserTurn {
  role: "user";
  tid: string; // stable client id — the natural key for persistence (never the array index)
  text: string;
}
interface AssistantTurn {
  role: "assistant";
  tid: string;
  steps: Step[];
  answer?: string;
  citedSql?: string[];
  model?: string;
  stepCount?: number;
  error?: string;
  status: "streaming" | "done" | "error";
}
type Turn = UserTurn | AssistantTurn;

/** A persisted turn carries a schema version alongside the Turn fields. */
interface StoredTurn {
  v?: number;
  role?: string;
  tid?: string;
  [k: string]: unknown;
}

/** Stable id per turn — survives retries/edits; the persistence natural key. */
const newId = (): string =>
  typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
    ? crypto.randomUUID()
    : `t-${Date.now()}-${Math.random().toString(36).slice(2)}`;

/** A conversation title from its first question, trimmed for the sidebar. */
const deriveTitle = (turns: Turn[]): string => {
  const firstUser = turns.find((t): t is UserTurn => t.role === "user");
  const raw = firstUser?.text.trim() || "New conversation";
  return raw.length > 60 ? `${raw.slice(0, 60)}…` : raw;
};

/** A pin title from a question, trimmed the same way everywhere. */
const trimTitle = (q: string): string => (q.length > 60 ? `${q.slice(0, 60)}…` : q);

/**
 * The per-part pin API threaded down to each artifact frame. `toggle` builds the
 * POST body lazily (so it captures the CLICKED card's displayed projection), reads
 * the current pinned state itself, and the conversationId is injected upstream.
 * `registerTransform` lets a chart frame publish its live projection so a whole-turn
 * pin can capture the displayed chart (not first-chart-wins on the raw spec).
 */
interface PartPin {
  question: string;
  isPinned: (kind: PartKind, sourceId: string) => boolean;
  toggle: (kind: PartKind, sourceId: string, buildBody: () => Record<string, unknown>) => void;
  registerTransform: (sourceId: string, t: ArtifactTransform) => void;
}

/** Pin API for the k-th table inside an answer's markdown (built per assistant turn). */
interface AnswerTablePin {
  isPinned: (k: number) => boolean;
  toggle: (k: number, rows: string[][]) => void;
}

type ChatEvent =
  | { type: "start"; question: string }
  | { type: "step"; step: Step }
  | { type: "answer"; text: string; citedSql: string[]; model: string; steps: number }
  | { type: "error"; message: string };

const STARTERS: { chip: string; question: string }[] = [
  { chip: "Churn por mês em 2024", question: "Quantas contas tiveram evento de churn e quantos eventos houve em cada mês de 2024?" },
  { chip: "Motivos declarados", question: "Quais os motivos de churn declarados nos eventos, com o número de eventos e de contas de cada um?" },
  { chip: "Satisfação por trimestre", question: "Como se distribuem as notas de satisfação dos tickets por trimestre, contando os tickets sem nota?" },
  { chip: "Uso fora da assinatura", question: "Quantos registros de uso caem fora do período da assinatura, mês a mês?" },
];

const TOOL_LABEL: Record<string, string> = {
  query_warehouse: "Consultou o banco",
  run_metric: "Rodou uma métrica conferida",
  list_metrics: "Listou as métricas",
  make_chart: "Montou um gráfico",
  describe_schema: "Leu o esquema",
};

function renderInline(text: string, keyBase: string): ReactNode[] {
  return text.split(/(\*\*[^*]+\*\*)/g).map((part, i) => {
    if (part.startsWith("**") && part.endsWith("**")) {
      return (
        <strong key={`${keyBase}-${i}`} className="font-semibold text-foreground">
          {part.slice(2, -2)}
        </strong>
      );
    }
    return <span key={`${keyBase}-${i}`}>{part}</span>;
  });
}

const isTableRow = (line: string): boolean => line.trim().startsWith("|");

/** A markdown separator row like |---|:--:|---|. */
const isTableSeparator = (line: string): boolean => {
  const t = line.trim();
  return t.includes("-") && /^\|?[\s:|-]+\|?$/.test(t);
};

const splitCells = (line: string): string[] => {
  let t = line.trim();
  if (t.startsWith("|")) t = t.slice(1);
  if (t.endsWith("|")) t = t.slice(0, -1);
  return t.split("|").map((c) => c.trim());
};

/** Right-align $/number/%/date cells in mono for a real analyst-table feel. */
const isNumericCell = (s: string): boolean => {
  const t = s.trim();
  if (/^\d{4}-\d{2}(-\d{2})?$/.test(t)) return true;
  return /^[$€£]?-?[\d,]+(\.\d+)?\s*[%MKB]?$/i.test(t);
};

function Table({
  head,
  body,
  keyBase,
  sortCol,
  sortDir,
  onSort,
}: {
  head?: string[];
  body: string[][];
  keyBase: string;
  sortCol?: number | null;
  sortDir?: "asc" | "desc";
  onSort?: (col: number) => void;
}) {
  const sortable = typeof onSort === "function";
  // Align each column by its DATA so the header sits over its values, not beside them:
  // a column is numeric when most of its non-empty cells parse as a number → header AND
  // cells both right-align. (The ARR-heading-drift fix Ronaldo flagged.)
  const colCount = Math.max(head?.length ?? 0, ...body.map((r) => r.length), 0);
  const numericCol = Array.from({ length: colCount }, (_, ci) => {
    let numeric = 0;
    let filled = 0;
    for (const r of body) {
      const cell = (r[ci] ?? "").trim();
      if (!cell || cell === "—") continue;
      filled += 1;
      if (isNumericCell(cell)) numeric += 1;
    }
    return filled > 0 && numeric / filled >= 0.6;
  });
  return (
    <div className="overflow-x-auto rounded-md border border-edge">
      <table className="w-full border-collapse text-[12.5px]">
        {head && (
          <thead>
            <tr className="bg-surface/60">
              {head.map((c, i) => {
                const active = sortCol === i;
                return (
                  <th
                    key={i}
                    onClick={sortable ? () => onSort!(i) : undefined}
                    className={`border-b border-edge px-2.5 py-1.5 text-[10px] font-medium uppercase tracking-wider ${
                      numericCol[i] ? "text-right" : "text-left"
                    } ${active ? "text-accent" : "text-faint"} ${sortable ? "cursor-pointer select-none hover:text-foreground" : ""}`}
                  >
                    {renderInline(c, `${keyBase}-th-${i}`)}
                    {active && <span aria-hidden className="ml-1">{sortDir === "asc" ? "↑" : "↓"}</span>}
                  </th>
                );
              })}
            </tr>
          </thead>
        )}
        <tbody>
          {body.map((r, ri) => (
            <tr key={ri} className="align-top">
              {r.map((c, ci) => (
                <td
                  key={ci}
                  className={`border-b border-edge/50 px-2.5 py-1.5 ${numericCol[ci] ? "text-right font-mono tabular-nums text-foreground" : "text-muted"}`}
                >
                  {renderInline(c, `${keyBase}-td-${ri}-${ci}`)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

/**
 * A markdown answer TABLE as an artifact: client-side sort (grounded by the one
 * display-number parser) + its own pin. Deliberately NO chart control — these
 * cells are LLM prose, so charting them would present ungrounded numbers as
 * authoritative (advisor-mandated). Sorting only reorders the rows already shown.
 */
function MarkdownTableArtifact({
  rows,
  keyBase,
  pinned,
  onTogglePin,
}: {
  rows: string[][];
  keyBase: string;
  pinned: boolean;
  /** Receives the displayed (sorted) head+body so the pin captures this card's state. */
  onTogglePin?: (displayed: string[][]) => void;
}) {
  const [head, ...body] = rows;
  const [sortCol, setSortCol] = useState<number | null>(null);
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const sortedBody = useMemo(
    () => (sortCol === null ? body : sortMarkdownBody(body, sortCol, sortDir)),
    [body, sortCol, sortDir],
  );
  const onSort = (col: number) => {
    if (sortCol === col) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else {
      setSortCol(col);
      setSortDir("desc");
    }
  };
  const displayed = head ? [head, ...sortedBody] : sortedBody;

  return (
    <div className="space-y-1.5">
      {onTogglePin && (
        <div className="flex items-center">
          <button
            type="button"
            onClick={() => onTogglePin(displayed)}
            // Veta's deck-draft pins are hidden (D46.5): the presentation comes from marked charts.
            hidden
            title={pinned ? "Pinned to your deck draft — click to remove" : "Pin this table to the deck draft"}
            aria-pressed={pinned}
            className={`group ml-auto inline-flex items-center gap-1 rounded border px-1.5 py-0.5 text-[10.5px] font-medium transition-colors ${
              pinned
                ? "border-accent/30 bg-accent-soft/50 text-accent hover:border-red-400/40 hover:bg-red-400/5 hover:text-red-300"
                : "border-edge text-muted hover:border-edge-strong hover:text-foreground"
            }`}
          >
            <svg viewBox="0 0 24 24" fill={pinned ? "currentColor" : "none"} stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" className="h-2.5 w-2.5">
              <path d="M12 17v5M9 10.76V6a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v4.76a2 2 0 0 0 .59 1.42l1.41 1.41A2 2 0 0 1 18 15.83V17H6v-1.17a2 2 0 0 1 .59-1.42L8 13a2 2 0 0 0 .59-1.42Z" />
            </svg>
            {pinned ? (
              <>
                <span className="group-hover:hidden">Pinned</span>
                <span className="hidden group-hover:inline">Remove</span>
              </>
            ) : (
              "Pin"
            )}
          </button>
        </div>
      )}
      <Table head={head} body={sortedBody} keyBase={keyBase} sortCol={sortCol} sortDir={sortDir} onSort={onSort} />
    </div>
  );
}

function Prose({ text, tablePin }: { text: string; tablePin?: AnswerTablePin }) {
  const blocks: ReactNode[] = [];
  let bullets: string[] = [];
  let tableIndex = 0; // stable k per markdown table, in document order — the pin's natural key
  const flush = (key: string) => {
    if (bullets.length === 0) return;
    const items = bullets;
    bullets = [];
    blocks.push(
      <ul key={`ul-${key}`} className="ml-1 space-y-1">
        {items.map((b, i) => (
          <li key={i} className="flex gap-2">
            <span className="mt-2 h-1 w-1 shrink-0 rounded-full bg-accent" />
            <span>{renderInline(b, `li-${key}-${i}`)}</span>
          </li>
        ))}
      </ul>,
    );
  };

  const lines = text.split("\n");
  for (let i = 0; i < lines.length; i++) {
    const raw = lines[i];
    const t = raw.trim();

    // Table — collect consecutive pipe rows, drop the separator row.
    if (isTableRow(raw)) {
      flush(`b${i}`);
      const tableLines: string[] = [];
      let j = i;
      while (j < lines.length && isTableRow(lines[j])) tableLines.push(lines[j++]);
      const rows = tableLines.filter((l) => !isTableSeparator(l)).map(splitCells);
      if (rows.length > 0) {
        const k = tableIndex++;
        blocks.push(
          <MarkdownTableArtifact
            key={`tbl-${i}`}
            rows={rows}
            keyBase={`tbl-${i}`}
            pinned={tablePin?.isPinned(k) ?? false}
            onTogglePin={tablePin ? (displayed) => tablePin.toggle(k, displayed) : undefined}
          />,
        );
      }
      i = j - 1;
      continue;
    }

    // Horizontal rule.
    if (/^-{3,}$/.test(t)) {
      flush(`b${i}`);
      blocks.push(<hr key={`hr-${i}`} className="border-edge/60" />);
      continue;
    }

    // Header (#, ##, ### …).
    const h = /^(#{1,6})\s+(.*)$/.exec(t);
    if (h) {
      flush(`b${i}`);
      blocks.push(
        <div
          key={`h-${i}`}
          className={h[1].length <= 2 ? "mt-1 text-[15px] font-semibold text-foreground" : "mt-0.5 text-[13px] font-semibold text-foreground"}
        >
          {renderInline(h[2], `h-${i}`)}
        </div>,
      );
      continue;
    }

    // Bullet.
    if (/^[-*•]\s+/.test(t)) {
      bullets.push(t.replace(/^[-*•]\s+/, ""));
      continue;
    }

    // Paragraph.
    flush(`b${i}`);
    if (t) blocks.push(<p key={`p-${i}`}>{renderInline(t, `p-${i}`)}</p>);
  }
  flush("end");
  return <div className="space-y-2.5 text-[14px] leading-relaxed text-muted">{blocks}</div>;
}

function StepRow({
  step,
  tid,
  stepIndex,
  citedSql,
  partPin,
  onDrill,
  sqlOrigem,
}: {
  step: Step;
  tid: string;
  stepIndex: number;
  citedSql: string[];
  partPin: PartPin;
  onDrill?: (spec: ChartSpec, label: string) => void;
  /** The query whose rows the chart plots (the last one before it in the turn), D46.5. */
  sqlOrigem?: string;
}) {
  const [open, setOpen] = useState(false);
  const area = useRef<HTMLDivElement>(null);

  // A make_chart step is the payload itself, not a detail to expand — render the
  // grounded chart inline in an ArtifactFrame (type/sort/chart⇄table + its own pin).
  // A click on a chart element still drills in (re-asks one filter deeper).
  if (step.chart) {
    const chart = step.chart;
    const sourceId = `${tid}:step${stepIndex}:chart`;
    return (
      <div className="veta-rise rounded-md border border-edge bg-surface p-3">
        <div ref={area}>
        <ArtifactFrame
          spec={chart}
          initialView="chart"
          tableColumns={[chart.x, ...chart.y]}
          pinned={partPin.isPinned("chart", sourceId)}
          onTransform={(t) => partPin.registerTransform(sourceId, t)}
          onTogglePin={(transform) =>
            partPin.toggle("chart", sourceId, () => ({
              sourceKind: "chart",
              sourceId,
              question: partPin.question,
              answer: null,
              citedSql,
              chart: { ...chart, transform } satisfies StoredChart,
              title: chart.title || trimTitle(partPin.question),
            }))
          }
          onAskDeeper={onDrill}
        />
        </div>
        {/* D46.5: a chat chart can go to the presentation or to one of the user's screens. */}
        <div className="mt-2 flex flex-wrap items-center gap-2 border-t border-edge pt-2" data-sem-captura>
          <MarcarToggle
            titulo={(chart.title || trimTitle(partPin.question)).slice(0, 200)}
            nota={`pergunta: ${trimTitle(partPin.question)}`.slice(0, 300)}
            sql={sqlOrigem ? [sqlOrigem] : []}
            alvo={area}
            rota="/chat"
            filtros=""
          />
          <span className="text-[11px] text-faint">Marcar para a apresentação</span>
          <EnviarParaTela chart={chart} sql={sqlOrigem ? [sqlOrigem] : []} />
        </div>
      </div>
    );
  }

  const hasDetail = Boolean(step.sql) || (step.rows?.length ?? 0) > 0;
  return (
    <div className="veta-rise overflow-hidden rounded-md border border-edge bg-surface">
      <button
        onClick={() => hasDetail && setOpen((o) => !o)}
        className={`flex w-full items-center gap-2 px-3 py-2 text-left ${hasDetail ? "cursor-pointer hover:bg-panel/60" : "cursor-default"}`}
      >
        <span className={`h-1.5 w-1.5 rounded-full ${step.isError ? "bg-red-500" : "bg-accent"}`} />
        <span className="text-[12px] text-muted">{TOOL_LABEL[step.tool] ?? step.tool}</span>
        {typeof step.rowCount === "number" && (
          <span className="font-mono text-[11px] text-faint">{step.rowCount.toLocaleString("en-US")} rows</span>
        )}
        {hasDetail && <span className="ml-auto font-mono text-[12px] text-faint">{open ? "−" : "+"}</span>}
      </button>
      {open && hasDetail && (
        <div className="space-y-2 border-t border-edge px-3 py-2.5">
          {step.sql && <Sql sql={step.sql} rowCount={step.rowCount} />}
          {step.rows && step.rows.length > 0 && (() => {
            const cols = step.columns && step.columns.length > 0 ? step.columns : Object.keys(step.rows[0]);
            const rows = step.rows;
            const spec = chartSpecFromRows(cols, rows, "Result set");
            const sourceId = `${tid}:step${stepIndex}:table`;
            return (
              <ArtifactFrame
                spec={spec}
                initialView="table"
                tableColumns={cols}
                pinned={partPin.isPinned("table", sourceId)}
                onTogglePin={() =>
                  partPin.toggle("table", sourceId, () => ({
                    sourceKind: "table",
                    sourceId,
                    question: partPin.question,
                    citedSql,
                    table: { columns: cols, rows: rows.slice(0, 50) },
                    title: trimTitle(partPin.question),
                  }))
                }
                onAskDeeper={onDrill}
              />
            );
          })()}
        </div>
      )}
    </div>
  );
}

function AssistantBlock({
  turn,
  question,
  pinned,
  onPin,
  partPin,
  onDrill,
}: {
  turn: AssistantTurn;
  question: string;
  pinned: boolean;
  onPin: () => void;
  partPin: PartPin;
  onDrill?: (spec: ChartSpec, label: string) => void;
}) {
  // Pin API for the markdown tables inside this turn's answer (keyed by the k-th
  // table in document order), and the narrative pin for just the prose.
  const answerTablePin: AnswerTablePin = {
    isPinned: (k) => partPin.isPinned("table", `${turn.tid}:answer:table${k}`),
    toggle: (k, rows) => {
      const sourceId = `${turn.tid}:answer:table${k}`;
      partPin.toggle("table", sourceId, () => ({
        sourceKind: "table",
        sourceId,
        question,
        citedSql: turn.citedSql ?? [],
        table: markdownRowsToTablePayload(rows),
        title: trimTitle(question),
      }));
    },
  };
  const narrativeId = `${turn.tid}:narrative`;
  const narrativePinned = partPin.isPinned("narrative", narrativeId);
  const toggleNarrative = () =>
    partPin.toggle("narrative", narrativeId, () => ({
      sourceKind: "narrative",
      sourceId: narrativeId,
      question,
      answer: turn.answer,
      citedSql: turn.citedSql ?? [],
      title: trimTitle(question),
    }));

  return (
    <div className="space-y-3">
      {turn.steps.length > 0 && (
        <div className="space-y-1.5">
          {turn.steps.map((s, i) => (
            <StepRow
              key={`${s.index}-${i}`}
              step={s}
              tid={turn.tid}
              stepIndex={s.index}
              citedSql={turn.citedSql ?? []}
              partPin={partPin}
              onDrill={onDrill}
              sqlOrigem={s.chart ? turn.steps.slice(0, i).reverse().find((x) => x.sql && !x.isError)?.sql : undefined}
            />
          ))}
        </div>
      )}

      {turn.status === "streaming" && !turn.answer && (
        <div className="flex items-center gap-2 text-[13px] text-faint">
          <span className="veta-pulse">●</span>
          <span>{turn.steps.length > 0 ? "Lendo as linhas…" : "Analisando…"}</span>
        </div>
      )}

      {turn.answer && (
        <div className="veta-rise">
          <Prose text={turn.answer} tablePin={answerTablePin} />
          <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1 text-[11px] text-faint">
            <span className="inline-flex items-center gap-1">
              <span className="h-1 w-1 rounded-full bg-emerald-400" />
              Grounded in {turn.citedSql?.length ?? 0} quer{(turn.citedSql?.length ?? 0) === 1 ? "y" : "ies"}
            </span>
            {turn.model && <span className="font-mono">{turn.model}</span>}
            {/* Narrative-only pin — secondary to the whole-turn pin, pins JUST the prose. */}
            <button
              onClick={toggleNarrative}
              // Veta's deck-draft pins are hidden (D46.5): the presentation comes from marked charts.
              hidden
              title={narrativePinned ? "Prose pinned — click to remove" : "Pin just this write-up to the deck draft"}
              aria-pressed={narrativePinned}
              className={`ml-auto inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-[10.5px] font-medium transition-colors ${
                narrativePinned
                  ? "border-accent/30 bg-accent-soft/40 text-accent hover:text-red-300"
                  : "border-edge/70 text-faint hover:border-edge-strong hover:text-muted"
              }`}
            >
              {narrativePinned ? "Prose pinned" : "Pin prose"}
            </button>
            <button
              onClick={onPin}
              // Veta's deck-draft pins are hidden (D46.5): the presentation comes from marked charts.
              hidden
              title={pinned ? "Pinned to your deck draft — click to remove" : "Pin this answer to the deck draft"}
              aria-pressed={pinned}
              className={`group ml-auto inline-flex items-center gap-1 rounded-md border px-2 py-0.5 text-[10.5px] font-medium transition-colors ${
                pinned
                  ? "border-accent/30 bg-accent-soft/50 text-accent hover:border-red-400/40 hover:bg-red-400/5 hover:text-red-300"
                  : "border-edge text-muted hover:border-edge-strong hover:text-foreground"
              }`}
            >
              <svg
                viewBox="0 0 24 24"
                fill={pinned ? "currentColor" : "none"}
                stroke="currentColor"
                strokeWidth="1.7"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="h-3 w-3"
              >
                <path d="M12 17v5M9 10.76V6a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v4.76a2 2 0 0 0 .59 1.42l1.41 1.41A2 2 0 0 1 18 15.83V17H6v-1.17a2 2 0 0 1 .59-1.42L8 13a2 2 0 0 0 .59-1.42Z" />
              </svg>
              {pinned ? (
                <>
                  {/* Pinned — label flips to "Remove" on hover so the toggle reads as reversible. */}
                  <span className="group-hover:hidden">Pinned</span>
                  <span className="hidden group-hover:inline">Remove</span>
                </>
              ) : (
                "Pin to deck"
              )}
            </button>
          </div>
        </div>
      )}

      {turn.error && (
        <div className="rounded-md border border-amber-400/30 bg-amber-400/5 px-3 py-2.5 text-[13px] leading-relaxed text-amber-200/90">
          {turn.error}
        </div>
      )}
    </div>
  );
}

export function Chat({ idleBrief }: { idleBrief?: ReactNode }) {
  const [messages, setMessages] = useState<Turn[]>([]);
  // The transcript as the model should see it on a follow-up (D46): question and written answer pairs.
  const messagesRef = useRef<Turn[]>([]);
  useEffect(() => {
    messagesRef.current = messages;
  }, [messages]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const busyRef = useRef(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  // ── Persistence spine ──────────────────────────────────────────────────────
  // convIdRef: the conversation these turns belong to (null = unsaved/fresh).
  // savedCountRef: how many turns are already persisted (= next seq to write).
  // persistingRef: a write is in flight (serialize — never two at once).
  // epochRef: bumped on every reset/load/delete; an in-flight write captures the
  //   epoch and aborts if it changed, so a write can never land in the wrong
  //   conversation (closes the delete→reset→stale-write race).
  const convIdRef = useRef<string | null>(null);
  const savedCountRef = useRef(0);
  const persistingRef = useRef(false);
  const epochRef = useRef(0);
  const [persistTick, bumpTick] = useReducer((x: number) => x + 1, 0);

  // Which artifacts are pinned to the deck draft — ONE set keyed by
  // `${source_kind}:${source_id}`, covering the whole-turn pin (`turn:<tid>`) and
  // every part pin (chart/table/narrative). Synced on mount + on every deck change.
  const [pinnedKeys, setPinnedKeys] = useState<Set<string>>(new Set());
  // Live projection each chart frame publishes, so a whole-turn pin can capture the
  // DISPLAYED chart of the turn's first framed chart (not first-chart-wins on the raw spec).
  const frameTransformsRef = useRef<Map<string, ArtifactTransform>>(new Map());

  /** Reset to a fresh, unsaved conversation (shared by new-chat + delete-active). */
  const resetToFresh = useCallback(() => {
    epochRef.current += 1;
    convIdRef.current = null;
    savedCountRef.current = 0;
    setMessages([]);
    setInput("");
    window.dispatchEvent(new CustomEvent("veta:active-conversation", { detail: { id: null } }));
  }, []);

  /**
   * Persist a contiguous batch of turns, lazily creating the conversation first.
   * Returns true only when it actually advanced savedCount — best-effort: a failed
   * write (or a stale epoch) returns false without advancing, so the turn retries
   * on the next state change rather than wedging the queue or looping tightly.
   */
  const persistTurns = useCallback(async (turns: Turn[], startSeq: number, epoch: number): Promise<boolean> => {
    try {
      // Lazy-create the conversation on the first turn — chained before any write,
      // never raced (the effect serializes via persistingRef).
      if (convIdRef.current === null) {
        const res = await fetch("/api/conversations", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ title: deriveTitle(turns) }),
        });
        if (!res.ok) return false;
        const data = (await res.json()) as { conversation?: { id?: string } };
        if (epoch !== epochRef.current) return false; // a reset/load happened mid-create — abandon
        const id = data.conversation?.id;
        if (!id) return false;
        convIdRef.current = id;
        window.dispatchEvent(new CustomEvent("veta:active-conversation", { detail: { id } }));
      }
      const convId = convIdRef.current;
      for (let i = 0; i < turns.length; i++) {
        if (epoch !== epochRef.current) return false; // stop writing to a now-stale conversation
        const turn = turns[i];
        const r = await fetch(`/api/conversations/${convId}/messages`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ turnId: turn.tid, seq: startSeq + i, role: turn.role, payload: { v: 1, ...turn } }),
        });
        if (!r.ok) return false; // write failed — retry on the next settle, don't advance
      }
      if (epoch !== epochRef.current) return false;
      savedCountRef.current = startSeq + turns.length;
      window.dispatchEvent(new CustomEvent("veta:history-changed"));
      return true;
    } catch {
      return false; // network error — best-effort; the next settle retries
    }
  }, []);

  /** Restore a saved conversation — rebuild the transcript from stored turns. */
  const restore = useCallback(async (convId: string): Promise<void> => {
    const res = await fetch(`/api/conversations/${convId}`);
    if (!res.ok) return;
    const data = (await res.json()) as { messages?: { payload: StoredTurn | null }[] };
    const restored: Turn[] = (data.messages ?? [])
      .map((m) => m.payload)
      .filter((p): p is StoredTurn => !!p && (p.role === "user" || p.role === "assistant") && typeof p.tid === "string")
      .map((p) => {
        // A turn persisted mid-stream is shown settled on restore.
        const t = p as unknown as Turn;
        return t.role === "assistant" && t.status === "streaming" ? { ...t, status: "done" as const } : t;
      });
    epochRef.current += 1; // invalidate any in-flight write from the prior conversation
    convIdRef.current = convId;
    savedCountRef.current = restored.length;
    setMessages(restored);
    setInput("");
    window.dispatchEvent(new CustomEvent("veta:active-conversation", { detail: { id: convId } }));
  }, []);

  // Pull every pin's natural key so all pin buttons (turn + parts) show the right state.
  const refreshPinned = useCallback(async () => {
    try {
      const res = await fetch("/api/saved-insights");
      if (!res.ok) return;
      const data = (await res.json()) as { savedInsights?: { source_kind: string; source_id: string }[] };
      setPinnedKeys(new Set((data.savedInsights ?? []).map((p) => `${p.source_kind}:${p.source_id}`)));
    } catch {
      /* best-effort — pin state is non-critical */
    }
  }, []);

  // Toggle a part pin (chart/table/narrative) by natural key. Optimistic; the
  // POST body is built lazily by the caller (capturing the clicked card's displayed
  // projection) and the active conversationId is injected here. Mirrors togglePin.
  const togglePart = useCallback(
    async (kind: PartKind, sourceId: string, buildBody: () => Record<string, unknown>, isPinned: boolean) => {
      const key = `${kind}:${sourceId}`;
      setPinnedKeys((prev) => {
        const next = new Set(prev);
        if (isPinned) next.delete(key);
        else next.add(key);
        return next;
      });
      try {
        if (isPinned) {
          await fetch("/api/saved-insights", {
            method: "DELETE",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ sourceKind: kind, sourceId }),
          });
        } else {
          await fetch("/api/saved-insights", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ ...buildBody(), conversationId: convIdRef.current }),
          });
        }
      } catch {
        /* best-effort */
      }
      window.dispatchEvent(new CustomEvent("veta:deck-changed"));
    },
    [],
  );

  // Toggle a finished grounded turn in the deck draft — pin it, or (if already
  // pinned) unpin it right here in the chat, no trip to the tray. Optimistic; the
  // deck-changed event reconciles Chat + the right-rail tray. Unpin is by natural
  // key (source_kind+source_id), so the chat never needs the pin's numeric id.
  const togglePin = useCallback(async (turn: AssistantTurn, question: string, isPinned: boolean) => {
    if (!turn.answer) return;
    const key = `turn:${turn.tid}`;
    setPinnedKeys((prev) => {
      const next = new Set(prev);
      if (isPinned) next.delete(key);
      else next.add(key);
      return next;
    });
    try {
      if (isPinned) {
        await fetch("/api/saved-insights", {
          method: "DELETE",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ sourceKind: "turn", sourceId: turn.tid }),
        });
      } else {
        // Carry the turn's first framed chart into the pin, re-grounded at deck time.
        // Capture its DISPLAYED projection (if the user switched type/sort) from the
        // frame-transform ref — not first-chart-wins on the raw spec.
        const firstChartIdx = turn.steps.findIndex((s) => s.chart);
        let chart: StoredChart | null = null;
        if (firstChartIdx >= 0) {
          const base = turn.steps[firstChartIdx].chart!;
          const t = frameTransformsRef.current.get(`${turn.tid}:step${firstChartIdx}:chart`);
          chart = t ? { ...base, transform: t } : base;
        }
        await fetch("/api/saved-insights", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            sourceKind: "turn",
            sourceId: turn.tid,
            conversationId: convIdRef.current,
            question,
            answer: turn.answer,
            citedSql: turn.citedSql ?? [],
            chart,
            title: question.length > 60 ? `${question.slice(0, 60)}…` : question,
          }),
        });
      }
    } catch {
      /* best-effort */
    }
    window.dispatchEvent(new CustomEvent("veta:deck-changed"));
  }, []);

  const patchLast = useCallback((patch: (a: AssistantTurn) => AssistantTurn) => {
    setMessages((prev) => {
      const copy = [...prev];
      for (let i = copy.length - 1; i >= 0; i--) {
        const turn = copy[i];
        if (turn.role === "assistant") {
          copy[i] = patch(turn);
          break;
        }
      }
      return copy;
    });
  }, []);

  const runQuestion = useCallback(
    async (raw: string) => {
      const question = raw.trim();
      if (!question || busyRef.current) return;
      busyRef.current = true;
      setBusy(true);
      setInput("");
      setMessages((prev) => [
        ...prev,
        { role: "user", tid: newId(), text: question },
        { role: "assistant", tid: newId(), steps: [], status: "streaming" },
      ]);

      try {
        const res = await fetch("/api/chat", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question, history: historico(messagesRef.current) }),
        });
        if (!res.ok || !res.body) {
          const detail = await res.text().catch(() => "");
          throw new Error(`Request failed (${res.status}). ${detail}`.trim());
        }

        const reader = res.body.getReader();
        const decoder = new TextDecoder();
        let buf = "";
        for (;;) {
          const { done, value } = await reader.read();
          if (done) break;
          buf += decoder.decode(value, { stream: true });
          let idx: number;
          while ((idx = buf.indexOf("\n\n")) !== -1) {
            const line = buf.slice(0, idx).trim();
            buf = buf.slice(idx + 2);
            if (!line.startsWith("data:")) continue;
            const evt = JSON.parse(line.slice(5).trim()) as ChatEvent;
            if (evt.type === "step") {
              patchLast((a) => ({ ...a, steps: [...a.steps, evt.step] }));
            } else if (evt.type === "answer") {
              patchLast((a) => ({
                ...a,
                answer: evt.text,
                citedSql: evt.citedSql,
                model: evt.model,
                stepCount: evt.steps,
                status: "done",
              }));
            } else if (evt.type === "error") {
              patchLast((a) => ({ ...a, error: evt.message, status: "error" }));
            }
          }
        }
      } catch (e) {
        patchLast((a) => ({ ...a, error: e instanceof Error ? e.message : String(e), status: "error" }));
      } finally {
        patchLast((a) => (a.status === "streaming" ? { ...a, status: "done" } : a));
        busyRef.current = false;
        setBusy(false);
      }
    },
    [patchLast],
  );

  // Drill-down: a click on a chart element is just the same question, one filter
  // deeper. Compose a natural-language follow-up that names the clicked value and
  // the chart's context, then send it through the SAME grounded loop — the agent
  // writes the filter SQL itself and cites it (we never hand-build a WHERE). The
  // drilled answer lands as a new grounded turn; the transcript is the breadcrumb.
  const handleDrill = useCallback(
    (spec: ChartSpec, label: string) => {
      const q = composeDrillQuestion(spec, label);
      if (q) void runQuestion(q);
    },
    [runQuestion],
  );

  // The insight feed feeds the chat: "Ask Veta →" dispatches this event.
  useEffect(() => {
    const onAsk = (e: Event) => {
      const detail = (e as CustomEvent<{ question?: string }>).detail;
      if (detail?.question) void runQuestion(detail.question);
    };
    window.addEventListener("veta:ask", onAsk);
    return () => window.removeEventListener("veta:ask", onAsk);
  }, [runQuestion]);

  // Persist newly-settled turns. Fires when the stream is idle and the last turn
  // is no longer streaming; serialized via persistingRef; bumpTick re-checks for
  // anything that arrived during a write.
  useEffect(() => {
    if (busy || persistingRef.current) return;
    if (savedCountRef.current >= messages.length) return;
    const last = messages[messages.length - 1];
    if (last && last.role === "assistant" && last.status === "streaming") return;
    const epoch = epochRef.current;
    const startSeq = savedCountRef.current;
    const toSave = messages.slice(startSeq);
    persistingRef.current = true;
    void persistTurns(toSave, startSeq, epoch)
      .then((advanced) => {
        persistingRef.current = false;
        if (advanced) bumpTick(); // re-run only after real progress — never a tight failure loop
      })
      .catch(() => {
        persistingRef.current = false;
      });
  }, [busy, messages, persistTick, persistTurns]);

  // Broadcast busy state so the sidebar can disable History while a stream runs.
  useEffect(() => {
    window.dispatchEvent(new CustomEvent("veta:chat-busy", { detail: { busy } }));
  }, [busy]);

  // Keep pinned-turn state in sync — on mount and whenever the deck changes
  // (a pin added here, or a pin removed from the tray).
  useEffect(() => {
    let alive = true;
    void (async () => {
      try {
        const res = await fetch("/api/saved-insights");
        if (!res.ok || !alive) return;
        const data = (await res.json()) as { savedInsights?: { source_kind: string; source_id: string }[] };
        if (alive) setPinnedKeys(new Set((data.savedInsights ?? []).map((p) => `${p.source_kind}:${p.source_id}`)));
      } catch {
        /* best-effort */
      }
    })();
    const onDeck = () => void refreshPinned();
    window.addEventListener("veta:deck-changed", onDeck);
    return () => {
      alive = false;
      window.removeEventListener("veta:deck-changed", onDeck);
    };
  }, [refreshPinned]);

  // History controls: new chat, load a saved conversation, react to a delete.
  useEffect(() => {
    const onNew = () => {
      if (busyRef.current) return;
      resetToFresh();
    };
    const onLoad = (e: Event) => {
      if (busyRef.current) return; // don't swap conversations mid-stream
      const id = (e as CustomEvent<{ id?: string }>).detail?.id;
      if (id && id !== convIdRef.current) void restore(id);
    };
    const onDeleted = (e: Event) => {
      const id = (e as CustomEvent<{ id?: string }>).detail?.id;
      if (id && id === convIdRef.current) resetToFresh(); // the open thread was deleted
    };
    window.addEventListener("veta:new-chat", onNew);
    window.addEventListener("veta:load-conversation", onLoad);
    window.addEventListener("veta:conversation-deleted", onDeleted);
    return () => {
      window.removeEventListener("veta:new-chat", onNew);
      window.removeEventListener("veta:load-conversation", onLoad);
      window.removeEventListener("veta:conversation-deleted", onDeleted);
    };
  }, [resetToFresh, restore]);

  // Deep-link: ?conversation=<id> on the authed dashboard restores that thread,
  // then strips the param so a refresh/share doesn't keep re-restoring. Runs once.
  useEffect(() => {
    if (typeof window === "undefined") return;
    const url = new URL(window.location.href);
    const cid = url.searchParams.get("conversation");
    if (!cid) return;
    void restore(cid);
    url.searchParams.delete("conversation");
    window.history.replaceState({}, "", `${url.pathname}${url.search}${url.hash}`);
  }, [restore]);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  const empty = messages.length === 0;

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div ref={scrollRef} className="min-h-0 flex-1 overflow-y-auto overscroll-contain">
        {empty ? (
          <div className="flex h-full flex-col gap-5 px-0.5 py-0.5">
            {idleBrief ?? (
              <div className="mt-6">
                <h1 className="text-2xl font-semibold tracking-tight text-foreground">Pergunte sobre o churn da RavenStack.</h1>
                <p className="mt-2 max-w-md text-[14px] leading-relaxed text-muted">
                  Veta answers in plain English and shows the exact SQL behind every number. The warehouse is read-only —
                  it can read every story and change nothing.
                </p>
              </div>
            )}
            <div className="flex flex-wrap items-center gap-2">
              <span className="text-[11px] font-medium uppercase tracking-wider text-faint">Ou comece por</span>
              {STARTERS.map((s) => (
                <button
                  key={s.chip}
                  onClick={() => void runQuestion(s.question)}
                  className="rounded-full border border-edge bg-panel px-3.5 py-1.5 text-[12.5px] text-muted transition-colors hover:border-edge-strong hover:text-foreground"
                >
                  {s.chip}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="space-y-7 pb-4">
            {messages.map((turn, i) => {
              if (turn.role === "user") {
                // A subtle left-accent card so the eye catches where each question begins
                // when scrolling a long transcript (the prompts no longer blend into the prose).
                return (
                  <div key={i} className="space-y-1 rounded-r-lg border-l-2 border-accent/50 bg-panel/40 py-2 pl-3 pr-3">
                    <div className="text-[10px] font-medium uppercase tracking-wider text-faint">You asked</div>
                    <p className="text-[15px] font-medium leading-snug text-foreground">{turn.text}</p>
                  </div>
                );
              }
              const prev = messages[i - 1];
              const question = prev && prev.role === "user" ? prev.text : "";
              const isPinned = pinnedKeys.has(`turn:${turn.tid}`);
              const partPin: PartPin = {
                question,
                isPinned: (kind, sourceId) => pinnedKeys.has(`${kind}:${sourceId}`),
                toggle: (kind, sourceId, buildBody) =>
                  void togglePart(kind, sourceId, buildBody, pinnedKeys.has(`${kind}:${sourceId}`)),
                registerTransform: (sourceId, t) => frameTransformsRef.current.set(sourceId, t),
              };
              return (
                <AssistantBlock
                  key={i}
                  turn={turn}
                  question={question}
                  pinned={isPinned}
                  onPin={() => void togglePin(turn, question, isPinned)}
                  partPin={partPin}
                  onDrill={handleDrill}
                />
              );
            })}
          </div>
        )}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          void runQuestion(input);
        }}
        className="mt-4 shrink-0"
      >
        <div className="flex items-center gap-2 rounded-xl border border-edge bg-panel px-3 py-2 focus-within:border-edge-strong">
          <input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Pergunte sobre churn, contas, assinaturas, tickets, uso…"
            disabled={busy}
            className="flex-1 bg-transparent text-[14px] text-foreground placeholder:text-faint focus:outline-none disabled:opacity-60"
          />
          <button
            type="submit"
            disabled={busy || input.trim().length === 0}
            className="rounded-lg bg-accent px-3.5 py-1.5 text-[13px] font-medium text-black transition-opacity hover:opacity-90 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {busy ? "…" : "Perguntar"}
          </button>
        </div>
        <p className="mt-1.5 px-1 text-[11px] text-faint">Toda resposta cita o SQL que rodou. Nenhum número aparece sem consulta.</p>
      </form>
    </div>
  );
}

/** Earlier question/answer pairs of this conversation, for the analyst's context on a follow-up. */
function historico(turns: Turn[]): { question: string; answer: string }[] {
  const pares: { question: string; answer: string }[] = [];
  for (let i = 0; i < turns.length - 1; i++) {
    const u = turns[i];
    const a = turns[i + 1];
    if (u.role === "user" && a.role === "assistant" && a.answer) pares.push({ question: u.text, answer: a.answer });
  }
  return pares.slice(-6);
}
