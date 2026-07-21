import { loadData } from "@/lib/data";
import { DataFreshness, SectionHeader } from "@/components/ui";
import { GraphExplorer } from "@/components/GraphExplorer";
import type { GraphEdge, GraphNode } from "@/lib/types";

interface NodeData { cutoff: string; modes: Record<"event-flow" | "pattern-explorer" | "governance-view", { nodes: GraphNode[]; node_count: number; truncated: boolean }> }
interface EdgeData { cutoff: string; modes: Record<"event-flow" | "pattern-explorer" | "governance-view", { edges: GraphEdge[]; edge_count: number; truncated: boolean }> }

export default async function GraphPage() {
  const [nodes, edges] = await Promise.all([loadData<NodeData>("graph_nodes.json"), loadData<EdgeData>("graph_edges.json")]);
  return <div><SectionHeader eyebrow="JourneyGraph" title="Impact without the hairball." description="Explore only promotable analytical relationships across event flow, patterns, and governance. Every mode is bounded, filtered, and descriptive." /><DataFreshness cutoff={nodes.cutoff} /><div className="mt-7"><GraphExplorer nodeData={nodes} edgeData={edges} /></div></div>;
}
