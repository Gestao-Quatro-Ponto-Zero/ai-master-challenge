import { useMemo, useState } from "react";
import type { Oportunidade } from "../types";

type SortKey = "score" | "prioridade" | "age_days";

const CONFIANCA_COLORS: Record<string, string> = {
  A: "bg-navy text-white",
  B: "bg-navy/70 text-white",
  C: "bg-gray-300 text-navy",
  D: "bg-alert text-white",
};

function formatUsd(value: number): string {
  return value.toLocaleString("pt-BR", { style: "currency", currency: "USD" });
}

export function DealTable({ oportunidades }: { oportunidades: Oportunidade[] }) {
  const [sortKey, setSortKey] = useState<SortKey>("score");
  const [sortDesc, setSortDesc] = useState(true);

  const ordenadas = useMemo(() => {
    const copy = [...oportunidades];
    copy.sort((a, b) => {
      const av = a[sortKey] ?? -Infinity;
      const bv = b[sortKey] ?? -Infinity;
      return sortDesc ? bv - av : av - bv;
    });
    return copy;
  }, [oportunidades, sortKey, sortDesc]);

  function handleSort(key: SortKey) {
    if (key === sortKey) {
      setSortDesc((prev) => !prev);
    } else {
      setSortKey(key);
      setSortDesc(true);
    }
  }

  if (oportunidades.length === 0) {
    return (
      <p className="text-muted text-sm py-8 text-center">
        Nenhuma oportunidade encontrada para os filtros atuais.
      </p>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm border-collapse">
        <thead>
          <tr className="text-left text-xs text-muted uppercase tracking-wide border-b border-border">
            <SortableHeader label="Score" active={sortKey === "score"} desc={sortDesc} onClick={() => handleSort("score")} />
            <th className="py-2 px-2">Estado</th>
            <th className="py-2 px-2">Produto</th>
            <th className="py-2 px-2">Vendedor</th>
            <SortableHeader label="Prioridade" active={sortKey === "prioridade"} desc={sortDesc} onClick={() => handleSort("prioridade")} />
            <SortableHeader label="Idade" active={sortKey === "age_days"} desc={sortDesc} onClick={() => handleSort("age_days")} />
            <th className="py-2 px-2">Confiança</th>
          </tr>
        </thead>
        <tbody>
          {ordenadas.map((o) => (
            <DealRow key={o.opportunity_id} oportunidade={o} />
          ))}
        </tbody>
      </table>
    </div>
  );
}

function SortableHeader({
  label,
  active,
  desc,
  onClick,
}: {
  label: string;
  active: boolean;
  desc: boolean;
  onClick: () => void;
}) {
  return (
    <th className="py-2 px-2">
      <button
        type="button"
        onClick={onClick}
        className={"flex items-center gap-1 " + (active ? "text-navy font-bold" : "hover:text-navy")}
      >
        {label}
        {active && <span>{desc ? "↓" : "↑"}</span>}
      </button>
    </th>
  );
}

function DealRow({ oportunidade: o }: { oportunidade: Oportunidade }) {
  return (
    <tr className="border-b border-border align-top hover:bg-bg/60">
      <td className="py-3 px-2 font-bold text-navy">{o.score.toFixed(1)}</td>
      <td className="py-3 px-2">
        <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-gray-100 text-navy border border-border">
          {o.estado_label}
        </span>
      </td>
      <td className="py-3 px-2">
        <div className="font-medium">{o.product}</div>
        {o.account && <div className="text-xs text-muted">{o.account}</div>}
      </td>
      <td className="py-3 px-2 text-muted">{o.sales_agent}</td>
      <td className="py-3 px-2 font-medium">{formatUsd(o.prioridade)}</td>
      <td className="py-3 px-2 text-muted">
        {o.age_days !== null ? `${Math.round(o.age_days)}d` : "—"}
      </td>
      <td className="py-3 px-2">
        <span
          title={o.razao_confianca}
          className={
            "inline-flex items-center justify-center w-6 h-6 rounded-full text-xs font-bold cursor-help " +
            CONFIANCA_COLORS[o.confianca]
          }
        >
          {o.confianca}
        </span>
      </td>
      <td className="py-3 px-2 max-w-md">
        <div className="text-xs text-muted mb-1">
          p̂ {(o.p_hat * 100).toFixed(1)}% · Valor {formatUsd(o.valor)} · Urgência {(o.urgencia * 100).toFixed(0)}%
        </div>
        <div className="text-xs text-navy">{o.plano_de_acao}</div>
      </td>
    </tr>
  );
}
