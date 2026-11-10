"use client";
// Prioridades do dia (O-32 e O-34): bloco escuro no padrão do deck, com os 20 leads do dia à mostra, na ordem da
// nota, sem fila. Cada lead em uma linha (nome · produto, nota em dourado, ✕ e ✓), com uma linha pequena embaixo
// (valor, dias e alerta). Clicar no lead abre o deal na parte "Por que a nota é N". ✓ registra o que foi feito
// (tipo de atividade e comentário obrigatórios, com o horário salvo) e ✕ pula o deal hoje. O item marcado fica na
// lista, esmaecido e com o estado; a lista não anda. Cada marcação vai para a linha do tempo do lead.
import { useState, type ReactNode } from "react";
import Link from "next/link";
import { pedir } from "@/lib/cliente";
import { CONFIG } from "@/lib/config";
import { dinheiro } from "@/lib/calculos";
import { resumoPrioridades } from "@/lib/prioridades";
import type { Papel, Prioridade } from "@/lib/tipos";
import { useAvisos } from "./Avisos";
import { IconeDeal } from "./Nota";
import { Botao } from "./ui/Botao";
import { AreaTexto, ErroFormulario } from "./ui/Campo";
import { Etiqueta } from "./ui/Etiqueta";
import { Icone } from "./ui/Icones";
import { Seletor } from "./ui/Seletor";

// Botões no escuro: ✓ em pílula dourada cheia (texto navy); ✕ em pílula com borda dourada (texto claro).
const BOTAO_FEITO =
  "inline-flex h-8 shrink-0 items-center justify-center gap-1.5 rounded-selo bg-ouro px-3 text-sm font-semibold text-escuro-2 hover:bg-dourado-claro disabled:opacity-50";
const BOTAO_PULAR =
  "inline-flex h-8 shrink-0 items-center justify-center gap-1.5 rounded-selo border border-fio-ouro px-3 text-sm font-semibold text-claro hover:bg-claro/10 disabled:opacity-50";

/** "Empresa · Produto": o nome padrão já traz o produto; um nome próprio ganha o produto ao lado. */
const nomeComProduto = (nome: string, produto: string) => (nome.includes(produto) ? nome : `${nome} · ${produto}`);

