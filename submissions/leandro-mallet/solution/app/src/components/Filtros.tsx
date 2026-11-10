"use client";
// Filtros do topo das telas: o campo livre (que vira etiquetas removíveis) e, para manager e admin,
// os seletores de região, manager e vendedor. Tudo fica no link da página.
import { useState } from "react";
import { usePathname, useRouter, useSearchParams } from "next/navigation";
import { codificar, type Etiqueta } from "@/lib/filtro/etiquetas";
import { interpretar, type Contexto } from "@/lib/filtro/interpretar";
import { Botao } from "./ui/Botao";
import { Campo } from "./ui/Campo";
import { EtiquetaRemovivel } from "./ui/Etiqueta";
import { Seletor as SeletorUi } from "./ui/Seletor";

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
        <Campo id="filtro-livre" type="search" value={frase} onChange={(e) => setFrase(e.target.value)} placeholder={`Filtrar: ex. "${exemplo}"`} className="min-w-0 flex-1" />
        <Botao type="submit" nivel="secundario">
          Filtrar
        </Botao>
      </form>
      {etiquetas.length ? (
        <div className="mt-2 flex flex-wrap items-center gap-2 text-sm">
          <span className="text-texto-2">Entendi assim:</span>
          {etiquetas.map((e, i) => (
            <EtiquetaRemovivel key={`${e.rotulo}-${i}`} rotuloRemover={`Remover o filtro ${e.rotulo}`} onRemover={() => aplicar(etiquetas.filter((_, j) => j !== i))}>
              {e.rotulo}
            </EtiquetaRemovivel>
          ))}
          <Botao nivel="discreto" tamanho="compacto" onClick={() => aplicar([])}>
            Limpar filtros
          </Botao>
        </div>
      ) : null}
    </div>
  );
}

/** Seletor que grava a escolha no link da página (ordem, região, manager, vendedor). */
export function Seletor({ nome, rotulo, valor, opcoes, todos }: { nome: string; rotulo: string; valor: string; opcoes: string[] | { valor: string; rotulo: string }[]; todos?: string }) {
  const ir = useLink();
  const lista = [
    ...(todos ? [{ valor: "", rotulo: todos }] : []),
    ...opcoes.map((o) => (typeof o === "string" ? { valor: o, rotulo: o } : o)),
  ];
  return (
    <div className="flex min-w-0 items-center gap-2 text-sm text-texto-2">
      <span aria-hidden>{rotulo}</span>
      <SeletorUi
        rotulo={rotulo}
        valor={valor}
        opcoes={lista}
        className="min-w-36"
        onMudar={(v) => ir({ [nome]: v || null, ...(nome === "regiao" ? { manager: null, vendedor: null } : nome === "manager" ? { vendedor: null } : {}) })}
      />
    </div>
  );
}
