"use client";
import { Estado } from "@/components/Estado";

/** Erro de qualquer tela: frase simples e o próximo passo; o detalhe técnico fica recolhido. */
export default function Erro({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  return (
    <Estado erro titulo="Não foi possível carregar esta tela" texto="Tente de novo em alguns segundos. Se continuar, avise o suporte com o código abaixo.">
      <button onClick={reset} className="rounded-controle bg-marinho px-4 py-2 text-sm font-semibold text-branco">
        Tentar de novo
      </button>
      {error.digest ? (
        <details className="text-xs text-texto-2">
          <summary className="cursor-pointer">Ver detalhes</summary>
          Código para suporte: {error.digest}
        </details>
      ) : null}
    </Estado>
  );
}
