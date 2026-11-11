"use client"

import { useState } from "react"

import { cn } from "@/lib/utils"

export interface FlowNode {
  id: string
  title: string
  subtitle: string
  detail: string
  kind?: "auto" | "review" | "human" | "base"
}

type Box = { x: number; y: number; w: number; h: number }
type Layout = { viewBox: string; boxes: Record<string, Box>; edges: { from: string; to: string; dashed?: boolean; label?: string; via?: "down" | "up" | "fan" | "loop" }[] }

const W = 136
const H = 64
const DESKTOP: Layout = {
  viewBox: "0 0 1050 460",
  boxes: {
    ticket: { x: 10, y: 160, w: W, h: H },
    embedding: { x: 168, y: 160, w: W, h: H },
    busca: { x: 326, y: 160, w: W, h: H },
    voto: { x: 484, y: 160, w: W, h: H },
    regra: { x: 642, y: 160, w: W, h: H },
    auto: { x: 840, y: 20, w: 170, h: H },
    review: { x: 840, y: 160, w: 170, h: H },
    human: { x: 840, y: 300, w: 170, h: H },
    base: { x: 642, y: 380, w: W, h: H },
  },
  edges: [
    { from: "ticket", to: "embedding" },
    { from: "embedding", to: "busca" },
    { from: "busca", to: "voto" },
    { from: "voto", to: "regra" },
    { from: "regra", to: "auto", via: "fan" },
    { from: "regra", to: "review", via: "fan" },
    { from: "regra", to: "human", via: "fan" },
    { from: "review", to: "base", dashed: true, via: "loop", label: "aprovação" },
    { from: "base", to: "regra", dashed: true, via: "up" },
  ],
}

const MW = 300
const MH = 58
const MOBILE: Layout = {
  viewBox: "0 0 360 760",
  boxes: {
    ticket: { x: 30, y: 10, w: MW, h: MH },
    embedding: { x: 30, y: 100, w: MW, h: MH },
    busca: { x: 30, y: 190, w: MW, h: MH },
    voto: { x: 30, y: 280, w: MW, h: MH },
    regra: { x: 30, y: 370, w: MW, h: MH },
    auto: { x: 4, y: 490, w: 112, h: 74 },
    review: { x: 124, y: 490, w: 112, h: 74 },
    human: { x: 244, y: 490, w: 112, h: 74 },
    base: { x: 30, y: 650, w: MW, h: MH },
  },
  edges: [
    { from: "ticket", to: "embedding", via: "down" },
    { from: "embedding", to: "busca", via: "down" },
    { from: "busca", to: "voto", via: "down" },
    { from: "voto", to: "regra", via: "down" },
    { from: "regra", to: "auto", via: "down" },
    { from: "regra", to: "review", via: "down" },
    { from: "regra", to: "human", via: "down" },
    { from: "review", to: "base", dashed: true, via: "down", label: "aprovação" },
  ],
}

function edgePath(a: Box, b: Box, via: Layout["edges"][number]["via"]): string {
  if (via === "down") {
    const x1 = a.x + a.w / 2
    const x2 = b.x + b.w / 2
    const y1 = a.y + a.h
    const y2 = b.y
    const my = (y1 + y2) / 2
    return x1 === x2 ? `M${x1},${y1} V${y2 - 2}` : `M${x1},${y1} V${my} H${x2} V${y2 - 2}`
  }
  if (via === "up") {
    const x = a.x + a.w / 2
    return `M${x},${a.y} V${b.y + b.h + 2}`
  }
  if (via === "fan") {
    const x1 = a.x + a.w
    const y1 = a.y + a.h / 2
    const x2 = b.x
    const y2 = b.y + b.h / 2
    const mx = (x1 + x2) / 2
    return `M${x1},${y1} H${mx} V${y2} H${x2 - 2}`
  }
  if (via === "loop") {
    // sai pela direita da Revisão humana, contorna o Somente humano por baixo e entra pela direita da base
    const y1 = a.y + a.h / 2
    const y2 = b.y + b.h / 2
    return `M${a.x + a.w},${y1} H${a.x + a.w + 22} V${y2} H${b.x + b.w + 2}`
  }
  return `M${a.x + a.w},${a.y + a.h / 2} H${b.x - 2}`
}

const STROKE: Record<NonNullable<FlowNode["kind"]> | "default", string> = {
  auto: "stroke-path-auto",
  review: "stroke-path-review",
  human: "stroke-path-human",
  base: "stroke-text-3",
  default: "stroke-border",
}

