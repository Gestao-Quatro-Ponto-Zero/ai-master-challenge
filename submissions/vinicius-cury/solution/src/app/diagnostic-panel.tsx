"use client";

import { useEffect, useState, useRef } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import mermaid from "mermaid";

type Scenario = "acelerar" | "desacelerar" | "redirecionar" | "quarentena" | "manter" | "liberar";

interface PairDiagnostic {
  channel: string;
  subject: string;
  scenario: Scenario;
  rPair: number | null;
  rSubject: number | null;
  divergence: string | null;
  totalTickets: number;
  closedWithCsat: number;
  avgDuration: number;
  avgCsat: number;
  impact: number;
  bestChannelForSubject: string | null;
  bestChannelCsat: number | null;
  redirectTo: string | null;
  redirectViable: boolean;
}

interface ScenarioSummary {
  scenario: Scenario;
  label: string;
  count: number;
  totalTickets: number;
  action: string;
}

interface DiagnosticData {
  pairs: PairDiagnostic[];
  scenarioSummaries: ScenarioSummary[];
  routingMatrix: Record<string, Record<string, Scenario | null>>;
  channels: string[];
  subjects: string[];
  subjectR: Record<string, number | null>;
}

const SCENARIO_CONFIG: Record<Scenario, { label: string; color: string; bg: string; border: string; symbol: string; cellBg: string }> = {
  acelerar: {
    label: "Acelerar",
    color: "text-red-800 dark:text-red-200",
    bg: "bg-red-100 dark:bg-red-900",
    border: "border-red-300 dark:border-red-700",
    symbol: "A",
    cellBg: "bg-red-200 text-red-900 dark:bg-red-800 dark:text-red-100 font-semibold",
  },
  desacelerar: {
    label: "Desacelerar",
    color: "text-blue-800 dark:text-blue-200",
    bg: "bg-blue-100 dark:bg-blue-900",
    border: "border-blue-300 dark:border-blue-700",
    symbol: "D",
    cellBg: "bg-blue-200 text-blue-900 dark:bg-blue-800 dark:text-blue-100 font-semibold",
  },
  redirecionar: {
    label: "Redirecionar",
    color: "text-orange-800 dark:text-orange-200",
    bg: "bg-orange-100 dark:bg-orange-900",
    border: "border-orange-300 dark:border-orange-700",
    symbol: "R",
    cellBg: "bg-orange-200 text-orange-900 dark:bg-orange-800 dark:text-orange-100 font-semibold",
  },
  quarentena: {
    label: "Quarentena",
    color: "text-yellow-800 dark:text-yellow-200",
    bg: "bg-yellow-100 dark:bg-yellow-900",
    border: "border-yellow-400 dark:border-yellow-600",
    symbol: "Q",
    cellBg: "bg-yellow-200 text-yellow-900 dark:bg-yellow-800 dark:text-yellow-100 font-semibold",
  },
  manter: {
    label: "Manter",
    color: "text-green-800 dark:text-green-200",
    bg: "bg-green-100 dark:bg-green-900",
    border: "border-green-300 dark:border-green-700",
    symbol: "M",
    cellBg: "bg-green-200 text-green-900 dark:bg-green-800 dark:text-green-100",
  },
  liberar: {
    label: "Liberar",
    color: "text-gray-700 dark:text-gray-300",
    bg: "bg-gray-100 dark:bg-gray-800",
    border: "border-gray-300 dark:border-gray-600",
    symbol: "L",
    cellBg: "bg-gray-200 text-gray-700 dark:bg-gray-700 dark:text-gray-300",
  },
};

function scenarioCellColor(scenario: Scenario | null): string {
  if (!scenario) return "bg-gray-50 dark:bg-gray-900 text-gray-400";
  return SCENARIO_CONFIG[scenario].cellBg;
}

function rColor(r: number | null): string {
  if (r === null) return "text-gray-400";
  if (r < -0.3) return "text-red-700 font-semibold dark:text-red-300";
  if (r < -0.1) return "text-red-600 dark:text-red-400";
  if (r > 0.3) return "text-blue-700 font-semibold dark:text-blue-300";
  if (r > 0.1) return "text-blue-600 dark:text-blue-400";
  return "text-gray-500";
}

