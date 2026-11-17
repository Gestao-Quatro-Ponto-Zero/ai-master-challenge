"use client";

import { createContext, useCallback, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { useSearchParams } from "next/navigation";
import type { Passo, ResultadoRecorte, Universo } from "@/engine/recorte";
import { BarChart } from "../charts/BarChart";
import { Ajustado } from "./Ajustado";
import { Painel, SqlList, SqlToggle } from "./Painel";

/**
 * Drill-down (D46, ISC-40). A chart that knows its slice (`recorte` prop) opens this panel on a
 * click: the slice's size, its breakdown by every other attribute (a click goes one level deeper),
 * the accounts in it against the rest of the base, a cross of two attributes and the records.
 * Every block is a Painel, so it shows its SQL and can be marked for the deck.
 */
export interface AlvoRecorte {
  universo: Universo;
  /** The dimension the chart groups by. */
  dim: string;
  /** Conditions the chart already holds (e.g. only accounts with churn_flag = 1). */
  base?: Passo[];
}

interface Estado {
  abrir: (universo: Universo, caminho: Passo[]) => void;
}
const Contexto = createContext<Estado | null>(null);

/** The click handler for a chart, or undefined when the chart has no slice. */
export function useAbrirRecorte(alvo: AlvoRecorte | undefined, dados: { label: string; chave?: string }[]): ((label: string) => void) | undefined {
  const ctx = useContext(Contexto);
  return useMemo(() => {
    if (!alvo || !ctx) return undefined;
    return (label: string) => {
      const d = dados.find((x) => x.label === label);
      if (!d) return;
      ctx.abrir(alvo.universo, [...(alvo.base ?? []), { dim: alvo.dim, valor: d.chave ?? d.label }]);
    };
  }, [alvo, ctx, dados]);
}

export function RecorteProvider({ children }: { children: ReactNode }) {
  const [aberto, setAberto] = useState<{ universo: Universo; caminho: Passo[] } | null>(null);
  const abrir = useCallback((universo: Universo, caminho: Passo[]) => setAberto({ universo, caminho }), []);
  return (
    <Contexto.Provider value={{ abrir }}>
      {children}
      {aberto && <RecorteModal inicial={aberto} fechar={() => setAberto(null)} />}
    </Contexto.Provider>
  );
}

const fmtInt = (n: number) => n.toLocaleString("pt-BR");
const fmtPct = (n: number) => `${n.toLocaleString("pt-BR", { maximumFractionDigits: 1 })}%`;
const fmtDec = (n: number) => n.toLocaleString("pt-BR", { maximumFractionDigits: 2 });
const fmtUsd = (n: number) => `US$ ${Math.round(n).toLocaleString("pt-BR")}`;
const FMT = { int: fmtInt, pct: fmtPct, dec: fmtDec, usd: fmtUsd };

const LARANJA = "#d95926";
const AZUL = "#3987e5";

function RecorteModal({ inicial, fechar }: { inicial: { universo: Universo; caminho: Passo[] }; fechar: () => void }) {
  const sp = useSearchParams();
  const filtros = sp.toString();
  const [caminho, setCaminho] = useState<Passo[]>(inicial.caminho);
  const [cruzar, setCruzar] = useState<[string, string] | null>(null);
  const [dados, setDados] = useState<ResultadoRecorte | null>(null);
  const [erro, setErro] = useState<string | null>(null);
  const [carregando, setCarregando] = useState(true);
  const [sqlTotal, setSqlTotal] = useState(false);

  useEffect(() => {
    let vivo = true;
    queueMicrotask(() => vivo && setCarregando(true));
    fetch("/api/recorte", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ universo: inicial.universo, caminho, cruzar, filtros }),
    })
      .then(async (r) => {
        const j = await r.json();
        if (!r.ok) throw new Error(j.error ?? `erro ${r.status}`);
        return j as ResultadoRecorte;
      })
      .then((j) => {
        if (!vivo) return;
        setDados(j);
        setErro(null);
      })
      .catch((e) => vivo && setErro(e instanceof Error ? e.message : String(e)))
      .finally(() => vivo && setCarregando(false));
    return () => {
      vivo = false;
    };
  }, [inicial.universo, caminho, cruzar, filtros]);

  useEffect(() => {
    const esc = (e: KeyboardEvent) => e.key === "Escape" && fechar();
    window.addEventListener("keydown", esc);
    return () => window.removeEventListener("keydown", esc);
  }, [fechar]);

  const descricao = dados ? dados.caminho.map((p) => `${p.tituloDim}: ${p.rotulo}`).join(" › ") : "";
  const aprofundar = (dim: string, valor: string) => setCaminho((c) => [...c, { dim, valor }]);

  const perguntar = () => {
    if (!dados) return;
    const q =
      `Aprofunde o recorte de ${dados.nomeUniverso} em que ${descricao} (${fmtInt(dados.total)} ${dados.unidade}, ${fmtInt(dados.contas)} contas). ` +
      `O que diferencia esse recorte do resto da base? Cruze com uso do produto, suporte e receita, e mostre em gráfico o que mais se destaca.`;
    window.dispatchEvent(new CustomEvent("veta:ask", { detail: { question: q } }));
    fechar();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-stretch justify-center bg-black/60 p-4" onClick={fechar}>
      <div
        role="dialog"
        aria-label="Detalhar recorte"
        className="flex w-full max-w-[1400px] flex-col overflow-hidden rounded-xl border border-edge-strong bg-background shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <header className="flex flex-wrap items-center gap-2 border-b border-edge px-4 py-2.5">
          <nav aria-label="Caminho do recorte" className="flex min-w-0 flex-1 flex-wrap items-center gap-1 text-[12.5px]">
            <span className="text-faint">{dados?.nomeUniverso ?? "Recorte"}</span>
            {(dados?.caminho ?? caminho.map((p) => ({ ...p, tituloDim: p.dim, rotulo: p.valor }))).map((p, i, arr) => (
              <span key={i} className="flex items-center gap-1">
                <span className="text-faint">›</span>
                {i < arr.length - 1 ? (
                  <button onClick={() => setCaminho((c) => c.slice(0, i + 1))} className="text-muted underline-offset-2 hover:text-foreground hover:underline">
                    {p.tituloDim}: {p.rotulo}
                  </button>
                ) : (
                  <span className="font-semibold text-foreground">
                    {p.tituloDim}: {p.rotulo}
                  </span>
                )}
              </span>
            ))}
          </nav>
          {caminho.length > inicial.caminho.length && (
            <button onClick={() => setCaminho((c) => c.slice(0, -1))} className="rounded border border-edge px-2 py-1 text-[11.5px] text-muted hover:border-edge-strong hover:text-foreground">
              ← Voltar um nível
            </button>
          )}
          <button onClick={perguntar} disabled={!dados} className="rounded border border-accent/60 bg-accent-soft px-2 py-1 text-[11.5px] font-medium text-accent hover:bg-accent/20 disabled:opacity-50">
            Perguntar ao analista sobre este recorte
          </button>
          <button onClick={fechar} aria-label="Fechar" className="rounded px-2 py-1 text-[12px] text-muted hover:text-foreground">
            Fechar ✕
          </button>
        </header>

        <div className="min-h-0 flex-1 overflow-y-auto px-4 py-3">
          {erro && <p className="rounded border border-red-500/50 bg-red-500/10 px-3 py-2 text-[12.5px] text-red-300">Não foi possível abrir o recorte: {erro}</p>}
          {!dados && !erro && <p className="text-[12.5px] text-muted">Carregando o recorte…</p>}
          {dados && (
            <div className={`flex flex-col gap-3 ${carregando ? "opacity-60" : ""}`}>
              <div className="flex flex-wrap items-baseline gap-x-5 gap-y-1">
                <p className="text-[22px] font-semibold tabular-nums text-foreground">
                  {fmtInt(dados.total)} <span className="text-[13px] font-normal text-muted">{dados.unidade}</span>
                </p>
                <p className="text-[13px] text-muted">
                  <span className="tabular-nums text-foreground">{fmtInt(dados.contas)}</span> contas ·{" "}
                  <span className="tabular-nums text-foreground">{fmtPct(dados.totalUniverso ? (100 * dados.total) / dados.totalUniverso : 0)}</span> dos {fmtInt(dados.totalUniverso)} {dados.unidade} no filtro
                </p>
                <SqlToggle aberto={sqlTotal} onClick={() => setSqlTotal(!sqlTotal)} />
                <p className="text-[11.5px] text-faint">Clique numa barra para descer mais um nível.</p>
              </div>
              {sqlTotal && <SqlList sql={[dados.sqlTotal]} />}

              {dados.perfil && (
                <Painel titulo={`${descricao} · contas do recorte × resto da base`} nota="média por conta, de vw_conta (receita, suporte e uso)" sql={[dados.perfil.sql]}>
                  <table className="w-full text-[12.5px]">
                    <thead>
                      <tr className="text-left text-[11px] text-faint">
                        <th className="py-1 font-medium">Métrica</th>
                        <th className="py-1 text-right font-medium">Recorte</th>
                        <th className="py-1 text-right font-medium">Resto da base</th>
                      </tr>
                    </thead>
                    <tbody>
                      {dados.perfil.linhas.map((l) => (
                        <tr key={l.metrica} className="border-t border-edge">
                          <td className="py-1 text-muted">{l.metrica}</td>
                          <td className="py-1 text-right tabular-nums text-foreground">{l.recorte === null ? "—" : FMT[l.formato](l.recorte)}</td>
                          <td className="py-1 text-right tabular-nums text-muted">{l.resto === null ? "—" : FMT[l.formato](l.resto)}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </Painel>
              )}

              <div className="grid grid-cols-1 gap-2 md:grid-cols-2 xl:grid-cols-3">
                {dados.quebras.map((q) => (
                  <div key={q.dim} className="grid h-[250px] min-w-0">
                    <QuebraPainel quebra={q} descricao={descricao} unidade={dados.unidade} onSelect={(chave) => aprofundar(q.dim, chave)} />
                  </div>
                ))}
              </div>

              <Cruzar dados={dados} cruzar={cruzar} setCruzar={setCruzar} descricao={descricao} />

              <Painel
                titulo={`${descricao} · registros`}
                nota={`${fmtInt(Math.min(200, dados.registros.linhas.length))} de ${fmtInt(dados.registros.total)} ${dados.unidade}, os mais recentes primeiro`}
                sql={[dados.registros.sql]}
              >
                <div className="max-h-[360px] overflow-auto">
                  <table className="w-full text-[11.5px]">
                    <thead className="sticky top-0 bg-panel">
                      <tr className="text-left text-faint">
                        {dados.registros.colunas.map((c) => (
                          <th key={c} className="whitespace-nowrap py-1 pr-3 font-medium">
                            {c}
                          </th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {dados.registros.linhas.map((l, i) => (
                        <tr key={i} className="border-t border-edge">
                          {dados.registros.colunas.map((c) => (
                            <td key={c} className="max-w-[280px] truncate py-1 pr-3 text-muted" title={String(l[c] ?? "")}>
                              {String(l[c] ?? "")}
                            </td>
                          ))}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Painel>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function QuebraPainel({
  quebra,
  descricao,
  unidade,
  onSelect,
}: {
  quebra: ResultadoRecorte["quebras"][number];
  descricao: string;
  unidade: string;
  onSelect: (chave: string) => void;
}) {
  // Accounts and subscriptions: the churn rate of each value (D36), like the chart clicked; events: counts.
  const temTaxa = quebra.dados.some((d) => d.taxa !== undefined) && !/churn_flag/.test(descricao);
  const [modo, setModo] = useState<"taxa" | "qtd">(temTaxa ? "taxa" : "qtd");
  const usarTaxa = temTaxa && modo === "taxa";
  const pontos = quebra.dados.slice(0, 30).map((d) => ({ label: d.label, value: usarTaxa ? (d.taxa ?? 0) : d.value, color: usarTaxa ? LARANJA : AZUL }));
  const longo = quebra.dados.length <= 12 && quebra.dados.some((d) => d.label.length > 12);
  const porRotulo = new Map(quebra.dados.map((d) => [d.label, d.chave]));
  return (
    <Painel
      titulo={`${descricao} · por ${quebra.titulo}`}
      nota={usarTaxa ? "% com churn_flag = 1 em cada grupo" : `${unidade} em cada grupo${quebra.dados.length > 30 ? " (30 maiores)" : ""}`}
      sql={[quebra.sql]}
    >
      {temTaxa && (
        <div className="flex gap-1 text-[10.5px]" data-sem-captura>
          {(["taxa", "qtd"] as const).map((m) => (
            <button key={m} onClick={() => setModo(m)} className={`rounded border px-1.5 py-0.5 ${modo === m ? "border-accent text-accent" : "border-edge text-faint hover:text-muted"}`}>
              {m === "taxa" ? "taxa de churn" : unidade}
            </button>
          ))}
        </div>
      )}
      <Ajustado>
        {(w, h) => (
          <BarChart
            data={pontos}
            valueFormat={usarTaxa ? fmtPct : fmtInt}
            horizontal={longo}
            fit={!longo}
            showValues={!longo}
            height={h}
            viewWidth={w}
            bare
            onSelect={(label) => {
              const chave = porRotulo.get(label);
              if (chave !== undefined) onSelect(chave);
            }}
          />
        )}
      </Ajustado>
    </Painel>
  );
}

function Cruzar({
  dados,
  cruzar,
  setCruzar,
  descricao,
}: {
  dados: ResultadoRecorte;
  cruzar: [string, string] | null;
  setCruzar: (c: [string, string] | null) => void;
  descricao: string;
}) {
  const usados = new Set(dados.caminho.map((p) => p.dim));
  const livres = dados.dimensoes.filter((d) => !usados.has(d.id));
  const [escolhaA, setA] = useState(cruzar?.[0] ?? "");
  const [escolhaB, setB] = useState(cruzar?.[1] ?? "");
  // A dimension that went into the path is no longer free: fall back to the first free ones.
  const livre = (id: string) => livres.some((d) => d.id === id);
  const a = livre(escolhaA) ? escolhaA : (livres[0]?.id ?? "");
  const b = livre(escolhaB) && escolhaB !== a ? escolhaB : (livres.find((d) => d.id !== a)?.id ?? "");
  const c = dados.cruzamento;
  const max = c ? Math.max(1, ...c.celulas.flat()) : 1;
  return (
    <section className="flex flex-col gap-2 rounded-lg border border-edge bg-panel px-3 py-2">
      <div className="flex flex-wrap items-center gap-2 text-[12.5px]">
        <span className="font-semibold text-foreground">Cruzar dois atributos dentro do recorte</span>
        <select value={a} onChange={(e) => setA(e.target.value)} className="rounded border border-edge bg-background px-2 py-1 text-[12px] text-foreground">
          {livres.map((d) => (
            <option key={d.id} value={d.id}>
              {d.titulo}
            </option>
          ))}
        </select>
        <span className="text-faint">×</span>
        <select value={b} onChange={(e) => setB(e.target.value)} className="rounded border border-edge bg-background px-2 py-1 text-[12px] text-foreground">
          {livres.map((d) => (
            <option key={d.id} value={d.id}>
              {d.titulo}
            </option>
          ))}
        </select>
        <button
          onClick={() => a && b && a !== b && setCruzar([a, b])}
          disabled={!a || !b || a === b}
          className="rounded border border-edge-strong px-2 py-1 text-[11.5px] text-foreground hover:border-accent disabled:opacity-50"
        >
          Cruzar
        </button>
      </div>
      {c && (
        <Painel titulo={`${descricao} · ${c.titulo}`} nota={`${dados.unidade} em cada combinação (até 15 linhas e colunas)`} sql={[c.sql]}>
          <div className="overflow-auto">
            <table className="text-[11.5px]">
              <thead>
                <tr>
                  <th />
                  {c.colunas.map((col) => (
                    <th key={col} className="whitespace-nowrap px-2 py-1 text-right font-medium text-faint">
                      {col}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {c.linhas.map((l, i) => (
                  <tr key={l}>
                    <td className="whitespace-nowrap py-1 pr-3 text-muted">{l}</td>
                    {c.celulas[i].map((v, j) => (
                      <td
                        key={j}
                        className="px-2 py-1 text-right tabular-nums text-foreground"
                        style={{ backgroundColor: v ? `rgba(57, 135, 229, ${0.12 + 0.6 * (v / max)})` : undefined }}
                      >
                        {v ? fmtInt(v) : "·"}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Painel>
      )}
    </section>
  );
}
