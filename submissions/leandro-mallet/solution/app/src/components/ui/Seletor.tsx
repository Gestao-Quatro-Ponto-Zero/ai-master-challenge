"use client";
// Seletor estilizado no lugar do <select> nativo, com a mesma altura do botão e do campo.
// Teclado: Enter, Espaço ou seta abrem; setas, Home e End andam; letra pula para a opção; Enter escolhe; Esc fecha.
// A lista abre por cima da página (posição fixa), para não ser cortada por diálogos com rolagem.
import { Fragment, useCallback, useEffect, useId, useLayoutEffect, useRef, useState, type KeyboardEvent } from "react";
import { semAcento } from "@/lib/calculos";
import type { TamanhoControle } from "./Botao";
import { Icone } from "./Icones";

export interface Opcao {
  valor: string;
  rotulo: string;
  /** Título do grupo: aparece uma vez, antes da primeira opção do grupo (as opções do mesmo grupo vêm juntas). */
  grupo?: string;
}

interface Props {
  valor: string;
  opcoes: Opcao[];
  onMudar: (valor: string) => void;
  /** Nome lido pelo leitor de tela (e o texto do rótulo visível, quando houver). */
  rotulo: string;
  /** Texto do botão quando o valor não está entre as opções (ex.: "Escolha o produto"). */
  textoVazio?: string;
  tamanho?: TamanhoControle;
  desligado?: boolean;
  autoFoco?: boolean;
  /** Menu de ação: o botão mostra sempre o textoVazio e a escolha dispara onMudar (ex.: mudar estágio). */
  acao?: boolean;
  className?: string;
}

interface Posicao {
  top: number;
  left: number;
  largura: number;
  maxAltura: number;
}

