import type { Deal } from "@/lib/data";
import { formatCompactUSD, formatInt } from "@/lib/format";
import type { Window } from "@/lib/playbook";
import { formatUSD, WINDOW_ALERT_DAYS } from "@/lib/scoring";

export interface MapProduct {
  name: string;
  price: number;
}

interface Props {
  deals: Deal[];
  products: MapProduct[];
  win: Window;
  maxCycle: number;
  peakAge: number;
  curve: number[];
  /** Deals da pilha selecionada: acendem no mapa; os demais apagam. */
  highlight: ReadonlySet<string>;
  describedBy: string;
  label: string;
}

/** Posição vertical estável de 0 a 1 a partir do id, para os pontos não se sobreporem sempre na mesma linha. */
function hash(s: string) {
  let h = 0;
  for (const c of s) h = (h * 31 + c.charCodeAt(0)) >>> 0;
  return h / 4294967295;
}

type Variant = "wide" | "mid" | "narrow" | "compact";

/**
 * Quatro desenhos do mesmo mapa, um por faixa de largura. O texto do SVG escala com a largura renderizada
 * (largura / viewBox), então cada faixa tem o viewBox certo para a fonte nunca cair de 13 px reais:
 *   largura do SVG ≈ viewport − 15 (barra) − 120 (margens e padding); em cada faixa o piso é ≥ 0,9 × 14,5 ≈ 13,05 px.
 *   wide   ≥ 1305 px  · viewBox 1300 (coluna de zumbis completa)
 *   mid    1035–1304  · viewBox 1000 (zumbis só com a contagem)
 *   narrow 900–1034   · viewBox 800  (sem coluna de zumbis; o total vai na descrição)
 *   compact < 900     · viewBox 360  (sem preços; centralizado, no máximo 520 px)
 */
const CFG: Record<Variant, { W: number; labelW: number; zW: number; laneH: number; fs: number; zBar: number; zValue: boolean; price: boolean; cls: string }> = {
  wide: { W: 1300, labelW: 170, zW: 260, laneH: 50, fs: 14.5, zBar: 110, zValue: true, price: true, cls: "hidden min-[1305px]:block" },
  mid: { W: 1000, labelW: 150, zW: 210, laneH: 46, fs: 14.5, zBar: 44, zValue: false, price: true, cls: "hidden min-[1035px]:block min-[1305px]:hidden" },
  narrow: { W: 800, labelW: 150, zW: 0, laneH: 46, fs: 14.5, zBar: 0, zValue: false, price: true, cls: "hidden min-[900px]:block min-[1035px]:hidden" },
  compact: { W: 330, labelW: 118, zW: 0, laneH: 34, fs: 14.5, zBar: 0, zValue: false, price: false, cls: "mx-auto max-w-[520px] min-[900px]:hidden" },
};

/**
 * Mapa idade × produto: cada deal vivo é um ponto na idade em que está hoje. Por trás, a curva de decisão;
 * a faixa dourada é a fase de decisão e, à direita do limite, ficam os zumbis por produto.
 * SVG à mão, sem biblioteca. O equivalente em texto é a descrição (`describedBy`) e a tabela de pilhas abaixo.
 */
export function CycleMap(props: Props) {
  return (
    <>
      {(["wide", "mid", "narrow", "compact"] as const).map((v) => (
        <MapSvg key={v} {...props} variant={v} />
      ))}
    </>
  );
}

