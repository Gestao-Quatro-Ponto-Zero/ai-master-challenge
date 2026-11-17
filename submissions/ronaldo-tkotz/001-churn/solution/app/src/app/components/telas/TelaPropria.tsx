"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import type { PainelTela, PedidoTela, TelaUsuario } from "@/engine/telasUsuario";
import { ChartView } from "../charts/ChartView";
import { Ajustado } from "./Ajustado";
import { Painel } from "./Painel";

/**
 * A screen the user builds with the analyst (D46.2, ISC-41): a request box, the panels the analyst
 * made (each with its SQL, markable for the deck, removable) and the analyst's notes per request.
 */
const SUGESTOES = [
  "Taxa de churn por plano e por tipo de cobrança",
  "As 15 contas com mais tickets escalados e se elas tiveram churn",
  "Uso de recursos beta nas contas que saíram × nas que ficaram",
  "Receita perdida por motivo de churn, mês a mês em 2024",
];

export function TelaPropria({ tela, pedidos: pedidosIniciais, paineis: paineisIniciais }: { tela: TelaUsuario; pedidos: PedidoTela[]; paineis: PainelTela[] }) {
  const router = useRouter();
  const [paineis, setPaineis] = useState(paineisIniciais);
  const [pedidos, setPedidos] = useState(pedidosIniciais);
  const [texto, setTexto] = useState("");
  const [ocupado, setOcupado] = useState(false);
  const [segundos, setSegundos] = useState(0);
  const [erro, setErro] = useState<string | null>(null);
  const [nome, setNome] = useState(tela.nome);
  const [editando, setEditando] = useState(false);
  const relogio = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => () => {
    if (relogio.current) clearInterval(relogio.current);
  }, []);

  const analisar = async (pedido: string) => {
    const p = pedido.trim();
    if (!p || ocupado) return;
    setOcupado(true);
    setErro(null);
    setSegundos(0);
    relogio.current = setInterval(() => setSegundos((s) => s + 1), 1000);
    try {
      const r = await fetch(`/api/telas/${tela.id}/analisar`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ pedido: p }) });
      const j = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(j.error ?? `erro ${r.status}`);
      setPedidos((x) => [...x, j.pedido]);
      setPaineis((x) => [...x, ...j.paineis]);
      setTexto("");
      if (j.paineis.length === 0) setErro("O analista respondeu sem gráfico. Veja a nota dele abaixo, ou peça um gráfico explicitamente.");
    } catch (e) {
      setErro(e instanceof Error ? e.message : String(e));
    } finally {
      if (relogio.current) clearInterval(relogio.current);
      setOcupado(false);
    }
  };

  const remover = async (id: number) => {
    const r = await fetch(`/api/telas/${tela.id}/paineis`, { method: "DELETE", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ painel: id }) });
    if (r.ok) setPaineis((x) => x.filter((p) => p.id !== id));
  };

  const renomear = async () => {
    setEditando(false);
    if (!nome.trim() || nome === tela.nome) return;
    await fetch(`/api/telas/${tela.id}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ nome }) });
    window.dispatchEvent(new CustomEvent("ravenstack:telas-mudaram"));
    router.refresh();
  };

  const apagar = async () => {
    if (!window.confirm(`Apagar a tela "${tela.nome}" e os ${paineis.length} painéis dela? Gráficos já marcados continuam na lista de marcados.`)) return;
    await fetch(`/api/telas/${tela.id}`, { method: "DELETE" });
    window.dispatchEvent(new CustomEvent("ravenstack:telas-mudaram"));
    router.push("/telas");
  };

  const pedidoDe = new Map(pedidos.map((p) => [p.id, p.pedido]));

  return (
    <div className="flex flex-col gap-3">
      <div className="flex flex-wrap items-center gap-2">
        {editando ? (
          <input
            autoFocus
            value={nome}
            onChange={(e) => setNome(e.target.value)}
            onBlur={renomear}
            onKeyDown={(e) => e.key === "Enter" && renomear()}
            maxLength={80}
            className="rounded border border-edge-strong bg-background px-2 py-1 text-[13px] text-foreground"
          />
        ) : (
          <button onClick={() => setEditando(true)} className="rounded border border-edge px-2 py-1 text-[11.5px] text-muted hover:border-edge-strong hover:text-foreground">
            Renomear tela
          </button>
        )}
        <button onClick={apagar} className="rounded border border-red-500/60 bg-red-500/10 px-2 py-1 text-[11.5px] font-medium text-red-400 hover:bg-red-500/20">
          Apagar tela
        </button>
        <span className="text-[11.5px] text-faint">
          {paineis.length} {paineis.length === 1 ? "painel" : "painéis"} · {pedidos.length} {pedidos.length === 1 ? "pedido" : "pedidos"} ao analista
        </span>
      </div>

      <section className="flex flex-col gap-2 rounded-lg border border-edge bg-panel px-3 py-3">
        <label htmlFor="pedido" className="text-[13px] font-semibold text-foreground">
          Peça uma análise ao analista
        </label>
        <p className="text-[11.5px] text-faint">
          O analista (DeepSeek) consulta o banco, faz os gráficos e eles entram nesta tela com o SQL de cada um. Ele lembra dos pedidos anteriores desta tela, então dá para pedir em sequência: &quot;agora só as contas Enterprise&quot;.
        </p>
        <textarea
          id="pedido"
          value={texto}
          onChange={(e) => setTexto(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) void analisar(texto);
          }}
          rows={2}
          maxLength={2000}
          placeholder="Ex.: compare a taxa de churn das contas que abriram tickets urgentes com as que não abriram, por plano"
          className="w-full resize-y rounded border border-edge bg-background px-2 py-1.5 text-[12.5px] text-foreground placeholder:text-faint"
        />
        <div className="flex flex-wrap items-center gap-2">
          <button
            onClick={() => void analisar(texto)}
            disabled={ocupado || !texto.trim()}
            className="rounded bg-accent px-3 py-1.5 text-[12px] font-semibold text-black hover:opacity-90 disabled:opacity-50"
          >
            {ocupado ? `Analisando… ${segundos}s` : "Analisar e adicionar à tela"}
          </button>
          {paineis.length === 0 &&
            !ocupado &&
            SUGESTOES.map((s) => (
              <button key={s} onClick={() => setTexto(s)} className="rounded-full border border-edge px-2 py-0.5 text-[11px] text-muted hover:border-edge-strong hover:text-foreground">
                {s}
              </button>
            ))}
        </div>
        {erro && <p className="text-[12px] text-red-300">{erro}</p>}
      </section>

      {paineis.length > 0 && (
        <div className="grid grid-cols-1 gap-2 xl:grid-cols-2">
          {paineis.map((p) => (
            <div key={p.id} className="grid h-[340px] min-w-0">
              <Painel
                titulo={p.titulo}
                nota={p.pedido_id && pedidoDe.get(p.pedido_id) ? `pedido: ${pedidoDe.get(p.pedido_id)}` : "enviado do chat"}
                sql={p.sql}
                acoes={
                  <button
                    onClick={() => void remover(p.id)}
                    title="Tirar este painel da tela"
                    className="grid h-[21px] w-[23px] place-items-center rounded border border-edge text-[11px] text-faint hover:border-red-500/60 hover:text-red-400"
                  >
                    ✕
                  </button>
                }
              >
                <Ajustado>{(_w, h) => <ChartView spec={p.chart} height={Math.max(120, h - 8)} bare />}</Ajustado>
              </Painel>
            </div>
          ))}
        </div>
      )}

      {pedidos.length > 0 && (
        <section className="flex flex-col gap-2 rounded-lg border border-edge bg-panel px-3 py-3">
          <h2 className="text-[13px] font-semibold text-foreground">Notas do analista</h2>
          {[...pedidos].reverse().map((p) => (
            <article key={p.id} className="border-t border-edge pt-2">
              <p className="text-[12px] font-medium text-foreground">{p.pedido}</p>
              <p className="mt-1 whitespace-pre-wrap text-[12px] leading-relaxed text-muted">{p.resposta}</p>
            </article>
          ))}
        </section>
      )}
    </div>
  );
}