function Diagram({ layout, nodes, active, setActive, className, compact }: { layout: Layout; nodes: FlowNode[]; active: string; setActive: (id: string) => void; className?: string; compact?: boolean }) {
  const byId = Object.fromEntries(nodes.map((n) => [n.id, n]))
  return (
    <svg viewBox={layout.viewBox} className={cn("h-auto w-full", className)} role="group" aria-label="Fluxo da triagem: do ticket aos 3 caminhos">
      <defs>
        <marker id={`arrow-${compact ? "m" : "d"}`} viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
          <path d="M0,0 L8,4 L0,8 z" className="fill-text-3" />
        </marker>
      </defs>
      {layout.edges.map((e) => {
        const a = layout.boxes[e.from]
        const b = layout.boxes[e.to]
        const d = edgePath(a, b, e.via)
        return (
          <g key={`${e.from}-${e.to}`}>
            <path d={d} fill="none" className="stroke-text-3" strokeWidth={1.25} strokeDasharray={e.dashed ? "4 4" : undefined} markerEnd={`url(#arrow-${compact ? "m" : "d"})`} />
            {e.label ? (
              <text
                x={compact ? a.x + a.w / 2 + 6 : b.x + b.w + 16}
                y={compact ? a.y + a.h + 30 : b.y + b.h / 2 - 6}
                className="fill-text-3 font-mono"
                fontSize={compact ? 10 : 11}
              >
                {e.label}
              </text>
            ) : null}
          </g>
        )
      })}
      {Object.entries(layout.boxes).map(([id, b]) => {
        const n = byId[id]
        if (!n) return null
        const isActive = active === id
        const stroke = STROKE[n.kind ?? "default"]
        return (
          <g
            key={id}
            role="button"
            tabIndex={0}
            aria-pressed={isActive}
            aria-label={`${n.title}: ${n.subtitle}`}
            onMouseEnter={() => setActive(id)}
            onFocus={() => setActive(id)}
            onClick={() => setActive(id)}
            onKeyDown={(ev) => {
              if (ev.key === "Enter" || ev.key === " ") {
                ev.preventDefault()
                setActive(id)
              }
            }}
            className="cursor-pointer outline-none [&:focus-visible>rect]:stroke-[3]"
          >
            <rect
              x={b.x}
              y={b.y}
              width={b.w}
              height={b.h}
              rx={12}
              className={cn(isActive ? "fill-surface-2" : "fill-surface", n.kind ? stroke : isActive ? "stroke-text-2" : "stroke-border")}
              strokeWidth={n.kind && n.kind !== "base" ? 2 : isActive ? 1.75 : 1.25}
              strokeDasharray={n.kind === "base" ? "5 4" : undefined}
            />
            <text x={b.x + b.w / 2} y={b.y + b.h / 2 - (compact && b.w < 150 ? 8 : 5)} textAnchor="middle" className="fill-text-1 font-sans font-semibold" fontSize={compact && b.w < 150 ? 12 : 13}>
              {compact && b.w < 150 ? n.title.split(" ")[0] : n.title}
            </text>
            {compact && b.w < 150 ? (
              <text x={b.x + b.w / 2} y={b.y + b.h / 2 + 8} textAnchor="middle" className="fill-text-1 font-sans font-semibold" fontSize={12}>
                {n.title.split(" ").slice(1).join(" ")}
              </text>
            ) : null}
            <text x={b.x + b.w / 2} y={b.y + b.h / 2 + (compact && b.w < 150 ? 24 : 14)} textAnchor="middle" className="fill-text-3 font-mono" fontSize={compact && b.w < 150 ? 9 : 9.5}>
              {compact && b.w < 150 ? "" : n.subtitle}
            </text>
          </g>
        )
      })}
    </svg>
  )
}

/** Diagrama do fluxo da automação (PRD §4.7): passar o mouse, focar ou tocar numa etapa mostra a regra. */
export function FlowDiagram({ nodes, initial = "regra" }: { nodes: FlowNode[]; initial?: string }) {
  const [active, setActive] = useState(initial)
  const node = nodes.find((n) => n.id === active) ?? nodes[0]
  return (
    <div className="flex flex-col gap-4">
      <Diagram layout={DESKTOP} nodes={nodes} active={active} setActive={setActive} className="hidden md:block" />
      <Diagram layout={MOBILE} nodes={nodes} active={active} setActive={setActive} className="mx-auto max-w-sm md:hidden" compact />
      <div className="rounded-lg border border-border bg-surface-2/60 p-4" aria-live="polite">
        <p className="text-sm font-semibold text-text-1">
          {node.title} <span className="font-mono text-xs font-normal text-text-3">· {node.subtitle}</span>
        </p>
        <p className="mt-1.5 text-sm leading-relaxed text-text-2">{node.detail}</p>
      </div>
    </div>
  )
}
