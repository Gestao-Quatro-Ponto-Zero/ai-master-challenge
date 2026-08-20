import type { Kpis, Session } from "../types";

function formatUsd(value: number): string {
  return value.toLocaleString("pt-BR", { style: "currency", currency: "USD" });
}

export function KpiTiles({ kpis, session }: { kpis: Kpis; session: Session }) {
  const tiles = [
    { label: "Oportunidades", value: kpis.total_oportunidades.toLocaleString("pt-BR") },
    { label: "Receita ganha", value: formatUsd(kpis.receita_ganha) },
    { label: "Valor esperado em aberto", value: formatUsd(kpis.valor_esperado_aberto) },
    {
      label: "Em Desistir",
      value: kpis.total_desistir.toLocaleString("pt-BR"),
      alert: true,
    },
    { label: "Maior negócio fechado", value: formatUsd(kpis.maior_negocio_fechado) },
  ];

  return (
    <div>
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
        {tiles.map((tile) => (
          <div
            key={tile.label}
            className={
              "rounded-sm border p-4 " +
              (tile.alert
                ? "border-alert bg-alert/5 text-alert"
                : "border-border bg-white text-navy")
            }
          >
            <div className="text-xs uppercase tracking-wide text-muted mb-1">
              {tile.label}
            </div>
            <div className="text-xl font-bold">{tile.value}</div>
          </div>
        ))}
      </div>
      <div className="text-xs text-muted mt-2">
        {kpis.data_inicio} → {kpis.data_fim}
        {kpis.idade_maxima_aberta !== null && (
          <> · {Math.round(kpis.idade_maxima_aberta)} dias no negócio aberto mais antigo do escopo</>
        )}
        {" · "}
        {session.identity} ({roleLabel(session.role)})
      </div>
    </div>
  );
}

function roleLabel(role: Session["role"]): string {
  if (role === "sales_agent") return "Sales Agent";
  if (role === "supervisor") return "Supervisor";
  return "Manager";
}
