"use client";
import { useEffect, useRef, type ReactNode } from "react";
import type { CorTag, Tag } from "@/lib/tipos";
import { BotaoIcone } from "./ui/Botao";
import { classeEtiqueta } from "./ui/Etiqueta";
import { Icone } from "./ui/Icones";

/** Caixa de diálogo padrão: véu, foco, Esc para fechar e clique fora. */
export function Dialogo({ titulo, largo, onFechar, children }: { titulo: string; largo?: boolean; onFechar: () => void; children: ReactNode }) {
  const caixa = useRef<HTMLDivElement>(null);
  useEffect(() => {
    caixa.current?.focus();
    const tecla = (e: KeyboardEvent) => e.key === "Escape" && onFechar();
    document.addEventListener("keydown", tecla);
    return () => document.removeEventListener("keydown", tecla);
  }, [onFechar]);
  return (
    <div className="fixed inset-0 z-40 flex items-stretch justify-center bg-veu sm:items-center sm:p-6" role="presentation" onClick={onFechar}>
      <div
        ref={caixa}
        tabIndex={-1}
        role="dialog"
        aria-modal="true"
        aria-label={titulo}
        className={`flex max-h-full w-full animate-entrar flex-col overflow-y-auto bg-superficie p-5 shadow-modal outline-none sm:rounded-cartao ${largo ? "max-w-4xl" : "max-w-lg"}`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-4 flex items-start justify-between gap-3">
          <h2 className="text-xl font-bold break-words">{titulo}</h2>
          <BotaoIcone icone="x" rotulo="Fechar" onClick={onFechar} />
        </div>
        {children}
      </div>
    </div>
  );
}

// Tags criadas pelo time: mesma forma da etiqueta, com a cor escolhida na criação.
const COR_TAG: Record<CorTag, string> = {
  "tag-1": "bg-tag-1 text-branco",
  "tag-2": "bg-tag-2 text-marinho",
  "tag-3": "bg-tag-3 text-marinho",
  "tag-4": "bg-tag-4 text-marinho",
  "tag-5": "bg-tag-5 text-branco",
  "tag-6": "bg-tag-6 text-branco",
};
export const CORES_TAG = Object.keys(COR_TAG) as CorTag[];

export function SeloTag({ tag, onRemover }: { tag: Pick<Tag, "nome" | "cor">; onRemover?: () => void }) {
  return (
    <span className={`${classeEtiqueta} ${onRemover ? "pr-0.5" : ""} ${COR_TAG[tag.cor]}`}>
      #{tag.nome}
      {onRemover ? (
        <button type="button" onClick={onRemover} aria-label={`Remover a tag ${tag.nome}`} title={`Remover a tag ${tag.nome}`} className="inline-flex h-5 w-5 items-center justify-center rounded-selo hover:bg-branco/25">
          <Icone nome="x" className="h-3 w-3" />
        </button>
      ) : null}
    </span>
  );
}

export { ErroFormulario } from "./ui/Campo";
