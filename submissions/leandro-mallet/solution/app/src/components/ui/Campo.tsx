// Campo de texto e área de texto: a mesma altura do botão, borda neutra em repouso, foco na cor da marca.
import { forwardRef, type InputHTMLAttributes, type ReactNode, type TextareaHTMLAttributes } from "react";
import type { TamanhoControle } from "./Botao";

const BASE =
  "block w-full rounded-controle border border-borda bg-superficie px-3 text-sm font-normal text-texto placeholder:text-texto-2 hover:border-borda-forte focus-visible:border-marinho disabled:bg-superficie-2 disabled:text-texto-2";

export function classeCampo(tamanho: TamanhoControle = "normal", extra = "") {
  return `${BASE} ${tamanho === "normal" ? "h-10" : "h-8"} ${extra}`;
}

export const Campo = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement> & { tamanho?: TamanhoControle }>(function Campo(
  { tamanho = "normal", className = "", ...resto },
  ref,
) {
  return <input ref={ref} className={classeCampo(tamanho, className)} {...resto} />;
});

export function AreaTexto({ className = "", ...resto }: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea className={`${BASE} py-2 ${className}`} {...resto} />;
}

/** Rótulo em cima do campo, com ajuda opcional embaixo. Use `htmlFor` para campos; o Seletor recebe o próprio rótulo. */
export function Rotulo({ texto, htmlFor, ajuda, className = "", children }: { texto: string; htmlFor?: string; ajuda?: ReactNode; className?: string; children: ReactNode }) {
  return (
    <div className={`grid gap-1 ${className}`}>
      {htmlFor ? (
        <label htmlFor={htmlFor} className="text-sm font-semibold">
          {texto}
        </label>
      ) : (
        <span className="text-sm font-semibold" aria-hidden>
          {texto}
        </span>
      )}
      {children}
      {ajuda ? <span className="text-xs text-texto-2">{ajuda}</span> : null}
    </div>
  );
}

/** Mensagem de erro do formulário: frase simples, com o próximo passo. */
export function ErroFormulario({ texto }: { texto: string | null }) {
  return texto ? (
    <p role="alert" className="rounded-controle border border-tom-negativo-texto/30 bg-tom-negativo px-3 py-2 text-sm text-tom-negativo-texto">
      {texto}
    </p>
  ) : null;
}
