"use client";
// Mudança de estágio: uma implementação só para arrastar o cartão, o seletor do cartão e o modal.
// Ganho pede o valor; Perdido pede confirmação e o motivo (opcional). Conflito de edição vira frase simples.
import { createContext, useCallback, useContext, useMemo, useRef, useState, type ReactNode } from "react";
import { pedir } from "@/lib/cliente";
import { dinheiro, ROTULO_ESTAGIO, ROTULO_MOTIVO } from "@/lib/calculos";
import type { DealVisao, Estagio, MotivoPerda, Papel } from "@/lib/tipos";
import { useAvisos } from "./Avisos";

type DealMinimo = Pick<DealVisao, "id" | "nome" | "estagio" | "preco" | "atualizadoEm">;
type Mudar = (deal: DealMinimo, para: Estagio) => Promise<boolean>;

const Contexto = createContext<Mudar>(async () => false);
export const useMudarEstagio = () => useContext(Contexto);

/** Transições que o seletor oferece (ESPEC-TELAS 2.6). Reabrir fica com manager e admin. */
export function transicoesDe(estagio: Estagio, papel: Papel): Estagio[] {
  if (estagio === "Prospecting") return ["Engaging", "Lost"];
  if (estagio === "Engaging") return ["Won", "Lost"];
  return papel === "vendedor" ? [] : ["Engaging"];
}

const MOTIVOS: MotivoPerda[] = ["preco", "concorrente", "sem_orcamento", "sem_resposta", "outro"];

