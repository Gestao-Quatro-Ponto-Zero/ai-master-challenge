"use client";

import { useState } from "react";
import { type ScoredDeal, scoreLabel } from "@/lib/scoring";
import { getActionTag, getUrgencyNote } from "@/lib/actions";
import { ScoreBadge } from "./ScoreBadge";

const PAGE_SIZE = 100;

interface DealTableProps {
  deals: ScoredDeal[];
  onRowClick: (deal: ScoredDeal) => void;
  onScoreClick?: (deal: ScoredDeal) => void;
}

function formatCurrency(value: number): string {
  if (value === 0) return "—";
  if (value >= 1000) return `$${(value / 1000).toFixed(1)}k`;
  return `$${value.toLocaleString()}`;
}

const stagePill: Record<string, string> = {
  Engaging:    "bg-blue-500/15 text-blue-400 border-blue-500/30",
  Prospecting: "bg-gray-500/15 text-gray-400 border-gray-500/30",
};

const priorityColor: Record<string, string> = {
  "Alta prioridade":  "text-emerald-400",
  "Média prioridade": "text-amber-400",
  "Baixa prioridade": "text-red-400",
};


export function DealTable({ deals, onRowClick, onScoreClick }: DealTableProps) {
  const [page, setPage] = useState(0);
  const totalPages = Math.ceil(deals.length / PAGE_SIZE);
  const paginated = deals.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE);
  const globalOffset = page * PAGE_SIZE;

  if (deals.length === 0) {
    return (
      <div className="text-center py-20 text-gray-500">
        <p className="text-lg">Nenhum deal encontrado com os filtros aplicados.</p>
      </div>
    );
  }

  return (
    <>
      <div className="overflow-x-auto rounded-xl border border-gray-800">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-800 bg-gray-900/80">
              <th className="hidden sm:table-cell text-left px-4 py-3 text-gray-400 font-medium whitespace-nowrap">#</th>
              <th className="text-left px-4 py-3 text-gray-400 font-medium whitespace-nowrap">Conta</th>
              <th className="hidden md:table-cell text-left px-4 py-3 text-gray-400 font-medium whitespace-nowrap">Produto</th>
              <th className="hidden sm:table-cell text-right px-4 py-3 text-gray-400 font-medium whitespace-nowrap">Ticket</th>
              <th className="text-left px-4 py-3 text-gray-400 font-medium whitespace-nowrap">Stage</th>
              <th className="text-right px-4 py-3 text-gray-400 font-medium whitespace-nowrap">Dias</th>
              <th className="hidden md:table-cell text-left px-4 py-3 text-gray-400 font-medium whitespace-nowrap">Vendedor</th>
              <th className="text-center px-4 py-3 text-gray-400 font-medium whitespace-nowrap">Score</th>
            </tr>
          </thead>
          <tbody>
            {paginated.map((deal, idx) => {
              const action = getActionTag(deal);
              const urgency = getUrgencyNote(deal);
              const label = scoreLabel(deal.score);
              const lblClass = priorityColor[label] ?? "text-gray-400";

              return (
                <tr
                  key={deal.opportunity_id}
                  onClick={() => onRowClick(deal)}
                  className={`
                    border-b border-gray-800/50 transition-colors cursor-pointer
                    ${idx % 2 === 0 ? "bg-gray-950" : "bg-gray-900/30"}
                    hover:bg-gray-800/60
                  `}
                >
                  <td className="hidden sm:table-cell px-4 py-3 text-gray-600 tabular-nums">
                    {globalOffset + idx + 1}
                  </td>

                  {/* Conta + action tag + urgency */}
                  <td className="px-4 py-3">
                    <div className="flex items-center gap-2 flex-wrap">
                      <span className="font-medium text-white">
                        {deal.account || <span className="text-gray-600 italic">Sem conta</span>}
                      </span>
                      <span className={`shrink-0 text-[10px] font-medium px-1.5 py-0.5 rounded border ${action.style}`}>
                        {action.label}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 mt-0.5 flex-wrap">
                      {deal.account_revenue > 0 && (
                        <span className="text-xs text-gray-500">${deal.account_revenue.toFixed(0)}M rev</span>
                      )}
                      {urgency && (
                        <span className={`text-[10px] font-medium ${
                          deal.score >= 70 && deal.days_in_stage <= 30
                            ? "text-emerald-500/70"
                            : "text-amber-500/70"
                        }`}>{urgency}</span>
                      )}
                    </div>
                  </td>

                  <td className="hidden md:table-cell px-4 py-3 text-gray-300 whitespace-nowrap">{deal.product}</td>

                  <td className="hidden sm:table-cell px-4 py-3 text-right tabular-nums text-gray-300 whitespace-nowrap">
                    {formatCurrency(deal.product_price)}
                  </td>

                  <td className="px-4 py-3">
                    <span className={`inline-block px-2 py-0.5 rounded-full border text-xs font-medium whitespace-nowrap ${
                      stagePill[deal.deal_stage] ?? stagePill.Prospecting
                    }`}>
                      {deal.deal_stage}
                    </span>
                  </td>

                  <td className="px-4 py-3 text-right tabular-nums">
                    <span className={
                      deal.days_in_stage > 90 ? "text-red-400 font-semibold" :
                      deal.days_in_stage > 30 ? "text-amber-400" : "text-gray-300"
                    }>
                      {deal.days_in_stage}
                    </span>
                  </td>

                  <td className="hidden md:table-cell px-4 py-3 text-gray-400 whitespace-nowrap">{deal.sales_agent}</td>

                  {/* Score + priority label */}
                  <td
                    className="px-4 py-3 text-center"
                    onClick={(e) => { e.stopPropagation(); if (onScoreClick) { onScoreClick(deal); } else { onRowClick(deal); } }}
                  >
                    <div className="flex flex-col items-center gap-0.5">
                      <ScoreBadge score={deal.score} />
                      <span className={`text-[9px] font-semibold leading-none ${lblClass}`}>
                        {label.split(" ")[0]}
                      </span>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between mt-4 px-1">
          <p className="text-sm text-gray-500">
            {globalOffset + 1}–{Math.min(globalOffset + PAGE_SIZE, deals.length)} de {deals.length} deals
          </p>
          <div className="flex items-center gap-1">
            <button onClick={() => setPage((p) => Math.max(0, p - 1))} disabled={page === 0}
              className="px-3 py-1.5 text-sm rounded-lg border border-gray-700 text-gray-400 hover:text-white hover:border-gray-500 disabled:opacity-30 disabled:cursor-not-allowed transition-colors">
              ← Anterior
            </button>
            {Array.from({ length: totalPages }, (_, i) => (
              <button key={i} onClick={() => setPage(i)}
                className={`w-8 h-8 text-sm rounded-lg transition-colors ${
                  i === page ? "bg-blue-600 text-white" : "text-gray-400 hover:bg-gray-800 border border-gray-700"
                }`}>
                {i + 1}
              </button>
            ))}
            <button onClick={() => setPage((p) => Math.min(totalPages - 1, p + 1))} disabled={page === totalPages - 1}
              className="px-3 py-1.5 text-sm rounded-lg border border-gray-700 text-gray-400 hover:text-white hover:border-gray-500 disabled:opacity-30 disabled:cursor-not-allowed transition-colors">
              Próxima →
            </button>
          </div>
        </div>
      )}
    </>
  );
}
