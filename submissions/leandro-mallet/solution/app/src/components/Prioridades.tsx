"use client";
// Prioridades do dia: a lista vem da nota; ✓ registra o que foi feito (tipo de atividade e comentário
// obrigatórios, com o horário salvo) e ✗ pula o deal hoje. Cada marcação vai para a linha do tempo do lead.
import { useState } from "react";
import Link from "next/link";
import { pedir } from "@/lib/cliente";
import { CONFIG } from "@/lib/config";
import { dinheiro } from "@/lib/calculos";
import { resumoPrioridades } from "@/lib/prioridades";
import type { Papel, Prioridade } from "@/lib/tipos";
import { useAvisos } from "./Avisos";
import { BarraNota, IconeDeal } from "./Nota";

export function Prioridades({ itens, papel, somenteLeitura }: { itens: Prioridade[]; papel: Papel; somenteLeitura: boolean }) {
  const avisos = useAvisos();
  const [registrando, setRegistrando] = useState<string | null>(null);
  const [tipo, setTipo] = useState("");
  const [comentario, setComentario] = useState("");
  const [erro, setErro] = useState<string | null>(null);
  const [enviando, setEnviando] = useState(false);
  const [saindo, setSaindo] = useState<string | null>(null);

  const pendentes = itens.filter((i) => !i.marcada);
  // "Feitas" conta só o ✓; o ✗ (pulada) não sobe o contador.
  const { feitas, puladas, meta } = resumoPrioridades(itens);
  const visiveis = pendentes.slice(0, CONFIG.prioridadesVisiveis);
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

  async function puxarMais() {
    setEnviando(true);
    const r = await pedir("/api/prioridades/mais", "POST");
    setEnviando(false);
    if (r.ok) avisos.atualizar();
    else avisos.erro(r.erro ?? "Não foi possível puxar mais itens.", r.codigo);
  }

  return (
    <section aria-labelledby="t-prioridades" className="rounded-cartao border border-linha-forte bg-marfim p-4 shadow-cartao">
      <h2 id="t-prioridades" className="text-lg font-bold">
        Prioridades do dia
      </h2>
      <p className="mt-1 text-sm text-texto-2">
        {vendedor ? "Os seus deals que mais valem o contato hoje, pela nota." : "Deals do time que pedem ação: atendimento atrasado, lead novo de encaixe alto e em risco de esfriar."}
      </p>
      <div className="mt-3 flex items-center gap-3 text-sm">
        <span className="whitespace-nowrap font-semibold">
          {feitas} de {meta} feitas
        </span>
        <div className="h-2 flex-1 overflow-hidden rounded-selo bg-trilho" role="progressbar" aria-valuemin={0} aria-valuemax={meta} aria-valuenow={feitas} aria-label="Prioridades feitas hoje">
          <div className="h-full rounded-selo bg-dourado" style={{ width: `${Math.min(100, (feitas / meta) * 100)}%` }} />
        </div>
        {puladas ? <span className="whitespace-nowrap text-xs text-texto-2">{puladas === 1 ? "1 pulada" : `${puladas} puladas`}</span> : null}
      </div>

      {itens.length === 0 ? (
        <p className="mt-4 rounded-controle border border-linha bg-fundo px-3 py-4 text-sm text-texto-2">
          {vendedor ? "Você não tem deals abertos para priorizar hoje." : "Nenhum deal do time pede ação hoje: sem atendimento atrasado, lead novo de encaixe alto ou deal em risco de esfriar."}{" "}
          <Link href="/pipeline" className="font-semibold text-bronze-escuro underline">
            Ir para o Pipeline
          </Link>
        </p>
      ) : visiveis.length === 0 ? (
        <div className="mt-4 rounded-controle border border-linha bg-fundo px-3 py-4 text-sm">
          <p className="font-semibold">
            Lista de hoje concluída: {feitas} ✓ e {puladas} ✗.
          </p>
          {somenteLeitura ? null : (
            <button onClick={puxarMais} disabled={enviando} className="mt-3 rounded-controle border border-marinho px-3 py-2 font-semibold disabled:opacity-50">
              Puxar mais 5
            </button>
          )}
        </div>
      ) : (
        <ol className="mt-4 grid gap-2">
          {visiveis.map((item, i) => {
            const d = item.deal;
            const aberto = registrando === d.id;
            return (
              <li key={d.id} className={`rounded-cartao border border-linha-forte bg-fundo p-3 ${saindo === d.id ? "animate-sair" : ""}`}>
                <div className="flex items-start gap-2">
                  <div className="min-w-0 flex-1">
                    <Link href={`/painel?deal=${encodeURIComponent(d.id)}`} scroll={false} className="block font-semibold break-words hover:underline">
                      {d.nome}
                    </Link>
                    <p className="text-xs text-texto-2">
                      {vendedor ? "" : `${d.vendedor} · `}
                      {dinheiro(d.valorEsperado)}
                      {d.diasDesdeAbertura !== null ? ` · aberto há ${d.diasDesdeAbertura} dias` : " · não iniciado"}
                    </p>
                  </div>
                  {/* Na lista do dia, o ícone só aparece como alerta (em risco ou esfriou); a explicação é o motivo da nota. */}
                  {d.icone === "em_risco" || d.icone === "esfriou" ? <IconeDeal icone={d.icone} dias={d.diasDesdeAbertura} comRotulo /> : null}
                </div>
                {item.atendimentoAtrasado ? (
                  <p className="mt-2 inline-block rounded-selo bg-aviso-fundo px-2 py-1 text-xs font-semibold text-bronze-escuro">Atendimento atrasado</p>
                ) : null}
                {item.motivo ? <p className="mt-2 text-sm text-texto-2">{item.motivo}</p> : null}
                <div className="mt-2">
                  <BarraNota score={d.score} faixa={d.faixaNota} />
                </div>
                {item.puladoDiasSeguidos >= CONFIG.diasPuladoAlerta ? (
                  <p className="mt-2 rounded-controle bg-aviso-fundo px-2 py-1 text-xs text-bronze-escuro">
                    Pulado {item.puladoDiasSeguidos} dias seguidos. Requalificar ou encerrar?
                  </p>
                ) : null}

                {somenteLeitura ? null : aberto ? (
                  <div className="mt-3 grid gap-2 border-t border-linha pt-3">
                    <label className="text-xs font-semibold">
                      O que foi feito
                      <select value={tipo} onChange={(e) => setTipo(e.target.value)} autoFocus className="mt-1 block w-full rounded-controle border border-linha-forte bg-fundo px-2 py-2 text-sm font-normal">
                        <option value="">Escolha o tipo de atividade</option>
                        {CONFIG.tiposAtividade.map((t) => (
                          <option key={t.codigo} value={t.codigo}>
                            {t.rotulo}
                          </option>
                        ))}
                      </select>
                    </label>
                    <label className="text-xs font-semibold">
                      Comentário
                      <textarea
                        value={comentario}
                        maxLength={280}
                        rows={2}
                        onChange={(e) => setComentario(e.target.value)}
                        placeholder="Ex.: pediu a proposta até sexta"
                        className="mt-1 block w-full rounded-controle border border-linha-forte px-2 py-2 text-sm font-normal"
                      />
                    </label>
                    <p className="text-xs text-texto-2">A data e a hora são salvas junto.</p>
                    {erro ? (
                      <p role="alert" className="rounded-controle border border-erro bg-erro-fundo px-2 py-1 text-xs text-erro">
                        {erro}
                      </p>
                    ) : null}
                    <div className="flex justify-end gap-2">
                      <button
                        onClick={() => {
                          setRegistrando(null);
                          setTipo("");
                          setComentario("");
                          setErro(null);
                        }}
                        className="rounded-controle border border-linha-forte px-3 py-2 text-sm"
                      >
                        Cancelar
                      </button>
                      <button onClick={() => marcar(d.id, "feita")} disabled={enviando} className="rounded-controle bg-marinho px-3 py-2 text-sm font-semibold text-branco disabled:opacity-50">
                        {enviando ? "Registrando…" : "Registrar"}
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="mt-3 flex justify-end gap-2">
                    <button onClick={() => marcar(d.id, "pulada")} disabled={enviando} className="rounded-controle border border-linha-forte px-3 py-2 text-sm font-semibold disabled:opacity-50">
                      ✗ Pular hoje
                    </button>
                    <button
                      onClick={() => {
                        // Sempre limpo: o tipo e o comentário de um item não podem ir para outro deal.
                        setTipo("");
                        setComentario("");
                        setRegistrando(d.id);
                        setErro(null);
                      }}
                      disabled={enviando}
                      className={`rounded-controle px-3 py-2 text-sm font-semibold disabled:opacity-50 ${i === 0 ? "bg-marinho text-branco" : "border border-marinho"}`}
                    >
                      ✓ Feito
                    </button>
                  </div>
                )}
              </li>
            );
          })}
        </ol>
      )}
      {pendentes.length > visiveis.length ? <p className="mt-3 text-xs text-texto-2">Próximos: {pendentes.length - visiveis.length} na fila.</p> : null}
    </section>
  );
}
