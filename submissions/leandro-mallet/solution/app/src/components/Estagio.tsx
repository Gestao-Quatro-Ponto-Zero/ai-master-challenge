"use client";
// Mudança de etapa: uma implementação só para arrastar o cartão, o controle do cartão e o modal.
// Atendimento pede o registro do contato (tipo de atividade e comentário obrigatórios); Fechado pede o valor;
// Perdido pede confirmação e o motivo (opcional). Conflito de edição vira frase simples.
import { createContext, useCallback, useContext, useMemo, useRef, useState, type ReactNode } from "react";
import { pedir } from "@/lib/cliente";
import { dinheiro, ROTULO_MOTIVO, SIMBOLO_MOEDA } from "@/lib/calculos";
import { CONFIG } from "@/lib/config";
import { destinosDe, ESTAGIO_DA_ETAPA, etapaDe, ROTULO_ETAPA, rotuloDestino, type Etapa } from "@/lib/etapas";
import type { DealVisao, MotivoPerda, Papel } from "@/lib/tipos";
import { useAvisos } from "./Avisos";
import { Botao } from "./ui/Botao";
import { AreaTexto, Campo, ErroFormulario } from "./ui/Campo";
import { Etiqueta } from "./ui/Etiqueta";
import { Seletor } from "./ui/Seletor";

type DealMinimo = Pick<DealVisao, "id" | "nome" | "estagio" | "preco" | "atualizadoEm" | "ultimoContato">;
type Mudar = (deal: DealMinimo, para: Etapa) => Promise<boolean>;

const Contexto = createContext<Mudar>(async () => false);
/** Leva o deal para outra etapa (com o diálogo que a etapa pede). */
export const useMudarEstagio = () => useContext(Contexto);

/** Etapas para onde o deal pode ir (ESPEC-TELAS 2.6, O-31). */
export const transicoesDe = (deal: Pick<DealVisao, "estagio" | "ultimoContato">, papel: Papel) => destinosDe(etapaDe(deal), papel);

const MOTIVOS: MotivoPerda[] = ["preco", "concorrente", "sem_orcamento", "sem_resposta", "outro"];
const TIPOS_CONTATO = CONFIG.tiposAtividade.filter((t) => t.contaComoContato);

/** Foca o campo ao abrir o diálogo, sem deslocar a página por baixo. */
const focarSemRolar = (el: HTMLInputElement | null) => el?.focus({ preventScroll: true });

type Pendente = { deal: DealMinimo; para: "atendimento" | "fechado" | "perdido" };

