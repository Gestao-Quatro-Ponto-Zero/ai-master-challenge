import { useMemo, useState } from "react";
import {
  Bar, BarChart, CartesianGrid, Cell, LabelList, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis,
} from "recharts";
import { dec, int, mes, nome, pct, pval, usd } from "./format";
import type { Palette } from "./theme";

type Row = Record<string, number | string | null>;

/* ---------------------------------------------------------------- tooltip padrão */
export function Tip({ active, payload, label, fmt, labelFmt }: {
  active?: boolean; payload?: { name: string; value: number; color: string }[]; label?: string;
  fmt: (v: number) => string; labelFmt?: (l: string) => string;
}) {
  if (!active || !payload?.length) return null;
  return (
    <div className="tt">
      <b>{labelFmt ? labelFmt(String(label)) : label}</b>
      {payload.map((p) => (
        <div className="row" key={p.name}>
          <span><i style={{ display: "inline-block", width: 8, height: 8, borderRadius: 2, background: p.color, marginRight: 6 }} />{p.name}</span>
          <span>{fmt(p.value)}</span>
        </div>
      ))}
    </div>
  );
}

const axisProps = (pal: Palette) => ({
  stroke: pal["--axis"], tick: { fill: pal["--muted"], fontSize: 11 }, tickLine: false,
});

/* ---------------------------------------------------------------- barras mensais (1 série) */
export function MonthlyBars({ data, k, nomeSerie, pal, fmt, height = 240, marca }: {
  data: Row[]; k: string; nomeSerie: string; pal: Palette; fmt: (v: number) => string; height?: number;
  marca?: { mes: string; texto: string };
}) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <BarChart data={data} margin={{ top: 18, right: 8, left: 0, bottom: 0 }} barCategoryGap={2}>
        <CartesianGrid vertical={false} stroke={pal["--grid"]} />
        <XAxis dataKey="mes" tickFormatter={mes} {...axisProps(pal)} interval="preserveStartEnd" minTickGap={18} />
        <YAxis {...axisProps(pal)} axisLine={false} width={48} tickFormatter={(v) => fmt(v)} />
        <Tooltip cursor={{ fill: pal["--grid"], opacity: 0.5 }} content={<Tip fmt={fmt} labelFmt={mes} />} />
        {marca && <ReferenceLine x={marca.mes} stroke={pal["--muted"]} label={{ value: marca.texto, position: "insideTopRight", fill: pal["--ink-2"], fontSize: 11 }} />}
        <Bar dataKey={k} name={nomeSerie} fill={pal["--s1"]} radius={[4, 4, 0, 0]} isAnimationActive={false} />
      </BarChart>
    </ResponsiveContainer>
  );
}

/* ---------------------------------------------------------------- linhas mensais (1–3 séries, mesma unidade) */
export function MonthlyLines({ data, series, pal, fmt, height = 240, marca }: {
  data: Row[]; series: { k: string; nome: string; cor: keyof Palette }[]; pal: Palette; fmt: (v: number) => string;
  height?: number; marca?: { mes: string; texto: string };
}) {
  const last = data[data.length - 1];
  return (
    <>
      {series.length > 1 && (
        <div className="legend">
          {series.map((s) => (
            <span key={s.k}><i style={{ background: pal[s.cor] }} />{s.nome}</span>
          ))}
        </div>
      )}
      <ResponsiveContainer width="100%" height={height}>
        <LineChart data={data} margin={{ top: 18, right: 56, left: 0, bottom: 0 }}>
          <CartesianGrid vertical={false} stroke={pal["--grid"]} />
          <XAxis dataKey="mes" tickFormatter={mes} {...axisProps(pal)} interval="preserveStartEnd" minTickGap={18} />
          <YAxis {...axisProps(pal)} axisLine={false} width={48} tickFormatter={(v) => fmt(v)} />
          <Tooltip cursor={{ stroke: pal["--axis"] }} content={<Tip fmt={fmt} labelFmt={mes} />} />
          {marca && <ReferenceLine x={marca.mes} stroke={pal["--muted"]} label={{ value: marca.texto, position: "insideTopLeft", fill: pal["--ink-2"], fontSize: 11 }} />}
          {series.map((s) => (
            <Line key={s.k} type="monotone" dataKey={s.k} name={s.nome} stroke={pal[s.cor]} strokeWidth={2}
              dot={false} activeDot={{ r: 4, stroke: pal["--surface"], strokeWidth: 2 }} isAnimationActive={false}>
              <LabelList dataKey={s.k} content={({ x, y, index }) =>
                index === data.length - 1 ? (
                  <text x={Number(x) + 6} y={Number(y) + 4} fontSize={11} fill={pal["--ink-2"]}>{fmt(Number(last[s.k]))}</text>
                ) : null} />
            </Line>
          ))}
        </LineChart>
      </ResponsiveContainer>
    </>
  );
}