export function Prioridades({ itens, papel, somenteLeitura, topo, className = "" }: { itens: Prioridade[]; papel: Papel; somenteLeitura: boolean; topo?: ReactNode; className?: string }) {
  const avisos = useAvisos();
  const [registrando, setRegistrando] = useState<string | null>(null);
  const [tipo, setTipo] = useState("");
  const [comentario, setComentario] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);
  const [saindo, setSaindo] = useState<string | null>(null);

  // "Feitas" conta só o ✓; o ✗ (pulada) não sobe o contador.
  const { feitas, puladas, pendentes, meta } = resumoPrioridades(itens);
  const vendedor = papel === "vendedor";

  async function marcar(dealId: string, resultado: "feita" | "pulada") {
    if (resultado === "feita" && (!tipo || !comentario.trim())) {
      setErro(!tipo ? "Escolha o tipo de atividade." : "Escreva o que foi feito.");
      return;
    }
    setEnviando(true);
    setErro(null);
    const r = await pedir<{ desfazer: string }>("/api/prioridades", "POST", {
      dealId,
      resultado,
      tipoAtividade: resultado === "feita" ? tipo : null,
      comentario: resultado === "feita" ? comentario : null,
    });
    setEnviando(false);
    if (!r.ok) {
      if (resultado === "feita") setErro(r.erro ?? "Não foi possível registrar. Tente de novo.");
      else avisos.erro(r.erro ?? "Não foi possível registrar. Tente de novo.", r.codigo);
      return;
    }
    setRegistrando(null);
    setTipo("");
    setComentario("");
    setSaindo(dealId);
    avisos.ok(resultado === "feita" ? "Registrado na linha do tempo do lead." : "Pulado hoje. O deal não muda.", r.dados?.desfazer);
    setTimeout(() => {
      setSaindo(null);
      avisos.atualizar();
    }, 200);
  }

  return (
    <section
      aria-labelledby="t-prioridades"
      className={`fundo-escuro flex flex-col rounded-cartao border border-escuro-1 p-4 text-claro-2 [&_*:focus-visible]:outline-ouro ${className}`}
    >
      {/* Topo fixo: título, alerta e o contador; a lista rola embaixo. */}
      <div className="shrink-0">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 id="t-prioridades" className="text-lg font-bold text-claro">
            Prioridades do dia
          </h2>
          {topo}
        </div>
        <p className="mt-1 text-sm text-claro-2">
          {vendedor ? "Os seus deals que mais valem o contato hoje, pela nota." : "Deals do time que pedem ação: atendimento atrasado, lead novo de encaixe alto e em risco de esfriar."}
        </p>
        <div className="mt-3 flex items-center gap-3 text-sm">
          <span className="font-semibold whitespace-nowrap text-claro">
            <span className="text-ouro tabular-nums">{feitas}</span> de {meta} feitas
          </span>
          <div className="h-1.5 flex-1 overflow-hidden rounded-selo bg-trilho-escuro" role="progressbar" aria-valuemin={0} aria-valuemax={meta} aria-valuenow={feitas} aria-label="Prioridades feitas hoje">
            <div className="h-full rounded-selo bg-ouro" style={{ width: `${Math.min(100, (feitas / meta) * 100)}%` }} />
          </div>
          {puladas ? <span className="text-xs whitespace-nowrap text-claro-3">{puladas === 1 ? "1 pulada" : `${puladas} puladas`}</span> : null}
        </div>
      </div>

      {itens.length === 0 ? (
        <p className="mt-4 border-t border-fio-ouro pt-4 text-sm text-claro-2">
          {vendedor ? "Você não tem deals abertos para priorizar hoje." : "Nenhum deal do time pede ação hoje: sem atendimento atrasado, lead novo de encaixe alto ou deal em risco de esfriar."}{" "}
          <Link href="/pipeline" className="font-semibold text-ouro underline underline-offset-4">
            Ir para o Pipeline
          </Link>
        </p>
      ) : (
        <ol className="mt-3 min-h-0 flex-1 overflow-y-auto pr-1">
          {pendentes === 0 ? (
            <li className="border-t border-fio-ouro py-2.5 text-sm font-semibold text-claro">
              Lista de hoje concluída: {feitas} ✓ e {puladas} ✗.
            </li>
          ) : null}
          {/* Os que faltam fazer primeiro; os marcados descem e ficam à mostra, esmaecidos. Em cada grupo, a ordem da nota. */}
          {[...itens.filter((i) => !i.marcada), ...itens.filter((i) => i.marcada)].map((item) => {
            const d = item.deal;
            const aberto = registrando === d.id;
            const marcado = item.marcada !== null;
            const porque = d.score === null ? "Ver o deal" : `Ver por que a nota é ${d.score}`;
            return (
              <li key={d.id} className={`border-t border-fio-ouro py-2.5 ${marcado ? "opacity-60" : ""} ${saindo === d.id ? "motion-safe:animate-pulsar" : ""}`}>
                <div className="flex items-center gap-2">
                  {/* Clicar no lead abre o racional da nota; os botões ✕ e ✓ ficam fora do link. */}
                  <Link
                    href={`/painel?deal=${encodeURIComponent(d.id)}&secao=nota`}
                    scroll={false}
                    title={item.motivo ? `${porque}. ${item.motivo}` : porque}
                    className="group flex min-w-0 flex-1 items-center gap-2 rounded-controle"
                  >
                    <span className="min-w-0 flex-1 truncate font-semibold text-claro group-hover:underline">{nomeComProduto(d.nome, d.produto)}</span>
                    <span className="shrink-0 text-lg leading-none font-bold text-ouro tabular-nums" aria-label={d.score === null ? "Sem nota" : `Nota ${d.score}`}>
                      {d.score ?? "—"}
                    </span>
                  </Link>
                  {marcado ? (
                    <Etiqueta tom={item.marcada === "feita" ? "positivo" : "neutro"} icone={item.marcada === "feita" ? "check" : item.marcada === "pulada" ? "x" : "conversa"}>
                      {item.marcada === "feita" ? "Feito" : item.marcada === "pulada" ? "Pulado" : "Contato hoje"}
                    </Etiqueta>
                  ) : somenteLeitura || aberto ? null : (
                    <>
                      <button type="button" onClick={() => marcar(d.id, "pulada")} disabled={enviando} aria-label={`Pular hoje: ${d.nome}`} title="Pular hoje" className={BOTAO_PULAR}>
                        <Icone nome="x" />
                      </button>
                      <button
                        type="button"
                        onClick={() => {
                          // Sempre limpo: o tipo e o comentário de um item não podem ir para outro deal.
                          setTipo("");
                          setComentario("");
                          setRegistrando(d.id);
                          setErro(null);
                        }}
                        disabled={enviando}
                        aria-label={`Feito: ${d.nome}`}
                        title="Feito"
                        className={BOTAO_FEITO}
                      >
                        <Icone nome="check" />
                      </button>
                    </>
                  )}
                </div>
                <div className="mt-1 flex flex-wrap items-center gap-x-2 gap-y-1 text-xs text-claro-3">
                  <span className="tabular-nums">
                    {vendedor ? "" : `${d.vendedor} · `}
                    {dinheiro(d.valorEsperado)}
                    {d.diasDesdeAbertura !== null ? ` · há ${d.diasDesdeAbertura} dias` : " · não iniciado"}
                  </span>
                  {d.icone === "em_risco" || d.icone === "esfriou" ? <IconeDeal icone={d.icone} dias={d.diasDesdeAbertura} /> : null}
                  {item.atendimentoAtrasado ? (
                    <Etiqueta tom="atencao" icone="relogio">
                      Atendimento atrasado
                    </Etiqueta>
                  ) : null}
                  {item.puladoDiasSeguidos >= CONFIG.diasPuladoAlerta ? (
                    <Etiqueta tom="atencao" icone="alerta" title="Requalificar ou encerrar?">
                      Pulado {item.puladoDiasSeguidos} dias seguidos
                    </Etiqueta>
                  ) : null}
                </div>

                {somenteLeitura || !aberto ? null : (
                  <div className="mt-3 grid gap-2 rounded-controle bg-superficie p-3 text-texto">
                    <div className="grid gap-1">
                      <span className="text-xs font-semibold" aria-hidden>
                        O que foi feito
                      </span>
                      <Seletor
                        rotulo="O que foi feito"
                        valor={tipo}
                        onMudar={setTipo}
                        textoVazio="Escolha o tipo de atividade"
                        autoFoco
                        className="w-full"
                        opcoes={CONFIG.tiposAtividade.map((t) => ({ valor: t.codigo, rotulo: t.rotulo }))}
                      />
                    </div>
                    <label className="grid gap-1 text-xs font-semibold">
                      Comentário
                      <AreaTexto value={comentario} maxLength={280} rows={2} onChange={(e) => setComentario(e.target.value)} placeholder="Ex.: pediu a proposta até sexta" />
                    </label>
                    <p className="text-xs text-texto-2">A data e a hora são salvas junto.</p>
                    <ErroFormulario texto={erro} />
                    <div className="flex justify-end gap-2">
                      <Botao
                        nivel="secundario"
                        tamanho="compacto"
                        onClick={() => {
                          setRegistrando(null);
                          setTipo("");
                          setComentario("");
                          setErro(null);
                        }}
                      >
                        Cancelar
                      </Botao>
                      <Botao nivel="primario" tamanho="compacto" onClick={() => marcar(d.id, "feita")} disabled={enviando}>
                        {enviando ? "Registrando…" : "Registrar"}
                      </Botao>
                    </div>
                  </div>
                )}
              </li>
            );
          })}
        </ol>
      )}
    </section>
  );
}
