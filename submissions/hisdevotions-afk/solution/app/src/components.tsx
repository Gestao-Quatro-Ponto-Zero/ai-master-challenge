import { useRef, useState, type CSSProperties, type MouseEvent, type ReactNode } from "react";
import { useApp } from "./data";
import { link } from "./router";
import { int, money, pct, sum } from "./format";
import type { Bucket, CurvePoint, Meta, OpenDeal, Reason } from "./types";

export const BUCKETS: Record<Bucket, { label: string; hint: string }> = {
  fechar: { label: "Fechar", hint: "Na janela em que os deals fecham" },
  decidir: { label: "Decidir", hint: "Parado além de qualquer ciclo já visto" },
  avancar: { label: "Avançar", hint: "Ainda cedo para fechar" },
  prospectar: { label: "Prospectar", hint: "Ainda não engajado" },
};

export const BUCKET_ORDER: Bucket[] = ["fechar", "avancar", "prospectar", "decidir"];

export function BucketTag({ bucket }: { bucket: Bucket }) {
  return <span className={`tag tag-${bucket}`}>{BUCKETS[bucket].label}</span>;
}

export const TIER_LABEL = { alta: "Alta", media: "Média", baixa: "Baixa" } as const;

/** O score é a chance de ganhar em 30 dias, em %. Nesta base o máximo possível
    é meta.peak_score (~31%), então o anel enche contra esse máximo, não contra
    100, e a faixa (alta/média/baixa) diz se o número é bom: um 28% é dos
    melhores deals possíveis, não uma nota baixa. */
export function Score({ deal, size = "sm", showTier = false }: { deal: OpenDeal; size?: "sm" | "lg"; showTier?: boolean }) {
  const { model } = useApp();
  if (deal.score == null)
    return (
      <span className={`score score-${size} score-none on-${deal.bucket}`} title="Sem score: deal parado além do maior ciclo, ou ainda em prospecção">
        —
      </span>
    );
  const peak = model.meta.peak_score;
  const fill = Math.min(100, (deal.score / peak) * 100);
  const tier = deal.tier ? TIER_LABEL[deal.tier] : "";
  const ring = (
    <span
      className={`score score-${size} on-${deal.bucket}`}
      style={{ "--pct": fill } as CSSProperties}
      title={`Chance de ganhar em 30 dias: ${deal.score}% (${tier.toLowerCase()}; o melhor deal possível nesta base tem ${peak}%)`}
    >
      {deal.score}<small>%</small>
    </span>
  );
  if (!showTier || !deal.tier) return ring;
  return (
    <span className="score-wrap">
      {ring}
      <span className={`tier tier-${deal.tier}`}>{tier}</span>
    </span>
  );
}

/** Sem conta, o produto vira o nome e a falta de conta é uma tag discreta:
    é higiene de cadastro, não a coisa mais importante da linha. */
export function DealName({ deal }: { deal: { account: string | null; product: string } }) {
  if (!deal.account)
    return (
      <>
        <span>{deal.product}</span>{" "}
        <span className="tag-noacc">sem conta</span>
      </>
    );
  return (
    <>
      <span>{deal.account}</span>
      <span className="deal-product">{deal.product}</span>
    </>
  );
}

/** Composição do pipeline declarado (US$ de lista) pelas quatro filas, na
    mesma cor e ordem do Forecast: dá para comparar grupos linha a linha. */
export function QueueBar({ deals, label }: { deals: OpenDeal[]; label: string }) {
  const total = deals.reduce((s, d) => s + d.price, 0);
  if (total === 0) return <span className="muted">sem pipeline aberto</span>;
  const parts = BUCKET_ORDER.map((b) => ({ b, v: deals.filter((d) => d.bucket === b).reduce((s, d) => s + d.price, 0) })).filter((x) => x.v > 0);
  const desc = parts.map((x) => `${BUCKETS[x.b].label} ${pct(x.v / total)}`).join(", ");
  return (
    <span className="queue-bar" role="img" aria-label={`${label}: ${desc}`} title={desc}>
      {parts.map((x) => (
        <span key={x.b} className={`stack-${x.b}`} style={{ flexGrow: x.v }} />
      ))}
    </span>
  );
}

