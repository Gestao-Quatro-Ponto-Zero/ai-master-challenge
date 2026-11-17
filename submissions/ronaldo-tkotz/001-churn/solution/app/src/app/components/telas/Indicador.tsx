/** A headline number in a screen's single header row (D32): plain label, value, at most one short note. */
export function Indicador({ rotulo, valor, nota, separa = false }: { rotulo: string; valor: string; nota?: string; separa?: boolean }) {
  return (
    <div className={`min-w-0 flex-auto whitespace-nowrap px-2 py-1.5 2xl:px-3 ${separa ? "border-l border-edge-strong" : "border-l border-edge first:border-l-0"}`}>
      <div className="truncate text-[10.5px] text-muted" title={rotulo}>{rotulo}</div>
      <div className="text-[19px] font-semibold leading-tight tabular-nums tracking-tight text-foreground">{valor}</div>
      {nota && <div className="truncate text-[10.5px] text-faint">{nota}</div>}
    </div>
  );
}

/** The header row that holds the Indicador tiles. */
export function Cabecalho({ children }: { children: React.ReactNode }) {
  return <section className="flex min-w-0 flex-wrap overflow-hidden rounded-lg border border-edge bg-panel py-1 xl:flex-nowrap">{children}</section>;
}
