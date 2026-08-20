import { useMemo } from "react";
import type { Confianca, Filtros, Oportunidade, Role } from "../types";

function uniqueSorted(values: (string | null)[]): string[] {
  return Array.from(new Set(values.filter((v): v is string => !!v))).sort((a, b) =>
    a.localeCompare(b, "pt-BR")
  );
}

export function FilterBar({
  todasOportunidades,
  role,
  filtros,
  onChange,
}: {
  todasOportunidades: Oportunidade[];
  role: Role;
  filtros: Filtros;
  onChange: (patch: Partial<Filtros>) => void;
}) {
  const opcoes = useMemo(
    () => ({
      vendedores: uniqueSorted(todasOportunidades.map((o) => o.sales_agent)),
      gerentes: uniqueSorted(todasOportunidades.map((o) => o.manager)),
      escritorios: uniqueSorted(todasOportunidades.map((o) => o.regional_office)),
      produtos: uniqueSorted(todasOportunidades.map((o) => o.product)),
    }),
    [todasOportunidades]
  );

  return (
    <div className="flex flex-wrap gap-3 items-end bg-white border border-border rounded-sm p-3">
      {role !== "sales_agent" && (
        <Select
          label="Vendedor"
          value={filtros.sales_agent ?? ""}
          options={opcoes.vendedores}
          onChange={(v) => onChange({ sales_agent: v || undefined })}
        />
      )}
      {role === "manager" && (
        <Select
          label="Gerente"
          value={filtros.manager ?? ""}
          options={opcoes.gerentes}
          onChange={(v) => onChange({ manager: v || undefined })}
        />
      )}
      {opcoes.escritorios.length > 1 && (
        <Select
          label="Escritório"
          value={filtros.regional_office ?? ""}
          options={opcoes.escritorios}
          onChange={(v) => onChange({ regional_office: v || undefined })}
        />
      )}
      <Select
        label="Produto"
        value={filtros.product ?? ""}
        options={opcoes.produtos}
        onChange={(v) => onChange({ product: v || undefined })}
      />
      <Select
        label="Confiança"
        value={filtros.confianca ?? ""}
        options={["A", "B", "C", "D"]}
        onChange={(v) => onChange({ confianca: (v as Confianca) || undefined })}
      />
      <NumberField
        label="Idade mín. (dias)"
        value={filtros.idade_min ?? ""}
        onChange={(v) => onChange({ idade_min: v || undefined })}
      />
      <NumberField
        label="Idade máx. (dias)"
        value={filtros.idade_max ?? ""}
        onChange={(v) => onChange({ idade_max: v || undefined })}
      />
      <button
        type="button"
        onClick={() =>
          onChange({
            sales_agent: undefined,
            manager: undefined,
            regional_office: undefined,
            product: undefined,
            confianca: undefined,
            idade_min: undefined,
            idade_max: undefined,
          })
        }
        className="text-xs text-muted hover:text-navy underline ml-auto"
      >
        Limpar filtros
      </button>
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

function NumberField({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="text-xs text-muted flex flex-col gap-1">
      {label}
      <input
        type="number"
        min={0}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="border border-border rounded-xs px-2 py-1.5 text-sm text-navy bg-white w-28"
      />
    </label>
  );
}
