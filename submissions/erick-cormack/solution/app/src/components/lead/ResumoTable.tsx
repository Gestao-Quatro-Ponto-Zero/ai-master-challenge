import { Link } from "@tanstack/react-router";
import { ArrowDown, ArrowUp } from "lucide-react";
import { useMemo, useState, type ReactNode } from "react";
import { useResumoVendedores, type ResumoVendedor } from "@/hooks/useResumoVendedores";
import { matchesFilters, type Filters } from "@/lib/filters";
import { formatNumber, formatPct, formatUSD } from "@/lib/format";
import { pctParado } from "@/lib/metrics";
import { cn } from "@/lib/utils";
import { EmptyState, ErrorState, LoadingState } from "./States";

type Row = ResumoVendedor & { pct_parado: number };
type Col = { key: keyof Row; header: string; numeric?: boolean; fmt?: (r: Row) => ReactNode; total?: (rows: Row[]) => ReactNode };

const ALERTA_PARADO = 0.7;
const sum = (rows: Row[], k: keyof Row) => rows.reduce((s, r) => s + (Number(r[k]) || 0), 0);

const cols: Col[] = [
  { key: "sales_agent", header: "Vendedor" },
  { key: "manager", header: "Manager" },
  { key: "regional_office", header: "Região" },
  { key: "deals_focar", header: "Focar", numeric: true },
  { key: "valor_esperado_focar", header: "Valor esperado em foco", numeric: true, fmt: (r) => formatUSD(r.valor_esperado_focar),
    total: (rs) => formatUSD(sum(rs, "valor_esperado_focar")) },
  { key: "deals_reta_final", header: "Reta final", numeric: true },
  { key: "deals_requalificar", header: "Parados", numeric: true },
  { key: "valor_parado", header: "Valor parado", numeric: true, fmt: (r) => formatUSD(r.valor_parado), total: (rs) => formatUSD(sum(rs, "valor_parado")) },
  { key: "pct_parado", header: "% do aberto parado", numeric: true, fmt: (r) => formatPct(r.pct_parado),
    total: (rs) => formatPct(pctParado(sum(rs, "deals_focar"), sum(rs, "deals_requalificar"), sum(rs, "deals_prospectar"))) },
  { key: "deals_sem_conta", header: "Sem conta", numeric: true },
  { key: "deals_possivel_duplicata", header: "Possível duplicata", numeric: true },
];

export function ResumoTable({ filters }: { filters: Filters }) {
  const { data, isLoading, error, refetch } = useResumoVendedores();
  const [sort, setSort] = useState<{ key: keyof Row; dir: 1 | -1 }>({ key: "pct_parado", dir: -1 });

  const rows = useMemo(() => {
    const base: Row[] = (data ?? [])
      .filter((r) => matchesFilters(r, filters))
      .map((r) => ({ ...r, pct_parado: pctParado(r.deals_focar ?? 0, r.deals_requalificar ?? 0, r.deals_prospectar ?? 0) }));
    return base.sort((a, b) => {
      const va = a[sort.key], vb = b[sort.key];
      if (typeof va === "number" || typeof vb === "number") return ((Number(va) || 0) - (Number(vb) || 0)) * sort.dir;
      return String(va ?? "").localeCompare(String(vb ?? ""), "pt-BR") * sort.dir;
    });
  }, [data, filters, sort]);

  const toggle = (key: keyof Row, numeric?: boolean) =>
    setSort((s) => (s.key === key ? { key, dir: (s.dir * -1) as 1 | -1 } : { key, dir: numeric ? -1 : 1 }));

  return (
    <div className="px-4 pb-10 md:px-8">
      <div className="rounded-lg border border-border bg-card">
        {isLoading ? <LoadingState /> : error ? <ErrorState error={error} onRetry={() => refetch()} /> : !rows.length ? (
          <EmptyState message="Nenhum vendedor neste recorte." />
        ) : (
          <div className="w-full overflow-x-auto">
            <table className="w-full min-w-[1000px] text-sm">
              <thead>
                <tr className="border-b border-border text-xs text-muted-foreground">
                  {cols.map((c) => (
                    <th key={c.key} className={cn("px-3 py-2 font-medium", c.numeric ? "text-right" : "text-left")}>
                      <button onClick={() => toggle(c.key, c.numeric)} className="inline-flex items-center gap-1 hover:text-foreground">
                        {c.header}
                        {sort.key === c.key && (sort.dir === 1 ? <ArrowUp className="h-3 w-3" /> : <ArrowDown className="h-3 w-3" />)}
                      </button>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {rows.map((r) => {
                  const alerta = r.pct_parado > ALERTA_PARADO;
                  return (
                    <tr key={r.sales_agent} className={cn("border-b border-border", alerta && "bg-warning-soft")}>
                      {cols.map((c) => (
                        <td key={c.key} className={cn("whitespace-nowrap px-3 py-2.5", c.numeric && "text-right tabular-nums",
                          c.key === "pct_parado" && alerta && "font-semibold text-warning-foreground")}>
                          {c.key === "sales_agent" ? (
                            <Link to="/pipeline" search={{ regiao: r.regional_office ?? "", manager: r.manager ?? "", vendedor: r.sales_agent ?? "" }}
                              className="font-medium text-primary underline-offset-2 hover:underline">
                              {r.sales_agent}
                            </Link>
                          ) : c.fmt ? c.fmt(r) : c.numeric ? formatNumber(r[c.key] as number) : (r[c.key] as string)}
                        </td>
                      ))}
                    </tr>
                  );
                })}
              </tbody>
              <tfoot>
                <tr className="bg-muted font-semibold">
                  {cols.map((c, i) => (
                    <td key={c.key} className={cn("px-3 py-2.5", c.numeric && "text-right tabular-nums")}>
                      {i === 0 ? `Total (${rows.length})` : c.total ? c.total(rows) : c.numeric ? formatNumber(sum(rows, c.key)) : ""}
                    </td>
                  ))}
                </tr>
              </tfoot>
            </table>
          </div>
        )}
      </div>
      <p className="mt-2 text-xs text-muted-foreground">Linhas em âmbar: mais de 70% do pipeline aberto parado além do limite histórico.</p>
    </div>
  );
}
