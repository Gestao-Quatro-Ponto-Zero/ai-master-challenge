// Hierarquia de superfícies:
//   Superficie — o painel de um bloco (branco, borda neutra, sem sombra);
//   Linha      — item de lista dentro dele: divisória entre itens, sem outra borda;
//   Cartao     — cartão solto (Pipeline): branco com borda leve, sem sombra pesada;
//   Numero     — número do Painel: leve, sem sombra.
import type { ReactNode } from "react";

export const classeSuperficie = "rounded-cartao border border-borda bg-superficie";
export const classeCartao = "rounded-cartao border border-divisoria bg-superficie hover:border-borda";

export function Superficie({ titulo, idTitulo, acoes, className = "", children }: { titulo?: string; idTitulo?: string; acoes?: ReactNode; className?: string; children: ReactNode }) {
  return (
    <section aria-labelledby={titulo ? idTitulo : undefined} className={`${classeSuperficie} p-4 ${className}`}>
      {titulo ? (
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <h2 id={idTitulo} className="text-lg font-bold">
            {titulo}
          </h2>
          {acoes}
        </div>
      ) : null}
      {children}
    </section>
  );
}

/** Lista com divisórias, para usar dentro de uma Superficie. */
export function ListaDivisoria({ className = "", children, ...resto }: { className?: string; children: ReactNode } & React.OlHTMLAttributes<HTMLOListElement>) {
  return (
    <ol className={`divide-y divide-divisoria ${className}`} {...resto}>
      {children}
    </ol>
  );
}

/** Segmentos (2 a 4 opções que se excluem): medida do funil, colunas do Pipeline no celular. */
export function Alternador<T extends string>({ rotulo, valor, opcoes, onMudar, papel = "group", className = "" }: { rotulo: string; valor: T; opcoes: { valor: T; rotulo: ReactNode }[]; onMudar: (v: T) => void; papel?: "group" | "tablist"; className?: string }) {
  return (
    <div role={papel} aria-label={rotulo} className={`inline-flex h-10 max-w-full shrink-0 gap-1 rounded-controle border border-borda bg-superficie-2 p-1 ${className}`}>
      {opcoes.map((o) => {
        const ativo = o.valor === valor;
        return (
          <button
            key={o.valor}
            type="button"
            role={papel === "tablist" ? "tab" : undefined}
            aria-selected={papel === "tablist" ? ativo : undefined}
            aria-pressed={papel === "group" ? ativo : undefined}
            onClick={() => onMudar(o.valor)}
            className={`min-w-0 flex-auto truncate rounded-controle px-3 text-sm font-semibold whitespace-nowrap ${ativo ? "bg-superficie text-marinho shadow-menu" : "text-texto-2 hover:text-marinho"}`}
          >
            {o.rotulo}
          </button>
        );
      })}
    </div>
  );
}

/** Caixa de marcar estilizada (tabela de Leads), acessível pelo teclado como a nativa. */
export function Marcador({ checked, onChange, rotulo }: { checked: boolean; onChange: () => void; rotulo: string }) {
  return (
    <span className="relative inline-flex h-5 w-5 items-center justify-center">
      <input
        type="checkbox"
        aria-label={rotulo}
        checked={checked}
        onChange={onChange}
        className="peer h-5 w-5 cursor-pointer appearance-none rounded-[5px] border border-borda-forte bg-superficie checked:border-marinho checked:bg-marinho focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-marinho"
      />
      <svg viewBox="0 0 24 24" aria-hidden className="pointer-events-none absolute h-3.5 w-3.5 text-branco opacity-0 peer-checked:opacity-100" fill="none" stroke="currentColor" strokeWidth={3} strokeLinecap="round" strokeLinejoin="round">
        <path d="M5 12.5l4.5 4.5L19 7.5" />
      </svg>
    </span>
  );
}
