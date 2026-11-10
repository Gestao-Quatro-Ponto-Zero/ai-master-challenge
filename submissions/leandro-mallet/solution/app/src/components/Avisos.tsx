"use client";
// Avisos curtos no rodapé ("Salvo", "Desfazer" por alguns segundos, erro em frase simples).
import { createContext, useCallback, useContext, useMemo, useRef, useState, type ReactNode } from "react";
import { useRouter } from "next/navigation";
import { CONFIG } from "@/lib/config";
import { pedir } from "@/lib/cliente";
import { fraseLoteDesfeito } from "@/lib/lotes";

interface Aviso {
  id: number;
  texto: string;
  tipo: "ok" | "erro";
  desfazer?: string | null;
  codigo?: string;
}

interface Api {
  ok: (texto: string, desfazer?: string | null) => void;
  erro: (texto: string, codigo?: string) => void;
  /** Recarrega os dados da tela depois de uma mudança (e avisa o modal aberto). */
  atualizar: () => void;
  revisao: number;
}

const Contexto = createContext<Api>({ ok: () => {}, erro: () => {}, atualizar: () => {}, revisao: 0 });
export const useAvisos = () => useContext(Contexto);

export function Avisos({ children }: { children: ReactNode }) {
  const [lista, setLista] = useState<Aviso[]>([]);
  const [revisao, setRevisao] = useState(0);
  const seq = useRef(1);
  const router = useRouter();
  const atualizar = useCallback(() => {
    setRevisao((r) => r + 1);
    router.refresh();
  }, [router]);

  const fechar = useCallback((id: number) => setLista((l) => l.filter((a) => a.id !== id)), []);
  const abrir = useCallback(
    (a: Omit<Aviso, "id">) => {
      const id = seq.current++;
      setLista((l) => [...l.slice(-2), { ...a, id }]);
      setTimeout(() => fechar(id), (a.tipo === "erro" ? 8 : CONFIG.segundosDesfazer) * 1000);
    },
    [fechar],
  );

  const api = useMemo<Api>(
    () => ({
      ok: (texto, desfazer) => abrir({ texto, tipo: "ok", desfazer }),
      erro: (texto, codigo) => abrir({ texto, tipo: "erro", codigo }),
      atualizar,
      revisao,
    }),
    [abrir, atualizar, revisao],
  );

  async function desfazer(a: Aviso) {
    fechar(a.id);
    const r = await pedir<{ restaurados?: number; pulados?: number }>("/api/desfazer", "POST", { token: a.desfazer });
    if (r.ok) {
      const lote = r.dados?.restaurados !== undefined ? { restaurados: r.dados.restaurados, pulados: r.dados.pulados ?? 0 } : null;
      abrir({ texto: lote ? fraseLoteDesfeito(lote) : "Desfeito.", tipo: "ok" });
      atualizar();
    } else abrir({ texto: r.erro ?? "Não foi possível desfazer.", tipo: "erro", codigo: r.codigo });
  }

  return (
    <Contexto.Provider value={api}>
      {children}
      <div className="pointer-events-none fixed inset-x-0 bottom-4 z-50 flex flex-col items-center gap-2 px-4" aria-live="polite">
        {lista.map((a) => (
          <div
            key={a.id}
            role={a.tipo === "erro" ? "alert" : "status"}
            className={`pointer-events-auto flex max-w-xl animate-entrar items-center gap-3 rounded-cartao px-4 py-3 text-sm shadow-modal ${
              a.tipo === "erro" ? "border border-erro bg-erro-fundo text-erro" : "bg-marinho text-branco"
            }`}
          >
            <span>{a.texto}</span>
            {a.desfazer ? (
              <button onClick={() => desfazer(a)} className="rounded-controle border border-dourado px-2 py-1 font-semibold text-dourado-claro">
                Desfazer
              </button>
            ) : null}
            {a.codigo ? (
              <details className="text-xs">
                <summary className="cursor-pointer underline">Ver detalhes</summary>
                <span>Código para suporte: {a.codigo}</span>
              </details>
            ) : null}
          </div>
        ))}
      </div>
    </Contexto.Provider>
  );
}
