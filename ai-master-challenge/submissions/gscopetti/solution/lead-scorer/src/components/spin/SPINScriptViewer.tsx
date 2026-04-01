import { useSPINReports } from '@/hooks/useSPINGenerator';
import { getTierInfo } from '@/utils/tiers';
import type { PipelineOpportunity, Account, Product, DealScore } from '@/types';
import { useState } from 'react';

interface SPINScriptViewerProps {
  dealScores: DealScore[];
  pipeline: PipelineOpportunity[];
  accounts: Account[];
  products: Product[];
}

export function SPINScriptViewer({
  dealScores,
  pipeline,
  accounts,
  products,
}: SPINScriptViewerProps) {
  const { reports } = useSPINReports(dealScores, pipeline, accounts, products);
  const [selectedReport, setSelectedReport] = useState(reports[0] || null);

  if (reports.length === 0) {
    return (
      <div className="bg-slate-800 rounded-lg border border-slate-700 p-6">
        <p className="text-slate-400">
          Nenhum deal com score ≥ 40 para gerar scripts SPIN.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Reports List */}
      <div className="bg-slate-800 rounded-lg border border-slate-700 p-4">
        <h3 className="font-bold text-lg mb-4">📋 Scripts SPIN Disponíveis</h3>
        <p className="text-xs text-slate-400 mb-3">{reports.length} deals com score ≥ 40</p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-h-96 overflow-y-auto">
          {reports.map((report) => {
            const tierInfo = getTierInfo(report.deal_score.tier);
            const isSelected = selectedReport?.deal_score.opportunity_id === report.deal_score.opportunity_id;

            return (
              <button
                key={report.deal_score.opportunity_id}
                onClick={() => setSelectedReport(report)}
                className={`p-3 rounded-lg border-2 transition text-left ${
                  isSelected
                    ? `${tierInfo.bgColor} border-white`
                    : 'bg-slate-900 border-slate-700 hover:border-slate-500'
                }`}
              >
                <div className="flex justify-between items-start">
                  <div>
                    <p className="font-bold text-sm">{report.deal_score.product}</p>
                    <p className="text-xs text-slate-300">
                      {report.context.accountName || 'Prospect'}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-sm">{report.deal_score.score}</p>
                    <p className="text-xs">{tierInfo.badge}</p>
                  </div>
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Selected Report Script */}
      {selectedReport && (
        <div className="bg-slate-800 rounded-lg border border-slate-700 p-6 space-y-6">
          {/* Header */}
          <div>
            <div className="flex justify-between items-start mb-4">
              <div>
                <h2 className="text-2xl font-bold">
                  {selectedReport.context.accountName || 'Prospect'}
                </h2>
                <p className="text-slate-400">
                  {selectedReport.deal_score.product} • {selectedReport.deal_score.deal_stage}
                </p>
              </div>
              <div className="text-right">
                <p className="text-4xl font-bold text-white">
                  {selectedReport.deal_score.score}
                </p>
                <p className="text-lg">{getTierInfo(selectedReport.deal_score.tier).badge}</p>
              </div>
            </div>

            {/* Quick Context */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-2 text-sm">
              {selectedReport.context.sector && (
                <div className="p-2 bg-slate-900 rounded">
                  <p className="text-xs text-slate-400">Setor</p>
                  <p className="font-bold text-sm">{selectedReport.context.sector}</p>
                </div>
              )}
              {selectedReport.context.employees && (
                <div className="p-2 bg-slate-900 rounded">
                  <p className="text-xs text-slate-400">Tamanho</p>
                  <p className="font-bold text-sm">
                    {(selectedReport.context.employees ?? 0).toLocaleString()}
                  </p>
                </div>
              )}
              {selectedReport.context.winRate !== undefined && (
                <div className="p-2 bg-slate-900 rounded">
                  <p className="text-xs text-slate-400">Win Rate</p>
                  <p className="font-bold text-sm">
                    {((selectedReport.context.winRate ?? 0) * 100).toFixed(0)}%
                  </p>
                </div>
              )}
              {selectedReport.context.totalDeals && (
                <div className="p-2 bg-slate-900 rounded">
                  <p className="text-xs text-slate-400">Deals</p>
                  <p className="font-bold text-sm">{selectedReport.context.totalDeals}</p>
                </div>
              )}
            </div>
          </div>

          {/* SPIN Script */}
          <div className="border-t border-slate-700 pt-6 space-y-4">
            {/* Situação */}
            <div>
              <h3 className="font-bold text-blue-400 mb-2">📍 SITUAÇÃO</h3>
              <p className="text-slate-200 leading-relaxed">
                {selectedReport.spin_script.situation}
              </p>
            </div>

            {/* Problema */}
            <div>
              <h3 className="font-bold text-yellow-400 mb-2">❓ PROBLEMA</h3>
              <p className="text-slate-200 leading-relaxed">
                {selectedReport.spin_script.problem}
              </p>
            </div>

            {/* Implicação */}
            <div>
              <h3 className="font-bold text-orange-400 mb-2">💥 IMPLICAÇÃO</h3>
              <p className="text-slate-200 leading-relaxed">
                {selectedReport.spin_script.implication}
              </p>
            </div>

            {/* Necessidade-Payoff */}
            <div>
              <h3 className="font-bold text-green-400 mb-2">🎯 NECESSIDADE-PAYOFF</h3>
              <p className="text-slate-200 leading-relaxed">
                {selectedReport.spin_script.need_payoff}
              </p>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="border-t border-slate-700 pt-4 flex gap-2">
            <button
              onClick={() => {
                const text = `${selectedReport.context.accountName}\n\n[S] SITUAÇÃO\n${selectedReport.spin_script.situation}\n\n[P] PROBLEMA\n${selectedReport.spin_script.problem}\n\n[I] IMPLICAÇÃO\n${selectedReport.spin_script.implication}\n\n[N] NECESSIDADE-PAYOFF\n${selectedReport.spin_script.need_payoff}`;
                navigator.clipboard.writeText(text);
                alert('✅ Script copiado para clipboard!');
              }}
              className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm flex-1"
            >
              📋 Copiar Script
            </button>
            <button
              onClick={() => {
                console.log('=== SELECTED REPORT ===', selectedReport);
                alert('✅ Relatório completo logado no console. Pressione F12 para ver.');
              }}
              className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-white rounded-lg text-sm flex-1"
            >
              🔍 Ver Detalhes
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
