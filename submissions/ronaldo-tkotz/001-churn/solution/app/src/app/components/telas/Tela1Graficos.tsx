"use client";

import { LineChart } from "../charts/LineChart";
import { ColumnChart } from "../charts/ColumnChart";

/**
 * Client wrappers for screen 1 (formatters stay on the client side of the boundary).
 * Colors: dark-mode categorical slots 1–2 (blue, orange) and an ordinal blue ramp for the
 * scores, validated with the dataviz validator; "no score" is neutral gray. One axis per chart.
 */
const AZUL = "#3987e5";
const LARANJA = "#d95926";
const NOTAS = ["#256abf", "#3987e5", "#86b6ef"];
const CINZA = "#6b6b78";

const int = (n: number) => n.toLocaleString("pt-BR");
const pct = (n: number) => `${n.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`;

export function ChurnContagens({ meses, contas, eventos }: { meses: string[]; contas: number[]; eventos: number[] }) {
  return (
    <LineChart
      categories={meses}
      series={[
        { name: "Contas com evento", values: contas, color: AZUL },
        { name: "Eventos", values: eventos, color: LARANJA },
      ]}
      yFormat={int}
      height={170}
      bare
    />
  );
}

export function ChurnTaxas({ meses, taxa, taxaNaBase }: { meses: string[]; taxa: number[]; taxaNaBase: number[] }) {
  return (
    <LineChart
      categories={meses}
      series={[
        { name: "Taxa (todas as contas com evento)", values: taxa, color: AZUL },
        { name: "Taxa (só contas ativas no mês)", values: taxaNaBase, color: LARANJA },
      ]}
      yFormat={pct}
      height={170}
      bare
    />
  );
}

export function Satisfacao({ trimestres, n3, n4, n5, sem }: { trimestres: string[]; n3: number[]; n4: number[]; n5: number[]; sem: number[] }) {
  return (
    <ColumnChart
      categories={trimestres}
      series={[
        { name: "Nota 3", values: n3, color: NOTAS[0] },
        { name: "Nota 4", values: n4, color: NOTAS[1] },
        { name: "Nota 5", values: n5, color: NOTAS[2] },
        { name: "Sem nota", values: sem, color: CINZA },
      ]}
      valueFormat={int}
      stacked
      height={210}
      bare
    />
  );
}

export function UsoTotal({ meses, com, sem }: { meses: string[]; com: number[]; sem: number[] }) {
  return (
    <LineChart
      categories={meses}
      series={[
        { name: "Com registros em alerta", values: com, color: AZUL },
        { name: "Sem registros em alerta", values: sem, color: LARANJA },
      ]}
      yFormat={int}
      height={170}
      bare
    />
  );
}

/** Small multiples: one panel per sector, same y scale is not forced (each shows its own trend). */
export function UsoSetor({ meses, valores }: { meses: string[]; valores: number[] }) {
  return <LineChart categories={meses} series={[{ name: "Registros", values: valores, color: AZUL }]} yFormat={int} height={110} bare />;
}
