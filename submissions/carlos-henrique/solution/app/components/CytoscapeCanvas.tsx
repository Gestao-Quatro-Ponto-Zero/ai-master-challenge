"use client";

import cytoscape from "cytoscape";
import { useEffect, useRef } from "react";
import type { GraphEdge, GraphNode } from "@/lib/types";

const colors: Record<string, string> = { EventType: "#315f8c", Pattern: "#b68433", Outcome: "#708253", QualityProfile: "#a85d76", Finding: "#c66b3d", Investigation: "#607089" };

export default function CytoscapeCanvas({ nodes, edges, onSelect }: { nodes: GraphNode[]; edges: GraphEdge[]; onSelect: (id: string) => void }) {
  const ref = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!ref.current) return;
    const cy = cytoscape({
      container: ref.current,
      elements: [
        ...nodes.map((node) => ({ data: { id: node.id, label: node.label, type: node.type } })),
        ...edges.map((edge) => ({ data: { id: edge.id, source: edge.source, target: edge.target, label: edge.type } }))
      ],
      style: [
        { selector: "node", style: { "background-color": (element) => colors[String(element.data("type"))] ?? "#607089", label: "data(label)", color: "#14233a", "font-size": "9px", "font-weight": 600, "text-wrap": "wrap", "text-max-width": "100px", "text-valign": "bottom", "text-margin-y": 10, width: 28, height: 28, "border-width": 2, "border-color": "#ffffff" } },
        { selector: "edge", style: { width: 1.2, "line-color": "#b9c4d2", "target-arrow-color": "#94a3b8", "target-arrow-shape": "triangle", "curve-style": "bezier", opacity: 0.55 } },
        { selector: ":selected", style: { "border-width": 4, "border-color": "#14233a", "line-color": "#14233a", "target-arrow-color": "#14233a" } }
      ],
      layout: nodes.length <= 10 ? { name: "circle", animate: false, fit: true, padding: 72, avoidOverlap: true, spacingFactor: 1.45 } as const : { name: "cose", animate: false, fit: true, padding: 40, nodeRepulsion: () => 12000, idealEdgeLength: () => 110 } as const
    });
    cy.on("tap", "node, edge", (event) => onSelect(event.target.id()));
    return () => cy.destroy();
  }, [nodes, edges, onSelect]);
  return <div ref={ref} className="h-[34rem] w-full rounded-xl bg-slate-50" role="img" aria-label={`JourneyGraph view with ${nodes.length} nodes and ${edges.length} edges`} />;
}