export function ProvedorEstagio({ children }: { children: ReactNode }) {
  const avisos = useAvisos();
  const [pendente, setPendente] = useState<{ deal: DealMinimo; para: Estagio } | null>(null);
  const [valor, setValor] = useState("");
  const [motivo, setMotivo] = useState<MotivoPerda | "">("");
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);
  const resolver = useRef<((ok: boolean) => void) | null>(null);

  const enviar = useCallback(
    async (deal: DealMinimo, para: Estagio, extra: { valor?: number; motivo?: MotivoPerda | null } = {}) => {
      const r = await pedir<{ desfazer: string }>(`/api/deals/${encodeURIComponent(deal.id)}/estagio`, "POST", { versao: deal.atualizadoEm, para, ...extra });
      if (r.ok) {
        avisos.ok(`${deal.nome}: ${ROTULO_ESTAGIO[para]}.`, r.dados?.desfazer);
        avisos.atualizar();
        return { ok: true as const };
      }
      if (r.status === 409) avisos.atualizar();
      return { ok: false as const, erro: r.erro ?? "Não foi possível mudar o estágio.", codigo: r.codigo };
    },
    [avisos],
  );

  const mudar = useCallback<Mudar>(
    async (deal, para) => {
      if (para === "Won" || para === "Lost") {
        setValor(String(deal.preco || ""));
        setMotivo("");
        setErro(null);
        setPendente({ deal, para });
        return new Promise<boolean>((res) => {
          resolver.current = res;
        });
      }
      const r = await enviar(deal, para);
      if (!r.ok) avisos.erro(r.erro, r.codigo);
      return r.ok;
    },
    [avisos, enviar],
  );

  function fechar(ok: boolean) {
    setPendente(null);
    resolver.current?.(ok);
    resolver.current = null;
  }

  async function confirmar() {
    if (!pendente) return;
    const ganho = pendente.para === "Won";
    const v = Number(valor);
    if (ganho && (!Number.isInteger(v) || v <= 0)) {
      setErro("Informe o valor de fechamento em dólares, sem centavos.");
      return;
    }
    setEnviando(true);
    const r = await enviar(pendente.deal, pendente.para, ganho ? { valor: v } : { motivo: motivo || null });
    setEnviando(false);
    if (r.ok) fechar(true);
    else setErro(r.erro);
  }

  const api = useMemo(() => mudar, [mudar]);
  const ganho = pendente?.para === "Won";

  return (
    <Contexto.Provider value={api}>
      {children}
      {pendente ? (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-veu p-4" role="presentation" onClick={() => fechar(false)}>
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="titulo-estagio"
            className="w-full max-w-md animate-entrar rounded-cartao bg-fundo p-5 shadow-modal"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 id="titulo-estagio" className="text-lg font-bold">
              {ganho ? "Encerrar como ganho" : "Encerrar como perdido"}
            </h2>
            <p className="mt-1 text-sm text-texto-2">{pendente.deal.nome}</p>
            {ganho ? (
              <label className="mt-4 block text-sm font-semibold">
                Valor de fechamento (US$)
                <input
                  autoFocus
                  inputMode="numeric"
                  value={valor}
                  onChange={(e) => setValor(e.target.value.replace(/\D/g, ""))}
                  className="mt-1 w-full rounded-controle border border-linha-forte px-3 py-2 font-normal"
                />
                <span className="mt-1 block text-xs font-normal text-texto-2">Sugestão: o preço de tabela, {dinheiro(pendente.deal.preco)}.</span>
              </label>
            ) : (
              <label className="mt-4 block text-sm font-semibold">
                Motivo da perda (opcional)
                <select
                  autoFocus
                  value={motivo}
                  onChange={(e) => setMotivo(e.target.value as MotivoPerda | "")}
                  className="mt-1 w-full rounded-controle border border-linha-forte bg-fundo px-3 py-2 font-normal"
                >
                  <option value="">Não informar</option>
                  {MOTIVOS.map((m) => (
                    <option key={m} value={m}>
                      {ROTULO_MOTIVO[m]}
                    </option>
                  ))}
                </select>
              </label>
            )}
            {erro ? (
              <p role="alert" className="mt-3 rounded-controle border border-erro bg-erro-fundo px-3 py-2 text-sm text-erro">
                {erro}
              </p>
            ) : null}
            <div className="mt-5 flex justify-end gap-2">
              <button onClick={() => fechar(false)} className="rounded-controle border border-linha-forte px-4 py-2 text-sm font-semibold">
                Cancelar
              </button>
              <button onClick={confirmar} disabled={enviando} className="rounded-controle bg-marinho px-4 py-2 text-sm font-semibold text-branco disabled:opacity-60">
                {enviando ? "Salvando…" : ganho ? "Encerrar como ganho" : "Encerrar como perdido"}
              </button>
            </div>
          </div>
        </div>
      ) : null}
    </Contexto.Provider>
  );
}

/** Seletor de estágio do cartão e do modal: só mostra as transições válidas. */
export function SeletorEstagio({ deal, papel, desligado }: { deal: DealMinimo; papel: Papel; desligado?: boolean }) {
  const mudar = useMudarEstagio();
  const opcoes = transicoesDe(deal.estagio, papel);
  if (desligado || opcoes.length === 0) return <span className="rounded-selo border border-linha-forte px-2 py-1 text-xs font-semibold">{ROTULO_ESTAGIO[deal.estagio]}</span>;
  const rotulo = (para: Estagio) =>
    deal.estagio === "Won" || deal.estagio === "Lost" ? "Reabrir (Em negociação)" : para === "Lost" && deal.estagio === "Prospecting" ? "Descartar (Perdido)" : `Mover para ${ROTULO_ESTAGIO[para]}`;
  return (
    <select
      aria-label={`Estágio de ${deal.nome}`}
      value=""
      onClick={(e) => e.stopPropagation()}
      onChange={(e) => {
        if (e.target.value) void mudar(deal, e.target.value as Estagio);
      }}
      className="max-w-full rounded-controle border border-linha-forte bg-fundo px-2 py-1 text-xs font-semibold"
    >
      <option value="">{ROTULO_ESTAGIO[deal.estagio]}</option>
      {opcoes.map((o) => (
        <option key={o} value={o}>
          {rotulo(o)}
        </option>
      ))}
    </select>
  );
}
