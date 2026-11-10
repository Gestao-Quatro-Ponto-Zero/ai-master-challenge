"use client";
// Prioridades do dia: a lista vem da nota; ✓ registra o que foi feito (tipo de atividade e comentário
// obrigatórios, com o horário salvo) e ✗ pula o deal hoje. Cada marcação vai para a linha do tempo do lead.
import { useState, type ReactNode } from "react";
import Link from "next/link";
import { pedir } from "@/lib/cliente";
import { CONFIG } from "@/lib/config";
import { dinheiro } from "@/lib/calculos";
import { resumoPrioridades } from "@/lib/prioridades";
import type { Papel, Prioridade } from "@/lib/tipos";
import { useAvisos } from "./Avisos";
import { BarraNota, IconeDeal } from "./Nota";
import { Botao, classeBotao } from "./ui/Botao";
import { AreaTexto, ErroFormulario } from "./ui/Campo";
import { Etiqueta } from "./ui/Etiqueta";
import { Icone } from "./ui/Icones";
import { Seletor } from "./ui/Seletor";
import { classeSuperficie, ListaDivisoria } from "./ui/Superficie";

export function Prioridades({ itens, papel, somenteLeitura, topo, className = "" }: { itens: Prioridade[]; papel: Papel; somenteLeitura: boolean; topo?: ReactNode; className?: string }) {
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
    <section aria-labelledby="t-prioridades" className={`${classeSuperficie} flex flex-col p-4 ${className}`}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h2 id="t-prioridades" className="text-lg font-bold">
          Prioridades do dia
        </h2>
        {topo}
      </div>
      <p className="mt-1 text-sm text-texto-2">
        {vendedor ? "Os seus deals que mais valem o contato hoje, pela nota." : "Deals do time que pedem ação: atendimento atrasado, lead novo de encaixe alto e em risco de esfriar."}
      </p>
      <div className="mt-3 flex items-center gap-3 text-sm">
        <span className="whitespace-nowrap font-semibold">
          {feitas} de {meta} feitas
        </span>
        <div className="h-1.5 flex-1 overflow-hidden rounded-selo bg-trilho" role="progressbar" aria-valuemin={0} aria-valuemax={meta} aria-valuenow={feitas} aria-label="Prioridades feitas hoje">
          <div className="h-full rounded-selo bg-dourado" style={{ width: `${Math.min(100, (feitas / meta) * 100)}%` }} />
        </div>
        {puladas ? <span className="whitespace-nowrap text-xs text-texto-2">{puladas === 1 ? "1 pulada" : `${puladas} puladas`}</span> : null}
      </div>

      {itens.length === 0 ? (
        <p className="mt-4 rounded-controle bg-superficie-2 px-3 py-4 text-sm text-texto-2">
          {vendedor ? "Você não tem deals abertos para priorizar hoje." : "Nenhum deal do time pede ação hoje: sem atendimento atrasado, lead novo de encaixe alto ou deal em risco de esfriar."}{" "}
          <Link href="/pipeline" className="font-semibold text-marinho underline underline-offset-4">
            Ir para o Pipeline
          </Link>
        </p>
      ) : visiveis.length === 0 ? (
        <div className="mt-4 rounded-controle bg-superficie-2 px-3 py-4 text-sm">
          <p className="font-semibold">
            Lista de hoje concluída: {feitas} ✓ e {puladas} ✗.
          </p>
          {somenteLeitura ? null : (
            <Botao nivel="primario" onClick={puxarMais} disabled={enviando} icone="mais" className="mt-3">
              Puxar mais 5
            </Botao>
          )}
        </div>
      ) : (
        <ListaDivisoria className="mt-3 min-h-0 flex-1 overflow-y-auto pr-1">
          {visiveis.map((item) => {
            const d = item.deal;
            const aberto = registrando === d.id;
            return (
              <li key={d.id} className={`py-2.5 ${saindo === d.id ? "motion-safe:animate-sair" : ""}`}>
                <div className="flex items-start gap-2">
                  <div className="min-w-0 flex-1">
                    <Link href={`/painel?deal=${encodeURIComponent(d.id)}`} scroll={false} title={d.nome} className="block truncate font-semibold hover:underline">
                      {d.nome}
                    </Link>
                    <p className="text-xs text-texto-2">
                      {vendedor ? "" : `${d.vendedor} · `}
                      {dinheiro(d.valorEsperado)}
                      {d.diasDesdeAbertura !== null ? ` · aberto há ${d.diasDesdeAbertura} dias` : " · não iniciado"}
                    </p>
                  </div>
                  {/* Na lista do dia, o ícone só aparece como alerta (em risco ou esfriou); a explicação é o motivo da nota. */}
                  {d.icone === "em_risco" || d.icone === "esfriou" ? <IconeDeal icone={d.icone} dias={d.diasDesdeAbertura} /> : null}
                </div>
                {item.atendimentoAtrasado ? (
                  <p className="mt-2">
                    <Etiqueta tom="atencao" icone="relogio">
                      Atendimento atrasado
                    </Etiqueta>
                  </p>
                ) : null}
                {item.motivo ? (
                  <p className="mt-1.5 line-clamp-2 text-sm text-texto-2" title={item.motivo}>
                    {item.motivo}
                  </p>
                ) : null}
                {item.puladoDiasSeguidos >= CONFIG.diasPuladoAlerta ? (
                  <p className="mt-2 flex items-center gap-2 text-xs text-tom-atencao-texto">
                    <Etiqueta tom="atencao" icone="alerta">
                      Pulado {item.puladoDiasSeguidos} dias seguidos
                    </Etiqueta>
                    Requalificar ou encerrar?
                  </p>
                ) : null}

                {somenteLeitura || aberto ? (
                  <div className="mt-2">
                    <BarraNota score={d.score} faixa={d.faixaNota} />
                  </div>
                ) : null}
                {somenteLeitura ? null : aberto ? (
                  <div className="mt-3 grid gap-2 rounded-controle bg-superficie-2 p-3">
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
                ) : (
                  <div className="mt-2 flex flex-wrap items-center justify-end gap-x-3 gap-y-2">
                    <div className="min-w-32 flex-1">
                      <BarraNota score={d.score} faixa={d.faixaNota} />
                    </div>
                    <Botao nivel="secundario" tamanho="compacto" icone="x" onClick={() => marcar(d.id, "pulada")} disabled={enviando}>
                      Pular hoje
                    </Botao>
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
                      className={classeBotao("primario", "compacto")}
                    >
                      <Icone nome="check" />
                      Feito
                    </button>
                  </div>
                )}
              </li>
            );
          })}
        </ListaDivisoria>
      )}
      {pendentes.length > visiveis.length ? <p className="mt-3 text-xs text-texto-2">Próximos: {pendentes.length - visiveis.length} na fila.</p> : null}
    </section>
  );
}
