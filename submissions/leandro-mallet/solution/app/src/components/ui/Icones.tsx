// Ícones em SVG (traço, 24×24, cor do texto). Nada de glifos como ícone.
import type { ReactNode, SVGProps } from "react";

export type NomeIcone =
  | "check" | "x" | "mais" | "seta-cima" | "seta-baixo" | "chevron" | "chama" | "alerta" | "floco" | "relogio" | "desfazer"
  | "cifrao" | "pessoa-mais" | "calendario" | "pessoas" | "conversa" | "trofeu" | "percentual" | "info";

const TRACOS: Record<NomeIcone, ReactNode> = {
  check: <path d="M5 12.5l4.5 4.5L19 7.5" />,
  x: <path d="M6 6l12 12M18 6L6 18" />,
  mais: <path d="M12 5v14M5 12h14" />,
  "seta-cima": <path d="M12 19V5M6 11l6-6 6 6" />,
  "seta-baixo": <path d="M12 5v14M6 13l6 6 6-6" />,
  chevron: <path d="M6 9l6 6 6-6" />,
  chama: <path d="M12 3c.6 3.4 4.5 5 4.5 9.6A4.5 4.5 0 0 1 12 17.2a4.5 4.5 0 0 1-4.5-4.6c0-2.6 1.8-3.6 2.3-6 1.3 1 1.7-.8 2.2-3.6ZM12 20.5v.01" />,
  alerta: <path d="M12 4 2.8 19.5h18.4L12 4Zm0 6v4.5m0 2.5v.01" />,
  floco: <path d="M12 3v18M4.2 7.5l15.6 9M4.2 16.5l15.6-9M9.5 4.5 12 7l2.5-2.5M9.5 19.5 12 17l2.5 2.5" />,
  relogio: <path d="M12 7v5l3 2M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />,
  desfazer: <path d="M9 14 4 9l5-5M4 9h10.5a5.5 5.5 0 0 1 0 11H11" />,
  cifrao: <path d="M12 3v18M16.5 7.5C16 6 14.3 5 12 5 9.5 5 7.5 6.3 7.5 8.2c0 4.3 9 2.8 9 7.3C16.5 17.6 14.4 19 12 19c-2.5 0-4.3-1.1-4.8-2.8" />,
  "pessoa-mais": <path d="M10 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8ZM3 21v-1a6 6 0 0 1 6-6h2a6 6 0 0 1 3.5 1.1M19 14v6M16 17h6" />,
  calendario: <path d="M4 6h16v15H4zM4 10h16M8 3v4M16 3v4" />,
  pessoas: <path d="M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8ZM2 21v-1a6 6 0 0 1 6-6h2a6 6 0 0 1 6 6v1M16 3.2a4 4 0 0 1 0 7.6M22 21v-1a6 6 0 0 0-4-5.6" />,
  conversa: <path d="M4 5h16v10H9l-5 4V5Z" />,
  trofeu: <path d="M8 4h8v5a4 4 0 0 1-8 0V4ZM8 6H4.5a3 3 0 0 0 3.5 4M16 6h3.5a3 3 0 0 1-3.5 4M12 13v4M8 21h8M9.5 17h5" />,
  info: <path d="M12 11v5m0-8.5v.01M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" />,
  percentual: <path d="M19 5 5 19M7.5 9.5a2 2 0 1 0 0-4 2 2 0 0 0 0 4ZM16.5 18.5a2 2 0 1 0 0-4 2 2 0 0 0 0 4Z" />,
};

export function Icone({ nome, className = "h-4 w-4", ...resto }: { nome: NomeIcone } & Omit<SVGProps<SVGSVGElement>, "children">) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={2} strokeLinecap="round" strokeLinejoin="round" aria-hidden className={`shrink-0 ${className}`} {...resto}>
      {TRACOS[nome]}
    </svg>
  );
}
