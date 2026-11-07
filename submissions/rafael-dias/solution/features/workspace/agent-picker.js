"use client";

import { useEffect, useRef, useState } from "react";
import { sortAgentsByOpen } from "../../lib/portfolio.mjs";
export default function AgentPicker({
  agents,
  agent,
  onChange,
  data,
  openCounts,
}) {
  const [open, setOpen] = useState(false),
    [query, setQuery] = useState("");
  const root = useRef(null),
    input = useRef(null);
  const counts =
    openCounts ||
    Object.fromEntries(
      agents.map((a) => [
        a,
        data.opportunities.filter((d) => d.sales_agent === a).length,
      ]),
    );
  const rankedAgents = sortAgentsByOpen(agents, counts);
  useEffect(() => {
    if (!open) return;
    input.current?.focus();
    const close = (e) => {
      if (!root.current?.contains(e.target)) setOpen(false);
    };
    const key = (e) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("pointerdown", close);
    document.addEventListener("keydown", key);
    return () => {
      document.removeEventListener("pointerdown", close);
      document.removeEventListener("keydown", key);
    };
  }, [open]);
  return (
    <div ref={root} className="agent-picker">
      <button
        className="agent-trigger"
        aria-label={`Trocar vendedor: ${agent}`}
        aria-expanded={open}
        onClick={() => {
          setOpen(!open);
          setQuery("");
        }}
      >
        <span className="avatar">
          {agent
            .split(" ")
            .map((x) => x[0])
            .slice(0, 2)
            .join("")}
        </span>
        <span>
          <small>CARTEIRA EM FOCO</small>
          <strong>{agent}</strong>
        </span>
        <span className="picker-chevron">⌄</span>
      </button>
      {open && (
        <section className="agent-popover" aria-label="Escolher carteira">
          <h3>De quem é a carteira?</h3>
          <p className="picker-sort-note">
            Mais oportunidades abertas primeiro
          </p>
          <input
            ref={input}
            aria-label="Buscar vendedor"
            placeholder="Buscar nome, gestor ou região…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <div className="agent-options">
            {rankedAgents
              .filter((a) => {
                const t = (data.historicalByAgent || []).find(
                  (t) => t.sales_agent === a,
                );
                return `${a} ${t?.manager || ""} ${t?.regional_office || ""}`
                  .toLowerCase()
                  .includes(query.toLowerCase());
              })
              .map((a) => {
                const t = (data.historicalByAgent || []).find(
                    (t) => t.sales_agent === a,
                  ),
                  n = counts[a] || 0;
                return (
                  <button
                    className={a === agent ? "selected" : ""}
                    key={a}
                    aria-pressed={a === agent}
                    onClick={() => {
                      onChange(a);
                      setOpen(false);
                    }}
                  >
                    <span className="avatar">
                      {a
                        .split(" ")
                        .map((x) => x[0])
                        .slice(0, 2)
                        .join("")}
                    </span>
                    <span>
                      <strong>{a}</strong>
                      <small>
                        {t?.regional_office} · {t?.manager}
                      </small>
                    </span>
                    <span className="agent-count">
                      {n}
                      <small>abertas</small>
                    </span>
                    {a === agent && <span>✓</span>}
                  </button>
                );
              })}
            {!agents.some((a) => {
              const t = (data.historicalByAgent || []).find(
                (t) => t.sales_agent === a,
              );
              return `${a} ${t?.manager || ""} ${t?.regional_office || ""}`
                .toLowerCase()
                .includes(query.toLowerCase());
            }) && <p>Nenhum vendedor encontrado.</p>}
          </div>
          <p className="picker-footnote">
            Carteiras originais do CRM · 35 vendedores · sem redistribuição
          </p>
        </section>
      )}
    </div>
  );
}
