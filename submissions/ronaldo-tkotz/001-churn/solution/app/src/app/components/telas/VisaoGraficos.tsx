"use client";

import { BarChart } from "../charts/BarChart";
import { PieChart } from "../charts/PieChart";
import { LineChart } from "../charts/LineChart";
import { Ajustado } from "./Ajustado";

/**
 * Client wrappers for the executive overview. Every chart fills its panel at the panel's real
 * pixel size (Ajustado), so the whole overview fits one screen without scrolling (D32).
 * Colour carries one meaning across the screen: blue = revenue, orange = churn (dark
 * categorical slots 1–2). The donuts use slots 1–4, which the dataviz validator passes
 * all-pairs in dark mode.
 */
const AZUL = "#3987e5";
const LARANJA = "#d95926";
const DONUT = ["#3987e5", "#d95926", "#199e70", "#c98500"];

type Formato = "usd" | "pct" | "int";
const FORMATOS: Record<Formato, (n: number) => string> = {
  usd: (n) => `US$ ${Math.round(n).toLocaleString("pt-BR")}`,
  pct: (n) => `${n.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`,
  int: (n) => n.toLocaleString("pt-BR"),
};

/** "US$ 10,2 mi" — compact money for axes, column tops and the donut centre. */
const usdCompacto = (n: number) =>
  n === 0
    ? "US$ 0"
    : n >= 1e6
      ? `US$ ${(n / 1e6).toLocaleString("pt-BR", { maximumFractionDigits: 1 })} mi`
      : `US$ ${Math.round(n / 1e3).toLocaleString("pt-BR")} mil`;

/** Column tops have little room: "2,4 mi" / "489 mil" (the panel title says it is US$). */
const usdColuna = (n: number) =>
  n >= 1e6 ? `${(n / 1e6).toLocaleString("pt-BR", { maximumFractionDigits: 1 })} mi` : `${Math.round(n / 1e3).toLocaleString("pt-BR")} mil`;

const COLUNA: Record<Formato, (n: number) => string> = { usd: usdColuna, pct: FORMATOS.pct, int: FORMATOS.int };

/** Height the line chart's HTML legend takes at this width (10px mono ≈ 6.2px a character). */
function alturaLegenda(nomes: string[], largura: number): number {
  const total = nomes.reduce((s, n) => s + n.length * 6.2 + 24, 0);
  return Math.ceil(total / Math.max(1, largura)) * 18 + 4;
}

/** Horizontal bars, for short lists (under five items). */
export function Barras({ dados, formato, tema }: { dados: { label: string; value: number }[]; formato: Formato; tema: "receita" | "churn" }) {
  const color = tema === "receita" ? AZUL : LARANJA;
  return (
    <Ajustado>
      {(w, h) => (
        <BarChart data={dados.map((d) => ({ ...d, color }))} valueFormat={FORMATOS[formato]} horizontal height={h} viewWidth={w} bare />
      )}
    </Ajustado>
  );
}

/**
 * One-hue ordinal ramps (D35): the lowest value in a chart takes the dim end, the highest the
 * bright end, so the eye finds the worst groups first. The dim ends clear 2:1 on the dark panel.
 */
const RAMPAS: Record<"receita" | "churn", [string, string, string]> = {
  churn: ["#8a3615", "#d95926", "#f28c5c"],
  receita: ["#1c5cab", "#3987e5", "#86b6ef"],
};
const hex = (c: string) => [1, 3, 5].map((i) => parseInt(c.slice(i, i + 2), 16));
function rampa(tema: "receita" | "churn", t: number): string {
  const [a, b, c] = RAMPAS[tema];
  const [de, ate, u] = t < 0.5 ? [a, b, t * 2] : [b, c, (t - 0.5) * 2];
  const x = hex(de);
  const y = hex(ate);
  return `#${x.map((v, i) => Math.round(v + (y[i] - v) * u).toString(16).padStart(2, "0")).join("")}`;
}

/** Columns with the value on top, for lists of five or more (D32); `gradiente` shades by value (D35). */
export function Colunas({
  dados,
  formato,
  tema,
  gradiente = false,
}: {
  dados: { label: string; value: number }[];
  formato: Formato;
  tema: "receita" | "churn";
  gradiente?: boolean;
}) {
  const base = tema === "receita" ? AZUL : LARANJA;
  const min = Math.min(...dados.map((d) => d.value));
  const max = Math.max(...dados.map((d) => d.value));
  const cor = (v: number) => (gradiente && max > min ? rampa(tema, (v - min) / (max - min)) : base);
  return (
    <Ajustado>
      {(w, h) => (
        <BarChart data={dados.map((d) => ({ ...d, color: cor(d.value) }))} valueFormat={COLUNA[formato]} horizontal={false} fit showValues height={h} viewWidth={w} bare />
      )}
    </Ajustado>
  );
}

