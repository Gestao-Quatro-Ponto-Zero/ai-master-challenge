export type Aba = "oportunidades" | "sobrecarga" | "gestao";

/** Navegação por visão: exatamente três abas, sem condicionamento a
 * papel (Requirement "Navegação por visão") — Sobrecarga é a única
 * superfície de listagem onde o vendedor sugerido aparece. */
export function ViewTabs({
  aba,
  onChange,
  sobrecarregadas,
}: {
  aba: Aba;
  onChange: (aba: Aba) => void;
  /** Contagem de oportunidades sobrecarregadas — exibida como badge na
   * aba, quando conhecida. */
  sobrecarregadas?: number;
}) {
  return (
    <div className="flex flex-wrap gap-2 border-b border-border pb-3">
      <TabButton label="Oportunidades" active={aba === "oportunidades"} onClick={() => onChange("oportunidades")} />
      <TabButton
        label="Sobrecarga"
        active={aba === "sobrecarga"}
        onClick={() => onChange("sobrecarga")}
        badge={sobrecarregadas}
      />
      <TabButton label="Gestão" active={aba === "gestao"} onClick={() => onChange("gestao")} />
    </div>
  );
}

function TabButton({
  label,
  active,
  onClick,
  badge,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
  badge?: number;
}) {
  return (
    <button
      type="button"
      aria-current={active ? "page" : undefined}
      onClick={onClick}
      className={
        "px-4 py-2 rounded-xs text-sm font-semibold border transition-colors flex items-center gap-2 " +
        (active ? "bg-navy text-white border-navy" : "bg-white text-navy border-border hover:border-gold")
      }
    >
      {label}
      {!!badge && (
        <span
          className={
            "text-xs font-bold rounded-full px-1.5 py-0.5 leading-none " +
            (active ? "bg-white text-navy" : "bg-gold/20 text-navy")
          }
        >
          {badge}
        </span>
      )}
    </button>
  );
}
