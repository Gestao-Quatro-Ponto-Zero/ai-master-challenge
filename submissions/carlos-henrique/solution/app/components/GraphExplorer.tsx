"use client";

import dynamic from "next/dynamic";
import { useCallback, useMemo, useState } from "react";
import type { GraphEdge, GraphNode, JsonValue } from "@/lib/types";
import { ExplainThis, LimitationCallout, StatusBadge } from "@/components/ui";
import { humanize } from "@/lib/format";

const CytoscapeCanvas = dynamic(() => import("@/components/CytoscapeCanvas"), { ssr: false, loading: () => <div className="flex h-[34rem] items-center justify-center rounded-xl bg-slate-100 text-sm text-muted">Loading reduced graph…</div> });
type Mode = "event-flow" | "pattern-explorer" | "governance-view";
type GraphData = { modes: Record<Mode, { nodes?: GraphNode[]; edges?: GraphEdge[]; node_count?: number; edge_count?: number; truncated: boolean }> };

export function GraphExplorer({ nodeData, edgeData }: { nodeData: GraphData; edgeData: GraphData }) {
  const [mode, setMode] = useState<Mode>("event-flow");
  const [minimumSupport, setMinimumSupport] = useState(0);
  const [selectedId, setSelectedId] = useState("");
  const [topN, setTopN] = useState(35);
  const allNodes = useMemo(() => nodeData.modes[mode].nodes ?? [], [nodeData, mode]);
  const allEdges = useMemo(() => edgeData.modes[mode].edges ?? [], [edgeData, mode]);
  const edgeLimit = mode === "event-flow" ? 16 : 80;
  const edges = useMemo(() => allEdges.filter((edge) => Number(edge.properties.account_support ?? 0) >= minimumSupport).slice(0, edgeLimit), [allEdges, edgeLimit, minimumSupport]);
  const connected = useMemo(() => new Set(edges.flatMap((edge) => [edge.source, edge.target])), [edges]);
  const nodes = useMemo(() => allNodes.filter((node) => mode !== "event-flow" || connected.has(node.id)).slice(0, topN), [allNodes, connected, mode, topN]);
  const allowed = useMemo(() => new Set(nodes.map((node) => node.id)), [nodes]);
  const visibleEdges = edges.filter((edge) => allowed.has(edge.source) && allowed.has(edge.target));
  const selected = nodes.find((node) => node.id === selectedId) ?? visibleEdges.find((edge) => edge.id === selectedId);
  const handleSelect = useCallback((id: string) => setSelectedId(id), []);
  return <section className="space-y-5">
    <div className="panel flex flex-wrap items-end gap-4 p-4">
      <label className="text-sm font-medium">Graph mode<select className="input-control mt-1 block min-w-52" value={mode} onChange={(event) => { setMode(event.target.value as Mode); setSelectedId(""); }}><option value="event-flow">Event flow</option><option value="pattern-explorer">Pattern explorer</option><option value="governance-view">Governance view</option></select></label>
      <label className="text-sm font-medium">Minimum account support<input className="input-control mt-1 block w-36" type="number" min={0} value={minimumSupport} onChange={(event) => setMinimumSupport(Number(event.target.value))} /></label>
      <label className="text-sm font-medium">Top N nodes<input className="mt-2 block w-44 accent-blue" type="range" min={10} max={35} value={topN} onChange={(event) => setTopN(Number(event.target.value))} /><span className="text-xs text-muted">{topN} maximum</span></label>
      <button className="button-secondary ml-auto" onClick={() => { setMinimumSupport(0); setTopN(35); setSelectedId(""); }}>Reset</button>
    </div>
    <LimitationCallout>Graph relationships are descriptive and do not imply causality. This view is explicitly truncated to {nodes.length} nodes and {visibleEdges.length} edges.</LimitationCallout>
    <div className="grid gap-5 xl:grid-cols-[1fr_22rem]">
      <div className="panel overflow-hidden p-3"><CytoscapeCanvas nodes={nodes} edges={visibleEdges} onSelect={handleSelect} /></div>
      <aside className="panel p-5" aria-live="polite"><p className="eyebrow">Selected evidence</p>{selected ? <><div className="mt-3 flex flex-wrap items-center gap-2"><h3 className="break-all text-lg font-semibold">{"label" in selected ? selected.label : humanize(selected.type)}</h3><StatusBadge value={selected.type} /></div><dl className="mt-5 space-y-3">{Object.entries(selected.properties).slice(0, 14).map(([key, value]) => <div key={key}><dt className="data-label">{humanize(key)}</dt><dd className="mt-1 break-words text-sm text-slate-700">{typeof value === "object" ? JSON.stringify(value) : String(value)}</dd></div>)}</dl><div className="mt-5"><ExplainThis label="Explain selected graph evidence" data={{ what_was_observed: `${"label" in selected ? selected.type : selected.type} is present in the governed ${humanize(mode)} view.`, why_it_appears_here: "It passed promotion and display-volume controls.", evidence: selected.properties as JsonValue, population: "MAIN with STRICT sensitivity", denominator: Number(selected.properties.denominator_accounts ?? selected.properties.account_support ?? 0), quality: String(selected.properties.quality_population ?? "Governed analytical graph"), stability: String(selected.properties.stability_status ?? "Not applicable"), limitations: ["DESCRIPTIVE_RELATIONSHIP", "TRUNCATED_VIEW"], authorized_next_step: "Inspect linked aggregate evidence.", prohibited_interpretation: "Do not infer causality or an account-level action." }} /></div></> : <p className="mt-4 text-sm leading-6 text-muted">Select a node or edge to inspect support, population, quality, stability, and limitations.</p>}</aside>
    </div>
  </section>;
}