export function Donut({ dados, formato }: { dados: { label: string; value: number }[]; formato: Formato }) {
  return (
    <Ajustado>
      {(w, h) => (
        <PieChart
          slices={dados.map((d, i) => ({ label: d.label, value: d.value, color: DONUT[i % DONUT.length] }))}
          valueFormat={formato === "usd" ? usdCompacto : FORMATOS[formato]}
          donut
          height={h}
          viewWidth={w}
          bare
        />
      )}
    </Ajustado>
  );
}

/**
 * Average age of the base, in months (D40): active accounts from signup (blue) and subscriptions in
 * force from their start (green, the third slot). One axis, both in months.
 */
export function IdadeMedia({ meses, contas, assinaturas }: { meses: string[]; contas: number[]; assinaturas: number[] }) {
  const nomes = ["Contas ativas (desde o cadastro)", "Assinaturas em vigor (desde o início)"];
  const mesesFmt = (n: number) => `${n.toLocaleString("pt-BR", { maximumFractionDigits: 1 })} m`;
  return (
    <Ajustado>
      {(w, h) => (
        <LineChart
          categories={meses}
          series={[
            { name: nomes[0], values: contas, color: AZUL },
            { name: nomes[1], values: assinaturas, color: DONUT[2] },
          ]}
          yFormat={mesesFmt}
          height={h - alturaLegenda(nomes, w)}
          viewWidth={w}
          area={false}
          bare
        />
      )}
    </Ajustado>
  );
}

/**
 * Plain month-by-month lines on one axis (D43): every series in the same unit. `tema` picks the
 * colour by meaning (volume = blue, problem = orange, third = green).
 */
export function LinhasMensais({
  meses,
  series,
  formato,
  yMax,
}: {
  meses: string[];
  series: { nome: string; valores: (number | null)[]; tema: "volume" | "problema" | "terceiro" }[];
  formato: "int" | "dec" | "pct";
  yMax?: number;
}) {
  const cor = { volume: AZUL, problema: LARANJA, terceiro: DONUT[2] };
  const fmt = {
    int: (n: number) => (n >= 1000 ? `${(n / 1000).toLocaleString("pt-BR", { maximumFractionDigits: 1 })} mil` : Math.round(n).toLocaleString("pt-BR")),
    dec: (n: number) => n.toLocaleString("pt-BR", { maximumFractionDigits: 2 }),
    pct: (n: number) => `${n.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`,
  }[formato];
  const nomes = series.map((s) => s.nome);
  return (
    <Ajustado>
      {(w, h) => (
        <LineChart
          categories={meses}
          series={series.map((s) => ({ name: s.nome, values: s.valores, color: cor[s.tema] }))}
          yFormat={fmt}
          yMax={yMax}
          height={h - (nomes.length > 1 ? alturaLegenda(nomes, w) : 0)}
          viewWidth={w}
          area={false}
          bare
        />
      )}
    </Ajustado>
  );
}

/** "+8,2%" / "−44,4%": growth reads with its sign. */
const pctSinal = (n: number) => `${n > 0 ? "+" : n < 0 ? "−" : ""}${Math.abs(n).toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`;

/** Month-on-month growth: the active base (blue) against churn (orange), one % axis. */
export function CrescimentoMensal({ meses, contas, churn, tendContas, tendChurn }: { meses: string[]; contas: number[]; churn: number[]; tendContas: number[]; tendChurn: number[] }) {
  const nomes = ["Contas ativas", "Contas com evento de churn", "tendência linear"];
  return (
    <Ajustado>
      {(w, h) => (
        <LineChart
          categories={meses}
          series={[
            { name: nomes[0], values: contas, color: AZUL },
            { name: nomes[1], values: churn, color: LARANJA },
          ]}
          yFormat={pctSinal}
          height={h - alturaLegenda(nomes, w)}
          viewWidth={w}
          area={false}
          trends={[tendContas, tendChurn]}
          trendLabel={nomes[2]}
          bare
        />
      )}
    </Ajustado>
  );
}

/**
 * Revenue won from new accounts (blue) against revenue lost to cancellations (orange), per month,
 * with each linear trend projected (dashed) until the lines meet.
 */
export function ReceitaNovaPerdida({
  meses,
  nova,
  perdida,
  tendNova,
  tendPerdida,
  inicioProjecao,
  cruzamento,
}: {
  meses: string[];
  nova: (number | null)[];
  perdida: (number | null)[];
  tendNova: (number | null)[];
  tendPerdida: (number | null)[];
  inicioProjecao: number;
  cruzamento: { index: number; label: string } | null;
}) {
  const nomes = ["Receita nova", "Receita perdida", "tendência linear de 2024"];
  return (
    <Ajustado>
      {(w, h) => (
        <LineChart
          categories={meses}
          series={[
            { name: nomes[0], values: nova, color: AZUL },
            { name: nomes[1], values: perdida, color: LARANJA },
          ]}
          trends={[tendNova, tendPerdida]}
          trendLabel={nomes[2]}
          yFormat={usdCompacto}
          projectFrom={inicioProjecao}
          marker={cruzamento ?? undefined}
          height={h - alturaLegenda(nomes, w)}
          viewWidth={w}
          area={false}
          bare
        />
      )}
    </Ajustado>
  );
}
