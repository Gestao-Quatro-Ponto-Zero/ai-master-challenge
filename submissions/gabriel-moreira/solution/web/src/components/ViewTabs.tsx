export type Aba = "oportunidades" | "gestao";

/** Navegação por visão: exatamente duas abas, sem condicionamento a
 * papel (Requirement "Navegação por visão") — substitui as cinco abas
 * de estado. */
export function ViewTabs({ aba, onChange }: { aba: Aba; onChange: (aba: Aba) => void }) {
  return (
    <div className="flex gap-2 border-b border-border pb-3">
      <TabButton label="Oportunidades" active={aba === "oportunidades"} onClick={() => onChange("oportunidades")} />
      <TabButton label="Gestão" active={aba === "gestao"} onClick={() => onChange("gestao")} />
    </div>
  );
}

function TabButton({ label, active, onClick }: { label: string; active: boolean; onClick: () => void }) {
  return (
    <button
      type="button"
      aria-current={active ? "page" : undefined}
      onClick={onClick}
      className={
        "px-4 py-2 rounded-xs text-sm font-semibold border transition-colors " +
        (active ? "bg-navy text-white border-navy" : "bg-white text-navy border-border hover:border-gold")
      }
    >
      {label}
    </button>
  );
}
