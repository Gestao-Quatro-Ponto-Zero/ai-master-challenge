"use client";

export function Brand({ className = "" }: { className?: string }) {
  return <p className={`text-[13px] font-bold uppercase tracking-[0.2em] text-fg-3 ${className}`}>Lead Scorer</p>;
}

/**
 * Aviso de que as marcações não saem do navegador (não há backend nem login). Aparece uma vez por tela,
 * junto dos botões que gravam: na ficha (três ações) e nas pilhas (só Feito).
 */
export function SavedNote({ pile = false, className = "" }: { pile?: boolean; className?: string }) {
  return <p className={`text-[13px] ${className}`}>{pile ? "Feito fica salvo só neste navegador." : "Feito, Adiar e Não está vivo ficam salvos só neste navegador."}</p>;
}

export function Select({
  label,
  value,
  onChange,
  options,
  all,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: string[];
  all: string;
}) {
  return (
    <label className="block">
      <span className="sr-only">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className={`h-11 w-full rounded-lg border bg-navy pl-3 pr-9 text-sm transition-colors hover:border-line-strong ${value ? "border-gold text-fg" : "border-line text-fg-2"}`}
      >
        <option value="">{all}</option>
        {options.map((o) => (
          <option key={o} value={o}>
            {o}
          </option>
        ))}
      </select>
    </label>
  );
}

export function Empty({ title, children }: { title: string; children?: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-dashed border-line-strong px-4 py-10 text-center">
      <p className="text-sm font-semibold text-fg">{title}</p>
      {children && <div className="mt-2 text-sm text-fg-2">{children}</div>}
    </div>
  );
}

/** Botão secundário. `paper`: sobre o papel (fundo claro); sem isso, sobre o navy. */
export function ghostButton(paper = false, extra = "") {
  const tone = paper ? "border-ink/30 text-ink hover:border-ink" : "border-line-strong text-fg hover:border-gold-hi hover:text-gold-hi";
  return `inline-flex min-h-11 items-center justify-center rounded-lg border px-4 text-sm font-semibold transition-colors ${tone} ${extra}`;
}

/** Normaliza para busca: sem acento e em minúsculas. */
export const fold = (s: string) => s.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();

/** "1 feito", "2 feitos". */
export const plural = (n: number, one: string, many: string) => `${n} ${n === 1 ? one : many}`;
