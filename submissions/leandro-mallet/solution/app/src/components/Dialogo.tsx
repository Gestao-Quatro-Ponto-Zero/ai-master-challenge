"use client";
import { useEffect, useRef, type ReactNode } from "react";
import type { CorTag, Tag } from "@/lib/tipos";

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
        className={`flex max-h-full w-full animate-entrar flex-col overflow-y-auto bg-fundo p-5 shadow-modal outline-none sm:rounded-cartao ${largo ? "max-w-4xl" : "max-w-lg"}`}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="mb-3 flex items-start justify-between gap-3">
          <h2 className="text-xl font-bold break-words">{titulo}</h2>
          <button onClick={onFechar} aria-label="Fechar" className="rounded-controle border border-linha-forte px-3 py-1 text-lg leading-none">
            ×
          </button>
        </div>
        {children}
      </div>
    </div>
  );
}

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
    <span className={`inline-flex items-center gap-1 rounded-selo px-2 py-1 text-xs font-semibold ${COR_TAG[tag.cor]}`}>
      #{tag.nome}
      {onRemover ? (
        <button onClick={onRemover} aria-label={`Remover a tag ${tag.nome}`} className="leading-none font-bold">
          ×
        </button>
      ) : null}
    </span>
  );
}

export const campo = "mt-1 block w-full rounded-controle border border-linha-forte bg-fundo px-3 py-2 text-sm font-normal";
export const botaoPrincipal = "rounded-controle bg-marinho px-4 py-2 text-sm font-semibold text-branco disabled:opacity-50";
export const botaoSecundario = "rounded-controle border border-marinho px-3 py-2 text-sm font-semibold disabled:opacity-50";
export const botaoNeutro = "rounded-controle border border-linha-forte px-3 py-2 text-sm";

export function ErroFormulario({ texto }: { texto: string | null }) {
  return texto ? (
    <p role="alert" className="rounded-controle border border-erro bg-erro-fundo px-3 py-2 text-sm text-erro">
      {texto}
    </p>
  ) : null;
}
