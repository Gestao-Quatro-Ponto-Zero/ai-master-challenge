"use client";
// Lotes das últimas 24 horas, com o "Desfazer este lote". Quem vê: quem aplicou, o manager do time e o admin.
import { useState } from "react";
import { pedir } from "@/lib/cliente";
import { plural } from "@/lib/calculos";
import { CONFIG } from "@/lib/config";
import { fraseLoteDesfeito, HORAS_DESFAZER_LOTE } from "@/lib/lotes";
import type { LoteRecente } from "@/lib/tipos";
import { useAvisos } from "./Avisos";
import { botaoNeutro, botaoSecundario, Dialogo, ErroFormulario } from "./Dialogo";
import { Esqueleto } from "./Estado";

const quando = (iso: string) =>
  new Date(iso).toLocaleString("pt-BR", { day: "2-digit", month: "2-digit", hour: "2-digit", minute: "2-digit", timeZone: CONFIG.fusoHorario });

export function LotesRecentes() {
  const avisos = useAvisos();
  const [aberto, setAberto] = useState(false);
  const [lotes, setLotes] = useState<LoteRecente[] | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [confirmando, setConfirmando] = useState<number | null>(null);
  const [enviando, setEnviando] = useState(false);

  async function carregar() {
    setErro(null);
    setLotes(null);
    const r = await pedir<{ lotes: LoteRecente[] }>("/api/lotes");
    if (r.ok && r.dados) setLotes(r.dados.lotes);
    else setErro(r.erro ?? "Não foi possível carregar os lotes.");
  }

  function abrir() {
    setAberto(true);
    setConfirmando(null);
    void carregar();
  }

  async function desfazer(lote: LoteRecente) {
    setEnviando(true);
    const r = await pedir<{ restaurados?: number; pulados?: number }>("/api/desfazer", "POST", { token: `lote:${lote.id}` });
    setEnviando(false);
    setConfirmando(null);
    if (!r.ok) {
      setErro(r.erro ?? "Não foi possível desfazer o lote.");
      return;
    }
    avisos.ok(fraseLoteDesfeito({ restaurados: r.dados?.restaurados ?? 0, pulados: r.dados?.pulados ?? 0 }));
    avisos.atualizar();
    await carregar();
  }

  return (
    <>
      <button onClick={abrir} className={botaoNeutro}>
        Lotes recentes
      </button>
      {aberto ? (
        <Dialogo titulo={`Lotes das últimas ${HORAS_DESFAZER_LOTE} horas`} largo onFechar={() => setAberto(false)}>
          <p className="text-sm text-texto-2">
            Desfazer devolve cada lead ao que era antes do lote. O lead que mudou depois fica como está.
          </p>
          <ErroFormulario texto={erro} />
          {lotes === null && !erro ? (
            <div className="mt-3 grid gap-2" aria-busy="true" aria-label="Carregando os lotes">
              <Esqueleto className="h-14" />
              <Esqueleto className="h-14" />
            </div>
          ) : null}
          {erro && lotes === null ? (
            <button onClick={() => void carregar()} className={`mt-3 ${botaoSecundario}`}>
              Tentar de novo
            </button>
          ) : null}
          {lotes?.length === 0 ? (
            <p className="mt-3 rounded-controle border border-linha bg-fundo px-3 py-4 text-sm text-texto-2">
              Nenhuma ação em lote nas últimas {HORAS_DESFAZER_LOTE} horas.
            </p>
          ) : null}
          {lotes?.length ? (
            <ul className="mt-3 grid gap-2">
              {lotes.map((l) => (
                <li key={l.id} className="flex flex-wrap items-center gap-3 rounded-controle border border-linha bg-fundo px-3 py-2 text-sm">
                  <div className="min-w-0 flex-1">
                    <p className="font-semibold">
                      {l.rotulo}: {plural(l.aplicados, "lead", "leads")}
                      {l.pulados ? <span className="font-normal text-texto-2"> ({l.pulados} não se aplicavam)</span> : null}
                    </p>
                    <p className="text-xs text-texto-2">
                      {l.meu ? "Você" : l.autor}, {quando(l.criadoEm)}
                      {l.desfeitoEm ? "" : ` · dá para desfazer até ${quando(l.desfazerAte)}`}
                    </p>
                  </div>
                  {l.desfeitoEm ? (
                    <span className="text-xs text-texto-2">
                      Desfeito{l.desfeitoPor ? ` por ${l.desfeitoPor}` : ""}, {quando(l.desfeitoEm)}
                    </span>
                  ) : confirmando === l.id ? (
                    <span className="flex items-center gap-2">
                      <button onClick={() => void desfazer(l)} disabled={enviando} className={botaoSecundario}>
                        {enviando ? "Desfazendo…" : "Confirmar"}
                      </button>
                      <button onClick={() => setConfirmando(null)} disabled={enviando} className={botaoNeutro}>
                        Cancelar
                      </button>
                    </span>
                  ) : (
                    <button onClick={() => setConfirmando(l.id)} className={botaoSecundario}>
                      Desfazer este lote
                    </button>
                  )}
                </li>
              ))}
            </ul>
          ) : null}
        </Dialogo>
      ) : null}
    </>
  );
}
