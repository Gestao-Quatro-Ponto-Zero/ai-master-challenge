import { ESTADO_LABELS, ESTADOS, type Estado, type Role } from "../types";

export type Aba = Estado | "gestao";

const TAB_STYLES: Record<Estado, string> = {
  foco_urgente: "data-[active=true]:bg-gold data-[active=true]:text-navy data-[active=true]:border-gold",
  acompanhar: "data-[active=true]:bg-navy data-[active=true]:text-white data-[active=true]:border-navy",
  engajar: "data-[active=true]:bg-navy/80 data-[active=true]:text-white data-[active=true]:border-navy/80",
  qualificar: "data-[active=true]:bg-gray-200 data-[active=true]:text-navy data-[active=true]:border-gray-300",
  desistir: "data-[active=true]:bg-alert data-[active=true]:text-white data-[active=true]:border-alert",
};

export function StateTabs({
  aba,
  onChange,
  role,
  counts,
}: {
  aba: Aba;
  onChange: (aba: Aba) => void;
  role: Role;
  counts?: Partial<Record<Estado, number>>;
}) {
  return (
    <div className="flex flex-wrap gap-2 border-b border-border pb-3">
      {ESTADOS.map((estado) => (
        <button
          key={estado}
          type="button"
          data-active={aba === estado}
          onClick={() => onChange(estado)}
          className={
            "px-4 py-2 rounded-xs text-sm font-semibold border border-border bg-white text-navy transition-colors " +
            TAB_STYLES[estado]
          }
        >
          {ESTADO_LABELS[estado]}
          {counts?.[estado] !== undefined && (
            <span className="ml-1.5 text-xs opacity-75">({counts[estado]})</span>
          )}
        </button>
      ))}
      {role !== "sales_agent" && (
        <button
          type="button"
          data-active={aba === "gestao"}
          onClick={() => onChange("gestao")}
          className="px-4 py-2 rounded-xs text-sm font-semibold border border-border bg-white text-navy data-[active=true]:bg-navy data-[active=true]:text-white data-[active=true]:border-navy transition-colors"
        >
          Gestão
        </button>
      )}
    </div>
  );
}
