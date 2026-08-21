import { useMemo } from "react";
import type { FilterOptions, Filtros } from "../types";

/** Filtros de organização (vendedor, gerente, escritório), produto e
 * confiança — ordinários sobre o funil inteiro, sem condicionamento a
 * papel (Requirement "Filtros"). Opções vêm de `/filter-options`, nunca
 * dos itens de uma página. Selecionar um gerente ou escritório encadeia
 * (restringe) as opções de vendedor. */
export function FilterBar({
  options,
  filtros,
  activeCount,
  onChange,
  onClearAll,
}: {
  options: FilterOptions;
  filtros: Filtros;
  activeCount: number;
  onChange: (patch: Partial<Filtros>) => void;
  onClearAll: () => void;
}) {
  const vendedores = useMemo(
    () =>
      options.vendedores
        .filter((v) => !filtros.manager || v.manager === filtros.manager)
        .filter((v) => !filtros.regional_office || v.regional_office === filtros.regional_office)
        .map((v) => v.nome)
        .sort((a, b) => a.localeCompare(b, "pt-BR")),
    [options.vendedores, filtros.manager, filtros.regional_office]
  );

  const gerentes = useMemo(
    () =>
      options.gerentes
        .filter((g) => !filtros.regional_office || g.regional_office === filtros.regional_office)
        .map((g) => g.nome)
        .sort((a, b) => a.localeCompare(b, "pt-BR")),
    [options.gerentes, filtros.regional_office]
  );

  return (
    <div className="flex flex-wrap gap-3 items-end bg-white border border-border rounded-sm p-3">
      <Select
        label="Vendedor"
        value={filtros.sales_agent ?? ""}
        options={vendedores}
        onChange={(v) => onChange({ sales_agent: v || undefined })}
      />
      <Select
        label="Gerente"
        value={filtros.manager ?? ""}
        options={gerentes}
        onChange={(v) => onChange({ manager: v || undefined })}
      />
      <Select
        label="Escritório"
        value={filtros.regional_office ?? ""}
        options={options.escritorios}
        onChange={(v) => onChange({ regional_office: v || undefined })}
      />
      <Select
        label="Produto"
        value={filtros.product ?? ""}
        options={options.produtos}
        onChange={(v) => onChange({ product: v || undefined })}
      />
      <div className="text-xs text-muted flex flex-col gap-1">
        Confiança (0–100)
        <div className="flex items-center gap-1">
          <input
            type="number"
            min={0}
            max={100}
            placeholder="mín"
            value={filtros.confianca_min ?? ""}
            onChange={(e) => onChange({ confianca_min: e.target.value || undefined })}
            className="border border-border rounded-xs px-2 py-1.5 text-sm text-navy bg-white w-20"
          />
          <span>–</span>
          <input
            type="number"
            min={0}
            max={100}
            placeholder="máx"
            value={filtros.confianca_max ?? ""}
            onChange={(e) => onChange({ confianca_max: e.target.value || undefined })}
            className="border border-border rounded-xs px-2 py-1.5 text-sm text-navy bg-white w-20"
          />
        </div>
      </div>

      <div className="ml-auto flex items-center gap-3">
        {activeCount > 0 && (
          <span className="text-xs text-muted">
            {activeCount} filtro{activeCount === 1 ? "" : "s"} ativo{activeCount === 1 ? "" : "s"}
          </span>
        )}
        <button
          type="button"
          onClick={onClearAll}
          disabled={activeCount === 0}
          className="text-xs text-muted hover:text-navy underline disabled:opacity-40 disabled:hover:text-muted disabled:no-underline"
        >
          Limpar filtros
        </button>
      </div>
    </div>
  );
}

function Select({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (value: string) => void;
}) {
  return (
    <label className="text-xs text-muted flex flex-col gap-1">
      {label}
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="border border-border rounded-xs px-2 py-1.5 text-sm text-navy bg-white min-w-[9rem]"
      >
        <option value="">Todos</option>
        {options.map((opt) => (
          <option key={opt} value={opt}>
            {opt}
          </option>
        ))}
      </select>
    </label>
  );
}
