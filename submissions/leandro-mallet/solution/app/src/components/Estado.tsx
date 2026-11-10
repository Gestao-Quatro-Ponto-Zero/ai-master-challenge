import type { ReactNode } from "react";

/** Estados padronizados de tela: vazio e erro, sempre com frase simples e o próximo passo. */
export function Estado({ titulo, texto, erro, children }: { titulo: string; texto: string; erro?: boolean; children?: ReactNode }) {
  return (
    <div className={`flex flex-col items-center gap-3 rounded-cartao border px-6 py-12 text-center ${erro ? "border-erro bg-erro-fundo" : "border-linha bg-marfim"}`}>
      <h2 className={`text-lg font-bold ${erro ? "text-erro" : ""}`}>{titulo}</h2>
      <p className="max-w-prose text-sm text-texto-2">{texto}</p>
      {children}
    </div>
  );
}

export function Esqueleto({ className = "" }: { className?: string }) {
  return <div aria-hidden className={`animate-pulsar rounded-controle bg-trilho ${className}`} />;
}