function MermaidChart() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    mermaid.initialize({
      startOnLoad: false,
      theme: "base",
      themeVariables: {
        primaryColor: "#e2e8f0",
        primaryTextColor: "#1e293b",
        primaryBorderColor: "#94a3b8",
        lineColor: "#64748b",
        secondaryColor: "#f1f5f9",
        tertiaryColor: "#fff",
        fontSize: "13px",
      },
      flowchart: { htmlLabels: true, curve: "basis", useMaxWidth: true },
    });

    const diagram = `flowchart TD
    A["Par Canal x Assunto"] --> B{"PASSO 1\\nr(tempo, CSAT) do par"}
    B -->|"r < -0.3"| C["ACELERAR\\nMais tempo = menos satisfacao\\nAgentes rapidos"]
    B -->|"r > 0.3"| D["DESACELERAR\\nMais tempo = mais satisfacao\\nAgentes especializados"]
    B -->|"r fraco, entre -0.3 e 0.3"| E{"PASSO 2\\nCSAT do par vs\\noutros canais"}
    E -->|"CSAT bom >= 3.5"| F["MANTER\\nCanal funciona bem"]
    E -->|"CSAT ruim < melhor - 0.5"| G{"PASSO 3\\nRedirecionamento\\nviavel?"}
    E -->|"CSAT neutro\\nsem diferencial"| H["LIBERAR\\nDeprioritizar"]
    E -->|"Todos os canais ruins"| I["QUARENTENA\\nProblema do assunto"]
    G -->|"Sim"| J["REDIRECIONAR\\nEnviar para canal\\ncom melhor CSAT"]
    G -->|"Nao"| I

    style C fill:#fecaca,stroke:#dc2626,color:#991b1b
    style D fill:#bfdbfe,stroke:#2563eb,color:#1e3a5f
    style F fill:#bbf7d0,stroke:#16a34a,color:#14532d
    style H fill:#e5e7eb,stroke:#6b7280,color:#374151
    style I fill:#fef08a,stroke:#ca8a04,color:#713f12
    style J fill:#fed7aa,stroke:#ea580c,color:#9a3412`;

    const render = async () => {
      if (!containerRef.current) return;
      try {
        const { svg } = await mermaid.render("diagnostic-mermaid-v2", diagram);
        containerRef.current.innerHTML = svg;
      } catch (err) {
        console.error("Mermaid render error:", err);
        containerRef.current.innerHTML = "<p>Erro ao renderizar diagrama</p>";
      }
    };
    render();
  }, []);

  return <div ref={containerRef} className="flex justify-center overflow-x-auto" />;
}

