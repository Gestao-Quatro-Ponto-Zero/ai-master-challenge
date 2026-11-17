"use client";

import { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { NovaTela } from "./NovaTela";

/** "Minhas telas" in the side menu (D46.2): the user's screens and "+ Nova tela". */
export function MinhasTelasNav() {
  const router = useRouter();
  const pathname = usePathname();
  const [telas, setTelas] = useState<{ id: string; nome: string }[]>([]);
  useEffect(() => {
    let vivo = true;
    const carregar = () =>
      fetch("/api/telas")
        .then((r) => (r.ok ? r.json() : { telas: [] }))
        .then((j: { telas: { id: string; nome: string }[] }) => vivo && setTelas(j.telas))
        .catch(() => {});
    void carregar();
    window.addEventListener("ravenstack:telas-mudaram", carregar);
    return () => {
      vivo = false;
      window.removeEventListener("ravenstack:telas-mudaram", carregar);
    };
  }, []);
  return (
    <div className="flex flex-col gap-0.5">
      <button onClick={() => router.push("/telas")} className="px-2.5 pb-1 text-left text-[10px] font-medium uppercase tracking-wider text-faint hover:text-muted">
        Minhas telas
      </button>
      <div className="flex max-h-[180px] flex-col gap-0.5 overflow-y-auto">
        {telas.map((t) => {
          const ativa = pathname === `/telas/${t.id}`;
          return (
            <button
              key={t.id}
              onClick={() => router.push(`/telas/${t.id}`)}
              aria-current={ativa ? "page" : undefined}
              title={t.nome}
              className={`flex items-center gap-2.5 truncate rounded-lg px-2.5 py-1.5 text-left text-[12.5px] transition-colors hover:bg-panel/60 hover:text-foreground ${ativa ? "bg-panel text-foreground" : "text-muted"}`}
            >
              <span className={`h-1.5 w-1.5 shrink-0 rounded-sm ${ativa ? "bg-accent" : "bg-edge-strong"}`} />
              <span className="truncate">{t.nome}</span>
            </button>
          );
        })}
      </div>
      <NovaTela compacto />
    </div>
  );
}
