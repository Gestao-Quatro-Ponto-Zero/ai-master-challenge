"use client";

import { ScatterChart } from "../charts/ScatterChart";
import { Ajustado } from "./Ajustado";

/**
 * Feature scatter (screen 3): one point per feature and phase, uses × error rate. Stable usage in blue,
 * beta usage in green (dark categorical slot 3, validated with the donut palette).
 */
const AZUL = "#3987e5";
const VERDE = "#199e70";

const nomeRecurso = (r: string) => r.replace(/^feature_(\d+)$/, "Recurso $1");
const mil = (n: number) => (n >= 1000 ? `${(n / 1000).toLocaleString("pt-BR", { maximumFractionDigits: 1 })} mil` : Math.round(n).toLocaleString("pt-BR"));
const pct = (n: number) => `${n.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`;

export function RecursosErros({ recursos }: { recursos: { recurso: string; usos: number; taxaErro: number; beta: boolean }[] }) {
  const pontos = (beta: boolean) => recursos.filter((r) => r.beta === beta).map((r) => ({ x: r.usos, y: r.taxaErro, label: `${nomeRecurso(r.recurso)} · ${beta ? "uso beta" : "uso estável"}` }));
  return (
    <Ajustado>
      {(w, h) => (
        <ScatterChart
          series={[
            { name: "Uso estável", points: pontos(false), color: AZUL },
            { name: "Uso beta", points: pontos(true), color: VERDE },
          ]}
          xLabel="usos no período"
          yLabel="taxa de erro"
          xFormat={mil}
          yFormat={pct}
          height={h - 22}
          viewWidth={w}
          bare
        />
      )}
    </Ajustado>
  );
}
