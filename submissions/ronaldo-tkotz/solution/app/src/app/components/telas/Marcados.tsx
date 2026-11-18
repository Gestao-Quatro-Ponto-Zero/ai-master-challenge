"use client";

import { createContext, useCallback, useContext, useEffect, useState, type RefObject } from "react";
import { usePathname, useSearchParams } from "next/navigation";
import { capturar } from "./captura";

/**
 * Marking charts for the deck (D44). The provider knows which panels are marked; the toggle in
 * each panel header copies the chart faithfully (captura.ts) and stores it, or removes the mark.
 * A chart is identified by screen + title + the filters in force: the same chart under another
 * filter is a different mark.
 */
interface Estado {
  chaves: Set<string>;
  definir: (chave: string, marcado: boolean) => void;
}
const Contexto = createContext<Estado | null>(null);

export function MarcadosProvider({ children }: { children: React.ReactNode }) {
  const [chaves, setChaves] = useState<Set<string>>(new Set());
  useEffect(() => {
    let vivo = true;
    fetch("/api/marcados")
      .then((r) => (r.ok ? r.json() : { marcados: [] }))
      .then((d: { marcados: { chave: string }[] }) => vivo && setChaves(new Set(d.marcados.map((m) => m.chave))))
      .catch(() => {});
    return () => {
      vivo = false;
    };
  }, []);
  const definir = useCallback((chave: string, marcado: boolean) => {
    setChaves((s) => {
      const n = new Set(s);
      if (marcado) n.add(chave);
      else n.delete(chave);
      return n;
    });
  }, []);
  return <Contexto.Provider value={{ chaves, definir }}>{children}</Contexto.Provider>;
}

/** Drops a mark from the shared state (after the server removed it). */
export function useDesmarcar(): (chave: string) => void {
  const ctx = useContext(Contexto);
  return (chave: string) => ctx?.definir(chave, false);
}

/** How many charts are marked (null outside the provider). */
export function useTotalMarcados(): number | null {
  return useContext(Contexto)?.chaves.size ?? null;
}

/** "setor=FinTech&plano=Pro" — the filters, in a stable order. */
function filtrosAtuais(sp: URLSearchParams): string {
  const pares = [...sp.entries()].filter(([, v]) => v).sort(([a], [b]) => a.localeCompare(b));
  return new URLSearchParams(pares).toString();
}

export function MarcarToggle({
  titulo,
  nota,
  sql,
  alvo,
  rota: rotaFixa,
  filtros: filtrosFixos,
}: {
  titulo: string;
  nota?: string;
  sql: string[];
  alvo: RefObject<HTMLElement | null>;
  /** Overrides for charts that do not belong to the page (the chat's, D46.5: rota "/chat", no filters). */
  rota?: string;
  filtros?: string;
}) {
  const ctx = useContext(Contexto);
  const caminho = usePathname();
  const rota = rotaFixa ?? caminho;
  const sp = useSearchParams();
  const [ocupado, setOcupado] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  if (!ctx) return null;
  const filtros = filtrosFixos ?? filtrosAtuais(new URLSearchParams(sp.toString()));
  const chave = `${rota}|${titulo}|${filtros}`;
  const marcado = ctx.chaves.has(chave);

  const alternar = async () => {
    if (ocupado) return;
    setOcupado(true);
    setErro(null);
    try {
      if (marcado) {
        const r = await fetch("/api/marcados", { method: "DELETE", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ chave }) });
        if (!r.ok) throw new Error((await r.json().catch(() => ({}))).error ?? `erro ${r.status}`);
        ctx.definir(chave, false);
      } else {
        const el = alvo.current;
        if (!el) throw new Error("gráfico não encontrado");
        const painel = el.closest("section");
        const fundo = painel ? getComputedStyle(painel).backgroundColor : "#121218";
        const c = await capturar(el, fundo);
        const r = await fetch("/api/marcados", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ chave, rota, filtros, titulo, nota: nota ?? null, sql, ...c }),
        });
        if (!r.ok) throw new Error((await r.json().catch(() => ({}))).error ?? `erro ${r.status}`);
        ctx.definir(chave, true);
      }
    } catch (e) {
      setErro(e instanceof Error ? e.message : String(e));
    } finally {
      setOcupado(false);
    }
  };

  const dica = erro ? `Não foi possível marcar: ${erro}` : marcado ? "Marcado para o deck. Clique para desmarcar." : "Marcar este gráfico para o deck";
  return (
    <button
      onClick={() => void alternar()}
      aria-pressed={marcado}
      title={dica}
      disabled={ocupado}
      className={`grid h-[21px] w-[23px] shrink-0 place-items-center rounded border transition-colors disabled:opacity-50 ${
        erro ? "border-red-400 text-red-400" : marcado ? "border-accent bg-accent-soft text-accent" : "border-edge text-faint hover:border-edge-strong hover:text-muted"
      }`}
    >
      <svg viewBox="0 0 24 24" fill={marcado ? "currentColor" : "none"} stroke="currentColor" strokeWidth="2" strokeLinejoin="round" className="h-3 w-3">
        <path d="M6 3h12v18l-6-4.5L6 21z" />
      </svg>
      <span className="sr-only">{marcado ? "Desmarcar" : "Marcar para o deck"}</span>
    </button>
  );
}