export function DiagnosticPanel() {
  const [data, setData] = useState<DiagnosticData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/tickets/diagnostic")
      .then((r) => r.json())
      .then((d) => { setData(d); setLoading(false); })
      .catch(() => setLoading(false));
  }, []);

  if (loading || !data) {
    return <div className="text-muted-foreground text-sm">Carregando diagnóstico...</div>;
  }

  const { pairs, scenarioSummaries, routingMatrix, channels, subjects, subjectR } = data;
  const divergences = pairs.filter((p) => p.divergence);

  return (
    <>
      {/* ============================================================ */}
      {/* SECTION 5: Diagnóstico — Duas Camadas de Análise */}
      {/* ============================================================ */}
      <section className="space-y-6">
        <div>
          <h2 className="text-lg font-semibold border-b pb-2">5. Diagnóstico: Classificação da Matriz Canal × Assunto</h2>
          <p className="text-sm text-muted-foreground mt-2">
            Duas perguntas para cada par Canal × Assunto:
            <strong> (1) Tempo influencia satisfação neste par?</strong> — Pearson r entre duração e CSAT dentro do par.
            Se r forte → acelerar ou desacelerar.
            <strong> (2) Se tempo não importa: este canal é bom para este assunto?</strong> — Comparar CSAT com outros canais.
            Se pior → redirecionar (se viável) ou quarentena.
          </p>
        </div>

        {/* Mermaid decision tree */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Árvore de Decisão — Processo de Classificação</CardTitle>
            <p className="text-xs text-muted-foreground">
              Passo 1: r(tempo, CSAT) do par determina se velocidade é o fator.
              Passo 2: se tempo não importa, compara CSAT entre canais.
              Passo 3: verifica viabilidade de redirecionamento.
            </p>
          </CardHeader>
          <CardContent>
            <MermaidChart />
          </CardContent>
        </Card>

        {/* Summary cards — 6 scenarios */}
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
          {scenarioSummaries.map((s) => {
            const cfg = SCENARIO_CONFIG[s.scenario];
            return (
              <Card key={s.scenario} className={`${cfg.border} border-2`}>
                <CardHeader className="pb-1 pt-3 px-3">
                  <CardTitle className={`text-xs font-medium ${cfg.color}`}>
                    <span className={`inline-flex items-center justify-center w-5 h-5 rounded text-[10px] font-bold mr-1.5 ${cfg.cellBg}`}>
                      {cfg.symbol}
                    </span>
                    {s.label}
                  </CardTitle>
                </CardHeader>
                <CardContent className="px-3 pb-3">
                  <div className="text-xl font-bold">{s.count}</div>
                  <p className="text-xs text-muted-foreground">
                    {s.totalTickets.toLocaleString()} tickets
                  </p>
                </CardContent>
              </Card>
            );
          })}
        </div>

        {/* Routing matrix heatmap */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Matriz de Roteamento: Canal × Assunto</CardTitle>
            <p className="text-xs text-muted-foreground">
              Cada célula mostra o cenário operacional para o par baseado na árvore de decisão acima.
              Letra = cenário. Cor = ação.
            </p>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm border-collapse">
                <thead>
                  <tr>
                    <th className="p-2 text-left font-medium text-muted-foreground border-b">
                      Canal ↓ / Assunto →
                    </th>
                    {subjects.map((s) => (
                      <th
                        key={s}
                        className="p-2 text-center font-medium text-xs border-b min-w-[55px]"
                        style={{ writingMode: "vertical-rl", textOrientation: "mixed" }}
                      >
                        {s}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {channels.map((ch) => (
                    <tr key={ch}>
                      <td className="p-2 font-medium border-r whitespace-nowrap">{ch}</td>
                      {subjects.map((sub) => {
                        const scenario = routingMatrix[ch]?.[sub];
                        const pair = pairs.find((p) => p.channel === ch && p.subject === sub);
                        const cfg = scenario ? SCENARIO_CONFIG[scenario] : null;
                        return (
                          <td
                            key={sub}
                            className={`p-1.5 text-center text-xs border ${scenarioCellColor(scenario)}`}
                            title={`${ch} × ${sub}: ${cfg?.label || "—"} | r=${pair?.rPair ?? "n/a"} | CSAT=${pair?.avgCsat?.toFixed(2) ?? "n/a"}${pair?.redirectTo ? ` → ${pair.redirectTo}` : ""}`}
                          >
                            {cfg ? cfg.symbol : "—"}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {/* Legend */}
            <div className="flex flex-wrap gap-3 mt-4 text-xs">
              {(["acelerar", "desacelerar", "redirecionar", "quarentena", "manter", "liberar"] as Scenario[]).map((s) => (
                <div key={s} className="flex items-center gap-1.5">
                  <span className={`inline-flex items-center justify-center w-5 h-5 rounded text-[10px] font-bold ${SCENARIO_CONFIG[s].cellBg}`}>
                    {SCENARIO_CONFIG[s].symbol}
                  </span>
                  <span>{SCENARIO_CONFIG[s].label}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Divergences — SubR ≠ PairR */}
        {divergences.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Divergências: r do Assunto ≠ r do Par</CardTitle>
              <p className="text-xs text-muted-foreground">
                Pares onde a correlação tempo×CSAT diverge do comportamento geral do assunto.
                Estes são os sinais mais interessantes — indicam que o canal muda a dinâmica do assunto.
              </p>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b text-left">
                      <th className="pb-2 pr-4 font-medium">Canal</th>
                      <th className="pb-2 pr-4 font-medium">Assunto</th>
                      <th className="pb-2 pr-4 text-right font-medium">r Assunto</th>
                      <th className="pb-2 pr-4 text-right font-medium">r Par</th>
                      <th className="pb-2 pr-4 text-center font-medium">Cenário</th>
                      <th className="pb-2 pr-4 font-medium">Divergência</th>
                    </tr>
                  </thead>
                  <tbody>
                    {divergences.map((p) => {
                      const cfg = SCENARIO_CONFIG[p.scenario];
                      return (
                        <tr key={`${p.channel}-${p.subject}`} className="border-b last:border-0 hover:bg-muted/50">
                          <td className="py-2 pr-4 font-medium">{p.channel}</td>
                          <td className="py-2 pr-4">{p.subject}</td>
                          <td className={`py-2 pr-4 text-right ${rColor(p.rSubject)}`}>
                            {p.rSubject !== null ? p.rSubject.toFixed(3) : "n/a"}
                          </td>
                          <td className={`py-2 pr-4 text-right ${rColor(p.rPair)}`}>
                            {p.rPair !== null ? p.rPair.toFixed(3) : "n/a"}
                          </td>
                          <td className="py-2 pr-4 text-center">
                            <span className={`inline-flex items-center justify-center w-5 h-5 rounded text-[10px] font-bold ${cfg.cellBg}`}>
                              {cfg.symbol}
                            </span>
                          </td>
                          <td className="py-2 pr-4 text-xs text-muted-foreground">{p.divergence}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Full pair table */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Todos os Pares — Classificação Completa</CardTitle>
            <p className="text-xs text-muted-foreground">
              Cada par Canal × Assunto com as duas dimensões de análise: r(tempo, CSAT) e nível de CSAT.
              Ordenado por impacto absoluto (|r × volume|).
            </p>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b text-left">
                    <th className="pb-2 pr-3 font-medium">Canal</th>
                    <th className="pb-2 pr-3 font-medium">Assunto</th>
                    <th className="pb-2 pr-3 text-center font-medium">Cenário</th>
                    <th className="pb-2 pr-3 text-right font-medium">r Par</th>
                    <th className="pb-2 pr-3 text-right font-medium">r Assunto</th>
                    <th className="pb-2 pr-3 text-right font-medium">CSAT</th>
                    <th className="pb-2 pr-3 text-right font-medium">Duração</th>
                    <th className="pb-2 pr-3 text-right font-medium">Tickets</th>
                    <th className="pb-2 pr-3 text-right font-medium">Impacto</th>
                    <th className="pb-2 pr-3 font-medium">Ação</th>
                  </tr>
                </thead>
                <tbody>
                  {pairs.map((p) => {
                    const cfg = SCENARIO_CONFIG[p.scenario];
                    return (
                      <tr key={`${p.channel}-${p.subject}`} className="border-b last:border-0 hover:bg-muted/50">
                        <td className="py-1.5 pr-3 font-medium text-xs">{p.channel}</td>
                        <td className="py-1.5 pr-3 text-xs">{p.subject}</td>
                        <td className="py-1.5 pr-3 text-center">
                          <span className={`inline-flex items-center justify-center w-5 h-5 rounded text-[10px] font-bold ${cfg.cellBg}`}
                                title={cfg.label}>
                            {cfg.symbol}
                          </span>
                        </td>
                        <td className={`py-1.5 pr-3 text-right text-xs ${rColor(p.rPair)}`}>
                          {p.rPair !== null ? p.rPair.toFixed(3) : "n/a"}
                        </td>
                        <td className={`py-1.5 pr-3 text-right text-xs ${rColor(p.rSubject)}`}>
                          {p.rSubject !== null ? p.rSubject.toFixed(3) : "n/a"}
                        </td>
                        <td className={`py-1.5 pr-3 text-right text-xs ${p.avgCsat < 2.5 ? "text-red-600 font-semibold" : p.avgCsat >= 3.5 ? "text-green-600 font-semibold" : ""}`}>
                          {p.avgCsat.toFixed(2)}
                        </td>
                        <td className="py-1.5 pr-3 text-right text-xs">{p.avgDuration.toFixed(1)}h</td>
                        <td className="py-1.5 pr-3 text-right text-xs">{p.totalTickets}</td>
                        <td className="py-1.5 pr-3 text-right text-xs">
                          <span className={`px-1 py-0.5 rounded ${
                            p.impact < -5 ? "bg-red-200 text-red-900 font-semibold" :
                            p.impact < 0 ? "bg-red-50 text-red-700" :
                            p.impact > 5 ? "bg-blue-200 text-blue-900 font-semibold" :
                            p.impact > 0 ? "bg-blue-50 text-blue-700" :
                            "text-gray-400"
                          }`}>
                            {p.impact !== 0 ? p.impact.toFixed(1) : "—"}
                          </span>
                        </td>
                        <td className="py-1.5 pr-3 text-xs">
                          {p.scenario === "redirecionar" && p.redirectTo ? (
                            <span className="text-orange-700 dark:text-orange-300">→ {p.redirectTo}</span>
                          ) : p.divergence ? (
                            <Badge variant="outline" className="text-[10px] border-amber-400 text-amber-700">DIV</Badge>
                          ) : null}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </section>

      {/* ============================================================ */}
      {/* SECTION 6: Plano de Ação — Roteamento Inteligente */}
      {/* ============================================================ */}
      <section className="space-y-6">
        <div>
          <h2 className="text-lg font-semibold border-b pb-2">6. Plano de Ação: Roteamento Inteligente</h2>
          <p className="text-sm text-muted-foreground mt-2">
            Ações agrupadas por cenário. Para &quot;Acelerar&quot;: agentes rápidos. Para &quot;Desacelerar&quot;: agentes especializados.
            Para &quot;Redirecionar&quot;: canal destino especificado. Para &quot;Quarentena&quot;: investigar causa raiz.
            Para &quot;Manter&quot;: não mexer. Para &quot;Liberar&quot;: realocar recursos.
          </p>
        </div>

        {(["acelerar", "desacelerar", "redirecionar", "quarentena", "manter", "liberar"] as Scenario[]).map((scenario) => {
          const cfg = SCENARIO_CONFIG[scenario];
          const scenarioPairs = pairs.filter((p) => p.scenario === scenario);
          if (scenarioPairs.length === 0) return null;

          const summary = scenarioSummaries.find((s) => s.scenario === scenario);

          return (
            <Card key={scenario} className={`${cfg.border} border`}>
              <CardHeader className="pb-2">
                <CardTitle className={`text-base ${cfg.color} flex items-center gap-2`}>
                  <span className={`inline-flex items-center justify-center w-6 h-6 rounded text-xs font-bold ${cfg.cellBg}`}>
                    {cfg.symbol}
                  </span>
                  {cfg.label} — {scenarioPairs.length} pares, {scenarioPairs.reduce((s, p) => s + p.totalTickets, 0).toLocaleString()} tickets
                </CardTitle>
                <p className="text-xs text-muted-foreground">{summary?.action}</p>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b text-left">
                        <th className="pb-2 pr-3 font-medium">Canal</th>
                        <th className="pb-2 pr-3 font-medium">Assunto</th>
                        <th className="pb-2 pr-3 text-right font-medium">r(tempo,CSAT)</th>
                        <th className="pb-2 pr-3 text-right font-medium">CSAT</th>
                        <th className="pb-2 pr-3 text-right font-medium">Duração</th>
                        <th className="pb-2 pr-3 text-right font-medium">Tickets</th>
                        {scenario === "redirecionar" && (
                          <th className="pb-2 pr-3 font-medium">Destino</th>
                        )}
                        {(scenario === "acelerar" || scenario === "desacelerar") && (
                          <th className="pb-2 pr-3 text-center font-medium">Diverge?</th>
                        )}
                      </tr>
                    </thead>
                    <tbody>
                      {scenarioPairs.map((p) => (
                        <tr key={`${p.channel}-${p.subject}`} className="border-b last:border-0 hover:bg-muted/50">
                          <td className="py-1.5 pr-3 font-medium">{p.channel}</td>
                          <td className="py-1.5 pr-3">{p.subject}</td>
                          <td className={`py-1.5 pr-3 text-right ${rColor(p.rPair)}`}>
                            {p.rPair !== null ? p.rPair.toFixed(3) : "n/a"}
                          </td>
                          <td className={`py-1.5 pr-3 text-right ${p.avgCsat < 2.5 ? "text-red-600 font-semibold" : p.avgCsat >= 3.5 ? "text-green-600 font-semibold" : ""}`}>
                            {p.avgCsat.toFixed(2)}
                          </td>
                          <td className="py-1.5 pr-3 text-right">{p.avgDuration.toFixed(1)}h</td>
                          <td className="py-1.5 pr-3 text-right">{p.totalTickets}</td>
                          {scenario === "redirecionar" && (
                            <td className="py-1.5 pr-3">
                              <span className="text-orange-700 dark:text-orange-300 font-medium">
                                → {p.redirectTo} <span className="text-xs text-muted-foreground">(CSAT {p.bestChannelCsat?.toFixed(2)})</span>
                              </span>
                            </td>
                          )}
                          {(scenario === "acelerar" || scenario === "desacelerar") && (
                            <td className="py-1.5 pr-3 text-center">
                              {p.divergence ? (
                                <Badge variant="outline" className="text-[10px] border-amber-400 text-amber-700" title={p.divergence}>DIV</Badge>
                              ) : null}
                            </td>
                          )}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </section>
    </>
  );
}