export function QueueLegend() {
  return (
    <ul className="queue-legend" aria-hidden="true">
      {BUCKET_ORDER.map((b) => (
        <li key={b} className={`legend-${b}`}>{BUCKETS[b].label}</li>
      ))}
    </ul>
  );
}

// ─── régua de idade: onde o deal está no ciclo histórico ────────────────────

export function AgeRuler({ age, meta, size = "sm" }: { age: number | null; meta: Meta; size?: "sm" | "lg" }) {
  const overflow = 40; // dias desenhados além do maior ciclo, a zona "sem histórico"
  const span = meta.max_cycle + overflow;
  const x = (a: number) => (Math.min(a, span - 2) / span) * 100;
  const h = size === "lg" ? 14 : 8;
  const label = age == null ? "não iniciado" : `${age} dias`;
  return (
    <div className={`ruler ruler-${size}`} aria-label={age == null ? "Deal não iniciado" : `Deal com ${age} dias em negociação`}>
      <svg viewBox={`0 0 100 ${h}`} preserveAspectRatio="none" aria-hidden="true">
        <rect x="0" y="0" width={x(meta.window_start)} height={h} className="z-avancar" />
        <rect x={x(meta.window_start)} y="0" width={x(meta.max_cycle) - x(meta.window_start)} height={h} className="z-fechar" />
        <rect x={x(meta.max_cycle)} y="0" width={100 - x(meta.max_cycle)} height={h} className="z-decidir" />
      </svg>
      {age != null && <span className="ruler-mark" style={{ left: `${x(age)}%` }} />}
      {size === "lg" ? (
        <div className="ruler-ticks">
          <span style={{ left: 0 }}>0</span>
          <span style={{ left: `${x(meta.window_start)}%` }}>{meta.window_start} dias: a janela abre</span>
          <span style={{ left: `${x(meta.max_cycle)}%` }}>{meta.max_cycle} dias: maior ciclo já visto</span>
        </div>
      ) : (
        <span className="ruler-label">{label}</span>
      )}
    </div>
  );
}

// ─── curva histórica: chance de ganhar e de fechar logo, por idade ──────────

const MIN_N = 30; // abaixo disso a curva é ruído de amostra pequena: não desenha

