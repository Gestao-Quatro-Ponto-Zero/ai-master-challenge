import type { ReactNode } from "react";
import { Icone } from "./ui/Icones";

/** Estados padronizados de tela: vazio e erro, sempre com frase simples e o próximo passo. */
export function Estado({ titulo, texto, erro, children }: { titulo: string; texto: string; erro?: boolean; children?: ReactNode }) {
  return (
    <div className={`flex flex-col items-center gap-3 rounded-cartao border px-6 py-12 text-center ${erro ? "border-tom-negativo-texto/30 bg-tom-negativo" : "border-borda bg-superficie-2"}`}>
      {erro ? <Icone nome="alerta" className="h-6 w-6 text-tom-negativo-texto" /> : null}
      <h2 className={`font-texto text-lg font-bold ${erro ? "text-tom-negativo-texto" : ""}`}>{titulo}</h2>
      <p className="max-w-prose text-sm text-texto-2">{texto}</p>
      {children}
    </div>
  );
}

/** Carregando: blocos cinza pulsando (parados com "reduzir movimento"). */
export function Esqueleto({ className = "" }: { className?: string }) {
  return <div aria-hidden className={`motion-safe:animate-pulsar rounded-controle bg-superficie-2 ${className}`} />;
}
