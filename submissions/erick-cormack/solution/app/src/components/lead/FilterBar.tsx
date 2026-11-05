import { useMemo } from "react";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { useParametros } from "@/hooks/useParametros";
import { useResumoVendedores } from "@/hooks/useResumoVendedores";
import type { Filters } from "@/lib/filters";
import { formatDate } from "@/lib/format";

const ALL = "__all__";

function uniq(v: (string | null)[]) {
  return [...new Set(v.filter((x): x is string => !!x))].sort((a, b) => a.localeCompare(b, "pt-BR"));
}

export function FilterBar({ filters, onChange }: { filters: Filters; onChange: (f: Filters) => void }) {
  const { data: equipe = [] } = useResumoVendedores();
  const { data: params } = useParametros();

  const regioes = useMemo(() => uniq(equipe.map((e) => e.regional_office)), [equipe]);
  const managers = useMemo(
    () => uniq(equipe.filter((e) => !filters.regiao || e.regional_office === filters.regiao).map((e) => e.manager)),
    [equipe, filters.regiao],
  );
  const vendedores = useMemo(
    () =>
      uniq(
        equipe
          .filter((e) => (!filters.regiao || e.regional_office === filters.regiao) && (!filters.manager || e.manager === filters.manager))
          .map((e) => e.sales_agent),
      ),
    [equipe, filters.regiao, filters.manager],
  );

  return (
    <div className="flex flex-col gap-3 border-b border-border bg-card px-4 py-3 md:flex-row md:items-end md:px-8">
      <div className="grid flex-1 grid-cols-1 gap-3 sm:grid-cols-3">
        <FilterSelect label="Região" value={filters.regiao} options={regioes}
          onChange={(regiao) => onChange({ regiao, manager: "", vendedor: "" })} />
        <FilterSelect label="Manager" value={filters.manager} options={managers}
          onChange={(manager) => onChange({ ...filters, manager, vendedor: "" })} />
        <FilterSelect label="Vendedor" value={filters.vendedor} options={vendedores}
          onChange={(vendedor) => onChange({ ...filters, vendedor })} />
      </div>
      {params && (
        <p className="text-xs text-muted-foreground md:pb-2">Retrato do CRM em {formatDate(params.data_referencia)}</p>
      )}
    </div>
  );
}

function FilterSelect({ label, value, options, onChange }: {
  label: string; value: string; options: string[]; onChange: (v: string) => void;
}) {
  return (
    <label className="flex flex-col gap-1 text-xs font-medium text-muted-foreground">
      {label}
      <Select value={value || ALL} onValueChange={(v) => onChange(v === ALL ? "" : v)}>
        <SelectTrigger className="h-9 bg-background text-sm text-foreground" aria-label={label}>
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={ALL}>Todos</SelectItem>
          {options.map((o) => (
            <SelectItem key={o} value={o}>{o}</SelectItem>
          ))}
        </SelectContent>
      </Select>
    </label>
  );
}