export function CurveChart({ curve, meta, age }: { curve: CurvePoint[]; meta: Meta; age?: number | null }) {
  const W = 900, H = 280, L = 44, B = 28, T = 10, R = 28;
  const x = (a: number) => L + (a / meta.max_cycle) * (W - L - R);
  const y = (p: number) => T + (1 - p) * (H - T - B);
  const reliable = curve.filter((c) => c.n >= MIN_N);
  const line = (f: (c: CurvePoint) => number) =>
    reliable.map((c, i) => `${i ? "L" : "M"}${x(c.age).toFixed(1)},${y(f(c)).toFixed(1)}`).join("");
  const firstAge = reliable[0]?.age ?? 0;
  const lastAge = reliable.at(-1)?.age ?? 0;
  const closeArea = `${line((c) => c.win_soon)}L${x(lastAge)},${y(0)}L${x(0)},${y(0)}Z`;
  const dealAge = age != null && age < meta.max_cycle ? age : null;

  const svgRef = useRef<SVGSVGElement>(null);
  const [hoverAge, setHoverAge] = useState<number | null>(null);
  // Passa o mouse pra ver qualquer idade, não só a do deal aberto: o gráfico
  // vira ferramenta de consulta, não só uma foto de UM ponto.
  const onMove = (e: MouseEvent<SVGSVGElement>) => {
    const rect = svgRef.current?.getBoundingClientRect();
    if (!rect || rect.width === 0) return;
    const internalX = ((e.clientX - rect.left) / rect.width) * W;
    const a = Math.round(((internalX - L) / (W - L - R)) * meta.max_cycle);
    setHoverAge(Math.min(Math.max(a, firstAge), lastAge));
  };
  const shownAge = hoverAge ?? dealAge;
  const point = shownAge != null ? curve[shownAge] : null;

  return (
    <figure className="curve">
      <svg
        ref={svgRef} viewBox={`0 0 ${W} ${H}`} role="img" aria-label="Chance de ganhar (sem prazo e em 30 dias) conforme a idade do deal; passe o mouse para consultar qualquer idade"
        onMouseMove={onMove} onMouseLeave={() => setHoverAge(null)}
      >
        <rect x={x(meta.window_start)} y={T} width={x(meta.max_cycle) - x(meta.window_start)} height={H - T - B} className="z-fechar" />
        {[0, 0.25, 0.5, 0.75, 1].map((p) => (
          <g key={p}>
            <line x1={L} x2={W - R} y1={y(p)} y2={y(p)} className="grid" />
            <text x={L - 6} y={y(p) + 4} textAnchor="end" className="axis">{pct(p)}</text>
          </g>
        ))}
        {[0, 30, 60, 90, 120, meta.max_cycle].map((a) => (
          <text key={a} x={x(a)} y={H - 8} textAnchor="middle" className="axis">{a}d</text>
        ))}
        <path d={closeArea} className="area-close" />
        <path d={line((c) => c.win)} className="line-win" />
        <line x1={L} x2={W - R} y1={y(meta.base_rate)} y2={y(meta.base_rate)} className="line-base" />
        {point && (
          <g className={hoverAge != null ? "curve-hover" : "curve-marker"}>
            <line x1={x(point.age)} x2={x(point.age)} y1={T} y2={H - B} className="line-now" />
            <circle cx={x(point.age)} cy={y(point.win)} r="5" className="dot-now" />
          </g>
        )}
      </svg>
      {point && (
        <div className="curve-tooltip" style={{ left: `${(x(point.age) / W) * 100}%` }}>
          <strong>{point.age} dias</strong>
          <span>Ganhar (sem prazo): {pct(point.win)}</span>
          <span>Ganhar em 30d: {pct(point.win_soon)}</span>
        </div>
      )}
      <figcaption>
        <span className="key key-win">Chance de ganhar, para quem chegou a essa idade</span>
        <span className="key key-close">Chance de ganhar nos próximos 30 dias (o score)</span>
        <span className="key key-base">Média geral ({pct(meta.base_rate)})</span>
      </figcaption>
    </figure>
  );
}

/** Um traço, um peso: o mesmo sistema de ícone para toda razão do score. */
function ReasonIcon({ kind }: { kind: Reason["kind"] }) {
  const stroke = { fill: "none", stroke: "currentColor", strokeWidth: 1.6, strokeLinecap: "round" as const };
  if (kind === "+") return <svg viewBox="0 0 14 14" width="14" height="14" aria-hidden="true"><line x1="7" y1="2.5" x2="7" y2="11.5" {...stroke} /><line x1="2.5" y1="7" x2="11.5" y2="7" {...stroke} /></svg>;
  if (kind === "-") return <svg viewBox="0 0 14 14" width="14" height="14" aria-hidden="true"><line x1="2.5" y1="7" x2="11.5" y2="7" {...stroke} /></svg>;
  if (kind === "!") return <svg viewBox="0 0 14 14" width="14" height="14" aria-hidden="true"><line x1="7" y1="3" x2="7" y2="8.2" {...stroke} /><circle cx="7" cy="10.8" r="0.9" fill="currentColor" stroke="none" /></svg>;
  return <svg viewBox="0 0 14 14" width="14" height="14" aria-hidden="true"><circle cx="7" cy="7" r="5.2" {...stroke} /><line x1="7" y1="6.3" x2="7" y2="9.8" {...stroke} /><circle cx="7" cy="4.1" r="0.9" fill="currentColor" stroke="none" /></svg>;
}

const reasonClass = (kind: Reason["kind"]) => (kind === "+" ? "up" : kind === "-" ? "down" : kind === "!" ? "warn" : "info");

