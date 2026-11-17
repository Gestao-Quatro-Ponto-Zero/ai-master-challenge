"use client";

import { useState } from "react";
import type { ChartSpec } from "@/engine/parts";

/** "Enviar para uma tela" (D46.5, ISC-43): puts a chat chart on one of the user's screens, with its SQL. */
export function EnviarParaTela({ chart, sql }: { chart: ChartSpec; sql: string[] }) {
  const [aberto, setAberto] = useState(false);
  const [telas, setTelas] = useState<{ id: string; nome: string }[] | null>(null);
  const [feito, setFeito] = useState<string | null>(null);
  const [erro, setErro] = useState<string | null>(null);

  const abrir = async () => {
    setAberto(!aberto);
    if (telas) return;
    const r = await fetch("/api/telas");
    setTelas(r.ok ? (await r.json()).telas : []);
  };
  const enviar = async (id: string | null, nome: string) => {
    setErro(null);
    try {
      let destino = id;
      if (!destino) {
        const r = await fetch("/api/telas", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ nome }) });
        if (!r.ok) throw new Error("não foi possível criar a tela");
        destino = (await r.json()).tela.id as string;
        window.dispatchEvent(new CustomEvent("ravenstack:telas-mudaram"));
      }
      const r = await fetch(`/api/telas/${destino}/paineis`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ chart, sql }) });
      if (!r.ok) throw new Error((await r.json().catch(() => ({}))).error ?? `erro ${r.status}`);
      setFeito(nome);
      setAberto(false);
    } catch (e) {
      setErro(e instanceof Error ? e.message : String(e));
    }
  };

  return (
    <div className="relative">
      <button onClick={() => void abrir()} className="rounded border border-edge px-2 py-0.5 text-[11px] text-muted hover:border-edge-strong hover:text-foreground">
        {feito ? `Na tela "${feito}" ✓` : "Enviar para uma tela"}
      </button>
      {aberto && (
        <div className="absolute bottom-full left-0 z-20 mb-1 flex w-56 flex-col gap-0.5 rounded-md border border-edge-strong bg-background p-1 shadow-xl">
          {telas === null && <span className="px-2 py-1 text-[11.5px] text-faint">Carregando…</span>}
          {telas?.map((t) => (
            <button key={t.id} onClick={() => void enviar(t.id, t.nome)} className="truncate rounded px-2 py-1 text-left text-[12px] text-muted hover:bg-panel hover:text-foreground">
              {t.nome}
            </button>
          ))}
          <button onClick={() => void enviar(null, chart.title || "Do chat")} className="rounded px-2 py-1 text-left text-[12px] text-accent hover:bg-panel">
            + Nova tela com este gráfico
          </button>
        </div>
      )}
      {erro && <span className="ml-2 text-[11px] text-red-400">{erro}</span>}
    </div>
  );
}
