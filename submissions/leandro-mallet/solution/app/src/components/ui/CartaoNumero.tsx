// Cartão de número do Painel (O-30), no modelo enviado pelo Leandro:
// fundo branco, raio de 12 px, borda fina, faixa de 3 px na lateral esquerda e brilho suave no canto,
// ambos na cor do grupo; ícone quadrado cheio na cor do grupo; rótulo pequeno; número grande em Manrope bold;
// embaixo, a pílula de variação (verde quando sobe, vermelha quando cai: as únicas cores fora da marca).
// Grupos: leads = navy; negociação e pipeline = dourado; fechamentos e conversão = dourado escuro.
import Link from "next/link";
import type { ReactNode } from "react";
import { Icone, type NomeIcone } from "./Icones";

export type GrupoNumero = "leads" | "negociacao" | "fechamento";

const GRUPO: Record<GrupoNumero, { faixa: string; icone: string; brilho: string }> = {
  leads: { faixa: "bg-grupo-leads", icone: "bg-grupo-leads", brilho: "bg-grupo-leads/10" },
  negociacao: { faixa: "bg-grupo-negociacao", icone: "bg-grupo-negociacao", brilho: "bg-grupo-negociacao/25" },
  fechamento: { faixa: "bg-grupo-fechamento", icone: "bg-grupo-fechamento", brilho: "bg-grupo-fechamento/15" },
};

export interface Variacao {
  texto: string;
  sobe: boolean;
}

/** Variação zero ("0%", "0 p.p."): não sobe nem cai. */
export const variacaoZero = (texto: string) => /^[↑↓]?\s*0(?:,0+)?\s*(?:%|p\.p\.)/.test(texto);

/** Pílula de variação: seta em SVG, verde quando sobe e vermelha quando cai; zero ou sem base, cinza e sem seta. */
export function PilulaVariacao({ variacao, rotulo }: { variacao: Variacao | null; rotulo?: string }) {
  const neutra = "inline-flex h-6 max-w-full items-center rounded-selo bg-tom-neutro px-2 text-xs font-semibold whitespace-nowrap text-tom-neutro-texto";
  if (!variacao) return <span className={neutra}>sem base para comparar</span>;
  const texto = `${rotulo ? `${rotulo} ` : ""}${variacao.texto.replace(/^[↑↓]\s*/, "")}`;
  if (variacaoZero(variacao.texto)) {
    return (
      <span title={texto} className={neutra}>
        <span className="truncate">{texto}</span>
      </span>
    );
  }
  return (
    <span
      title={texto}
      className={`inline-flex h-6 max-w-full items-center gap-1 rounded-selo px-2 text-xs font-semibold whitespace-nowrap ${
        variacao.sobe ? "bg-tom-positivo text-tom-positivo-texto" : "bg-tom-negativo text-tom-negativo-texto"
      }`}
    >
      <Icone nome={variacao.sobe ? "seta-cima" : "seta-baixo"} className="h-3.5 w-3.5" />
      <span className="truncate">{texto}</span>
    </span>
  );
}

interface Props {
  rotulo: string;
  valor: string;
  grupo: GrupoNumero;
  icone: NomeIcone;
  linha?: string;
  /** Pílulas de variação e outras etiquetas embaixo do número. */
  rodape?: ReactNode;
  /** "Como ler este número". */
  info?: string;
  href?: string;
  /** Cartão de destaque (Total de leads): degradê creme e número dourado. */
  destaque?: boolean;
  className?: string;
}

export function CartaoNumero({ rotulo, valor, grupo, icone, linha, rodape, info, href, destaque, className = "" }: Props) {
  const g = GRUPO[grupo];
  const corpo = (
    <>
      <div className="flex items-center gap-2">
        <span className={`inline-flex h-7 w-7 shrink-0 items-center justify-center rounded-controle text-branco ${g.icone}`} aria-hidden>
          <Icone nome={icone} className="h-4 w-4" />
        </span>
        <p className={`min-w-0 text-xs font-semibold text-texto-2 ${info ? "pr-7" : ""}`}>{rotulo}</p>
      </div>
      <p className={`mt-2.5 font-texto text-numero leading-none font-bold whitespace-nowrap tabular-nums ${destaque ? "text-numero-dourado" : "text-marinho"}`}>{valor}</p>
      {linha ? <p className="mt-1.5 truncate text-sm text-texto-2" title={linha}>{linha}</p> : null}
    </>
  );
  return (
    <div
      className={`relative isolate flex flex-col rounded-numero border border-borda p-4 pl-5 ${
        destaque ? "bg-linear-to-br from-creme-1 to-creme-2" : "bg-superficie"
      } ${className}`}
    >
      {/* Faixa e brilho ficam numa camada recortada; o "Como ler" pode abrir para fora do cartão. */}
      <span aria-hidden className="pointer-events-none absolute inset-0 -z-10 overflow-hidden rounded-numero">
        <span className={`absolute inset-y-0 left-0 w-[3px] ${g.faixa}`} />
        <span className={`absolute -top-10 -right-10 h-28 w-28 rounded-selo blur-2xl ${g.brilho}`} />
      </span>
      {href ? (
        <Link href={href} className="block rounded-controle hover:underline">
          {corpo}
        </Link>
      ) : (
        corpo
      )}
      {rodape ? <div className="mt-2.5 flex flex-wrap gap-1.5">{rodape}</div> : null}
      {info ? (
        <details className="group absolute top-3 right-3 z-10 text-xs text-texto-2">
          <summary className="flex h-7 w-7 cursor-pointer list-none items-center justify-center rounded-controle text-marinho hover:bg-superficie-2 [&::-webkit-details-marker]:hidden" title="Como ler este número">
            <Icone nome="info" className="h-4 w-4" />
            <span className="sr-only">Como ler este número</span>
          </summary>
          <p className="absolute top-8 right-0 w-64 rounded-controle border border-borda bg-superficie p-3 shadow-menu">{info}</p>
        </details>
      ) : null}
    </div>
  );
}