/** O motivo que mais pesa na decisão: o primeiro sinal (+/-) da lista, pulando
    os informativos ("i"/"!"). A ordem já vem do motor — idade primeiro,
    depois comparações — então é sempre o mesmo motivo que justifica o score. */
function topReason(reasons: Reason[]): Reason {
  return reasons.find((r) => r.kind === "+" || r.kind === "-") ?? reasons[0];
}

export function ReasonList({ reasons }: { reasons: Reason[] }) {
  const top = topReason(reasons);
  return (
    <ul className="reasons">
      {reasons.map((r) => (
        <li key={r.text} className={`reason reason-${reasonClass(r.kind)}${r === top ? " reason-primary" : ""}`}>
          <span className="reason-icon"><ReasonIcon kind={r.kind} /></span>
          {r.text}
        </li>
      ))}
    </ul>
  );
}

export function DecisionButtons({ deal }: { deal: OpenDeal }) {
  const { decisions, decide } = useApp();
  const current = decisions[deal.id];
  const [note, setNote] = useState(current?.note ?? "");
  if (current)
    return (
      <div className="decision done">
        <p>
          Marcado como {current.kind}.
          <button className="btn-link" onClick={() => decide(deal.id, null)}>Desfazer</button>
        </p>
        <input
          type="text" className="decision-note" placeholder="Nota (opcional): por que essa decisão?"
          value={note} onChange={(e) => setNote(e.target.value)}
          onBlur={() => note !== (current.note ?? "") && decide(deal.id, current.kind, note)}
        />
      </div>
    );
  // O botão sugerido (ver suggest_decide no motor) vem destacado; o outro
  // continua um clique de distância, a decisão final é sempre do vendedor.
  const closeSuggested = deal.suggested_action === "encerrar";
  return (
    <div className="decision">
      <button className={closeSuggested ? "btn btn-quiet" : "btn btn-decidir"} onClick={() => decide(deal.id, "requalificado")}>Requalifiquei</button>
      <button className={closeSuggested ? "btn btn-decidir" : "btn btn-quiet"} onClick={() => decide(deal.id, "encerrado")}>Encerrar como perdido</button>
    </div>
  );
}

/** Linha compacta de deal usada em Meu Dia e Contas: o motivo que mais pesa
    vai junto do dado, não só na ficha do deal — decidir não deveria exigir
    abrir outra tela. */
export function DealRow({ deal }: { deal: OpenDeal }) {
  const { model } = useApp();
  const top = topReason(deal.reasons);
  return (
    <li className="deal-row">
      <Score deal={deal} />
      <div className="deal-row-main">
        <a className="deal-row-title" href={link("deal", deal.id)}><DealName deal={deal} /></a>
        <div className="deal-row-sub">
          <span>{money(deal.price)}</span>
          <span>{deal.agent}</span>
        </div>
        <p className={`reason reason-compact reason-${reasonClass(top.kind)}`} title={top.text}>
          <span className="reason-icon"><ReasonIcon kind={top.kind} /></span>
          <span className="reason-text">{top.text}</span>
        </p>
      </div>
      <AgeRuler age={deal.age} meta={model.meta} />
    </li>
  );
}

export function Empty({ children }: { children: ReactNode }) {
  return <p className="empty">{children}</p>;
}

// ─── tabela por grupo (manager, região, vendedor): a mesma na Overview e no Forecast ─

export interface GroupRow {
  name: string;
  ds: OpenDeal[];
  region: string;
  declared: number;
  stalled: number;
  share: number;
  soon: number;
  expected: number;
  window: number;
  /** deals vivos em negociação (Fechar + Avançar); 0 = funil travado */
  live: number;
}

/** Agrupa os deals abertos e já deixa na ordem de "precisa de atenção":
    primeiro quem não tem nada vivo em negociação, depois o maior % do valor parado. */
