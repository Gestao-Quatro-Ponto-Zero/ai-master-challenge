"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

/** Creates a screen and opens it (D46.2). `compacto` is the sidebar's "+ Nova tela". */
export function NovaTela({ compacto = false }: { compacto?: boolean }) {
  const router = useRouter();
  const [nome, setNome] = useState("");
  const [ocupado, setOcupado] = useState(false);
  const criar = async (n: string) => {
    if (ocupado) return;
    setOcupado(true);
    try {
      const r = await fetch("/api/telas", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ nome: n }) });
      const j = await r.json();
      if (r.ok) {
        window.dispatchEvent(new CustomEvent("ravenstack:telas-mudaram"));
        router.push(`/telas/${j.tela.id}`);
      }
    } finally {
      setOcupado(false);
    }
  };
  if (compacto) {
    return (
      <button
        onClick={() => {
          const n = window.prompt("Nome da nova tela", "Minha análise");
          if (n !== null) void criar(n);
        }}
        disabled={ocupado}
        className="flex items-center gap-2.5 rounded-lg px-2.5 py-1.5 text-left text-[12.5px] text-faint transition-colors hover:bg-panel/60 hover:text-foreground"
      >
        <span className="grid h-4 w-4 place-items-center text-[14px] leading-none">+</span>
        Nova tela
      </button>
    );
  }
  return (
    <form
      onSubmit={(e) => {
        e.preventDefault();
        void criar(nome);
      }}
      className="flex gap-2"
    >
      <input
        value={nome}
        onChange={(e) => setNome(e.target.value)}
        maxLength={80}
        placeholder="Nome da tela (ex.: Churn das contas Enterprise)"
        className="min-w-0 flex-1 rounded border border-edge bg-background px-2 py-1.5 text-[12.5px] text-foreground placeholder:text-faint"
      />
      <button type="submit" disabled={ocupado} className="rounded bg-accent px-3 py-1.5 text-[12px] font-semibold text-black hover:opacity-90 disabled:opacity-50">
        Criar tela
      </button>
    </form>
  );
}
