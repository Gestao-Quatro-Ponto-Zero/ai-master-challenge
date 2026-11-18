"use client";

import { useId, useState } from "react";
import { scaleWithIntervals, tightScale } from "./LineChart";

/**
 * Columns with a line drawn over them (D49): the columns are a volume on the left axis, the line a
 * rate on the right axis, one point per column. Both axes start at 0 and share the grid lines (same
 * number of intervals). The legend names which axis each mark follows.
 */
export interface ColunasLinhaProps {
  rotulos: string[];
  colunas: number[];
  linha: number[];
  nomeColunas: string;
  nomeLinha: string;
  fmtColunas: (n: number) => string;
  fmtLinha: (n: number) => string;
  corColunas: string;
  corLinha: string;
  height: number;
  viewWidth: number;
  /** Widest a column may get, in viewBox units (few categories → wider columns). */
  larguraMax?: number;
  /** Print the line's value beside each point (for a few categories only). */
  rotularLinha?: boolean;
  onSelect?: (rotulo: string) => void;
}

const GRID = "#23232b";
const LABEL = "#9a9aa6";
const SURFACE = "#111115";
const CHAR = 6.2; // 10px mono, viewBox units a character

export function ColunasLinha({
  rotulos,
  colunas,
  linha,
  nomeColunas,
  nomeLinha,
  fmtColunas,
  fmtLinha,
  corColunas,
  corLinha,
  height,
  viewWidth,
  larguraMax = 42,
  rotularLinha = false,
  onSelect,
}: ColunasLinhaProps) {
  const titleId = useId();
  const [hover, setHover] = useState<number | null>(null);
  const n = rotulos.length;
  if (n === 0) return null;

  const esq = tightScale(colunas);
  const dir = scaleWithIntervals(linha, esq.ticks.length - 1);
  const left = Math.max(40, Math.ceil(Math.max(...esq.ticks.map((t) => fmtColunas(t).length)) * CHAR) + 12);
  const right = Math.max(40, Math.ceil(Math.max(...dir.ticks.map((t) => fmtLinha(t).length)) * CHAR) + 12);
  const plotWidth = Math.max(1, viewWidth - left - right);
  const banda = plotWidth / n;

  // Category labels: straight when they fit their band, else at -40° with room below.
  const maiorRotulo = Math.max(...rotulos.map((r) => r.length));
  const girar = maiorRotulo * 6 > banda - 6;
  const rad = (40 * Math.PI) / 180;
  const bottom = girar ? Math.ceil(Math.sin(rad) * maiorRotulo * 6) + 16 : 20;
  const top = 12;
  const plotHeight = Math.max(1, height - top - bottom);
  const base = top + plotHeight;

  const yEsq = (v: number) => base - (Math.max(0, v) / esq.max) * plotHeight;
  const yDir = (v: number) => base - (Math.max(0, v) / dir.max) * plotHeight;
  const xCentro = (i: number) => left + banda * i + banda / 2;
  const largura = Math.min(larguraMax, Math.max(10, banda * 0.6));
  const pontos = linha.map((v, i) => ({ x: xCentro(i), y: yDir(v) }));
  const caminho = pontos.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x.toFixed(2)} ${p.y.toFixed(2)}`).join(" ");

  const tipX = hover === null ? 0 : (xCentro(hover) / viewWidth) * 100;
  const tipLado = tipX > 66 ? "-translate-x-[calc(100%+12px)]" : tipX < 34 ? "translate-x-[12px]" : "-translate-x-1/2";
  const tipY = hover === null ? 0 : Math.min(yEsq(colunas[hover]), pontos[hover].y);
  const tipAbaixo = tipY < height * 0.45;
  const tipTop = Math.max(0, Math.min(90, (tipY / height) * 100));

  return (
    <div>
      <div className="mb-2 flex flex-wrap gap-x-3 gap-y-1 text-[10px] text-muted">
        <span className="flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-[2px]" style={{ backgroundColor: corColunas }} />
          <span className="font-mono">{nomeColunas} (eixo esq.)</span>
        </span>
        <span className="flex items-center gap-1.5">
          <svg width="16" height="8" aria-hidden="true">
            <line x1="0" x2="16" y1="4" y2="4" stroke={corLinha} strokeWidth="2" />
            <circle cx="8" cy="4" r="2.5" fill={corLinha} />
          </svg>
          <span className="font-mono">{nomeLinha} (eixo dir.)</span>
        </span>
      </div>

      <div className="relative veta-rise" onMouseLeave={() => setHover(null)}>
        <svg viewBox={`0 0 ${viewWidth} ${height}`} width="100%" role="img" aria-labelledby={titleId} className="block w-full">
          <title id={titleId}>{`${nomeColunas} em colunas e ${nomeLinha} em linha, por categoria`}</title>

          {esq.ticks.map((t, i) => {
            const y = yEsq(t);
            return (
              <g key={`g-${i}`}>
                <line x1={left} x2={viewWidth - right} y1={y} y2={y} stroke={GRID} strokeOpacity={t === 0 ? 1 : 0.5} />
                <text x={left - 8} y={y + 4} textAnchor="end" fontSize="10" fill={LABEL} className="font-mono">
                  {fmtColunas(t)}
                </text>
                <text x={viewWidth - right + 8} y={y + 4} textAnchor="start" fontSize="10" fill={LABEL} className="font-mono">
                  {fmtLinha(dir.ticks[i] ?? 0)}
                </text>
              </g>
            );
          })}

          {colunas.map((v, i) => {
            const y = yEsq(v);
            return (
              <rect
                key={`c-${i}`}
                x={xCentro(i) - largura / 2}
                y={y}
                width={largura}
                height={Math.max(0, base - y)}
                rx={3}
                fill={corColunas}
                fillOpacity={hover === null || hover === i ? 0.9 : 0.55}
              />
            );
          })}

          <path d={caminho} fill="none" stroke={corLinha} strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />
          {pontos.map((p, i) => (
            <g key={`p-${i}`}>
              <circle cx={p.x} cy={p.y} r={hover === i ? 5.5 : 4.5} fill={corLinha} stroke={SURFACE} strokeWidth="2" />
              {rotularLinha && (
                <text
                  x={p.x}
                  y={p.y - 10}
                  textAnchor="middle"
                  fontSize="11"
                  fontWeight="600"
                  fill="#e6e6ea"
                  stroke={SURFACE}
                  strokeWidth="3.5"
                  strokeLinejoin="round"
                  paintOrder="stroke"
                  className="font-mono tabular-nums"
                >
                  {fmtLinha(linha[i])}
                </text>
              )}
            </g>
          ))}

          {rotulos.map((r, i) => {
            const x = xCentro(i);
            const y = base + 14;
            return (
              <text
                key={`r-${i}`}
                x={x}
                y={y}
                textAnchor={girar ? "end" : "middle"}
                fontSize="10"
                fill={LABEL}
                transform={girar ? `rotate(-40 ${x} ${y})` : undefined}
              >
                {r}
              </text>
            );
          })}

          {rotulos.map((r, i) => (
            <rect
              key={`h-${i}`}
              x={left + banda * i}
              y={top}
              width={banda}
              height={plotHeight}
              fill="transparent"
              className={onSelect ? "cursor-pointer" : undefined}
              onMouseEnter={() => setHover(i)}
              onClick={onSelect ? () => onSelect(r) : undefined}
            />
          ))}
        </svg>

        {hover !== null && (
          <div
            className={`pointer-events-none absolute z-10 min-w-36 ${tipLado} ${tipAbaixo ? "translate-y-[12px]" : "-translate-y-[calc(100%+12px)]"} rounded-md border border-edge-strong bg-panel/95 px-2.5 py-2 text-[11px] shadow-[0_8px_24px_rgba(0,0,0,0.28)] backdrop-blur-sm`}
            style={{ left: `${tipX}%`, top: `${tipTop}%` }}
          >
            <div className="mb-1 text-[10px] font-medium uppercase tracking-wider text-faint">{rotulos[hover]}</div>
            {[
              { nome: nomeColunas, cor: corColunas, valor: fmtColunas(colunas[hover]) },
              { nome: nomeLinha, cor: corLinha, valor: fmtLinha(linha[hover]) },
            ].map((e) => (
              <div key={e.nome} className="flex items-center justify-between gap-3">
                <span className="flex items-center gap-1.5 whitespace-nowrap text-muted">
                  <span className="h-2 w-2 rounded-full" style={{ backgroundColor: e.cor }} />
                  {e.nome}
                </span>
                <span className="whitespace-nowrap font-mono tabular-nums text-foreground">{e.valor}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