function MapSvg({ deals, products, win, maxCycle, peakAge, curve, highlight, describedBy, label, variant }: Props & { variant: Variant }) {
  const { W, labelW, zW, laneH, fs, zBar, zValue, price, cls } = CFG[variant];
  const compact = variant === "compact";
  const topY = 54;
  const bottom = 38;
  const plotW = W - labelW - zW - (compact ? 8 : 24);
  const H = topY + products.length * laneH + bottom;
  const x = (a: number) => labelW + (a / maxCycle) * plotW;
  const laneBot = topY + products.length * laneH;
  const mx = Math.max(...curve);
  const cy = (p: number) => laneBot - (p / mx) * (laneBot - topY + 30);
  const path = curve.map((p, a) => `${a ? "L" : "M"}${x(a).toFixed(1)},${cy(p).toFixed(1)}`).join("");

  const live = deals.filter((d) => d.status === "ativo");
  const zombies = new Map<string, { n: number; v: number }>();
  for (const d of deals) {
    if (d.status !== "zumbi") continue;
    const z = zombies.get(d.product) ?? { n: 0, v: 0 };
    z.n++;
    z.v += d.price;
    zombies.set(d.product, z);
  }
  const zMax = Math.max(1, ...[...zombies.values()].map((z) => z.n));
  const zTotal = [...zombies.values()].reduce((s, z) => ({ n: s.n + z.n, v: s.v + z.v }), { n: 0, v: 0 });
  const laneOf = new Map(products.map((p, i) => [p.name, i]));
  const axis = compact ? [0, win.start, win.end, maxCycle] : [0, 30, win.start, peakAge, win.end, maxCycle];
  const dots = [...live].sort((a, b) => Number(highlight.has(a.id)) - Number(highlight.has(b.id)));
  const zx = x(maxCycle) + 24;

  return (
    <svg viewBox={`0 0 ${W} ${H}`} role="img" aria-label={label} aria-describedby={describedBy} className={`block h-auto w-full ${cls}`}>
      <rect x={x(win.start)} y={topY - 26} width={x(win.end) - x(win.start)} height={laneBot - topY + 26} fill="var(--color-gold)" opacity=".12" />
      <rect x={x(maxCycle - WINDOW_ALERT_DAYS)} y={topY - 26} width={x(maxCycle) - x(maxCycle - WINDOW_ALERT_DAYS)} height={laneBot - topY + 26} fill="var(--color-risk)" opacity=".09" />
      <text x={x(win.start / 2)} y={topY - 32} fontSize={fs} fontWeight="600" textAnchor="middle" className="fill-fg-2">
        {compact ? "cedo" : "ainda cedo"}
      </text>
      <text x={x((win.start + win.end) / 2)} y={topY - 32} fontSize={fs} fontWeight="600" textAnchor="middle" className="fill-gold-hi">
        {compact ? "decisão" : `fase de decisão · dias ${win.start}–${win.end}`}
      </text>
      <text x={x(maxCycle - WINDOW_ALERT_DAYS / 2)} y={topY - 32} fontSize={fs} fontWeight="600" textAnchor="middle" className="fill-risk">
        {compact ? "fim" : `últimos ${WINDOW_ALERT_DAYS} dias`}
      </text>

      <path d={`${path} L${x(maxCycle)},${laneBot} L${x(0)},${laneBot} Z`} fill="var(--color-gold)" opacity=".08" />
      <path d={path} fill="none" stroke="var(--color-gold)" strokeWidth="1.5" opacity=".6" />

      {products.map((p, i) => {
        const y0 = topY + i * laneH;
        const z = zombies.get(p.name);
        const barW = (z ? z.n / zMax : 0) * zBar;
        return (
          <g key={p.name}>
            <line x1={labelW} x2={x(maxCycle)} y1={y0 + laneH} y2={y0 + laneH} stroke="var(--color-line)" />
            <text x="0" y={y0 + laneH / 2 + (price ? -3 : 5)} fontSize={variant === "wide" ? 15 : fs} fontWeight="600" className="fill-fg">
              {p.name}
            </text>
            {price && (
              <text x="0" y={y0 + laneH / 2 + 16} fontSize={fs} className="fill-fg-3">
                {formatUSD(p.price)}
              </text>
            )}
            {zW > 0 && z && (
              <>
                <rect x={zx} y={y0 + laneH / 2 - 7} width={barW} height="14" rx="2" fill="var(--color-brick)" />
                <text x={zx + barW + 8} y={y0 + laneH / 2 + 5} fontSize={fs} className="fill-risk">
                  {zValue ? `${formatInt(z.n)} · ${formatCompactUSD(z.v)}` : formatInt(z.n)}
                </text>
              </>
            )}
          </g>
        );
      })}

      {dots.map((d) => {
        const lane = laneOf.get(d.product);
        if (lane === undefined || d.ageDays === null) return null;
        const on = highlight.has(d.id);
        const yy = topY + lane * laneH + 8 + hash(d.id) * (laneH - 16);
        return (
          <circle
            key={d.id}
            cx={x(d.ageDays).toFixed(1)}
            cy={yy.toFixed(1)}
            r={on ? (compact ? 3.6 : 4.8) : compact ? 2.4 : 3.2}
            fill={on ? "var(--color-gold-hi)" : "var(--color-fg-3)"}
            opacity={on ? 1 : 0.45}
            style={{ transition: "opacity .25s" }}
          />
        );
      })}

      <line x1={x(maxCycle)} x2={x(maxCycle)} y1={topY - 26} y2={laneBot + 6} stroke="var(--color-risk)" strokeWidth="1.5" />
      {axis.map((a) => (
        <text key={a} x={x(a)} y={laneBot + 22} fontSize={fs} textAnchor={(compact || zW === 0) && a === maxCycle ? "end" : "middle"} className={a === maxCycle ? "fill-risk" : "fill-fg-3"}>
          {!compact && a === peakAge ? `pico ${a}` : a}
        </text>
      ))}
      {zW > 0 && (
        <>
          <text x={zx} y={topY - 32} fontSize={fs} fontWeight="600" className="fill-risk">
            zumbis · {formatInt(zTotal.n)} · {formatCompactUSD(zTotal.v)}
          </text>
          <text x={zx} y={laneBot + 22} fontSize={fs} className="fill-fg-3">
            nenhum fechou no histórico
          </text>
        </>
      )}
    </svg>
  );
}
