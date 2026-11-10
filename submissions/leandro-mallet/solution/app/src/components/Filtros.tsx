"use client";
// Filtros do topo das telas: o campo livre (que vira etiquetas removíveis) e, para manager e admin,
// os seletores de região, manager e vendedor. Tudo fica no link da página.
import { useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { codificar, type Etiqueta } from "@/lib/filtro/etiquetas";
import { interpretar, type Contexto } from "@/lib/filtro/interpretar";

function useLink() {
  const params = useSearchParams();
  const caminho = usePathname();
  const router = useRouter();
  return (mudancas: Record<string, string | null>) => {
    const p = new URLSearchParams(params.toString());
    for (const [k, v] of Object.entries(mudancas)) if (v) p.set(k, v); else p.delete(k);
    p.delete("deal");
    p.delete("n");
    router.push(p.size ? `${caminho}?${p}` : caminho, { scroll: false });
  };
}

export function FiltroLivre({ contexto, etiquetas, exemplo }: { contexto: Contexto; etiquetas: Etiqueta[]; exemplo: string }) {
  const [frase, setFrase] = useState("");
  const ir = useLink();
  const aplicar = (lista: Etiqueta[]) => ir({ f: lista.length ? codificar(lista) : null });

  function enviar(e: React.FormEvent) {
    e.preventDefault();
    if (!frase.trim()) return;
    const novas = interpretar(frase, contexto).etiquetas;
    const semRepetir = novas.filter((n) => !etiquetas.some((x) => x.rotulo === n.rotulo));
    aplicar([...etiquetas, ...semRepetir]);
    setFrase("");
  }

  return (
    <div className="min-w-0 flex-1 basis-full sm:basis-0">
      <form onSubmit={enviar} className="flex gap-2">
        <label className="sr-only" htmlFor="filtro-livre">
          Filtrar
        </label>
        <input
          id="filtro-livre"
          type="search"
          value={frase}
          onChange={(e) => setFrase(e.target.value)}
          placeholder={`Filtrar: ex. "${exemplo}"`}
          className="min-w-0 flex-1 rounded-controle border border-linha-forte bg-fundo px-3 py-2 text-sm"
        />
        <button type="submit" className="rounded-controle border border-marinho px-3 py-2 text-sm font-semibold">
          Filtrar
        </button>
      </form>
      {etiquetas.length ? (
        <div className="mt-2 flex flex-wrap items-center gap-2 text-sm">
          <span className="text-texto-2">Entendi assim:</span>
          {etiquetas.map((e, i) => (
            <span key={`${e.rotulo}-${i}`} className="inline-flex items-center gap-1 rounded-selo border border-dourado bg-marfim py-1 pr-1 pl-3">
              {e.rotulo}
              <button
                onClick={() => aplicar(etiquetas.filter((_, j) => j !== i))}
                aria-label={`Remover o filtro ${e.rotulo}`}
                className="rounded-selo px-2 leading-none font-bold text-bronze-escuro hover:bg-dourado-claro"
              >
                ×
              </button>
            </span>
          ))}
          <button onClick={() => aplicar([])} className="text-bronze-escuro underline">
            Limpar filtros
          </button>
        </div>
      ) : null}
    </div>
  );
}

export function Seletor({ nome, rotulo, valor, opcoes, todos }: { nome: string; rotulo: string; valor: string; opcoes: string[] | { valor: string; rotulo: string }[]; todos?: string }) {
  const ir = useLink();
  return (
    <label className="flex items-center gap-2 text-sm text-texto-2">
      {rotulo}
      <select
        value={valor}
        onChange={(e) => ir({ [nome]: e.target.value || null, ...(nome === "regiao" ? { manager: null, vendedor: null } : nome === "manager" ? { vendedor: null } : {}) })}
        className="max-w-full rounded-controle border border-linha-forte bg-fundo px-2 py-2 text-sm text-texto"
      >
        {todos ? <option value="">{todos}</option> : null}
        {opcoes.map((o) => {
          const op = typeof o === "string" ? { valor: o, rotulo: o } : o;
          return (
            <option key={op.valor} value={op.valor}>
              {op.rotulo}
            </option>
          );
        })}
      </select>
    </label>
  );
}
