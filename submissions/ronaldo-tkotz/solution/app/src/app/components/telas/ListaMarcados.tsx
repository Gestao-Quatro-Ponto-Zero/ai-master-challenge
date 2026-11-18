"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useDesmarcar } from "./Marcados";

interface Item {
  id: number;
  chave: string;
  titulo: string;
  nota: string | null;
  tela: string;
  filtros: string;
  largura: number;
  altura: number;
}

/** The marked charts as cards, with the .pptx for all and PNG/SVG for each (D44). */
export function ListaMarcados({ itens }: { itens: Item[] }) {
  const router = useRouter();
  const desmarcar = useDesmarcar();
  const [removendo, setRemovendo] = useState<number | null>(null);

  const remover = async (item: Item) => {
    setRemovendo(item.id);
    try {
      const r = await fetch(`/api/marcados/${item.id}`, { method: "DELETE" });
      if (r.ok) {
        desmarcar(item.chave);
        router.refresh();
      }
    } finally {
      setRemovendo(null);
    }
  };

  if (itens.length === 0) {
    return (
      <div className="rounded-lg border border-dashed border-edge-strong bg-panel/50 p-6 text-[13px] text-muted">
        Nenhum gráfico marcado ainda. Nas telas, clique no marcador ao lado do botão SQL de cada gráfico.
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-4">
      <p className="text-[12px] text-faint">
        {itens.length} {itens.length === 1 ? "gráfico marcado" : "gráficos marcados"}, na ordem em que foram marcados
      </p>
      <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {itens.map((item, i) => (
          <article key={item.id} className="flex min-w-0 flex-col gap-2 rounded-lg border border-edge bg-panel p-3">
            <div className="flex items-start gap-2">
              <span className="font-mono text-[11px] text-accent">{String(i + 1).padStart(2, "0")}</span>
              <div className="min-w-0 flex-1">
                <h2 className="truncate text-[13px] font-semibold text-foreground" title={item.titulo}>{item.titulo}</h2>
                {item.nota && <p className="truncate text-[11px] text-faint" title={item.nota}>{item.nota}</p>}
              </div>
            </div>
            {/* The slide frame (16:9): the chart keeps its proportions inside, as in the .pptx. */}
            <div className="flex aspect-video items-center justify-center overflow-hidden rounded border border-edge bg-background p-2">
              {/* eslint-disable-next-line @next/next/no-img-element -- a stored snapshot served by our own API */}
              <img
                src={`/api/marcados/${item.id}`}
                alt={item.titulo}
                width={item.largura}
                height={item.altura}
                className="h-full w-full object-contain"
              />
            </div>
            <p className="text-[11px] text-muted">
              {item.tela} · {item.filtros}
            </p>
            <div className="flex items-center gap-3 text-[11.5px]">
              <a href={`/api/marcados/${item.id}?baixar=1`} className="text-faint hover:text-foreground">PNG</a>
              <a href={`/api/marcados/${item.id}?formato=svg&baixar=1`} className="text-faint hover:text-foreground">SVG</a>
              <button
                onClick={() => void remover(item)}
                disabled={removendo === item.id}
                className="ml-auto rounded border border-red-500/60 bg-red-500/10 px-2 py-0.5 font-medium text-red-400 transition-colors hover:bg-red-500/20 hover:text-red-300 disabled:opacity-50"
              >
                Desmarcar
              </button>
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