export function groupDeals(deals: OpenDeal[], key: (d: OpenDeal) => string): GroupRow[] {
  const map = new Map<string, OpenDeal[]>();
  for (const d of deals) map.set(key(d), [...(map.get(key(d)) ?? []), d]);
  return [...map.entries()]
    .map(([name, ds]) => {
      const declared = sum(ds, (d) => d.price);
      const stalled = sum(ds.filter((d) => d.bucket === "decidir"), (d) => d.price);
      return {
        name, ds, region: ds[0].region, declared, stalled,
        share: declared ? stalled / declared : 0,
        soon: sum(ds, (d) => d.ev_soon),
        expected: sum(ds, (d) => d.ev),
        window: ds.filter((d) => d.bucket === "fechar").length,
        live: ds.filter((d) => d.bucket === "fechar" || d.bucket === "avancar").length,
      };
    })
    .sort(byAttention);
}

const byAttention = (a: GroupRow, b: GroupRow) => (a.live === 0 ? 0 : 1) - (b.live === 0 ? 0 : 1) || b.share - a.share;

type GroupSort = "atencao" | "name" | "declared" | "stalled" | "share" | "window" | "soon" | "expected";

const GROUP_COLUMNS: [GroupSort, string][] = [
  ["declared", "Declarado"],
  ["stalled", "Valor parado"],
  ["share", "% do valor parado"],
  ["window", "Deals na janela"],
  ["soon", "Receita esperada (30d)"],
  ["expected", "Esperado (sem prazo)"],
];

export function GroupTable({ rows, label, showRegion, onSelect, selectHint }: {
  rows: GroupRow[];
  label: string;
  showRegion?: boolean;
  onSelect: (row: GroupRow) => void;
  selectHint: string;
}) {
  const [sort, setSort] = useState<{ key: GroupSort; dir: 1 | -1 }>({ key: "atencao", dir: -1 });
  const value = (r: GroupRow, k: GroupSort) => (k === "name" ? r.name : k === "atencao" ? 0 : r[k]);
  const sorted =
    sort.key === "atencao"
      ? rows.slice().sort(byAttention)
      : rows.slice().sort((a, b) => {
          const x = value(a, sort.key), y = value(b, sort.key);
          return (typeof x === "string" ? x.localeCompare(y as string) : (x as number) - (y as number)) * sort.dir;
        });
  const head = (key: GroupSort, text: string, className?: string) => (
    <th scope="col" className={className} aria-sort={sort.key === key ? (sort.dir === 1 ? "ascending" : "descending") : undefined}>
      <button onClick={() => setSort({ key, dir: sort.key === key ? (-sort.dir as 1 | -1) : key === "name" ? 1 : -1 })}>{text}</button>
    </th>
  );

  return (
    <>
      <QueueLegend />
      <div className="table-wrap">
        <table className="deals group-table">
          <thead>
            <tr>
              {head("name", label)}
              <th scope="col">Composição do valor aberto</th>
              {GROUP_COLUMNS.map(([k, t]) => head(k, t, "num"))}
            </tr>
          </thead>
          <tbody>
            {sorted.map((r) => (
              <tr key={r.name} className={r.live === 0 ? "row-stuck" : undefined}>
                <th scope="row">
                  <button className="row-link" onClick={() => onSelect(r)}>{r.name}</button>
                  {r.live === 0 && <span className="tag-alert">nada na janela de fechamento</span>}
                  {showRegion && <span className="muted block">{r.region}</span>}
                </th>
                <td><QueueBar deals={r.ds} label={r.name} /></td>
                <td className="num">{money(r.declared)}</td>
                <td className="num">{money(r.stalled)}</td>
                <td className="num">{pct(r.share)}</td>
                <td className="num">{int(r.window)}</td>
                <td className="num">{money(r.soon)}</td>
                <td className="num">{money(r.expected)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="queue-note">
        {sort.key === "atencao" ? "Primeiro quem não tem nada na janela de fechamento, depois o maior % do valor parado. " : ""}
        Clique num cabeçalho para ordenar e num nome para {selectHint}.
      </p>
    </>
  );
}