export function Seletor({ valor, opcoes, onMudar, rotulo, textoVazio, tamanho = "normal", desligado, autoFoco, acao, className = "" }: Props) {
  const id = useId();
  const botao = useRef<HTMLButtonElement>(null);
  const lista = useRef<HTMLUListElement>(null);
  const [aberto, setAberto] = useState(false);
  const [ativo, setAtivo] = useState(0);
  const [pos, setPos] = useState<Posicao | null>(null);
  const atual = acao ? undefined : opcoes.find((o) => o.valor === valor);
  const texto = atual?.rotulo ?? textoVazio ?? "Escolha";

  const fechar = useCallback((devolverFoco: boolean) => {
    setAberto(false);
    setPos(null);
    if (devolverFoco) botao.current?.focus();
  }, []);

  function abrir() {
    if (desligado || opcoes.length === 0) return;
    const i = opcoes.findIndex((o) => o.valor === valor);
    setAtivo(i >= 0 && !acao ? i : 0);
    setAberto(true);
  }

  // Posição da lista: embaixo do botão ou, sem espaço, em cima.
  useLayoutEffect(() => {
    if (!aberto || !botao.current) return;
    const r = botao.current.getBoundingClientRect();
    const baixo = window.innerHeight - r.bottom - 8;
    const cima = r.top - 8;
    const desejada = Math.min(320, opcoes.length * 40 + 8);
    const emCima = baixo < Math.min(desejada, 200) && cima > baixo;
    const maxAltura = Math.max(120, Math.min(desejada, emCima ? cima : baixo));
    const largura = Math.max(r.width, 176);
    const left = Math.min(r.left, window.innerWidth - largura - 8);
    setPos({ top: emCima ? r.top - maxAltura - 4 : r.bottom + 4, left: Math.max(8, left), largura, maxAltura });
  }, [aberto, opcoes.length]);

  // Com a lista na tela, o foco vai para ela (as setas andam pelas opções).
  useEffect(() => {
    if (aberto && pos) lista.current?.focus({ preventScroll: true });
  }, [aberto, pos]);

  // Fecha ao clicar fora, ao rolar a página ou ao mudar o tamanho da janela.
  useEffect(() => {
    if (!aberto) return;
    const fora = (e: PointerEvent) => {
      const alvo = e.target as Node;
      if (!lista.current?.contains(alvo) && !botao.current?.contains(alvo)) fechar(false);
    };
    const rolar = (e: Event) => {
      if (!lista.current?.contains(e.target as Node)) fechar(false);
    };
    const redimensionar = () => fechar(false);
    document.addEventListener("pointerdown", fora);
    window.addEventListener("scroll", rolar, true);
    window.addEventListener("resize", redimensionar);
    return () => {
      document.removeEventListener("pointerdown", fora);
      window.removeEventListener("scroll", rolar, true);
      window.removeEventListener("resize", redimensionar);
    };
  }, [aberto, fechar]);

  useEffect(() => {
    if (aberto) document.getElementById(`${id}-op-${ativo}`)?.scrollIntoView({ block: "nearest" });
  }, [aberto, ativo, id]);

  function escolher(i: number) {
    const o = opcoes[i];
    fechar(true);
    if (o && (acao || o.valor !== valor)) onMudar(o.valor);
  }

  function teclaBotao(e: KeyboardEvent<HTMLButtonElement>) {
    if (["ArrowDown", "ArrowUp", "Enter", " "].includes(e.key)) {
      e.preventDefault();
      abrir();
    }
  }

  function teclaLista(e: KeyboardEvent<HTMLUListElement>) {
    const ultimo = opcoes.length - 1;
    if (e.key === "ArrowDown") setAtivo((a) => Math.min(ultimo, a + 1));
    else if (e.key === "ArrowUp") setAtivo((a) => Math.max(0, a - 1));
    else if (e.key === "Home") setAtivo(0);
    else if (e.key === "End") setAtivo(ultimo);
    else if (e.key === "Enter" || e.key === " ") escolher(ativo);
    else if (e.key === "Escape") fechar(true);
    else if (e.key === "Tab") {
      fechar(false);
      return;
    } else if (e.key.length === 1) {
      const letra = semAcento(e.key).toLowerCase();
      const depois = [...opcoes.slice(ativo + 1), ...opcoes.slice(0, ativo + 1)];
      const achada = depois.find((o) => semAcento(o.rotulo).toLowerCase().startsWith(letra));
      if (achada) setAtivo(opcoes.indexOf(achada));
    } else return;
    e.preventDefault();
    e.stopPropagation();
  }

  const altura = tamanho === "normal" ? "h-10 px-3" : "h-8 px-2.5";
  return (
    <>
      <button
        ref={botao}
        type="button"
        aria-haspopup="listbox"
        aria-expanded={aberto}
        aria-controls={aberto ? `${id}-lista` : undefined}
        aria-label={acao ? rotulo : `${rotulo}: ${texto}`}
        disabled={desligado}
        autoFocus={autoFoco}
        onClick={(e) => {
          e.stopPropagation();
          if (aberto) fechar(false);
          else abrir();
        }}
        onKeyDown={teclaBotao}
        className={`inline-flex max-w-full min-w-0 items-center justify-between gap-2 rounded-controle border bg-superficie text-left text-sm text-texto hover:border-borda-forte disabled:cursor-not-allowed disabled:bg-superficie-2 disabled:text-texto-2 ${
          aberto ? "border-marinho" : "border-borda"
        } ${altura} ${acao ? "font-semibold" : ""} ${className}`}
      >
        <span className={`truncate ${atual || acao ? "" : "text-texto-2"}`}>{texto}</span>
        <Icone nome="chevron" className={`h-4 w-4 text-texto-2 motion-safe:transition-transform ${aberto ? "rotate-180" : ""}`} />
      </button>
      {aberto && pos ? (
        <ul
          ref={lista}
          id={`${id}-lista`}
          role="listbox"
          tabIndex={-1}
          aria-label={rotulo}
          aria-activedescendant={`${id}-op-${ativo}`}
          onKeyDown={teclaLista}
          onClick={(e) => e.stopPropagation()}
          style={{ top: pos.top, left: pos.left, minWidth: pos.largura, maxHeight: pos.maxAltura }}
          className="fixed z-[60] max-w-[calc(100vw-1rem)] overflow-y-auto rounded-controle border border-borda bg-superficie p-1 shadow-menu outline-none motion-safe:animate-entrar"
        >
          {opcoes.map((o, i) => {
            const marcado = !acao && o.valor === valor;
            const titulo = o.grupo && o.grupo !== opcoes[i - 1]?.grupo ? o.grupo : null;
            return (
              <Fragment key={o.valor}>
              {titulo ? (
                <li role="presentation" className="px-3 pt-2 pb-1 text-xs font-semibold text-texto-2">
                  {titulo}
                </li>
              ) : null}
              <li
                id={`${id}-op-${i}`}
                role="option"
                aria-selected={marcado}
                onPointerMove={() => setAtivo(i)}
                onClick={() => escolher(i)}
                className={`flex min-h-9 cursor-pointer items-center justify-between gap-3 rounded-controle px-3 py-2 text-sm ${i === ativo ? "bg-superficie-2" : ""} ${marcado ? "font-semibold" : ""}`}
              >
                <span>
                  {o.rotulo}
                  {o.grupo ? <span className="sr-only">, {o.grupo}</span> : null}
                </span>
                {marcado ? <Icone nome="check" className="h-4 w-4 text-marinho" /> : null}
              </li>
              </Fragment>
            );
          })}
        </ul>
      ) : null}
    </>
  );
}
