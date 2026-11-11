// Botão em 3 níveis, com a mesma altura e o mesmo raio em todo o app.
//   primário  — navy cheio: a ação principal da tela ou do cartão (uma por bloco);
//   secundário — fundo branco com borda neutra: as outras ações;
//   discreto  — só texto: ações de apoio (limpar, cancelar dentro de linha, ver mais).
// Tamanho "normal" (40 px) nas telas e diálogos; "compacto" (32 px) dentro de cartões e linhas.
import type { ButtonHTMLAttributes, ReactNode } from "react";
import { Icone, type NomeIcone } from "./Icones";

export type NivelBotao = "primario" | "secundario" | "discreto";
export type TamanhoControle = "normal" | "compacto";

const NIVEL: Record<NivelBotao, string> = {
  primario: "bg-marinho text-branco hover:bg-marinho-2 border border-marinho",
  secundario: "bg-superficie text-marinho border border-borda hover:border-borda-forte hover:bg-superficie-2",
  discreto: "bg-transparent text-marinho border border-transparent underline-offset-4 hover:underline",
};
const TAMANHO: Record<TamanhoControle, string> = {
  normal: "h-10 px-4 text-sm",
  compacto: "h-8 px-3 text-sm",
};

/** Classes do botão, para usar também em links que parecem botão. */
export function classeBotao(nivel: NivelBotao = "secundario", tamanho: TamanhoControle = "normal", extra = "") {
  return `inline-flex shrink-0 items-center justify-center gap-2 rounded-controle font-semibold whitespace-nowrap transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${NIVEL[nivel]} ${TAMANHO[tamanho]} ${extra}`;
}

type Props = ButtonHTMLAttributes<HTMLButtonElement> & { nivel?: NivelBotao; tamanho?: TamanhoControle; icone?: NomeIcone; children?: ReactNode };

export function Botao({ nivel = "secundario", tamanho = "normal", icone, className = "", type = "button", children, ...resto }: Props) {
  return (
    <button type={type} className={classeBotao(nivel, tamanho, className)} {...resto}>
      {icone ? <Icone nome={icone} /> : null}
      {children}
    </button>
  );
}

/** Botão só com ícone (fechar, remover). Sempre com rótulo para leitor de tela. */
export function BotaoIcone({ icone, rotulo, tamanho = "normal", className = "", ...resto }: Omit<Props, "children" | "nivel"> & { icone: NomeIcone; rotulo: string }) {
  const lado = tamanho === "normal" ? "h-10 w-10" : "h-8 w-8";
  return (
    <button
      type="button"
      aria-label={rotulo}
      title={rotulo}
      className={`inline-flex shrink-0 items-center justify-center rounded-controle border border-borda bg-superficie text-marinho hover:border-borda-forte hover:bg-superficie-2 disabled:opacity-50 ${lado} ${className}`}
      {...resto}
    >
      <Icone nome={icone} />
    </button>
  );
}
