"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import type { DeckMarcados } from "@/engine/deckMarcados";

/**
 * The presentation built from the marked charts (D45): an optional brief, the build button, the
 * pyramid to review (governing thought, SCQA, sections and action titles, actions) and the .pptx.
 */
export function Apresentacao({ deck, desatualizado, total }: { deck: DeckMarcados | null; desatualizado: boolean; total: number }) {
  const router = useRouter();
  const [briefing, setBriefing] = useState(deck?.briefing ?? "");
  const [montando, setMontando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);

  const montar = async () => {
    setMontando(true);
    setErro(null);
    try {
      const r = await fetch("/api/marcados/deck", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ briefing }) });
      if (!r.ok) throw new Error((await r.json().catch(() => ({}))).error ?? `erro ${r.status}`);
      router.refresh();
    } catch (e) {
      setErro(e instanceof Error ? e.message : String(e));
    } finally {
      setMontando(false);
    }
  };

  const pronto = deck && !desatualizado;
  return (
    <section className="flex flex-col gap-3 rounded-lg border border-edge bg-panel p-4">
      <div className="flex flex-wrap items-start gap-3">
        <div className="min-w-0 flex-1">
          <h2 className="text-[14px] font-semibold text-foreground">Apresentação</h2>
          <p className="mt-0.5 max-w-3xl text-[12px] leading-relaxed text-muted">
            Montada como pirâmide de Minto: a ideia central primeiro, o contexto em SCQA, os gráficos agrupados em seções que sustentam a ideia, um título de ação por slide e as ações recomendadas. O texto é escrito pela IA; cada número é conferido contra o SQL do gráfico, e o que não confere sai.
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <button
            onClick={() => void montar()}
            disabled={montando || total === 0}
            className="rounded-md border border-edge-strong px-3 py-1.5 text-[12.5px] font-medium text-foreground transition-colors hover:border-accent hover:text-accent disabled:opacity-50"
          >
            {montando ? "Montando… (até 1 min)" : deck ? "Montar de novo" : "Montar apresentação"}
          </button>
          {pronto ? (
            <a href="/api/marcados/pptx" download className="rounded-md border border-accent bg-accent-soft px-3 py-1.5 text-[12.5px] font-medium text-accent transition-colors hover:bg-accent hover:text-background">
              Baixar .pptx
            </a>
          ) : (
            <span className="rounded-md border border-edge px-3 py-1.5 text-[12.5px] text-faint" title="Monte a apresentação primeiro">Baixar .pptx</span>
          )}
        </div>
      </div>

      <label className="flex flex-col gap-1">
        <span className="text-[11px] text-faint">Público e objetivo (opcional): orienta a ideia central e a ênfase</span>
        <textarea
          value={briefing}
          onChange={(e) => setBriefing(e.target.value)}
          maxLength={600}
          rows={2}
          placeholder="Ex.: diretoria da RavenStack; decidir onde agir primeiro para reduzir o churn"
          className="resize-y rounded-md border border-edge bg-background px-2.5 py-1.5 text-[12.5px] text-foreground placeholder:text-faint focus:border-accent focus:outline-none"
        />
      </label>

      {erro && <p className="text-[12px] text-red-400">Não foi possível montar: {erro}</p>}
      {deck && desatualizado && <p className="text-[12px] text-amber-400">Os gráficos marcados mudaram depois da última montagem. Monte de novo para baixar.</p>}

      {deck && (
        <div className="flex flex-col gap-3 border-t border-edge pt-3">
          <div>
            <span className="font-mono text-[10.5px] uppercase tracking-wider text-accent">Ideia central</span>
            <p className="text-[15px] font-semibold leading-snug text-foreground">{deck.ideiaCentral}</p>
            <p className="mt-0.5 text-[11.5px] text-faint">
              {deck.titulo} · {deck.autor === "ia" ? "arranjo da IA" : "arranjo por regra (sem IA)"} · {new Date(deck.criadoEm).toLocaleString("pt-BR")}
            </p>
          </div>
          <div className="grid gap-2 text-[12px] md:grid-cols-3">
            {([["Situação", deck.scqa.situacao], ["Complicação", deck.scqa.complicacao], ["Pergunta", deck.scqa.pergunta]] as const).map(([r, t]) => (
              <div key={r} className="rounded border border-edge bg-background/50 p-2">
                <span className="text-[10.5px] uppercase tracking-wider text-faint">{r}</span>
                <p className="text-muted">{t}</p>
              </div>
            ))}
          </div>
          <div className="grid gap-2" style={{ gridTemplateColumns: `repeat(${Math.max(1, deck.secoes.length)}, minmax(0, 1fr))` }}>
            {deck.secoes.map((s, i) => (
              <div key={i} className="flex flex-col gap-1.5 border-t-2 border-accent pt-1.5">
                <span className="font-mono text-[11px] text-accent">{String(i + 1).padStart(2, "0")}</span>
                <p className="text-[12.5px] font-semibold leading-snug text-foreground">{s.titulo}</p>
                <ul className="flex flex-col gap-1">
                  {s.graficos.map((g) => (
                    <li key={g.marcadoId} className="text-[11.5px] leading-snug text-muted">
                      ▪ {g.tituloAcao}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
          {deck.recomendacoes.length > 0 && (
            <div>
              <span className="text-[10.5px] uppercase tracking-wider text-faint">Ações recomendadas</span>
              <ul className="mt-1 flex flex-col gap-0.5 text-[12px] text-muted">
                {deck.recomendacoes.map((r, i) => (
                  <li key={i}>▪ {r}</li>
                ))}
              </ul>
            </div>
          )}
          {deck.avisos.length > 0 && (
            <details className="text-[11.5px] text-amber-400/90">
              <summary className="cursor-pointer">Conferência dos números: {deck.avisos.length} {deck.avisos.length === 1 ? "ajuste" : "ajustes"}</summary>
              <ul className="mt-1 flex flex-col gap-0.5 text-faint">
                {deck.avisos.map((a, i) => (
                  <li key={i}>{a}</li>
                ))}
              </ul>
            </details>
          )}
        </div>
      )}
    </section>
  );
}