/* ---------------------------------------------------------------- satisfação */
export function SatBars({ data, pal }: { data: { nota: string; tickets: number }[]; pal: Palette }) {
  const total = data.reduce((a, b) => a + b.tickets, 0);
  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={data} margin={{ top: 22, right: 8, left: 0, bottom: 0 }} barCategoryGap="22%">
        <CartesianGrid vertical={false} stroke={pal["--grid"]} />
        <XAxis dataKey="nota" {...axisProps(pal)} />
        <YAxis {...axisProps(pal)} axisLine={false} width={40} />
        <Tooltip cursor={{ fill: pal["--grid"], opacity: 0.5 }}
          content={<Tip fmt={(v) => `${int(v)} (${pct(v / total)})`} labelFmt={(l) => (l === "Sem nota" ? l : `Nota ${l}`)} />} />
        <Bar dataKey="tickets" name="Tickets" radius={[4, 4, 0, 0]} isAnimationActive={false}>
          {data.map((d) => <Cell key={d.nota} fill={d.nota === "Sem nota" ? pal["--s2"] : pal["--s1"]} />)}
          <LabelList dataKey="tickets" position="top" fill={pal["--ink-2"]} fontSize={11} formatter={(v: number) => int(v)} />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

/* ---------------------------------------------------------------- força das correlações */
export type Corr = {
  alvo: string; categoria: string; variavel: string; forca: number; p: number; q: number;
  media_churn?: number; media_retida?: number; niveis?: { nivel: string; taxa: number; n: number }[];
};

export function leitura(c: Corr, rotulo: [string, string]) {
  if (c.niveis) {
    const s = [...c.niveis].sort((a, b) => b.taxa - a.taxa);
    const hi = s[0], lo = s[s.length - 1];
    return `maior: ${hi.nivel} ${pct(hi.taxa, 0)} (n=${int(hi.n)}) · menor: ${lo.nivel} ${pct(lo.taxa, 0)} (n=${int(lo.n)})`;
  }
  const a = c.media_churn ?? 0, b = c.media_retida ?? 0;
  const d = b ? a / b - 1 : null;
  const f = (v: number) => (Math.abs(v) < 1 ? dec(v, 3) : dec(v, Math.abs(v) >= 100 ? 0 : 2));
  const dd = d == null ? "" : Math.abs(d) < 0.005 ? " (±0%)" : ` (${d > 0 ? "+" : ""}${pct(d, 0)})`;
  return `${rotulo[0]} ${f(a)} × ${rotulo[1]} ${f(b)}${dd}`;
}

export function ForcaBars({ rows, pal }: { rows: Corr[]; pal: Palette }) {
  const narrow = typeof window !== "undefined" && window.innerWidth < 640;
  const data = rows.map((r) => ({ ...r, label: nome(r.variavel) }));
  const h = Math.max(160, data.length * 26 + 40);
  return (
    <ResponsiveContainer width="100%" height={h}>
      <BarChart data={data} layout="vertical" margin={{ top: 18, right: 40, left: 8, bottom: 0 }} barCategoryGap={4}>
        <CartesianGrid horizontal={false} stroke={pal["--grid"]} />
        <XAxis type="number" domain={[0, 0.4]} ticks={[0, 0.1, 0.2, 0.3, 0.4]} tickFormatter={(v) => dec(v, 1)} {...axisProps(pal)} />
        <YAxis type="category" dataKey="label" width={narrow ? 118 : 170} {...axisProps(pal)} axisLine={false} tick={{ fill: pal["--ink-2"], fontSize: 12 }} />
        <ReferenceLine x={0.1} stroke={pal["--muted"]} label={narrow ? undefined : { value: "fraca", position: "top", fill: pal["--muted"], fontSize: 11 }} />
        <ReferenceLine x={0.2} stroke={pal["--muted"]} label={narrow ? undefined : { value: "moderada", position: "top", fill: pal["--muted"], fontSize: 11 }} />
        <Tooltip cursor={{ fill: pal["--grid"], opacity: 0.5 }} content={({ active, payload }) => {
          if (!active || !payload?.length) return null;
          const r = payload[0].payload as Corr & { label: string };
          return (
            <div className="tt">
              <b>{r.label}</b>
              <div className="row"><span>Força</span><span>{dec(r.forca, 2)}</span></div>
              <div className="row"><span>p bruto</span><span>{pval(r.p)}</span></div>
              <div className="row"><span>q (corrigido)</span><span>{pval(r.q)}</span></div>
            </div>
          );
        }} />
        <Bar dataKey="forca" name="Força" radius={[0, 4, 4, 0]} isAnimationActive={false}>
          {data.map((d) => <Cell key={d.variavel} fill={d.q < 0.05 ? pal["--s2"] : pal["--s1"]} />)}
          <LabelList dataKey="forca" position="right" fill={pal["--ink-2"]} fontSize={11} formatter={(v: number) => dec(v, 2)} />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

/* ---------------------------------------------------------------- taxa de churn por segmento com IC 95% */
export function SegmentCI({ itens, media, pal }: {
  itens: { nivel: string; n: number; churn: number; taxa: number; ic: [number, number]; mrr_ativo: number }[];
  media: number; pal: Palette;
}) {
  const max = 0.6;
  const x = (v: number) => `${(v / max) * 100}%`;
  const sorted = [...itens].sort((a, b) => b.taxa - a.taxa);
  return (
    <div role="table" aria-label="Taxa de churn por segmento com intervalo de confiança de 95%">
      <div style={{ display: "grid", gridTemplateColumns: "minmax(90px,140px) 1fr 92px", gap: 8, fontSize: 12, color: pal["--muted"], marginBottom: 6 }}>
        <span>Segmento</span>
        <span style={{ position: "relative" }}>
          {[0, 0.2, 0.4, 0.6].map((t) => (
            <span key={t} style={{ position: "absolute", left: x(t), transform: t ? "translateX(-50%)" : undefined }}>{pct(t, 0)}</span>
          ))}
        </span>
        <span style={{ textAlign: "right" }}>Churn (n)</span>
      </div>
      {sorted.map((s) => (
        <div role="row" key={s.nivel} title={`IC 95%: ${pct(s.ic[0])} a ${pct(s.ic[1])} · MRR ativo ${usd(s.mrr_ativo)}`}
          style={{ display: "grid", gridTemplateColumns: "minmax(90px,140px) 1fr 92px", gap: 8, alignItems: "center", height: 30 }}>
          <span role="cell" style={{ fontSize: 13 }}>{s.nivel}</span>
          <span role="cell" style={{ position: "relative", height: 20, borderLeft: `1px solid ${pal["--axis"]}` }}>
            <span style={{ position: "absolute", left: x(media), top: -4, bottom: -4, borderLeft: `1px solid ${pal["--muted"]}` }} />
            <span style={{ position: "absolute", left: x(s.ic[0]), width: `calc(${x(s.ic[1])} - ${x(s.ic[0])})`, top: 8, height: 4, borderRadius: 2, background: pal["--s1"], opacity: 0.35 }} />
            <span style={{ position: "absolute", left: x(s.taxa), top: 4, width: 12, height: 12, marginLeft: -6, borderRadius: 999, background: pal["--s1"], boxShadow: `0 0 0 2px ${pal["--surface"]}` }} />
          </span>
          <span role="cell" style={{ textAlign: "right", fontSize: 13, fontVariantNumeric: "tabular-nums" }}>{pct(s.taxa, 0)} <span style={{ color: pal["--muted"] }}>({int(s.n)})</span></span>
        </div>
      ))}
      <div className="legend" style={{ marginTop: 8 }}>
        <span><i style={{ background: pal["--s1"], borderRadius: 999 }} />taxa de churn</span>
        <span><i style={{ background: pal["--s1"], opacity: 0.35, height: 4 }} />intervalo de confiança 95%</span>
        <span><i style={{ background: pal["--muted"], width: 1 }} />média geral {pct(media, 0)}</span>
      </div>
    </div>
  );
}

/* ---------------------------------------------------------------- heatmap de Spearman */
export function Heatmap({ vars, vals, pal, isDark }: { vars: string[]; vals: (number | null)[][]; pal: Palette; isDark: boolean }) {
  const [hover, setHover] = useState<{ i: number; j: number } | null>(null);
  const pos = isDark ? "57,135,229" : "42,120,214";
  const neg = isDark ? "230,103,103" : "227,73,72";
  const color = (v: number | null) =>
    v == null ? "transparent" : `rgba(${v >= 0 ? pos : neg},${Math.min(1, Math.abs(v)) * 0.95 + 0.03})`;
  const cat = (v: string) => v.split("_")[0];
  const n = vars.length;
  const h = hover ? { a: vars[hover.i], b: vars[hover.j], v: vals[hover.i][hover.j] } : null;
  return (
    <div>
      <div className="tt" style={{ minHeight: 44, marginBottom: 10, boxShadow: "none" }} aria-live="polite">
        {h ? (
          <><b>{nome(h.a)} × {nome(h.b)}</b><div className="row"><span>ρ de Spearman</span><span>{dec(h.v, 2)}</span></div></>
        ) : <span style={{ color: pal["--muted"] }}>Passe o mouse (ou toque) numa célula para ver o par e o valor.</span>}
      </div>
      <div className="heat-scroll">
        <div style={{ display: "grid", gridTemplateColumns: `180px repeat(${n}, minmax(9px, 1fr))`, gap: 1, minWidth: 180 + n * 10 }}
          onMouseLeave={() => setHover(null)}>
          {vars.map((v, i) => (
            <div key={v} style={{ display: "contents" }}>
              <div className="heat-axis" style={{
                paddingRight: 6, lineHeight: "10px", fontSize: 10, textAlign: "right",
                borderTop: i > 0 && cat(vars[i - 1]) !== cat(v) ? `1px solid ${pal["--axis"]}` : undefined,
                color: hover?.i === i ? pal["--ink"] : undefined,
              }}>{nome(v)}</div>
              {vars.map((w, j) => (
                <div key={w} className="hcell" onMouseEnter={() => setHover({ i, j })} onClick={() => setHover({ i, j })}
                  style={{ background: color(vals[i][j]), aspectRatio: "1", outline: hover && (hover.i === i || hover.j === j) ? `1px solid ${pal["--axis"]}` : undefined }} />
              ))}
            </div>
          ))}
        </div>
      </div>
      <div className="legend" style={{ marginTop: 10 }}>
        <span><i style={{ background: `rgba(${neg},.9)` }} />correlação negativa</span>
        <span><i style={{ background: pal["--grid"] }} />sem correlação</span>
        <span><i style={{ background: `rgba(${pos},.9)` }} />correlação positiva</span>
      </div>
    </div>
  );
}

/* ---------------------------------------------------------------- matriz motivo × comentário */
export function Matrix({ linhas, colunas, valores, pal, isDark }: { linhas: string[]; colunas: string[]; valores: number[][]; pal: Palette; isDark: boolean }) {
  const max = Math.max(...valores.flat());
  const base = isDark ? "57,135,229" : "42,120,214";
  const PT: Record<string, string> = {
    budget: "orçamento", competitor: "concorrente", features: "funcionalidades", pricing: "preço", support: "suporte", unknown: "desconhecido",
    "(sem comentário)": "(sem comentário)", "missing features": "“missing features”", "switched to competitor": "“switched to competitor”", "too expensive": "“too expensive”",
  };
  const tot = useMemo(() => valores.flat().reduce((a, b) => a + b, 0), [valores]);
  return (
    <div className="tbl-wrap" style={{ border: 0 }}>
      <table className="mx" aria-label="Motivo registrado versus comentário do cliente">
        <thead>
          <tr><th style={{ textAlign: "left" }}>Motivo registrado ↓ / comentário →</th>{colunas.map((c) => <th key={c} style={{ whiteSpace: "normal" }}>{PT[c] ?? c}</th>)}</tr>
        </thead>
        <tbody>
          {linhas.map((l, i) => (
            <tr key={l}>
              <th style={{ textAlign: "left", position: "static" }}>{PT[l] ?? l}</th>
              {valores[i].map((v, j) => {
                const a = v / max;
                return <td key={j} className="c" title={`${int(v)} de ${int(tot)} eventos`}
                  style={{ background: `rgba(${base},${0.08 + a * 0.6})`, color: a > 0.75 && !isDark ? "#fff" : pal["--ink"] }}>{int(v)}</td>;
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
