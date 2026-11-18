"use client";

import { usePathname, useRouter, useSearchParams } from "next/navigation";
import type { OpcoesFiltro } from "@/engine/filtros";

const CAMPOS: { key: keyof OpcoesFiltro; label: string }[] = [
  { key: "setor", label: "Setor" },
  { key: "pais", label: "País" },
  { key: "origem", label: "Origem" },
  { key: "plano", label: "Plano" },
];

/**
 * Global filters (ISC-20): one row above the screen, kept in the URL so every screen
 * and every link reads the same filters. The server validates each value again.
 */
export function FiltrosBar({ opcoes }: { opcoes: OpcoesFiltro }) {
  const router = useRouter();
  const pathname = usePathname();
  const params = useSearchParams();

  const set = (key: string, value: string) => {
    const p = new URLSearchParams(params.toString());
    if (value) p.set(key, value);
    else p.delete(key);
    const q = p.toString();
    router.push(q ? `${pathname}?${q}` : pathname);
  };

  const ativos = CAMPOS.some((c) => params.get(c.key)) || params.get("alerta") === "sem";

  return (
    <div className="flex flex-wrap items-center gap-2 border-b border-edge bg-surface/60 px-4 py-2">
      <span className="text-[10.5px] font-medium uppercase tracking-wider text-faint">Filtros</span>
      {CAMPOS.map((c) => (
        <label key={c.key} className="inline-flex items-center gap-1.5 text-[12px] text-muted">
          {c.label}
          <select
            value={params.get(c.key) ?? ""}
            onChange={(e) => set(c.key, e.target.value)}
            className="rounded-md border border-edge bg-panel px-2 py-1 text-[12px] text-foreground"
          >
            <option value="">todos</option>
            {opcoes[c.key].map((v) => (
              <option key={v} value={v}>
                {v}
              </option>
            ))}
          </select>
        </label>
      ))}
      <label className="inline-flex items-center gap-1.5 text-[12px] text-muted">
        Registros em alerta
        <select
          value={params.get("alerta") === "sem" ? "sem" : ""}
          onChange={(e) => set("alerta", e.target.value)}
          className="rounded-md border border-edge bg-panel px-2 py-1 text-[12px] text-foreground"
        >
          <option value="">com (padrão)</option>
          <option value="sem">sem</option>
        </select>
      </label>
      {ativos && (
        <button onClick={() => router.push(pathname)} className="ml-auto text-[12px] text-muted underline-offset-2 hover:text-foreground hover:underline">
          Limpar filtros
        </button>
      )}
    </div>
  );
}