export function ProvedorEstagio({ children }: { children: ReactNode }) {
  const avisos = useAvisos();
  const [pendente, setPendente] = useState<Pendente | null>(null);
  const [valor, setValor] = useState("");
  const [motivo, setMotivo] = useState<MotivoPerda | "">("");
  const [tipo, setTipo] = useState("");
  const [comentario, setComentario] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);
  const resolver = useRef<((ok: boolean) => void) | null>(null);

  const enviar = useCallback(
    async (deal: DealMinimo, para: Etapa, extra: { valor?: number; motivo?: MotivoPerda | null } = {}) => {
      const r = await pedir<{ desfazer: string }>(`/api/deals/${encodeURIComponent(deal.id)}/estagio`, "POST", {
        versao: deal.atualizadoEm,
        para: ESTAGIO_DA_ETAPA[para],
        ...extra,
      });
      if (r.ok) {
        avisos.ok(`${deal.nome}: ${ROTULO_ETAPA[para]}.`, r.dados?.desfazer);
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
      if (para === "atendimento" || para === "fechado" || para === "perdido") {
        setValor(String(deal.preco || ""));
        setMotivo("");
        setTipo("");
        setComentario("");
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
    if (pendente.para === "atendimento") {
      if (!tipo) return setErro("Escolha o tipo de atividade.");
      if (!comentario.trim()) return setErro("Escreva o que foi feito.");
      setEnviando(true);
      const r = await pedir<{ desfazer: string }>(`/api/deals/${encodeURIComponent(pendente.deal.id)}/atendimento`, "POST", {
        tipoAtividade: tipo,
        comentario,
      });
      setEnviando(false);
      if (!r.ok) return setErro(r.erro ?? "Não foi possível registrar. Tente de novo.");
      avisos.ok(`${pendente.deal.nome}: ${ROTULO_ETAPA.atendimento}. Registrado na linha do tempo do lead.`, r.dados?.desfazer);
      avisos.atualizar();
      fechar(true);
      return;
    }
    const fechado = pendente.para === "fechado";
    const v = Number(valor);
    if (fechado && (!Number.isInteger(v) || v <= 0)) {
      setErro("Informe o valor de fechamento: um número inteiro maior que zero.");
      return;
    }
    setEnviando(true);
    const r = await enviar(pendente.deal, pendente.para, fechado ? { valor: v } : { motivo: motivo || null });
    setEnviando(false);
    if (r.ok) fechar(true);
    else setErro(r.erro);
  }

  const api = useMemo(() => mudar, [mudar]);
  const titulo =
    pendente?.para === "atendimento" ? "Registrar atendimento" : pendente?.para === "fechado" ? "Encerrar como fechado" : "Encerrar como perdido";

  return (
    <Contexto.Provider value={api}>
      {children}
      {pendente ? (
        <div className="fixed inset-0 z-40 flex items-center justify-center bg-veu p-4" role="presentation" onClick={() => fechar(false)}>
          <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="titulo-estagio"
            className="w-full max-w-md animate-entrar rounded-cartao bg-superficie p-5 shadow-modal"
            onClick={(e) => e.stopPropagation()}
          >
            <h2 id="titulo-estagio" className="text-lg font-bold">
              {titulo}
            </h2>
            <p className="mt-1 text-sm text-texto-2">{pendente.deal.nome}</p>
            {pendente.para === "atendimento" ? (
              <div className="mt-4 grid gap-3">
                <p className="text-sm text-texto-2">O lead entra em Atendimento com o primeiro contato registrado.</p>
                <div className="grid gap-1 text-sm font-semibold">
                  <span aria-hidden>O que foi feito</span>
                  <Seletor
                    rotulo="O que foi feito"
                    valor={tipo}
                    onMudar={setTipo}
                    textoVazio="Escolha o tipo de atividade"
                    autoFoco
                    className="w-full font-normal"
                    opcoes={TIPOS_CONTATO.map((t) => ({ valor: t.codigo, rotulo: t.rotulo }))}
                  />
                </div>
                <label className="grid gap-1 text-sm font-semibold">
                  Comentário
                  <AreaTexto value={comentario} maxLength={280} rows={3} onChange={(e) => setComentario(e.target.value)} placeholder="Ex.: pediu a proposta até sexta" />
                </label>
                <p className="text-xs text-texto-2">A data e a hora são salvas junto.</p>
              </div>
            ) : pendente.para === "fechado" ? (
              <label className="mt-4 grid gap-1 text-sm font-semibold">
                Valor de fechamento ({SIMBOLO_MOEDA})
                <Campo ref={focarSemRolar} inputMode="numeric" value={valor} onChange={(e) => setValor(e.target.value.replace(/\D/g, ""))} />
                <span className="text-xs font-normal text-texto-2">Sugestão: o preço de tabela, {dinheiro(pendente.deal.preco)}.</span>
              </label>
            ) : (
              <div className="mt-4 grid gap-1 text-sm font-semibold">
                <span aria-hidden>Motivo da perda (opcional)</span>
                <Seletor
                  rotulo="Motivo da perda (opcional)"
                  valor={motivo}
                  onMudar={(v) => setMotivo(v as MotivoPerda | "")}
                  autoFoco
                  className="w-full font-normal"
                  opcoes={[{ valor: "", rotulo: "Não informar" }, ...MOTIVOS.map((m) => ({ valor: m, rotulo: ROTULO_MOTIVO[m] }))]}
                />
              </div>
            )}
            <div className="mt-3">
              <ErroFormulario texto={erro} />
            </div>
            <div className="mt-5 flex justify-end gap-2">
              <Botao nivel="secundario" onClick={() => fechar(false)}>
                Cancelar
              </Botao>
              <Botao nivel="primario" onClick={confirmar} disabled={enviando}>
                {enviando ? "Salvando…" : pendente.para === "atendimento" ? "Registrar atendimento" : titulo}
              </Botao>
            </div>
          </div>
        </div>
      ) : null}
    </Contexto.Provider>
  );
}

/** Controle de etapa do cartão e do modal: mostra a etapa atual e só oferece os destinos válidos. */
export function SeletorEstagio({ deal, papel, desligado }: { deal: DealMinimo; papel: Papel; desligado?: boolean }) {
  const mudar = useMudarEstagio();
  const etapa = etapaDe(deal);
  const opcoes = destinosDe(etapa, papel);
  if (desligado || opcoes.length === 0) return <Etiqueta tom="neutro">{ROTULO_ETAPA[etapa]}</Etiqueta>;
  return (
    <Seletor
      acao
      tamanho="compacto"
      rotulo={`Etapa de ${deal.nome}: ${ROTULO_ETAPA[etapa]}. Mudar`}
      textoVazio={ROTULO_ETAPA[etapa]}
      valor=""
      onMudar={(v) => void mudar(deal, v as Etapa)}
      opcoes={opcoes.map((o) => ({ valor: o, rotulo: rotuloDestino(etapa, o) }))}
    />
  );
}
